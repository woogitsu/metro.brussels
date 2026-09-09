# Nastawy trzech pisarzy, których formatu nie wolno tknąć (6.A21)

**Zmierzone 09.09.2026 na:** `c45a782`, kontener tej sesji.
**Przyrząd:** `dotnet run --project src/Sim.Runner`, `tools/ci/assert_line_trace.py`
na sześciu osiach, `python3 tools/tests/test_all.py test_csv_provenance.py`
i `dotnet test tests/Sim.Tests`.

---

## 1. Co zrobione i jaką drogą

Trzy pisarze — `drive`, `replay` i oba pliki `line` (`--trace`, `--calls`) — zapisują
od tej pozycji nastawy przebiegu w **pliku OBOK**: `<plik wyniku>.provenance.txt`.
Słownik `BEZ_NASTAW` w `tools/tests/test_csv_provenance.py` zmalał z **czterech**
wpisów do **jednego** (`Axis`), i to była treść pola „Skończone, gdy": słownik miał
**zmaleć**, a nie zmienić brzmienie.

**To jest odstępstwo od pola „Wyjście" i mówię o tym wprost.** Pole żądało „nastaw
w tych trzech plikach **albo** rozstrzygnięcia, że format któregokolwiek zostaje
nietknięty na stałe". Dostarczam trzecią rzecz: **format nietknięty co do bajtu,
a nastawy obok**. Powód nie jest wygodą — jest pomiarem z §2 i §3: droga „w pliku"
jest zamknięta czterema regułami naraz, a droga „format zostaje, nastawy giną"
zostawiłaby usterkę 6.A20 nienaprawioną w trzech z pięciu pisarzy.

## 2. Dlaczego nie DO pliku — zmierzone, nie wyczytane

Wklejenie nastaw na początek pliku (kształt `budget` i `service-day`) łamie w tych
trzech naraz cztery rzeczy. Kontrola negatywna **KN-7**: `drive` zmieniony na kształt
`new List<string>(Provenance("drive", …)) { DriveTelemetry.Header }`, po czym cały
łańcuch odmawia:

```
Failed DriveTelemetryKeepsThePinnedHeaderAndGetsSettingsBeside [52 ms]
 Assert.AreEqual failed. Expected:<step,t_s,chainage_m,distance_m,speed_mps,speed_kmh,accel_mps2,throttle,brake,phase>. Actual:<# polecenie: drive>. pierwszy wiersz telemetrii przestał być nagłówkiem
Failed CompareStillAcceptsATelemetryFileWrittenWithSettingsBeside [28 ms]
 Assert.AreEqual failed. Expected:<0>. Actual:<1>. compare przy progu 0 odrzuciło dwa przebiegi tego samego scenariusza
```

**`compare` kończy kodem 1 na dwóch przebiegach TEGO SAMEGO scenariusza** — czyli
konsument odrzuca plik, w którym nastawy stoją w środku. To nie jest przewidywanie
z lektury `Compare`; to jego kod wyjścia.

## 3. Pomiar rozstrzygający: plik obok nie zmienia ANI JEDNEGO bajtu

`line --trace` jest z tych trzech najtwardszy, bo wzorcem jest **SHA-256 całego
pliku**, a `tools/ci/assert_line_trace.py` mówi wprost, że przeliczanie wzorców
należy do commita zmieniającego wersję środowiska. Gdyby plik obok cokolwiek
w śladzie zmienił, ta pozycja musiałaby przeliczyć wzorce sześciu osi — czyli złamać
cudzą regułę. Przebieg sześciu osi z nowym kodem, ta sama komenda co w
`sim-tests.yml`:

```
$ for AXIS in L1_A L1_B L2_E L5_C L5_D L6_F; do
    dotnet run --project src/Sim.Runner --configuration Release --no-build -- line \
      --axis "data/track/$AXIS.json" --limit-kmh 72 --exchange-s 20 \
      --trace "$TRACES/$AXIS.csv" > /dev/null
  done
$ python3 tools/ci/assert_line_trace.py --traces "$TRACES"
[SLAD] sześć osi zgadza się z wzorcem co do bajtu
kod: 0
```

**Zero zmian we wzorcach, zero zmian w scenie Godota, zero zmian w `--tolerance`.**
Katalog śladów po przebiegu ma dwa razy więcej plików, i to jest cała różnica:

```
-rw-r--r-- 1 root root 3686193 L5_D.csv
-rw-r--r-- 1 root root     194 L5_D.csv.provenance.txt
```

Bramka wzorca zbiera ślady po `*.csv`, więc pliku `.provenance.txt` nie widzi — i to
jest pilnowane osobną asercją, nie zbiegiem okoliczności (§5, KN-6).

## 4. Co niosą trzy pliki obok

