# 6.D351 · Podproces kosztuje w bramkach tyle, ile kosztuje CZYTANIE KOLEJKI — `doctor.sh` płaci 157 s z 200, z czego ok. 9 s na przebieg to cztery odczyty `docs/TASKS.md`

**Data:** 23.09.2026 · **Gałąź:** `claude/6d351-koszt-podprocesow` · **Baza:** `ac50600`

Pozycja **liczy i rozbija**. Nie usuwa żadnego podprocesu, niczego nie zastępuje atrapą,
nie rusza `doctor.sh` ani zapadek czasu.

Przyrząd: `sitecustomize.py` podłożony zestawowi przez `PYTHONPATH`. Owija
`subprocess.Popen.__init__` i `subprocess.Popen.wait`. Każde uruchomienie zapisuje moduł
testowy ze stosu wywołań, pierwsze cztery elementy `argv` i czas od startu do `wait`.
Dzieci nie są instrumentowane (zmienna `PODPROC_DZIECKO`), więc podproces podprocesu
wlicza się w czas rodzica, a nie jako osobne wywołanie. Jeden pełny przebieg
`test_all.py` na bazie `ac50600`: 2664/2664, kod 0, 615 zapisów.

Poza `subprocess` szukałem też `os.system`, `os.popen`, `os.exec*`, `os.spawn*`,
`pty` i `create_subprocess`. W modułach testowych nie ma ani jednego wywołania. Trzy
trafienia wyszukiwarki to komentarz, słowo `empty.` i docstring.

---

## 1. Kontrola przyrządu ZDANA co do tysięcznej — ale dopiero po odtworzeniu, CO było „dniem” w 6.D332

Pole żądało, żeby oba moduły z 6.D341 §8 wyszły w klasie „startuje podproces”, a ich
łączny przyrost wyniósł **17,774 s**. Pierwsze podejście dało **16,944 s**:

```
dzien = data URUCHOMIENIA przebiegu w UTC
2026-09-14 n= 41   2026-09-20 n= 57
RAZEM 16.944  [6.D341: 17,774]
```

Nie poprawiałem liczby, tylko szukałem, czym różni się czytnik. Liczności nie zgadzały
się z 6.D332 §3.1 (tam n=42 i n=48), więc różnica jest w tym, **które artefakty
należą do dnia**. Sprawdziłem cztery warianty przydziału: data przebiegu albo artefaktu,
w UTC albo w CEST. Żaden nie dał obu median naraz. Rozstrzygnęły dwa fakty:

- 6.D332 jest z **20.09.2026**, czyli pobierało artefakty W TRAKCIE dnia 20.09. Po
  posortowaniu artefaktów z 20.09 po czasie utworzenia pierwsze 48 kończy się
  o 19:58:53 UTC, a 49. powstał o 20:28:59 UTC.
- Przebieg 34791207467 wystartował 13.09 o 23:58:28 UTC, a jego artefakt powstał
  **14.09 o 00:00:38 UTC**. Dniem w 6.D332 jest więc data ARTEFAKTU, nie przebiegu.

Z tymi dwiema regułami mediany odtwarzają się co do trzeciego miejsca, a kontrola
przechodzi:

```
2026-09-14 n=42 cpu 209.425 wall 133.272
2026-09-20 n=48 cpu 357.408 wall 253.407
test_doctor_queue_claim.py    12.450 ->  24.131  +11.681  klasa podproces: True
test_doctor_test_log.py        0.000 ->   6.093   +6.093  klasa podproces: True
RAZEM +17.774 s   [6.D341: 17,774]
```

Obie liczby referencyjne 6.D332 (209,425 i 357,408 s CPU) oraz 6.D341 (133,272
i 253,407 s ściany) wychodzą z tego samego zbioru. Zbiór jest więc ten sam, a nie
tylko zgodny w jednej liczbie.

## 2. Cztery liczby, których żądało pole

```
modulow z podprocesem 24   wywolan 614   czas podprocesow 199.5 s
wywolan w samym test_all.py: 1   (git ls-files, 0,005 s)
```

1. **Modułów, które startują podproces: 24** ze 139. Moduł `test_suite_runtime_budget.py`
   ma w tekście słowo `subprocess`, ale tylko w komentarzu, i w przebiegu nie startuje
   niczego.
2. **Wywołań w jednym przebiegu: 614** z modułów testowych, **615** razem z jednym
   wywołaniem samego `test_all.py`.
