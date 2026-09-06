# Zapadka zapasu liczyła pracę skończoną — i sama kazała ją tam trzymać

**Zmierzone 05.09.2026 na commicie:** `8edb1d8`

`CLAUDE.md` §8 obiecuje: „Agent nigdy nie ma mniej niż 24 godziny pracy przed sobą",
a `tools/tests/test_backlog.py` miał tego pilnować, „żeby reguła nie była życzeniem
zapisanym w dokumencie". Tego dnia okazało się, że **stała się nim mimo bramki** —
i to nie przez lukę w liczeniu, tylko przez sprzężenie zwrotne, które sama bramka
wytworzyła.

## 1. Mechanizm — reguła obrócona przeciwko sobie

Zapadka `MINIMUM_DOCUMENTED_ITEMS` wolno tylko podnosić. Pozycja udokumentowana,
która zostaje wykonana i **wychodzi** z kolejki, tę zapadkę zbija. Więc jej nie
zdejmowano: każda taka pozycja dostawała adnotację

> **ZROBIONE w #NNN — wpis zostaje w kolejce z powodu zapadki, nie dlatego, że jest
> do zrobienia**

i zostawała w tabeli. Adnotacja jest uczciwa i mówi prawdę wprost. Problem jest
w liczniku: liczył `ready_items`, czyli **wszystko, co stoi w tabeli jako praca** —
razem z tymi wpisami.

Im więcej pracy agent wykonywał, tym bardziej licznik przestawał mówić o pracy.

## 2. Pomiar w chwili wykrycia

Po scaleniu #271, tym samym licznikiem:

| | |
|---|---:|
| pozycji w tabeli (`ready_items`) | 24 |
| z adnotacją `ZROBIONE` | **10** |
| realnie do wzięcia | 14 |
| udokumentowanych wg starego licznika | 12 |
| **udokumentowanych i jednocześnie niezrobionych** | **5** |

Zapadka stała na dwunastu i **świeciła na zielono**. Gwarancja doby pracy była oparta
na liczbie, której siedem dwunastych stanowiły wspomnienia po pracy.

Siódemka z nazwiska: 6.B1, 6.B10, 6.B6, 6.B7, 6.B8, 6.D5, 6.D6.

## 3. Co się zmieniło

**`open_items(text)`** — pozycje kolejki bez adnotacji `ZROBIONE`. Liczą się z niej
teraz obie rzeczy: próg doby pracy (`test_the_queue_holds_at_least_a_day_of_work`)
i zapadka (`documented_items`).

**Zapadka jest przebazowana, nie obniżona.** 12 → 11 nie jest cofnięciem, bo **mierzy
inny zbiór** i liczby po obu stronach zmiany nie są porównywalne. „Wolno tylko
podnosić" biegnie od nowa, od jedenastu. Cały komentarz przy stałej jest z tego powodu
przepisany, a nie dopisany obok.

**Sześć nowych bloków sześciu pól** — 6.A5, 6.A6, 6.C3, 6.C4, 6.D1, 6.D4. Żadnego nie
wymyśliłem: wszystkie sześć **stały już w kolejce** jako wiersze tabeli bez opisu, jak
je wykonać. Pola są odczytane z drzewa i przy każdym stoi, skąd:

| pozycja | najtwardsze źródło |
|---|---|
| 6.D1 | treść commita `90a8c31` — sześć osi, **453 107 wierszy**, rozjazd w wierszu **2910** przy progu przesuniętym o 0,1 %. Liczb tych nie ma w żadnym pliku `reports/` ani `docs/` |
| 6.D4 | docstring `test_readme_claims.py`: „liczba stojąca w jednym miejscu i nigdzie nie liczona rozjeżdża się bezszelestnie" — plus pięć istniejących bramek tej rodziny |
| 6.C3 | `DriveTelemetry.Header`, `ColumnCount = 10`; `--telemetry` jest dziś **wyjściem** (`FirstRun.cs:1717` otwiera plik do zapisu) |
| 6.C4 | `RunPlan.cs:42` — `KnownViews = { "cab", "chase", "outside" }`, a nieznany widok jest **błędem**, nie cichą kabiną (`:325`) |
| 6.A6 | `DriverCommand.Coast` istnieje jako **stan**, nie jako strategia; rezerwa rozkładowa z T-113 daje drugą stronę porównania (4,3 s najciaśniej, 45,3 s najluźniej) |
| 6.A5 | `BrakingEnergyAccount.cs` mówi wprost, że **nie ma sprawności odzysku** w żadnym źródle — stąd wymóg dwóch wariantów skrajnych zamiast jednej liczby |

