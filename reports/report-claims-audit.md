# Liczby w `reports/` wobec kodu — co da się sprawdzić, a czego nie wolno

**Zmierzone 06.09.2026 na commicie:** `e2382f7`

Pozycja 6.D4 brzmi: „wartość wypisana w raporcie musi dać się odtworzyć z repo".
Pierwszy pomiar pokazał, że w tym brzmieniu **żądanie jest za szerokie** — i to jest
najważniejszy wynik tej pozycji, ważniejszy od samej bramki.

## 1. Klasa, której nie wolno pilnować równością — i pomiar, który to pokazał

Osiem twierdzeń w `reports/` ma postać „`plik_testowy`, N testów". Wszystkie osiem da
się sprawdzić maszynowo: wystarczy policzyć `def test_` albo `[TestMethod]`.
Wynik porównania:

| raport | plik | mówi | jest |
|---|---|---:|---:|
| `L1_A-chunks.md:215` | `tools/tests/test_chunks.py` | 29 | **51** |
| `L1_A-geometry.md:112` | `tools/tests/test_sweep.py` | 17 | **35** |
| `L1_A-lod.md:347` | `tools/tests/test_lod.py` | 50 | **75** |
| `M7-clearance-profile.md:18` | `tools/tests/test_clearance_profile.py` | 28 | **88** |
| `M7-shell.md:77` | `tools/tests/test_m7_shell.py` | 22 | **21** |
| `T-400-stage-3b.md:46` | `tests/Sim.Tests/StationServiceTests.cs` | 13 | **17** |
| `linecore-budget.md:371` | `tests/Sim.Tests/LineBudgetTests.cs` | 9 | **10** |
| `mutation-triage-parametry.md:4` | `tools/tests/test_parameter_boundaries.py` | 28 | 28 |

**Siedem z ośmiu rozjechało się** — i siedem z ośmiu jest **poprawnych**. Raport
opisywał plik w dniu pomiaru; plik od tamtej pory urósł. Dwa z tych rozjazdów zrobiłem
sam dziś, dopisując testy w `test_chunks.py` i `test_sweep.py` przy triażu 6.B6.

Bramka żądająca tu równości kazałaby **przepisywać datowany pomiar przy każdym
dopisanym teście** — czyli robić dokładnie to, czego zakazuje 6.D3 i czego pilnuje
`tools/tests/test_report_hygiene.py`. Ta klasa zostaje niepilnowana, świadomie.

Jeden wiersz odstaje w drugą stronę: `M7-shell.md` mówi **22**, a plik ma **21**.
Raport nie mógł policzyć więcej testów, niż plik miał w dniu pomiaru, więc albo dwa
testy zniknęły, albo liczba była nieprawdziwa od początku. Zgłaszam, nie rozstrzygam:
rozstrzygnięcie wymaga przejścia historii tego pliku, a to osobna praca.

## 2. Klasa, którą sprawdzać można: wartość stałej

Wartość stałej nie jest pomiarem. Albo zgadza się z kodem, albo raport wysyła
czytelnika po próg, którego nie ma. Ta różnica — między „ile było wtedy" a „ile wynosi
ta stała" — jest jedyną, na której stoi `tools/tests/test_report_claims.py`.

Pomiar: **65 różnych nazw stałych** pada w raportach, **37** z nich ma definicję
w `tools/` albo `src/`, a **12** jest zacytowanych razem z wartością. Wszystkie 12
zgadzają się z kodem.

Zero rozjazdów nie znaczy, że bramka jest pusta: znaczy, że wchodzi na czysty stan
i od tej chwili nie pozwoli mu się zepsuć.

## 3. Zwężenie wzorca — cała robota tej pozycji

Wersja pierwsza brała „nazwa w grawisach, potem dowolna liczba w promieniu 80 znaków"
i dała **3 fałszywe alarmy na 15 trafień**, czyli 20 %. Wszystkie trzy z tego samego
powodu — raport wymieniał stałe w tabeli odwzorowań:

```
219 → `DEFAULT_MAX_CHUNK_M`, 237 → `DEFAULT_STATION_HALO_M`, 250 → `DEFAULT_MIN_CHUNK_M`
```

Wzorzec brał **numer wiersza następnej pary** jako wartość poprzedniej: „`DEFAULT_MAX_CHUNK_M`
mówi 237, kod 800.0". Bramka z takim udziałem fałszywych alarmów zostałaby wyłączona
przy trzecim przebiegu, i słusznie.

Zwężenie jest jednym warunkiem: **między nazwą a liczbą nie wolno postawić przecinka,
strzałki ani grawisu.** To wycina wyliczenia i tabele odwzorowań, a zostawia wszystkie
cztery postacie, w których raporty naprawdę podają wartość:

```
`M7_WIDTH_M` 2,70                              — nazwa i liczba obok siebie
`SLAB_GROWTH_STEPS` = 6                        — ze znakiem równości
`PARALLEL_M` jest granicą włącznie: 30,0 m     — w zdaniu
Szerokość równa `RUNNING_TUNNEL_MAX_M` (15,0 m) — w nawiasie
```

Po zwężeniu: **12 trafień, 0 rozjazdów, 0 fałszywych alarmów.**

## 4. Trzy rzeczy, bez których ta bramka byłaby ozdobą

- **Próg na liczbę sprawdzonych twierdzeń** (`MINIMUM_CLAIMS = 10`). Literówka we
  wzorcu dałaby zero trafień, zero rozjazdów i zieloną bramkę. Ta sama pułapka, którą
  `test_report_hygiene.py` zamyka progiem `seen >= 500`.
- **Kontrola detektora** — siedem przypadków: cztery postacie, które mają wejść, i trzy,
  które nie (w tym ta tabela odwzorowań). Bez niej wzorzec mógłby po cichu wrócić do
  wersji z 20 % fałszywych alarmów.
