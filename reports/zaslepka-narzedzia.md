# Przegląd mutacyjny nie dochodził do końca (6.B35)

**Zmierzone 07.09.2026 na commicie:** `5c10764783b61d823d4f7ae2c403ea05ed9f073a`
(gałąź `claude/6b35-zaslepka-narzedzia`).

## 1. Objaw: kod 2, zanim policzy pierwszą mutację

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py --workers 2
[MUTACJE] 2 mutacji do policzenia, 2 robotników, commit 5c10764, klasy operator,prog,…
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] PRZERWANE — zestaw PADA w czystym drzewie, bez żadnej mutacji (kod 1):
  ['test_every_module_delegates_to_the_one_runner:',
   'test_every_test_module_can_be_run_directly:']
  — dopóki tak jest, każda mutacja zostanie zapisana jako zabita, a przegląd nie
  mierzy niczego
KOD_WYJSCIA=2
```

Dwie nazwy w nawiasie to bramka `test_module_entrypoints.py`, czyli **6.D25 — moja
własna pozycja**. Żąda ona od każdego `test_*.py` wykonywalnego strażnika `__main__`
delegującego do `test_all`. `OWN_TESTS_STUB` — treść, którą `neutralise_own_tests`
wpisuje w miejsce `tools/tests/test_mutation_sweep.py` w **każdym** drzewie roboczym —
była samym docstringiem, więc w każdym takim drzewie zestaw padał, a kalibracja
przerywała przegląd.

**Narzędzie było niesprawne od scalenia 6.D25 i nikt tego nie zauważył**, bo od tamtej
pory nikt nie odpalił pełnego przeglądu. Znalazło to 6.B20 (#359), potwierdziłem
osobno na treści zaślepki, a niezależnie natknęła się na to 6.B16 (#360), która musiała
użyć lokalnego, niecommitowanego obejścia, żeby cokolwiek zmierzyć.

## 2. Rzecz, którą warto powiedzieć wprost: kalibracja zadziałała

To nie jest awaria bez pointy. Wyrocznia tego narzędzia brzmi „zestaw padł, czyli
mutacja została wykryta" — i jest prawdziwa **tylko wtedy**, gdy zestaw nie pada bez
mutacji. Gdyby kalibracji nie było, przegląd zameldowałby **100 % zabić** i nic w
wyniku by tego nie zdradziło; sto procent wygląda jak sukces. Zdarzyło się to już dwa
razy (OOM 02.09.2026, kasacja pliku 05.09.2026) i za drugim razem nie było żadnej
obrony. Dziś obrona zadziałała: narzędzie **odmówiło** zamiast skłamać w stronę
„wszystko w porządku".

## 3. Poprawka: zaślepka jest pełnoprawnym modułem testowym

Trzy rzeczy, każda wymuszona przez inną regułę, i każda **zmierzona**, nie założona:

| co | dlaczego | zmierzone |
|---|---|---|
| strażnik `__main__` z delegacją | bramka 6.D25 żąda od każdego `test_*.py` | KN-1 niżej |
| co najmniej jeden test | `test_all.main(<plik>)` odmawia przy zerze testów | KN-2 niżej |
| asercja w tym teście | `assertion_gate` liczy test bez asercji jako PORAŻKĘ (#139) | pilnuje nowy test |

Zaślepka niesie więc docstring, **jeden test tożsamości** (mówiący, czym ten plik jest)
i strażnik. Docstring wyjaśnia, dlaczego wszystkie trzy są konieczne — bo bez tego
zdania następny, kto będzie chciał „uprościć" zaślepkę do samego docstringu, zrobi to
samo, co ja przy 6.D25.

## 4. Stan po zmianie — pełny przegląd DOSZEDŁ do końca

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py --workers 2
[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów)
[MUTACJE] 2 mutacji do policzenia, 2 robotników, commit 5c10764, klasy operator,prog,logika,argument,przypisanie
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] sonda pokrycia: jeden przebieg zestawu z licznikiem wierszy
[MUTACJE] wykonywanych wierszy dotyczy 2 z 2 mutacji; pozostałe 0 siedzą w kodzie, którego zestaw nie uruchamia
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0 (w tym 0 nieuruchomionych), nierozstrzygniętych 0
KOD_WYJSCIA=0
```

Dziennik ma dwa wiersze, po jednym na mutację. `--list` też kończy się kodem 0.

## 5. Ile testów ma zestaw w drzewie roboczym — pomiar, o który prosiło pole „Wyjście"

Pole żądało sprawdzenia, czy zaślepka z jednym testem nie zmienia liczby, na której
stoi kalibracja. Zmierzone na prawdziwym drzewie roboczym `git worktree`, z zaślepką
wpisaną dokładnie tak, jak robi to narzędzie:

```
zaslepka NOWA (docstring + 1 test + straznik):   1785 testow, 99 modulow, kod 0
zaslepka ze straznikiem, ale BEZ testu:          1784 testow, 98 modulow, kod 0
```