Stan po zmianie: **24 pozycje w tabeli, 14 do wzięcia, 11 udokumentowanych** przy progu
12. Brakuje jednej i `docs/TASKS.md` musi o tym mówić — pilnuje tego
`test_the_documented_shortfall_is_written_down_while_it_lasts`, i po tej zmianie
akapit o niedoborze wrócił.

## 4. Bramka i jej kontrola negatywna — WYKONANA

`test_the_reserve_counts_work_to_take_not_work_already_done` sprawdza trzy rzeczy na
jednym tekście: że `open_items` jest podzbiorem `ready_items`, że **każda** odsiana
pozycja naprawdę nosi znacznik, i że zapadka nie liczy pozycji spoza zbioru do wzięcia.

Kontrola negatywna: przywrócenie starego liczenia w `documented_items`.

```
FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: opisanych pozycji jest 18,
     a zapadka stoi na 11 — podnieś ją do 12 w tym samym commicie, w którym dopisujesz blok
FAIL test_the_reserve_counts_work_to_take_not_work_already_done: zapadka liczy pozycję,
     której nie da się wziąć: ['6.B1', '6.B10', '6.B6', '6.B7', '6.B8', '6.D5', '6.D6']
  1620/1622 przeszło
```

Do tego `test_the_open_item_filter_reacts_to_the_marker_and_not_to_something_else` —
trzy wiersze sztucznego planu, z których jeden zawiera prozę „coś **do zrobienia**"
i ma **zostać**. Bez tego filtr mógłby łapać słowo zamiast adnotacji i nikt by nie
zauważył.

## 5. Czego ta zmiana świadomie nie zrobiła

- **Nie zdjęła żadnej pozycji z adnotacją `ZROBIONE`.** Teraz już można — nie liczą
  się do zapadki, więc ich zdjęcie niczego nie zbija. Ale to jest osobne porządkowanie
  i osobna decyzja, gdzie mają wylądować: w tabeli domknięć czy poza planem.
- **Nie dopisała siódmego bloku**, żeby dobić do dwunastu. Zostały cztery pozycje bez
  bloku (5.6, 6.A3, 6.B5 i 6.B9 ma go już) — i każda ma powód, dla którego jeszcze go
  nie dostała: 5.6 wymaga ustalenia, czym jest R-002, którego repozytorium nie zna;
  6.A3 potrzebuje `build/timetable.json`, którego nie ma w drzewie; 6.B5 jest
  w większości zmierzona (promienie sześciu osi w `packages-BF-alignment.md` §1,
  skrajnia A/B/E w `clearance-BE.md`), a reszta wpada w decyzję o pakietach C, D i F.
  Dopisanie im pól z głowy byłoby dokładnie tym, czego zabrania `CLAUDE.md` §8.

## 6. Zauważone przy okazji, nie tknięte

**`test_dimension_audit.py::test_prose_naming_the_platform_parameter_carries_the_value_from_the_code`
ma za szeroki wzorzec.** `NAMES_THE_PLATFORM_PARAMETER` łapie sam napis
`jawny parametr`, więc zdanie o **zupełnie innym** parametrze — udziale odzysku
w bloku 6.A5 — zapaliło bramkę żądającą wartości 95,0 m:

```
FAIL test_prose_naming_the_platform_parameter_carries_the_value_from_the_code:
     długość peronu inna niż 95,0 m w kodzie:
     ['docs/TASKS.md:1265: wariantów skrajnych odzysku, 0 % i 100 %**, jako jawny parametr …']
```

Obszedłem to przeformułowaniem własnego zdania, bo zwężenie cudzej bramki jest pracą
spoza tego zadania (`CLAUDE.md` §4.10). Zgłaszam, zamiast poprawiać po cichu.

## 7. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/test_all.py
  1622/1622 przeszło

$ python3 -c "…test_backlog…"
w tabeli: 24 | do wzięcia: 14 | udokumentowanych i niezrobionych: 11 | zapadka: 11
```
