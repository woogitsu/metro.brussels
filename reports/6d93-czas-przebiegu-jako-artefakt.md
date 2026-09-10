# Czas przebiegu wychodzi z joba jako artefakt (10.09.2026)

**Zmierzone 10.09.2026 na:** `b596a68` lokalnie i na przebiegu CI gałęzi
(`e3e22f3`, scalanka `4fafbf0`), kontener tej sesji i runner `metro-wsl-DOM-NEW-02`.
**Przyrząd:** `tools/tests/test_all.py` (`zapisz_czasy`), nowy
`tools/ci/timing_record.py`, nowy `tools/tests/test_timing_record.py`,
`.github/workflows/python-tests.yml`, API artefaktów GitHuba.

---

## 1. Stan przed

`tools/tests/test_all.py:533` wypisywał „czas per moduł (malejąco)" przy każdym
przebiegu, a `python-tests.yml` nie miał **ani jednego** kroku `upload-artifact`
(pozostałe osiem workflowów ma). Trend czasu istniał więc wyłącznie w logu
pojedynczego przebiegu, a lista `POMIARY` w `test_suite_runtime_budget.py` jest
uzupełniana ręcznie i rośnie tylko wtedy, gdy ktoś o niej pamięta.

## 2. Co powstało

- `test_all.py` zapisuje czasy **maszynowo**, ale wyłącznie gdy poprosi go o to
  zmienna `METRO_TIMING_OUT`. Bez zmiennej nie powstaje żaden plik — zapis do drzewa
  przy każdym przebiegu byłby dokładnie tym oknem, które 6.D90 zmierzyło jako mylące
  dla równoległej kontroli czystości, a `git clean -ffdx` z checkoutu i tak zabrałby
  go przy następnym przebiegu.
- `tools/ci/timing_record.py` dokłada to, czego proces zestawu nie zna: czas ściany
  i **czas CPU dzieci**, mierzony przez powłokę wbudowanym `times` (6.D42 — w `$(...)`
  daje zera), oraz ich stosunek.
- Krok CI ustawia zmienną na ścieżkę w `$RUNNER_TEMP`, skleja artefakt **PRZED**
  werdyktem czasu i wynosi go z `if: always()`. Obie decyzje mają ten sam powód:
  przebieg przekraczający próg jest dokładnie tym, którego czasy chce się obejrzeć.

## 3. Odczytany artefakt z prawdziwego przebiegu

Pole „Skończone, gdy" żąda sprawdzenia na przebiegu CI, nie lokalnie. Przebieg
`34466369899`, job `tools`, artefakt `czas-zestawu` (1971 B spakowany, 9976 B
rozpakowany):

```
{'schema': 1, 'commit': '4fafbf0ab3e3254a55e87039210a6f35e31602f6',
 'runner': 'metro-wsl-DOM-NEW-02', 'workflow': 'Python tool tests',
 'python': '3.14.4', 'wall_s': 51.672, 'odkryte': 2178, 'wykonane': 2178,
 'modulow': 116, 'wall_powloki_s': 52.324, 'cpu_s': 81.83, 'cpu_na_sciane': 1.564}

wpisów modułów:            116
suma testów w modułach:   2178
```

**Wpisów jest 116, czyli tyle, ile modułów przebieg wykonał wedle własnego
podsumowania**, i suma testów w nich zgadza się z `wykonane` co do jedności. Nie jest
to lista dziesięciu najwolniejszych — pięć najszybszych modułów też w niej stoi,
z czasem `0.0 s`.

```
pięć najwolniejszych:
    test_dotnet_version.py     9.053 s   (38 testów)
    test_mutation_sweep.py     8.656 s  (114 testów)
    test_station_layout.py     3.975 s   (17 testów)
    test_curve_radius_axes.py  3.805 s   (14 testów)
    test_ci_workflows.py       3.307 s   (76 testów)
```

Wypis kroku CI, dla porównania z zawartością pliku:

```
  [CZAS] zapisano /home/mateusz/actions-runner-metro-02/_work/_temp/czas-modulow.json
czas sciany test_all.py: 52.324 s (prog 150.0 s)
czas CPU zestawu: 81.830 s
[CZAS] …/czas-zestawu.json: 116 modułów, 2178 testów, ściana 52.324 s,
       CPU 81.83 s, CPU/ściana 1.564
czas sciany 52.324 s w progu 150.0 s, stosunek CPU/sciana 1.564 (podloga 0.75)
```

Kod wyjścia joba: **success**, tak samo jak przed pozycją.

## 4. Trzy rzeczy, których nie dało się zobaczyć bez tego artefaktu

- **Runner ma Pythona 3.14.4**, a kontener tej sesji 3.11.15. Różnica dwóch wydań
  większych stała dotąd wyłącznie w logu, którego nikt nie zestawiał.
- **Ten sam zestaw chodzi na runnerze dwa razy szybciej**: 52,3 s ściany wobec
  103,2 s w kontenerze. Porównywanie czasów między maszynami bez metadanych byłoby
  więc czytaniem różnicy sprzętu jako regresu kodu — dlatego nazwa runnera i stosunek
  CPU/ściana są w pliku, a nie w komentarzu.