Czyli **+1 test i +1 moduł** wobec wariantu bez testu. Dla kalibracji jest to bez
znaczenia i **to też jest zmierzone, a nie wywnioskowane**: `baseline_problem` czyta
werdykt `run_suite`, nie liczbę testów —

```python
passed, failed, code = run(worktree, timeout)
if passed is True:
    return None
```

— a `run_suite` szuka wiersza podsumowania i pyta o `padło/przeszło`. Liczba testów
w drzewie roboczym jest o 68 mniejsza niż w repozytorium (69 prawdziwych testów
narzędzia zastąpione jednym) i była o 69 mniejsza przed tą poprawką.

## 6. Kontrole negatywne — WYKONANE, dwie

```
KN-1  zaslepka wraca do samego docstringu
      $ mutation_sweep.py --only tools/blender/lod_paths.py --workers 2
      [MUTACJE] PRZERWANE — zestaw PADA w czystym drzewie, bez żadnej mutacji (kod 1):
        ['test_every_module_delegates_to_the_one_runner:',
         'test_every_test_module_can_be_run_directly:']
      KOD_WYJSCIA=2
      + bramka: FAIL test_the_stub_is_a_full_test_module_not_just_a_docstring

KN-2  zaslepka ze straznikiem, ale BEZ ani jednego testu
      $ python3 tools/tests/test_mutation_sweep.py     (w drzewie roboczym)
      RAZEM 0.000 s, 0 testow, 0 modulow
      FAIL <bramka asercji>: nie odkryto ani jednego testu — bramka nie ma na co patrzec
      kod: 1
      a nowa zaslepka w tym samym miejscu: RAZEM 1 testow, 1 modulow, kod: 0
```

**KN-1 dowodzi, że to poprawka odblokowała przegląd**, a nie zbieg okoliczności: ta
sama komenda, na tym samym commicie, różni się wyłącznie treścią zaślepki i wraca
kodem 2 z tymi samymi dwiema nazwami.

**KN-2 dowodzi, że sam strażnik nie wystarcza** — i to jest ta połowa, którą łatwo
pominąć: zestaw w drzewie roboczym przechodzi (kod 0) także z zaślepką bez testu, więc
przegląd by ruszył. Dopiero **droga pojedynczego modułu** — ta, którą 6.D25 kazała
zrównać z drogą zestawu — kończy się wtedy kodem 1. Zaślepka spełniająca literę
bramki, ale nie jej sens, byłaby więc niesprawnością następnego rodzaju.

## 7. Asercja, która przybijała usterkę — przepisana, nie skasowana

`test_przygotowanie_drzewa_zdejmuje_testy_narzedzia_nie_kasujac_pliku` żądał:

```python
assert "def test_" not in tresc, tresc
assert ast.parse(tresc).body and isinstance(
    ast.parse(tresc).body[0], ast.Expr), "zaślepka ma być samym docstringiem"
```

To ta asercja trzymała usterkę na miejscu. **Intencja zostaje ta sama** — prawdziwej
treści testów narzędzia w zaślepce nie ma — i to ona jest sprawdzana dziś: zaślepka
niesie dokładnie jeden test, i to test tożsamości, a nie żaden z prawdziwych.

Nowy test kształtu czyta zaślepkę **tym samym przyrządem, który ją odrzucił**:
`ma_straznik()` i `DELEGACJA` z `test_module_entrypoints.py`. Bramka widzi tylko pliki
LEŻĄCE w drzewie, a zaślepka powstaje dopiero w drzewie roboczym przeglądu — i to jest
dokładnie ta luka, w której usterka mogła żyć dobę.

## 8. Weryfikacja

```
$ python3 tools/tests/test_mutation_sweep.py
  69/69 przeszło

$ python3 tools/tests/test_all.py
  RAZEM 73.844 s, 1856 testów, 99 modułów
kod: 0
```

1856 = 1855 + **1** (jeden test kształtu w istniejącym module). Zestawy C# nietknięte.

## 9. Czego świadomie nie zrobiono

- **Nie rozluźniono bramki z 6.D25** — pole „Poza zakresem". Ona ma rację: moduł
  testowy bez strażnika kończył się kodem 0, nie wykonawszy ani jednego testu, i po to
  powstała. Usterka była w zaślepce, nie w bramce.
- **Nie zmieniono niczego w tym, CO przegląd mierzy** — ani operatorów, ani limitu
  czasu, ani sondy pokrycia.
- **Nie dopisano bramki uruchamiającej `main()` narzędzia.** To 6.B37, wpisana do
  kolejki właśnie dlatego, że ta usterka przeżyła dobę: żaden test nie chodzi drogą
  narzędzia, wszystkie wołają funkcje wewnętrzne.

## 10. Co zauważone przy okazji, nietknięte

- **Sonda pokrycia zajęła większość tych dziesięciu minut**, tak jak zmierzyła 6.B20
  (416,7–426,6 s z 534,3–600,3 s). Pełny przegląd dwóch mutacji trwa więc dziś tyle,
  ile trwa — i to jest osobna pozycja (6.B36), nie skutek uboczny tej poprawki.