```
$ cat L5_D.csv.provenance.txt
# polecenie: line --trace
# axis: data/track/L5_D.json
# limit_kmh: 72
# exchange_s: 20
# brake_usage: 1
# stop_window_m: 5
# load: AW0
# coast_from_m: brak
# signalling: brak (LineRun bez ATP)

$ cat drive.csv.provenance.txt
# polecenie: drive
# scenario: package-a-first-run
# vehicle: M7
# sample_every_steps: 120

$ cat replay.csv.provenance.txt
# polecenie: replay
# keys: tests/data/manual-keys-limit.log
# axis: data/track/L1_A.json
# signalling: data/design/signalling/classic-2026.json
# sample_every_steps: 120
# notch_rate_per_s: 0.8
# exchange_s: 8
# stop_window_m: 5
# atp: nie
# limit_kmh: z planu
```

Dwie rzeczy w treści są wyborem, nie przypadkiem. **`coast_from_m: brak`, nie `0`** —
brak wybiegu to `null`, a nie zero (6.A6), i plik nastaw ma mówić to samo, co
przejazd. **`limit_kmh: z planu`** w `replay` — bo tam limit bez `--atp` pochodzi
z planu sygnalizacji, a wpisanie liczby udawałoby nastawę, której nikt nie podał.

Nastawy `line` składa **jeden** pomocnik (`LineSettingsForProvenance`), choć pisarzy
jest dwóch: dwie listy obok siebie rozjechałyby się przy pierwszej nowej opcji, czyli
byłyby tą samą usterką, którą 6.D44 zmierzyło na kopiach listy bibliotek w CI.

## 5. Bramki: detektor PRZEKIEROWANY, i sprawdza więcej

Detektor `z_nastawami` znał jeden kształt (`new List<string>(Provenance(`). Doszedł
drugi (`WriteProvenanceBeside(`) — a samo dopisanie kształtu byłoby **poluzowaniem**,
bo wystarczyłoby wtedy wołanie pomocnika, który nie zapisuje nic. Dlatego razem
z kształtem doszły trzy bramki:

1. `test_every_writer_lands_in_exactly_one_of_the_three_boxes` — **przybite trzy
   zbiory naraz** (nastawy w pliku / obok / powód), rozłączność obu par i równość
   sumy ze zbiorem pisarzy. Poprzednia wersja przybijała jeden zbiór i była zielona
   nad każdym układem pozostałych pięciu pisarzy — w tym nad takim, w którym wszyscy
   trafiają do `BEZ_NASTAW`, czyli nad zamianą zadania na listę wymówek.
2. `test_the_sidecar_writer_cannot_be_a_no_op` — cztery warunki na sam pomocnik:
   zapisuje, składa treść przez `Provenance`, liczy nazwę przez `ProvenancePathFor`,
   a nazwa wychodzi ze ścieżki pliku wyniku i **nie kończy się na `.csv`**.
3. `test_every_sidecar_names_the_same_path_as_the_file_it_describes` — pierwszy
   argument obu wołań w tej samej metodzie musi się zgadzać. Bez tego plik nastaw
   mógłby opisywać inny przebieg niż ten, obok którego leży.

Do tego trzy testy C# (`tests/Sim.Tests/ProvenanceSidecarTests.cs`), bo żadna
z bramek wyżej nie uruchamia runnera: sprawdzają nagłówek na dysku, **brak wiersza
`#` w pliku wyniku** (drugi kierunek — bez tego test byłby zielony także po wklejeniu
nastaw do środka) i to, że `compare --tolerance 0` plik przyjmuje.

### Kontrole negatywne — siedem, każda wykonana

| # | mutacja | co padło |
|---|---|---|
| KN-1 | `drive` bez wołania nastaw | 3 bramki, każda nazywa `Drive`; 4/7 |
| KN-2 | `replay` bez wołania nastaw | 3 bramki, każda nazywa `Replay`; 4/7 |
| KN-3 | **tylko jeden z dwóch** pisarzy `line` traci nastawy | **wyłącznie** bramka par ścieżek: „zapisane `['callsPath', 'tracePath']`, opisane `['callsPath']`"; 6/7 |
| KN-4 | nastawy `--calls` wskazują plik śladu | bramka par ścieżek: „opisane `['tracePath', 'tracePath']`"; 6/7 |
| KN-5 | pomocnik nic nie zapisuje | „pomocnik nic nie zapisuje"; 6/7 |
| KN-6 | plik nastaw nazwany `.provenance.csv` | „bramki CI zbierają ślady po `*.csv` i wciągnęłyby nastawy jako ślad"; 6/7 |
| KN-7 | nastawy WKLEJONE do telemetrii `drive` | dwa testy C#, w tym `compare` z kodem **1** |

**KN-3 jest tu najważniejsza i dlatego stoi osobno.** Przy częściowym zdjęciu bramka
pudełek **została ZIELONA** — `LineCommand` nadal ma jedno wołanie, więc nadal leży
w pudełku „obok" — i padła wyłącznie bramka par ścieżek. To jest dowód, że trzecia
bramka nie jest nadmiarowa: łapie stan, którego dwie pierwsze nie widzą.

`md5` `src/Sim.Runner/Program.cs` przed pierwszą mutacją i po każdym przywróceniu:
`bf6823b05a2e51cae2a783718af5881a`. Po każdej mutacji
`find tools -name __pycache__ -type d -exec rm -rf {} +` (6.D41).

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py test_csv_provenance.py
  7/7 przeszło