- **`commit` w artefakcie to SHA SCALANKI** (`4fafbf0`), nie wierzchołka gałęzi
  (`e3e22f3`), bo `GITHUB_SHA` w zdarzeniu `pull_request` wskazuje scalankę. To jest
  poprawne i zgodne z §9: zielony job mówi o scalance nazwanej w jego własnym logu,
  więc artefakt ma nazywać dokładnie to, co job liczył.

## 5. Sześć kontroli negatywnych, `md5sum -c: OK` po każdej — dwie ZIELONE

Cache bajtkodu czyszczony przed każdym przebiegiem (6.D86).

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | zapis bierze tylko dziesięć najwolniejszych modułów | **czerwona** 5/6 |
| KN-2 | zapis powstaje ZAWSZE, pod ustaloną nazwą w `/tmp` | **zielona** — bramka patrzyła nie tam |
| KN-2b | ta sama mutacja, po dodaniu wypisu `[CZAS] zapisano` | **czerwona** 5/6 |
| KN-3 | sklejenie artefaktu przeniesione PO werdykt | **czerwona** 5/6 |
| KN-4 | krok artefaktu bez `if: always()` | **czerwona** 5/6 |
| KN-5 | zapis idzie do workspace zamiast do `$RUNNER_TEMP` | **zielona** — asercja pasowała do innego miejsca |
| KN-5b | ta sama mutacja, po zawężeniu asercji do WARTOŚCI zmiennej | **czerwona** 5/6 |
| KN-6 | `scal` przestaje odmawiać zerowej ściany | **czerwona** 5/6 |

**KN-2 wyszła zielona i to jest znalezisko o mojej własnej bramce.** Asercja brzmiała
„po przebiegu bez zmiennej nie ma pliku POD ŻĄDANĄ ŚCIEŻKĄ" — a mutacja zapisywała pod
inną, ustaloną nazwą w `/tmp`. Bramka sprawdzała więc ścieżkę, o którą sama poprosiła,
i nie miała jak zobaczyć zapisu obok. Zestaw zapisuje teraz wiersz `[CZAS] zapisano
<ścieżka>`, a kontrola czyta wypis dziecka: mutacja czerwienieje, bo wiersz pada tam,
gdzie pojawić się nie miał. Wiersz jest przy okazji użyteczny w logu CI.

**KN-5 wyszła zielona z tego samego powodu, tylko po stronie YAML-a.** Asercja pytała,
czy `$RUNNER_TEMP/` pada gdziekolwiek w ciele kroku — a pada tam dwa razy, więc zapis
przeniesiony do workspace nadal ją zadowalał przez argument `--in` stojący niżej.
Asercja wyciąga teraz **wartość** `METRO_TIMING_OUT` i żąda, żeby to ONA zaczynała się
od `$RUNNER_TEMP/`, plus sprawdza, że sklejenie czyta dokładnie ten plik.

**KN-6 pokazała, że odmowa nie była odmową**: przy zerowej ścianie `scal` wywracał się
dopiero na dzieleniu, więc czytający dostawał `ZeroDivisionError` zamiast zdania.
Asercja rozróżnia teraz odmowę od wyjątku arytmetycznego i mówi to wprost.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_timing_record.py
  -> 6/6 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 104,327 s, 2178 testów, 116 modułów, kod 0
  -> 2178/2178 przeszło
```

Zestaw **2172 → 2178**, moduły **115 → 116**. Zapadka `MIN_REPORTS` została w tym
commicie podniesiona ze dwustu jedenastu na dwieście dwanaście — słownie, bo
`test_report_claims.py` czyta pierwszą liczbę po nazwie stałej jako twierdzenie o jej
bieżącej wartości.

## 7. Czego świadomie nie zrobiłem

Nie tknąłem `SUITE_RUNTIME_BUDGET_S` ani `werdykt` — pole „Poza zakresem" wyklucza
jedno i drugie, a 6.D42 jest zrobione. **Nie zautomatyzowałem porównywania przebiegów
z różnych maszyn**: pole „Poza zakresem" wyklucza to bez metadanych, a metadane
dopiero od dziś istnieją — pierwszy artefakt nie jest jeszcze szeregiem. Nie ruszyłem
listy `POMIARY`: jest uzupełniana ręcznie i tak zostaje, bo jej zmiana wymagałaby
tknięcia bramki budżetu.

Nie zrealizowałem drugiej połowy propozycji audytu („raport czasu nie zmienia werdyktu
mutanta") — pole „Czego ta pozycja NIE robi" wyjaśnia dlaczego, i pomiar to potwierdza:
`mutation_sweep.run_suite` czyta z procesu zestawu wyłącznie `N/M przeszło` i kod
wyjścia, więc czas na werdykt nie wpływa i nie ma czego rozdzielać.

## 8. Zauważone i nietknięte

Artefakt ma `retention-days: 30`, czyli szereg czasowy będzie miał trzydzieści dni
pamięci. To wystarcza, żeby zobaczyć regres, i nie wystarcza, żeby zobaczyć trend
kwartalny; zbieranie ich w jedno miejsce jest osobną robotą i nie ma dziś pozycji.

Czasy pięciu najszybszych modułów wychodzą jako `0.0 s` — rozdzielczość zapisu to
milisekunda, a te moduły są od niej szybsze. Dla trendu to bez znaczenia, ale suma
takich wpisów nie jest sumą czasu przebiegu i nikt nie powinien jej tak czytać.
