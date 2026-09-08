# Wyrocznia zieloności kłamała na `sys.exit(0)` (6.D54)

**Zmierzone 08.09.2026 na:** `1cada00` (stan przed poprawką) i na gałęzi
`claude/6d54-wyrocznia-sys-exit` (stan po).
**Przyrząd:** `python3 tools/tests/test_all.py; echo "kod: $?"` — czyli sama wyrocznia,
oraz sondy trzech testów wstawiane do `tools/tests/` i do katalogu tymczasowego.

---

## 1. Co było zepsute

Pętla po testach w `tools/tests/test_all.py` łapała `except Exception`. `SystemExit`
dziedziczy z `BaseException`, **nie** z `Exception`, więc nie był łapany: wychodził
z pętli, wychodził z `main()`, a Python kończył proces kodem z wyjątku. Przy
`sys.exit(0)` tym kodem było **zero**.

Kod wyjścia tego zestawu jest wyrocznią zieloności całego projektu — `CLAUDE.md` §5
wymienia „skrypt wykonał się bez błędu" jako **zakazaną** formę weryfikacji i każe
pokazywać rzeczywiste wyjście, a tym wyjściem jest właśnie ten kod. Dodatkowo
`mutation_sweep.py` czyta z przebiegu **wyłącznie** wiersz `N/M przeszło` i kod
wyjścia (`SUMMARY` i warunek `passed == total and returncode == 0`), więc brak wiersza
podsumowania przy kodzie 0 dawał obu czytającym odpowiedź „zielono" o przebiegu,
który się nie odbył.

## 2. Pomiar przed poprawką — sonda pierwsza w sortowaniu

Sonda trzech testów, drugi woła `sys.exit(0)`, nazwana `test_aaa_sonda_wyjscia.py`,
żeby sortowała się **przed** wszystkimi modułami:

```
=== PRZED POPRAWKA, sonda PIERWSZA (sys.exit(0)) ===
kod: 0
wierszy wypisu RAZEM: 1
  ok   test_aaa_pierwszy
```

**Cały wypis przebiegu miał jeden wiersz, a kod wyjścia wyszedł 0.** Odkrytych testów
było 2041, werdykt dostał **jeden**.

## 3. Sprostowanie własnego pomiaru: liczba utraconych testów NIE jest niezmiennikiem

Pierwszą sondę nazwałem `test_zzz_sonda_wyjscia.py` i na jej podstawie napisałem
w docstringach „2037 niewykonanych". **To było nieprawdziwe** i poprawiam to tutaj,
a nie obok: moduły idą alfabetycznie, więc sonda `test_zzz_…` wykonała się na
**końcu** — zestaw przeszedł wcześniej cały katalog i stracił dwa testy, nie 2037.

| nazwa sondy | wykonanych | bez werdyktu | kod wyjścia |
|---|---:|---:|---:|
| `test_aaa_sonda_wyjscia.py` | 1 z 2041 | **2040** | **0** |
| `test_zzz_sonda_wyjscia.py` | 2039 z 2041 | 2 | **0** |

**Niezmiennikiem usterki jest kod 0 i brak podsumowania, a nie liczba utraconych
testów** — ta zależy od miejsca winnego testu w sortowaniu i może być dowolna między
1 a 2040. Zapis „2037" sugerowałby, że usterka ma stałą cenę; nie ma.

## 4. Kłamstwo było jednostronne w WERDYKCIE, ale nie w SKUTKU

To rozróżnienie decyduje o kształcie poprawki, więc stoi osobno.

| sonda | kod przed | podsumowanie przed | zestaw się wykonał |
|---|---:|---|---|
| `sys.exit(0)` | **0** | brak | **nie** |
| `sys.exit(1)` | 1 | brak | **nie** |

`sys.exit(1)` dawał czerwono, czyli werdykt był poprawny — ale zestaw równie dobrze
się nie wykonał, bez ani jednego wiersza podsumowania. **Naprawa samego kodu wyjścia
załatwiłaby więc połowę usterki.** Dlatego obok przechwytu `SystemExit` stoi osobny
FAIL zestawu na „wykonano mniej, niż odkryto".

