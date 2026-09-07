# Moduł testowy uruchomiony wprost (6.D25)

**Zmierzone 07.09.2026 na commicie:** `c28630d9d635cddb55c9195b3273096e0d75b6a5`
(gałąź `claude/6d25-modul-wprost`).

## 1. Stan wyjściowy: kod 0 przy zerze wykonanych testów

Pozycja wzięła się z mojej własnej kontroli negatywnej przy 6.A18. Opcja została zdjęta
z tabeli `KnownOptions`, bramka uruchomiona wprost:

```
$ python3 tools/tests/test_runner_options.py
kod: 0
```

i odczytałem to jako „bramka się nie zapala". Nieprawda — moduł nie miał strażnika
`__main__`, więc uruchomiony wprost wykonał same definicje, **zero testów**, i skończył
się zerem, nieodróżnialnie od przebiegu, w którym wszystko przeszło. Ta sama kontrola
przez `test_all.py` dała `FAIL` wskazujący wpis po nazwie.

## 2. Ile tego było — i dlaczego pierwsza liczba była zła

Raport 6.A18 podał „84 z 89". **Liczba była zaniżona, bo zmierzyłem ją grepem:**

```
$ grep -l '__main__' tools/tests/test_*.py | wc -l
5
$ python3 - <<'EOF'   # ten sam katalog, przez ast, strażniki na poziomie modułu
modulow test_*.py: 91
z WYKONYWALNYM straznikiem __main__ (ast, poziom modulu): 2
    tools/tests/test_all.py
    tools/tests/test_reference_snapshot.py
EOF
```

Trzy z pięciu trafień grepa to **nie strażniki**: słowo `__main__` w prozie docstringów
(`test_braking`, `test_ci_workflows`) i w **danych testowych** `test_mutation_sweep.py`,
który sprawdza, że generator mutacji nie mutuje strażnika — więc trzyma jego tekst jako
napis. Prawdziwa proporcja to **89 z 91**, czyli usterka była szersza, niż ją opisałem.

To jest na temat, nie na marginesie: przyrząd, którym mierzyłem usterkę przyrządów, miał
**tę samą wadę** — patrzył na tekst, nie na strukturę. Bramka z tej pozycji czyta `ast`
i ma na to osobny test z modułem, w którym `__main__` występuje wyłącznie w prozie.

## 3. Kształt rozwiązania: jedna droga, nie 91 kopii

Pole „Wyjście" dawało dwa warianty — wspólny przebiegacz albo odmowa z kodem różnym od
zera. Wybrany jest **wspólny przebiegacz**, bo odmowa naprawiłaby kłamstwo, nie odruch:
`python3 tools/tests/<moduł>.py` jest naturalnym sposobem sprawdzenia jednej bramki
i ma po prostu działać.

`test_all.py` dostał jeden parametr:

```
$ python3 tools/tests/test_all.py test_runner_options
  5/5 przeszło
  RAZEM 0.004 s, 5 testów, 1 modułów
kod: 0
```

`only` zawęża **wyłącznie odkrywanie**. Licznik asercji, werdykt, wypis i kod wyjścia są
tą samą drogą, co dla całego zestawu — więc przebieg jednego modułu nie może być
łagodniejszy od przebiegu wszystkich. Odmowa przy zerze testów jest za darmo, bo
`AG.suite_verdict` już ją miał.

Strażnik w modułach jest **identyczny** i deleguje do tego jednego przebiegacza; osobny
test tego pilnuje. Własna pętla po `globals()` w każdym module byłaby 91 kopiami
przebiegacza — a jedna z nich **już istniała**:

```python
# tools/tests/test_reference_snapshot.py, przed tą zmianą
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        ...
    print("\n  PythonReference.cs == tools/physics/reference.py, co do bitu")
    return 0
```

i miała **dokładnie tę usterkę**, przed którą ta pozycja broni: gdyby `globals()`
przestało dawać funkcje `test_`, pętla nie miałaby czego wykonać, wypisała „co do bitu"
i zwróciła **0**. Zero testów meldowane jako zgodność co do bitu jest gorsze od
czerwonego kroku CI. Zamienione na wspólny przebiegacz; krok CI
(`python3 tools/tests/test_reference_snapshot.py` w `sim-tests.yml`) nadal jest bramką,
a przy okazji zyskał licznik asercji, którego ta pętla nie miała.

Rozbiór wiersza poleceń stoi w **strażniku** `test_all.py`, nie w `main()`. To nie jest
szczegół stylu: `main()` bez argumentu woła `mutation_sweep.py` (podproces bez
argumentów) i `test_assertion_gate.py` (wprost, w tym samym procesie) — argparse
w `main()` wyjmowałby argumenty spod tamtych dwóch wywołań, a `mutation_sweep.py:572`
opisuje już raz przeżyty `SystemExit` z argparse wychodzący poza `test_all.py`.