kod: 0
```

Pełne zestawy — w bloku ZROBIONE pozycji 6.A21 w `docs/TASKS.md`.

## 7. Czego świadomie nie zrobiłem

- **Nie tknąłem scenY Godota ani `--tolerance`.** Przy tej drodze nie ma czego
  tknąć — pliki porównywane są bit w bit te same, co przed zmianą (§3). Pole
  „Skończone, gdy" żądało zielonego przebiegu `godot-first-run.yml`, **jeżeli**
  którykolwiek pisarz wymagałby zmiany w scenie; żaden nie wymagał, a workflow
  odpala się i tak, bo `src/Sim.Runner/**` stoi w jego `paths:`.
- **Nie przeliczyłem wzorców w `tools/ci/golden/`.** `git diff --stat` na tym
  katalogu jest puste, czego żądało pole „Weryfikacja" — i to jest mocniejsze niż
  „przeliczone razem z opisem", bo przeliczanie należy do commita zmieniającego
  wersję środowiska.
- **Nie dodałem nastaw na stdout**, gdy `drive`/`replay` piszą telemetrię bez `--out`.
  Wiersze `#` na stdout byłyby zmianą kształtu wypisu, czyli zmianą wyroczni dla
  `grep` (6.A16, 6.A27, 6.A30) — inna pozycja niż ta.
- **`axis --dump-points` zostaje bez nastaw**, z powodem, który był tam już wcześniej:
  surowe punkty osi nie są wynikiem przejazdu, więc nie ma nastaw do opisania.
- **Nie zmieniłem znaczenia telemetrii ani kolumn** — zabraniało tego pole „Poza
  zakresem", a plik obok nie dotyka ani jednej kolumny.
- **Nie przepisałem §3 raportu 6.A20**, który mówi o tych trzech „odłożone". To zapis
  decyzji z jego dnia; dopisany jest tam jeden wiersz odsyłający tutaj, żeby czytelnik
  nie brał tabeli z 07.09 za stan bieżący (6.D49: żywe odniesienie wolno poprawić,
  zapis historyczny zostaje).

## 8. Zauważone przy okazji, nie tknięte

**Pole „Weryfikacja" tej pozycji wołało katalog, którego w drzewie nie ma — i bramka
pól tego nie widzi.** Polecenie `git diff --stat tools/ci/golden/` odpowiada
`fatal: ambiguous argument 'tools/ci/golden/': unknown revision or path not in the
working tree`; wzorce śladu leżą w `tests/data/golden-trace/` (sześć plików próbki
plus manifest). Dlaczego bramka `test_no_verification_field_names_a_file_outside_the_tree_and_outside_its_own_output`
przepuściła to, choć moją własną pomyłkę z 6.D64 złapała tego samego dnia — zmierzone,
nie wyczytane:

```
wzorzec: (?<![A-Za-z0-9_./-])(\.?[A-Za-z0-9_][A-Za-z0-9_./+-]*/[A-Za-z0-9_][A-Za-z0-9_.+-]*\.(?:geojson|csproj|…|py|cs))(?![A-Za-z0-9])
trafienia dla `git diff --stat tools/ci/golden/`   : []
trafienia dla `python3 tools/ci/nie-ma-takiego.py` : ['tools/ci/nie-ma-takiego.py']
```

Wzorzec żąda znanego **rozszerzenia**, więc ścieżka KATALOGOWA jest dla niego
niewidzialna. To ta sama rodzina, co martwe pole `PATH_TOKEN` na ścieżkach
zaczynających się kropką (6.D59), tylko po drugiej stronie: tam kropka na początku,
tu brak rozszerzenia na końcu.

**Licznik wzorca „pole nazywa plik o związku pozornym albo ścieżkę nie z drzewa,
a bramka tego nie widzi" doszedł tym samym do PIĘCIU** — próg, który sam sobie
postawiłem 08.09.2026 i powtórzyłem w `reports/uzupelnienie-kolejki-09-09.md` §6.
Pozycji tu nie dopisuję, bo commit ma jedno zadanie (`CLAUDE.md` §4.10); wchodzi
do kolejki przy najbliższym jej uzupełnieniu, razem z tym pomiarem.

**`ProvenancePathFor` musiało zmienić widoczność z `internal` na `public`**, bo
`tests/Sim.Tests` nie ma `InternalsVisibleTo` do `Sim.Runner` — sprawdzone, nie
założone: kompilator odrzucił pierwszą wersję testu komunikatem
`CS0117: 'Program' does not contain a definition for 'ProvenancePathFor'`. Alternatywą
było dopisanie atrybutu `InternalsVisibleTo` do `Sim.Runner`, czyli otwarcie CAŁEGO
wnętrza projektu dla testów zamiast jednej metody. Wybrałem węższe, ale nie jest to
wybór bez kosztu: nazwa pliku obok jest od teraz częścią publicznego API runnera.
Zgłaszam, bo to decyzja o kształcie API, a nie skutek tej pozycji.
