# Pomiar zapisany bez nastaw, które go wyprodukowały (6.A20)

**Zmierzone 07.09.2026 na commicie:** `ee01bdf21f234dba04d803d6739d58eccfcdf9a0`
(gałąź `claude/6a20-csv-z-nastawami`).

## 1. Stan wyjściowy — dwa pliki, jedna różnica, i to nie ta właściwa

6.A18 naprawiła to po stronie **wypisu**: nagłówek `[BUDŻET]` mówi od niej, czy
przejazd był z wybiegiem. Ale wypis leci na konsolę i ginie z nią; **plik z `--out`
przeżywa proces i to on trafia do raportów.**

Dwa przebiegi `budget`, różniące się **wyłącznie** `--coast-from-m`, przed tą zmianą:

```
$ diff build/przed-z.csv build/przed-bez.csv
2c2
< 9,3,1.8279,5.0121,20000,1,88935.5,88935.5,88935.5,0.00,11.2441,1.004,0.135
---
> 9,3,1.8356,5.0045,20000,1,77237.5,77237.5,77237.5,0.00,12.9471,1.004,0.155

$ cat build/przed-z.csv
trains_declared,trains_on_line_max,...,us_per_step,cpu_over_wall,frame_budget_pct
9,3,1.8279,5.0121,20000,1,88935.5,88935.5,88935.5,0.00,11.2441,1.004,0.135
```

Cały plik to **dwa wiersze**: nagłówek i pomiar. Nic nie mówi, który przejazd go dał.

I to nie jest niedogodność teoretyczna. W tej parze przebieg **z** wybiegiem wyszedł
**szybszy** (88 935 vs 77 237 kroków/s) — czyli w drugą stronę niż wyszedłby przy
dłuższym oknie, bo przy `--steps 20000` szum czasu przewyższa efekt nastawy. Czytający
te dwa pliki wyciągnąłby wniosek przeciwny do prawdziwego i **nie miałby czym tego
sprawdzić**.

## 2. Jak jest teraz

```
# polecenie: budget
# axis: L1_A
# signalling_plan: classic-2026-L1_A
# limit_kmh: 72.00
# exchange_s: 20.0
# headway_s: 10.0
# turnback_s: 0.0
# brake_usage: 1.000
# stop_window_m: 5.0
# load: AW0
# atp: nie
# coast: wybieg 250.0 m odcinka
# steps: 20000
# warmup: 0
# repeats: 1
trains_declared,trains_on_line_max,...
9,3,1.8279,5.0121,...
```

i ta sama para plików, ta sama komenda `diff`:

```
$ diff build/z-wybiegiem.csv build/bez-wybiegu.csv
12c12
< # coast: wybieg 250.0 m odcinka
---
> # coast: wybieg wyłączony
17c17
< 9,3,1.8279,5.0121,20000,1,77338.6,...
> 9,3,1.8356,5.0045,20000,1,118575.7,...
```

**Różnica w nastawie stoi w pliku, nad różnicą w liczbach.** To jest dokładnie
kryterium pola „Weryfikacja".

Trzy decyzje warte uzasadnienia:

- **Wiersze `#`, nie dodatkowe kolumny.** Kolumna powtarza tę samą nastawę tyle razy,
  ile jest wierszy pomiaru; `#` pomija `pandas.read_csv(comment="#")` i jeden filtr
  w `csv`. Osobny test pilnuje, że prefiks `#` nie zniknie — bez niego plik przestaje
  być CSV-em, który cokolwiek otworzy.
- **Jedna metoda, nie dwie kopie.** Gdyby każdy pisarz składał ten blok sam, rozjazd
  formatu wyglądałby jak różnica nastawy, a nie jak różnica wypisu — ta sama pułapka,
  którą `LineRunSettings.CoastDescription` zamknęło przy 6.A18.
- **`# coast:` bierze zdanie z `settings.CoastDescription`**, czyli z tego samego
  miejsca, co nagłówek konsolowy. Plik i wypis nie mogą powiedzieć o wybiegu dwóch
  różnych rzeczy.

## 3. Zrobione DWA z pięciu pisarzy, i to nie jest skrócenie zadania

Pole „Poza zakresem" tej pozycji przewidywało dokładnie ten wynik: „jeżeli wybrany
kształt zmienia format czytany przez cokolwiek […] to `drive`/`replay` zostają na
osobną pozycję". Pomiar pokazał, że dotyczy to **trzech** pisarzy, nie dwóch, i każdy
z innego powodu:

| pisarz | co przybija format | wynik |
|---|---|---|
| `budget --out` | nic — żaden plik ani bramka go nie czyta | **zrobione** |
| `service-day --out` | nic | **zrobione** |
| `drive` / `replay` | `Compare` wymaga, by `left[0]` był **dokładnie** `DriveTelemetry.Header`, a każdy wiersz miał `ColumnCount` kolumn; ten sam format pisze scena Godota i `godot-first-run.yml` porównuje oba przy `--tolerance 0` | odłożone |
| `line --calls` | `godot-first-run.yml:1114` porównuje plik rdzenia z plikiem **SCENY** — format wspólny z implementacją w Godocie | odłożone |
| `line --trace` | `tools/ci/assert_line_trace.py` liczy **SHA-256 całego pliku** wobec wzorców przybitych do RODZINY runtime'u .NET | odłożone |