- **Kontrola czytnika kodu** — bez niej pusty słownik stałych dałby zielone wszystko.
  Test sprawdza, że czytnik widzi ponad sto stałych, czyta oba języki, i że wzorzec
  definicji nie łapie ani porównania (`if PROG_M == 1.5:`), ani wywołania.

Stałą zdefiniowaną w dwóch miejscach z różnymi wartościami czytnik **pomija**: raport
cytujący taką nazwę nie ma jednej prawdy do porównania, a zgadywanie, którą miał na
myśli, byłoby gorsze od milczenia.

## 4a. Bramka wywróciła się na własnym raporcie — i dobrze

Pierwszy przebieg po napisaniu tego pliku zapalił bramkę na **tym raporcie**. Sekcja 5
niżej cytuje wyjście kontroli negatywnej, a w nim stoi zdanie

```
`BACKGROUND_TOLERANCE` mówi 0,03, kod 0.02
```

czyli dokładnie kształt, którego wzorzec szuka — z liczbą, która **z założenia** jest
nieprawdziwa, bo pochodzi z sabotażu.

Klasa jest szersza niż ten jeden przypadek: każdy raport triażu w tym repozytorium
cytuje wyjścia poleceń, a wyjście kontroli negatywnej **musi** zawierać złą liczbę.
Bramka, która czyta cytaty jak twierdzenia, karałaby za pokazywanie dowodu.

Poprawka: wiersze między ogrodzeniami ``` są pomijane. Po niej trafień jest nadal
**12** i nadal 0 rozjazdów — pominięcie nie kosztowało ani jednego prawdziwego
twierdzenia, bo raporty podają wartości stałych w prozie i w tabelach, nie w blokach
kodu. Pilnuje tego osobny test na sztucznym pliku z liczbą po obu stronach ogrodzenia.

## 5. Kontrola negatywna — WYKONANA

Zmiana w `reports/mutation-triage-wizualna.md` liczby przy `BACKGROUND_TOLERANCE`
z 0,02 na 0,03:

```
FAIL test_every_constant_quoted_in_a_report_carries_the_value_from_the_code:
     raporty podają inną wartość niż kod:
     ['mutation-triage-wizualna.md:54: `BACKGROUND_TOLERANCE` mówi 0,03, kod 0.02']
  1625/1626 przeszło
```

Plik przywrócony, zestaw z powrotem na 1626/1626.

## 6. Czego ta pozycja świadomie nie zrobiła

- **Nie poprawiła ani jednej liczby w raportach.** Siedem rozjazdów z sekcji 1 to
  datowane pomiary i przeliczanie ich jest zakazane. Ósmy (`M7-shell.md`) jest
  zgłoszony, nie poprawiony.
- **Nie objęła `docs/`.** Ta sama pętla po `docs/*.md` jest osobną pracą i osobnym
  ryzykiem: dokumentacja opisuje stan bieżący, więc granica „pomiar czy twierdzenie"
  przebiega tam inaczej niż w raportach.
- **Nie zwęziła `test_dimension_audit.py`**, którego wzorzec `NAMES_THE_PLATFORM_PARAMETER`
  łapie sam napis „jawny parametr" i przy #272 zapalił się na zdaniu o odzysku energii.
  Zgłoszone tam, nie tknięte tu.

## 6a. Znalezione przy okazji: zapadka zapasu żąda uzupełnienia w tym samym commicie

Adnotowanie tej pozycji jako `ZROBIONE` **zapaliło bramkę** `test_the_documented_reserve_does_not_regress`:

```
pozycji z kompletem sześciu pól jest 10 przy zapadce 11
```

Mechanizm jest skutkiem zmiany z #272. Zapadka liczy teraz pozycje udokumentowane
**i niezrobione**, więc domknięcie takiej pozycji **obniża licznik o jeden**. Bramka
świeci na czerwono nie dlatego, że coś zepsuto, tylko dlatego, że wykonano pracę.

Dwie możliwe lektury i obie są spójne:

1. **Bramka działa, jak ma.** Reguła zapasu mówi: „poniżej progu **pierwszym zadaniem
   jest uzupełnienie fazy 6**". Domknięcie pozycji zjada zapas, więc zapas trzeba
   uzupełnić — i to natychmiast, a nie „kiedyś". Tak zrobiłem tutaj: dopisałem blok
   sześciu pól dla **6.A3** (odtworzenie doby służby z bloków GTFS; trzy liczby
   z T-113 — 71 obiegów, 56 naraz o 07:06:44 — dają gotowe kryterium „Skończone, gdy").
2. **Sprzężenie jest za ciasne.** Każde domknięcie udokumentowanej pozycji wymusza
   napisanie nowego bloku w **tym samym commicie**, co miesza dwie różne prace i łamie
   regułę „jedno zadanie = jeden commit" z `CLAUDE.md` §4.10.

Rozstrzygnięcie należy do właściciela. Gdyby wybrać drugą lekturę, poprawka jest
prosta i **nie osłabia** żadnej z dwóch ochron: rozdzielić liczby. Monotoniczna
zapadka pilnowałaby **liczby napisanych bloków** (`detail_sections`, rośnie tylko przez
pisanie i spada tylko przez kasowanie), a osobny próg — **zapasu pozycji do wzięcia**
(`documented_items`, wolno mu opadać, gdy praca jest wykonywana). Dziś obie role niesie
jedna stała i dlatego wchodzą sobie w drogę.

## 7. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/test_all.py
  1627/1627 przeszło
```

Pięć nowych testów w `tools/tests/test_report_claims.py`. Zero zmian w kodzie
produkcyjnym i zero zmian w liczbach istniejących raportów.