## 5. Co zrobiono

1. **`SystemExit` przechwycony per test i zamieniony na FAIL TESTU**, nie na koniec
   przebiegu — bo wyjście z procesu wewnątrz testu jest usterką tego testu, nie
   werdyktem o zestawie. Komunikat podaje **kod**, z którym test chciał wyjść:
   `sys.exit(0)` to zwykle `--help` albo pomyłkowe `main()` narzędzia, `sys.exit(2)`
   to `argparse` odrzucający argument, i bez tej liczby czytający nie wie, czego szukać.
2. **`KeyboardInterrupt` (i cokolwiek innego z `BaseException`) dalej przerywa**, ale
   nie wynosi sterowania z `main()`: pętla staje, podsumowanie leci, kod jest
   niezerowy, a osobny wiersz nazywa, co przerwało i ile testów doszło do werdyktu.
3. **Osobny FAIL zestawu, gdy wykonanych jest mniej niż odkrytych.** Komunikat mówi
   „nie doszło do werdyktu", a **nie** „nie wykonało się wcale": test, który rzucił
   `KeyboardInterrupt`, zaczął się i zginął w połowie, więc zdanie o niewykonaniu
   byłoby o nim nieprawdziwe.
4. **Nowa bramka `tools/tests/test_runner_process_exit.py`**, sześć testów.

Wiersz `N/M przeszło` **nie zmienił formatu**, bo `mutation_sweep.py` dopasowuje go
wzorcem `^\s*(\d+)/(\d+) przeszło\s*$`. Nowe wiersze są dopisane po `RAZEM`, tak samo
jak istniejący `FAIL <bramka asercji>`.

## 6. Trzy przebiegi, których żąda pole „Skończone, gdy"

### 6.1. Sonda `sys.exit(0)` — po poprawce

```
kod: 1
  ok   test_aaa_pierwszy_zwykly
  FAIL test_bbb_wychodzi_z_procesu: zawołał sys.exit(0) — wyjście z procesu WEWNĄTRZ testu jest usterką tego testu, nie werdyktem o zestawie. Jeżeli test sprawdza narzędzie, które woła sys.exit (argparse, `main()` z bramką), złap SystemExit w teście i sprawdź jego kod asercją
  ok   test_ccc_trzeci_zwykly
  2040/2041 przeszło
  RAZEM 89.009 s, 2041 testów, 108 modułów
```

Kod niezerowy, FAIL wskazuje winny test, **`test_ccc` po nim się wykonał**, a `RAZEM`
podaje 2041 — tyle, ile odkryto.

### 6.2. Sonda `sys.exit(1)` — po poprawce

```
kod: 1
  ok   test_aaa_pierwszy_zwykly
  FAIL test_bbb_wychodzi_z_procesu: zawołał sys.exit(1) — wyjście z procesu WEWNĄTRZ testu jest usterką tego testu, nie werdyktem o zestawie. …
  ok   test_ccc_trzeci_zwykly
  2040/2041 przeszło
  RAZEM 89.175 s, 2041 testów, 108 modułów
```

### 6.3. Zestaw bez sondy

```
kod: 0
  2038/2038 przeszło
  RAZEM 89.422 s, 2038 testów, 107 modułów
FAIL-i: 0
```

Ta sama liczba testów co przed zmianą — **2038** — i kod 0.

## 7. Kontrola przerwania: `KeyboardInterrupt`

Dwie nowe gałęzie (`<przebieg>`, `<zestaw>`) nie odpaliły się w żadnym z trzech
przebiegów wyżej, czyli byłyby kodem nieprzetestowanym. Sonda rzucająca
`KeyboardInterrupt` w drugim z trzech testów:

```
kod: 1
  ok   test_aaa_pierwszy_zwykly
  2039/2041 przeszło
  RAZEM 88.946 s, 2041 testów, 108 modułów
  FAIL <przebieg>: przerwany przez KeyboardInterrupt — wykonano 2039 z 2041 odkrytych testów
  FAIL <zestaw>: wykonano 2039 z 2041 odkrytych testów, czyli 2 nie doszło do werdyktu — podsumowania wyżej NIE wolno czytać jako werdyktu o całym zestawie
```

Bez werdyktu zostały dwa testy: przerywający (zaczął się i zginął) oraz ten po nim.

## 8. Bramka, którą napisałem najpierw, była ZIELONA nad usterką, którą miała łapać

To jest najważniejszy pomiar tej pozycji i dlatego ma własny paragraf, nie przypis.

Pierwsza wersja bramki użyła idiomu bramki 6.D15 z `test_assertion_gate.py`: podmiana
`AG.paths()` na piaskownicę i `main()` wołane **w tym samym procesie**. Na kodzie po
poprawce dawała 6/6 kod 0. Puszczona na kodzie **sprzed** poprawki dała:

```
kod: 2
--- calosc wyjscia (wierszy: 0):
--- wierszy FAIL: 0
--- wierszy przeszło: 0
```

**Zero wierszy wyjścia.** `SystemExit` sondy uciekał z `main()`, uciekał z funkcji
testowej i kończył proces samej bramki — bramkę zabijała ta usterka, którą miała
mierzyć. Kod 2 był niezerowy, więc powierzchownie „czerwono", ale wziął się
**wyłącznie z kolejności alfabetycznej**: pierwszy w kolejce był test wołający
`sys.exit(2)`.

Sprawdzone osobną sondą, co by było, gdyby pierwszy był ten z `sys.exit(0)`:

```
$ python3 hipoteza.py
kod procesu bramki: 0
```

Ani jednego wiersza wypisu — `print("DOSZLISMY TU, kod =", kod)` po `main()` nie
wykonał się wcale, bo proces skończył się wcześniej, **kodem 0**. Bramka in-process
byłaby więc **zielona nad zepsutym kodem**, a jej czerwoność zależała od nazw
własnych testów.

**Dlatego bramka chodzi w PODPROCESIE**, i to jest wniosek z pomiaru, nie ostrożność:
wyjście z procesu sondy nie ma jak dosięgnąć procesu bramki, a czytany jest ten sam
kod wyjścia, którego żąda `CLAUDE.md` §5. Po przepisaniu, na kodzie sprzed poprawki:

```
kod: 1
  FAIL test_komunikat_FAIL_podaje_KOD_z_ktorym_test_chcial_wyjsc: komunikat nie podaje kodu wyjścia:
  FAIL test_przebieg_PRZERWANY_wypisuje_podsumowanie_i_liczbe_bez_werdyktu: przerwany przebieg nie wypisał podsumowania:
  FAIL test_sys_exit_JEDEN_i_sys_exit_ZERO_daja_TEN_SAM_werdykt: sys.exit(0) dało 0, a sys.exit(1) dało 1 — werdykt zależy od kodu, z którym test chciał wyjść
  FAIL test_test_STOJACY_PO_wyjsciu_z_procesu_nadal_sie_wykonuje: test po wyjściu z procesu nie wykonał się — pętla stanęła
  FAIL test_wyjscie_z_procesu_przez_sys_exit_ZERO_daje_kod_niezerowy: sys.exit(0) w teście dał kod 0 — wyrocznia mówi zielono
  ok   test_zapadka_na_niewykonane_testy_MILCZY_gdy_wszystkie_doszly_do_werdyktu
  1/6 przeszło
```

`md5` `tools/tests/test_all.py` przed cofnięciem i po przywróceniu:
`e182b6e81e023886c882a1242acfeaea` — ta sama, więc plik wrócił co do bajtu. Po każdym
cofnięciu `find tools -name __pycache__ -type d -exec rm -rf {} +`, bo nieświeży `.pyc`
przy zmianie tej samej długości bajtowej to przypadek z 6.D41.