3. **Wywołań POWTÓRNYCH.** Liczba zależy od tego, co uznać za „ten sam skrypt”, więc
   podaję obie granice:
   - skrypt z repozytorium wołany po ścieżce bezwzględnej: **96 wywołań 10 skryptów,
     z tego 86 powtórnych**. Sam `doctor.sh` to **37 wywołań, 36 powtórnych, 157,12 s**;
   - każdy program z pierwszym argumentem (`git log`, `python -c`, …): **550
     powtórnych z 614**.
   **Wywołań powtórnych jest dużo, ale cache systemu plików nic tu nie tłumaczy.**
   Trzy kolejne przebiegi `bash doctor.sh --no-tests` dały 10,714 / 10,527 / 10,321 s,
   więc drugi start nie jest wyraźnie tańszy od pierwszego. Rozrzut czasów bierze się
   z GAŁĘZI, którą doctor idzie, nie z pamięci podręcznej (§3).
4. **Udział w medianie ściany zestawu**, czyli suma median modułów z podprocesem
   dzielona przez medianę ściany dnia:

   ```
   2026-09-14  79.262 s / 133.272 s = 59.5 %
   2026-09-20 138.051 s / 253.407 s = 54.5 %
   ```

   Suma median nie jest medianą sumy (6.D341 §1), więc to jest udział przybliżony.
   Na pojedynczym artefakcie `main` z 23.09 (ac50600) wychodzi 53,1 %.

Lista imienna, moduł · wywołań · czas podprocesów w przebiegu z instrumentacją:

```
  test_dotnet_version.py                       39   112.65 s
  test_doctor_queue_claim.py                    3    33.00 s
  test_mutation_sweep.py                      168    11.56 s
  test_doctor_test_log.py                       7    11.51 s
  test_commit_claims.py                         9    10.03 s
  test_next_task.py                             5     5.75 s
  test_report_claims.py                       260     3.65 s
  test_platform_length_in_pipeline.py           3     2.54 s
  test_detail_layout.py                         2     2.10 s
  test_mass_copies.py                           2     1.83 s
  test_bytecode_staleness.py                   16     1.17 s
  test_ci_workflows.py                         40     1.03 s
  test_module_entrypoints.py                    7     0.73 s
  test_runner_process_exit.py                   7     0.69 s
  test_vertical_profile.py                      4     0.27 s
  test_conflict_markers.py                     12     0.23 s
  test_timing_record.py                         2     0.23 s
  test_shot_metadata_gate.py                    3     0.20 s
  test_assertion_gate.py                        4     0.17 s
  test_godot_warning_gate.py                    3     0.10 s
  test_validate_axis.py                         1     0.04 s
  test_line_trace_gate.py                       9     0.02 s
  test_engine_version.py                        4     0.02 s
  test_runner_options.py                        4     0.01 s
```

**Trzy moduły, które wołają `doctor.sh`, płacą 157,12 s z 199,5 s czasu podprocesów,
czyli 79 %.** Wszystkie pozostałe wywołania, a jest ich 577, kosztują razem 42 s.

## 3. GŁÓWNE ZNALEZISKO: koszt `doctor.sh` to nie start i nie sprawdzanie narzędzi, tylko cztery odczyty kolejki

Pole ostrzegało, żeby nie brać kosztu podprocesu za koszt tego, co podproces liczy.
Rozdzieliłem to i wyszło **odwrotnie niż zakładała rodzina „cudzego skryptu”**. Start
kosztuje prawie nic, a prawie cały koszt to praca, i to praca, która z narzędziami
nie ma nic wspólnego.

Czasy 37 wywołań `doctor.sh` z przebiegu z instrumentacją są **dwumodalne**:

```
test_doctor_queue_claim.py 3 ['12.49', '10.27', '10.24']
test_doctor_test_log.py 7 ['2.13', '1.92', '1.49', '1.51', '1.49', '1.45', '1.52']
test_dotnet_version.py 27 ['1.25', '10.08', '1.16', '1.18', '1.24', '10.31', ...]
```

Śledzenie `bash -x` jednego pełnego przebiegu, osiem najdłuższych kroków:

```
3.53 ++ python3 -c '... import test_backlog as B; print(len(B.do_wziecia(io.open("docs/TASKS.md", ...
1.83 ++ python3 -c '... import test_backlog as B; print(", ".join(B.czeka_na_wlasciciela(io.open("...
1.80 ++ python3 -c '... import test_backlog as B; t = io.open("docs/TASKS.md", encoding="utf-8 ...
1.76 ++ python3 -c '... import test_backlog as B; print(len(B.open_items(io.open("docs/TASKS.md", ...
0.65 + blender --background --python-expr pass
0.17 ++ dotnet --version
0.14 ++ /root/.dotnet/dotnet --version
0.14 ++ cut -d. -f1
```

Te same cztery polecenia wyjęte z `doctor.sh` i uruchomione osobno, z wyczyszczonym
bajtkodem, trzy razy:

```
4 1.80 1.77 3.58 1.83 suma 8.97  sam import 0.02  pusty python 0.012
4 1.69 1.71 3.54 1.82 suma 8.77  sam import 0.02  pusty python 0.012
4 1.77 1.85 3.41 1.67 suma 8.70  sam import 0.02  pusty python 0.011
```

`doctor.sh` z atrapą SDK 8.0.100, czyli z wymaganym sprawdzeniem niespełnionym (wtedy
sekcja kolejki się nie wykonuje; w wypisie zero wierszy o kolejce):

```
1.483 s   1.421 s   1.435 s
```

Rozbicie jednego pełnego przebiegu `doctor.sh`, ok. 10,5 s:

| część | koszt | skąd |
|---|---|---|
| start interpretera ×4 | 0,05 s | `python3 -c pass` = 0,012 s |
| import `test_backlog` ×4 | 0,08 s | 0,02 s na import |
| **cztery parsowania `docs/TASKS.md`** | **8,7–9,0 s** | `open_items` ~1,75 s, `do_wziecia` ~3,5 s |
| reszta doctora (narzędzia, wersje, Blender) | ~1,4 s | przebieg z atrapą starego SDK |

Stąd dwumodalność. Wywołanie po 1,2–1,5 s to doctor zatrzymany atrapą, zanim dojdzie
do kolejki, a wywołanie po ~10 s to doctor, który do niej doszedł. **12 z 37 wywołań dochodzi do kolejki** (trzy w
`test_doctor_queue_claim.py`, dziewięć w `test_dotnet_version.py`) i te dwanaście
kosztuje razem 125,50 s ze 157,12. Po ~9 s na odczyt kolejki daje to ok. 105–108 s
samego czytania `docs/TASKS.md`.

**To jest też odpowiedź na pytanie, dlaczego ta rodzina drożeje.** Koszt wywołania
nie rośnie z liczbą testów ani z `doctor.sh`, tylko z **długością `docs/TASKS.md`**
(dziś 16 797 wierszy). Każda nowa pozycja kolejki podnosi go w każdym z 12 wywołań.
6.D341 §8 nazwało te dwa moduły jedynymi w dziesiątce, „które nie czytają ani prozy,
ani drzewa”. Zmierzone: **czytają prozę**, tylko pośrednio, przez skrypt, który ją
czyta.

## 4. Założenia, które pole i 6.D341 niosły, sprawdzone

Przewidywań przed pomiarem nie spisałem, więc tej sekcji nie nazywam przewidywaniami.
Są to trzy założenia wyczytane z pola i z 6.D341 §8, każde z wynikiem:

| założenie | skąd | wynik |
|---|---|---|
| koszt tej rodziny to „uruchomienie cudzego skryptu” | 6.D341 §8 | **obalone**: start i sondy to ~1,4 s, odczyt kolejki ~9 s |
| powtórne wywołanie może być tańsze o cache systemu plików | pole „Czego NIE wolno przyjąć” | **niepotwierdzone**: 10,714 / 10,527 / 10,321 s; rozrzut robi gałąź, nie cache |
| oba moduły „nie czytają ani prozy, ani drzewa” | 6.D341 §8 | **obalone**: czytają `docs/TASKS.md` przez `doctor.sh` |

## 5. Czego świadomie nie zrobiłem

- **Nie zmieniłem `doctor.sh` ani żadnej bramki.** Dwie oczywiste drogi to jeden odczyt
  kolejki zamiast czterech albo atrapa `docs/TASKS.md` w testach, które pytają o SDK,
  a nie o kolejkę. Obie są zmianą bramek i decyzją właściciela, i obie są poza
  zakresem tej pozycji.
- **Nie mierzyłem, dlaczego jedno `open_items` na 16 797 wierszach trwa ~1,75 s.**
  To pytanie o `test_backlog.py`, nie o podprocesy. Zapisałem je jako 6.D358.
- **Nie liczyłem udziału na CPU.** Artefakt `czas-zestawu` nie ma per-modułowego CPU
  (6.D341 §1), więc udział jest udziałem ściany.

## 6. Co zauważyłem przy okazji, ale nie tknąłem

Przy PR #757 `tools` dał `cpu_s = 487,2 s` na tym samym runnerze, na którym `main`
z tą samą bazą dał 407,3 s. Spowolnienie rozłożyło się na moduły, których PR nie
dotyka, a w tym samym oknie na maszynie chodziły joby Blendera. To jest rozrzut
opisany w 6.D332 §1, a nie nowy przypadek. Zapisuję go tylko dlatego, że wyszedł
przy tej pozycji.