`line --trace` jest tu najciekawszy: tamta bramka mówi wprost, że przeliczanie wzorców
(`--update`) należy do commita, który **zmienia wersję środowiska**, i ma być w jego
treści opisane. Dopisanie metadanych przeliczyłoby wszystkie wzorce jako **skutek
uboczny** — czyli dokładnie to, czego tamta bramka zabrania. Zrobienie tego „przy
okazji" byłoby złamaniem cudzej reguły, nie postępem.

`axis --dump-points` jest szóstym pisarzem i **nie należy do tej pozycji z innego
powodu**: zapisuje surowe punkty osi, bez nagłówka i bez pomiaru, więc nie ma nastaw,
które miałby opisać. Sprawdzone, a nie założone — nie ma ani jednego konsumenta:

```
$ grep -rn "dump-points" .github/ tools/ docs/ tests/ | grep -v Program.cs
tools/tests/test_csv_provenance.py:57:   (tylko powód w bramce)
```

## 4. Bramka: żaden pisarz nie milczy bez powodu

`tools/tests/test_csv_provenance.py` nie pilnuje, że **każdy** pisarz ma nastawy — trzy
nie mogą. Pilnuje, że **żaden nie milczy bez powodu**: pisarz bez `Provenance` i bez
wpisu z powodem zapala bramkę. Bez tego ósmy pisarz, dopisany kiedyś indziej, po prostu
nie miałby nastaw i nikt by nie zauważył — dokładnie tak, jak nie miało ich siedem.

**Pierwsza wersja tej bramki sama się zapaliła, i miała rację.** Kluczowała po nazwie
zmiennej (`lines`, `rows`), a te nazwy są **używane ponownie**: `lines` składa
i telemetrię `drive`, i plik `service-day`; `rows` — i punkty osi, i `line --calls`,
i pomiar `budget`. Klucz, który nie rozróżnia dwóch różnych formatów, nie ma prawa
orzekać o żadnym z nich. Klucz jest teraz **metodą polecenia**, wyciętą po położeniu
nagłówków w pliku.

## 5. Kontrole negatywne — WYKONANE, cztery

| | co zepsute | wynik |
|---|---|---|
| KN-1 | `budget` przestaje wołać `Provenance` | `FAIL …_either_carries_settings_or_says_why_not: … Budget` + `FAIL …_are_the_two_that_do_carry_them` |
| KN-2 | wpis z powodem dla polecenia, które **żadnego pliku nie zapisuje** | `FAIL test_no_excuse_outlives_the_writer_it_describes: … Parity` |
| KN-3 | nastawy przestają być komentarzem (`#` znika) | `FAIL test_the_helper_exists_and_prefixes_every_setting_with_a_hash` |
| KN-4 | **zadanie zamienione na listę wymówek**: `budget` wyjęty z `Provenance` i wpisany do `BEZ_NASTAW` z powodem brzmiącym wiarygodnie | `FAIL …_are_the_two_that_do_carry_them: … ['ServiceDayCommand']` |

KN-4 jest tu najważniejsza. Bramka zbudowana tylko na regule „albo nastawy, albo
powód" byłaby zielona także wtedy, gdyby **wszystkie siedem** pisarzy trafiło do listy
powodów — czyli gdyby pozycja została zamieniona na zbiór wymówek. Kontrola pozytywna
przybija zakres: nastawy mają nieść **dokładnie** `Budget` i `ServiceDayCommand`.

## 5a. Bramka kolejki złapała moją literówkę w tym samym commicie

Nie kontrola, tylko zdarzenie. Wpisując wiersz 6.A21 zapomniałem znaku nowej linii na
końcu podmienianego tekstu, więc wiersz **skleił się** z następnym — 6.D26 przestał być
wierszem tabeli, choć jego blok szczegółów stał nietknięty:

```
  FAIL test_no_detail_block_describes_a_number_that_left_the_tables:
  blok szczegółów 6.D26 nie ma wiersza w żadnej tabeli
```

Sklejone wiersze wyglądają w markdownie prawie normalnie i przeczytałbym je bez
zatrzymania. Bramka nazwała pozycję, której wiersz zniknął — nie „tabela jest
uszkodzona", tylko **która** pozycja go straciła.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py
  RAZEM 107.331 s, 1811 testów, 95 modułów
kod: 0

$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 552, Skipped: 0, Total: 552
```

552 = 549 + **3** nowe testy C#; liczba jest tu częścią weryfikacji, po nauczce
z 6.B27. Trzeci z nich sprawdza **parę** plików, nie jeden: kryterium 6.A20 nie brzmi
„w pliku stoją nastawy", tylko „z dwóch plików da się odczytać, którą się różnią".

## 7. Czego świadomie nie zrobiono

- **Trzech pisarzy z §3** — każdy z wypisanym powodem, każdy stoi w bramce z nazwą
  tego, co przybija jego format. Idą do kolejki jako **6.A21**.
- **Nie tknięto `axis --dump-points`** — §3, inny powód niż tamte trzy.
- **Nie tknięto formatu telemetrii ani wzorców śladu.** Wzorce leżą w
  `tests/data/golden-trace/` — **nie** w `tools/ci/golden/`, jak napisałem najpierw:
  ścieżkę wziąłem z pamięci, a `git diff` odpowiedział `unknown revision or path not
  in the working tree`, czyli poprawnym błędem na wymyśloną ścieżkę. Prawdziwa stoi
  w `assert_line_trace.py:246` jako `--golden default="tests/data/golden-trace"`.
  Sprawdzone na właściwej: `git show --stat HEAD -- tests/data/golden-trace/` nie
  pokazuje ani jednego pliku.
- **Nie wybrano wartości domyślnych** dla żadnej nastawy — pole „Poza zakresem".