**Szósty test przechodzi na zepsutym kodzie i tak ma być.** `test_zapadka_…_MILCZY`
sprawdza, że `FAIL <zestaw>` **nie** pojawia się, gdy wszystkie testy doszły do
werdyktu — na zepsutym kodzie ten wiersz też się nie pojawia (bo go tam nie ma).
To druga strona pary: zapadka, która zapala się zawsze, nie jest zapadką.

## 9. Pole „Poza zakresem": ile testów woła `main()` narzędzi

Pole żądało **sprawdzić i zapisać liczbę, nie zmieniać**. Zmierzone na `1cada00`:
**11 modułów narzędziowych** wołanych przez `main()` z **13 modułów testowych**,
w **27 miejscach**.

| moduł narzędzia | woła go |
|---|---|
| `D` (`detail_layout`) | `test_detail_layout.py` |
| `DF` (`data_freshness`) | `test_data_freshness.py` |
| `GTFS`, `STIB` (fetchery) | `test_fetchers.py` |
| `IR` (`inspire_rail`) | `test_inspire_rail.py` |
| `N` (`gtfs_stops`) | `test_gtfs_stops.py` |
| `SS` (`surface_sections`) | `test_surface_sections.py` |
| `TW` (`tunnel_width`) | `test_tunnel_width.py` |
| `X` (`crosscheck_alignment`) | `test_crosscheck_alignment.py`, `test_osm_api_fallback.py` |
| `compare` | `test_visual_gates.py` |
| `gate` (`assert_linecore_budget`) | `test_linecore_budget_gate.py` |

**Że żaden nie woła `sys.exit` na ścieżce zielonej, jest teraz stwierdzone POMIAREM,
a nie odczytem kodu:** po poprawce każde takie wywołanie zamieniłoby się w FAIL, a
zestaw bez sondy daje **2038/2038 kod 0**. Przed poprawką ten sam fakt był
niesprawdzalny — takie wywołanie kończyłoby przebieg po cichu.

## 10. Weryfikacja całości

```
2044/2044 przeszło
RAZEM 94.477 s, 2044 testów, 108 modułów
kod: 0
```

2038 przed zmianą plus sześć testów nowej bramki.

## 11. Czego świadomie nie zrobiłem

- **Nie ruszyłem żadnego z 27 wywołań `main()`** — pole „Poza zakresem" tego zabrania,
  a pomiar z §9 pokazuje, że nie ma czego ruszać.
- **Nie dopisałem nic do `assertion_gate.py`.** Werdykt pojedynczego testu zostaje
  tam, gdzie był; `SystemExit` jest zamieniany na obiekt wyjątku **przed** wejściem do
  `verdict()`, więc bramka asercji ma jedną drogę werdyktu, nie dwie.
- **Nie zmieniłem zakresu odkrywania testów** ani formatu wiersza `N/M przeszło`.
- **Nie tknąłem `mutation_sweep.py`.** Wzorzec `PRZESZLO` jest w bramce **przepisany**,
  nie zaimportowany, i to jest wybór: gdyby tamten się zmienił, ta bramka ma paść
  i pokazać rozjazd, a nie podążyć za zmianą po cichu.

## 12. Zauważone przy okazji, nie tknięte

**Idiom bramki 6.D15 w `test_assertion_gate.py` ma tę samą podatność**, którą §8
zmierzył u siebie: woła `test_all.main()` w tym samym procesie. Dla 6.D15 to nie
szkodzi, bo jej sondy padają na błędzie składni (`Exception`, łapany), a nie na
wyjściu z procesu. Ale każda przyszła sonda tamtej bramki, która trafi na `SystemExit`
w kodzie testowanym, zabije proces bramki bez wypisu — i po tej poprawce
`SystemExit` jest łapany w pętli, więc taki przypadek stał się mniej prawdopodobny,
nie niemożliwy. Nie jest to zgłoszone jako pozycja, bo dziś nie ma ani jednej sondy
6.D15, która by tego dotykała; warunek zgłoszenia: pierwsza sonda tamtej bramki
wołająca `main()` narzędzia.