## 4. Uruchomienie wprost wyciągnęło DWIE usterki, których nikt nie widział

Pętla po wszystkich modułach — czyli kryterium „Skończone, gdy" tej pozycji, wykonane
na wszystkich 91, a nie na przykładzie — znalazła dwa moduły, które wprost nie działały:

**`test_dimension_audit.py` — `ModuleNotFoundError: No module named 'station_components'`.**
Moduł wkładał do `sys.path` `tools/blender`, a `station_components` leży w `tools/track`.
Działał **wyłącznie w całym zestawie**, bo `test_all.py` wkłada obie ścieżki, zanim
cokolwiek zaimportuje — czyli jechał na cudzym `sys.path`. Dopisana brakująca linia.
Zależność od kolejności ładowania jest w zestawie testów usterką sama w sobie i nie
zgłosiłoby jej nic, dopóki jedynym sposobem uruchomienia był cały zestaw.

**`test_assertion_gate.py::test_gate_instrumented_this_suite_for_real` — `FAIL: 161`.**
Test brzmiał `assert AG.sites() > 3000`, a `AG.sites()` liczy miejsca asercji
**załadowane w tym przebiegu**, nie miejsca na drzewie. Dopóki jedynym sposobem
uruchomienia był cały zestaw, obie liczby były tą samą liczbą. Rozdzielony na dwie
asercje: że instrumentacja **tego** przebiegu zadziałała (`sites() > 0`) i że drzewo ma
ponad 3000 miejsc — to drugie liczone wprost z plików przez `ast` (**4609** na dziś),
więc niezależne od tego, ile modułów wczytał akurat ten przebieg. Wyszło z tego
mocniejsze niż jedna asercja, bo pilnuje obu rzeczy osobno.

## 5. Kryterium „Skończone, gdy" — pętla po wszystkich 91

```
$ for f in tools/tests/test_*.py; do out=$(python3 "$f" 2>&1); kod=$?; \
      n=$(printf '%s' "$out" | grep -oE '[0-9]+ testów' | head -1 | grep -oE '^[0-9]+'); \
      [ "$kod" != 0 ] || [ -z "$n" ] || [ "$n" = 0 ] && echo "PROBLEM: $f kod=$kod testow=${n:-brak}"; done
modulow: 91, z problemem: 0, suma testow z przebiegow pojedynczych: 3535
```

Suma 3535 przy zestawie liczącym 1790 testów **nie jest błędem** i warto powiedzieć,
dlaczego, zamiast zostawić liczbę, która wygląda na podwójne liczenie: w pętli jest też
`tools/tests/test_all.py`, a on bez argumentu uruchamia **cały** zestaw. Rozłożone:

```
caly zestaw:                            1790
suma pojedynczych bez test_all.py:      1745
test_all jako JEDEN modul:                45
                                   1745 + 45 = 1790
```

Przebiegi pojedynczych modułów **dzielą zestaw dokładnie** — ani jeden test nie jest
liczony dwa razy i ani jeden nie wypada.

## 6. Kontrole negatywne — WYKONANE

```
KN-1  straznik zdjety z tools/tests/test_lod_paths.py
      FAIL test_every_test_module_can_be_run_directly: modul testowy bez straznika
      `__main__` — uruchomiony wprost skonczy sie kodem 0, nie wykonawszy ani jednego
      testu: tools/tests/test_lod_paths.py
      FAIL test_every_module_delegates_to_the_one_runner: ... tools/tests/test_lod_paths.py

KN-2  straznik z WLASNA petla po globals() zamiast delegacji
      FAIL test_every_module_delegates_to_the_one_runner: straznik nie deleguje do
      wspolnego przebiegacza (test_all.main(__file__)): tools/tests/test_lod_paths.py
```

Oba nazywają moduł po nazwie. Po przywróceniu — zielono.

Dwie dalsze kontrole nie są jednorazowe: **są testami** i chodzą przy każdym przebiegu.
Moduł piaskownicy **bez ani jednego testu**, uruchomiony wprost, musi skończyć się
kodem różnym od zera i wypisem `nie odkryto ani jednego testu`; nazwa modułu
z literówką musi być odmową, nie pustym przebiegiem. Sprawdzane **wykonaniem**
w podprocesie, nie odczytaniem kodu — bo o to właśnie poszło w §1.

**Pierwsza wersja tego testu wisiała 300 s do timeoutu**, bo uruchamiała w podprocesie
*ten sam plik*, czyli siebie — rekursja bez dna. Dlatego oba przebiegi idą na modułach
piaskownicy z jednego szablonu, a nie na prawdziwych plikach zestawu.

## 6a. Bramka zapaliła się na cudzej zmianie, zanim wyszła z gałęzi

Nie kontrola negatywna, tylko pierwsze prawdziwe użycie. Podczas przestawiania tej
gałęzi na `main` wszedł `tools/tests/test_constant_names.py` z 6.B25 — moduł dopisany
**po** wygenerowaniu strażników:

```
  FAIL test_every_test_module_can_be_run_directly: modul testowy bez straznika
  `__main__` — uruchomiony wprost skonczy sie kodem 0, nie wykonawszy ani jednego
  testu: tools/tests/test_constant_names.py
  FAIL test_every_module_delegates_to_the_one_runner: ... tools/tests/test_constant_names.py
```

Zapadka zadziałała na tym, po co jest: nowy moduł bez strażnika nie przechodzi. To jest
też odpowiedź na pytanie, czy 91 strażników nie zgnije — nie zgnije, bo 92. wymaga
dopisania strażnika w tym samym commicie.

## 7. Weryfikacja

```
$ python3 tools/tests/test_all.py
  RAZEM 98.882 s, 1796 testów, 92 modułów
kod: 0
```

Czas jest wyższy od tego z wcześniejszych dzisiejszych przebiegów (65–67 s) i **nie
jest to koszt tej zmiany** — ale to zdanie wymagało pomiaru, nie wnioskowania, bo
pierwsze wyjaśnienie („nowa bramka zajmuje 0,5 s, więc to sąsiedztwo") nie odpowiadało
na skok o **32 s**. Trzy kolejne przebiegi dały 98,9 / 100,9 / 102,1 s, a wcześniejsze
trzy 66,8 / 66,9 / 67,4 s — stabilnie po obu stronach, więc szumem to nie jest.
Kandydatów było dwóch: regres wprowadzony gdzieś około 6.A18 albo obciążenie maszyny.

Rozstrzygnięte przez zmierzenie **tego samego modułu w dwóch drzewach**,
`test_station_layout.py`, na który przypada cały skok (22,7 s → 35,3 s):

```
=== PRZED 6.A18 (a6463db) ===
test_station_layout: 34.86 s, 17 testow
=== main (ma 6.A18) ===
test_station_layout: 34.91 s, 17 testow
```

**34,86 s i 34,91 s** — ten sam moduł jest dziś równie wolny w drzewie sprzed 6.A18,
więc żaden commit go nie zwolnił; zwolniła maszyna. Ten sam moduł mierzy 22,7 s albo
34,9 s w zależności od obciążenia hosta, czyli **1,54× rozrzutu**, i to jest liczba
warta zapamiętania przy czytaniu każdego progu czasowego w tym repozytorium. Próg
zestawu ma nadal zapas i mieszka w `test_suite_runtime_budget.py`, nie tutaj — ale
zapisany tam **pomiar** maksimum jest niższy od tego, co maszyna dziś pokazuje, i to
jest osobna pozycja kolejki.

## 8. Czego świadomie nie zrobiono

- **Zamiany zestawu na `pytest` albo `unittest`** — pole „Poza zakresem" tej pozycji.
  To zmiana zależności i przebiegacza (`CLAUDE.md` §8).
- **Nie tknięto `MEASURED_MAX_WALL_S`.** Dzisiejszy przebieg jest wyższy niż zapisany
  tam pomiar, ale to sąsiedztwo maszyny, nie regres — a dat pomiarów się nie przelicza.
- **Nie ruszono `mutation_sweep.py`.** Woła `test_all.py` jako podproces **bez
  argumentów**, więc jego droga jest niezmieniona; sprawdzone tym, że jego 65 testów
  przechodzi, a nie założeniem.
- **Nie dopisano bramki na jazdę po cudzym `sys.path`** — i to jest pozycja, którą
  **odwołałem po zmierzeniu**, zamiast wpisać ją do kolejki. Pierwsze przejście dało
  „5 modułów importuje z katalogu, którego same nie wstawiają" i wyglądało na
  znalezisko. Nieprawda: przyrząd szukał napisów **wewnątrz** wywołania `sys.path.insert`,
  a `test_tuning_constants.py` i `test_parameter_boundaries.py` wstawiają ścieżki
  **pętlą** — nazwy katalogów stoją w krotce nad wywołaniem, nie w nim. Trzy pozostałe
  trafienia importowały rodzeństwo z `tools/tests`, czyli z katalogu skryptu, który przy
  uruchomieniu wprost jest w `sys.path[0]`. Poprawiony pomiar:

  ```
  modulow: 92
  importujacych z katalogu, ktorego nie wstawiaja: 0
  ```

  Zostaje więc **jeden** przypadek — `test_dimension_audit.py` z §4, naprawiony tutaj.
  Bramka strukturalna na to zjawisko nie ma dziś czego pilnować, a pozycja kolejki
  oparta na tamtej piątce opisywałaby usterkę, której nie ma. Trzeci raz dzisiaj ten sam
  wzorzec (§2, §4 i tu): **liczba wzięta z przyrządu patrzącego na tekst, nie na
  strukturę.** Pętla z §5 zostaje jedynym sprawdzeniem tego zjawiska i wystarcza,
  bo ujawnia je przez padnięcie, a nie przez wnioskowanie.
