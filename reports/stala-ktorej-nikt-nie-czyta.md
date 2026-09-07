# Stała, której nikt nie czyta (6.B29)

**Zmierzone 07.09.2026 na commicie:** `6e6a04e8f50a2d0903f23e3faef0866aff0a2f44`
(gałąź `claude/6b29-martwa-stala-bramka`).

## 1. Po co, jeżeli 6.B25 już usunęło tę stałą

Bo 6.B25 usunęło **jedną**, a nie zjawisko. `MIN_RADIUS_M = 20.0` stało
w `tools/blender/clearance.py` od swojego pierwszego commita (#50, 01.09.2026),
nieczytane przez nic — i zdążyło w tym czasie zostać zacytowane w docstringu innego
modułu **jako granica obowiązująca**. To jest właściwy koszt martwej stałej: nie ciężar
w pliku, ale **zdanie o repozytorium, które ktoś przeczyta i uzna za prawdziwe**.

Bramka z 6.B25 (`test_constant_names.py`) tego nie łapie i jej kontrola negatywna KN-1
pokazała to wprost: stała przywrócona do `clearance.py` nie tworzy **kolizji**, bo
drugiej definicji już nie ma, więc tamta bramka milczy. Dwa różne zjawiska, dwa testy.

## 2. Zasięg: wybrany po zmierzeniu trzech, nie z góry

Pierwsza wersja brała tylko wartości proste (`int`, `float`, `str`) — bo taka była
stała, która to wywołała. Sprawdzone, ile kosztuje zawężenie:

```
proste (int/float/str)      definicji=242  nieczytanych=1  ['LOCATION_STATION']
literalne (+ dict, list)    definicji=348  nieczytanych=1  ['LOCATION_STATION']
wszystkie                   definicji=705  nieczytanych=1  ['LOCATION_STATION']
```

**Liczba nieczytanych jest ta sama we wszystkich trzech.** Zawężenie nie kupiłoby
czystości, tylko oddało zasięg: martwy słownik progów albo martwa krotka nazw byłyby
dokładnie tym samym zdaniem o repozytorium, a węższa bramka by ich nie zgłosiła.
Wzięty jest więc zasięg **najszerszy** — każde przypisanie modułowe na WIELKIE litery.

To rozstrzyga też rozbieżność w samym wpisie kolejki: 6.B29 mówiło o **696** stałych,
bo taką liczbę dał pomiar pomocniczy przy 6.B25, liczący wszystkie nazwy wielkimi
literami. Dzisiejsze **705** to ta sama populacja na drzewie o dwa moduły większym;
242 z tego to podzbiór o wartościach prostych. Bramka pokrywa **705**.

## 3. Wypis, którego żądało pole „Weryfikacja"

```
[STALE] modulowych w tools/ i src/:       705
[STALE] nieczytanych nigdzie w drzewie:   1
[STALE] z tego uzasadnionych:             1
[STALE] bez uzasadnienia:                 0
    LOCATION_STATION -> tools/track/normalize_stops.py
```

Ta jedna jest uzasadniona i **wpis mówi, w którym pliku stoi** — bo powód bez pliku
starzeje się bez śladu: stała przeniesiona gdzie indziej zostawia zdanie, którego nie
da się sprawdzić. Osobny test to przybija.

## 4. Odczyt liczony przez `ast`, a `*.sh` i `.github/` osobno

Grep na nazwie złapałby ją w komentarzu, w docstringu i w napisie — a właśnie tak
`MIN_RADIUS_M` **wyglądało na żyjące**. Liczone są więc `Name` w kontekście `Load`
i `Attribute`, bo stałą czyta się też jako `M.NAZWA`; bez tego drugiego każda stała
czytana wyłącznie przez cudzy moduł — czyli większość tych, które cokolwiek znaczą —
wyszłaby jako martwa. Oba warunki mają swój test na przyrządzie, nie na drzewie.

`*.sh` i `.github/*.yml` są sprawdzane **osobno i tekstem**, i to nie jest ostrożność
na zapas: `tools/ci/vehicle_clearance.sh` oraz `tools/ci/station_details.sh` zawierają
pełne programy w `python3 -c`, więc stała czytana wyłącznie stamtąd **nie jest martwa**,
a `ast` po plikach `.py` jej nie zobaczy — treść tamtego wywołania jest dla niego
napisem. Fałszywy odczyt jest tu tańszą pomyłką niż fałszywa martwota: pierwsza
przemilcza jedną stałą, druga kazałaby usunąć coś, co działa.

## 5. Kontrole negatywne — WYKONANE, cztery

| | co zepsute | wynik |
|---|---|---|
| KN-1 | martwe `MIN_RADIUS_M` wraca do `clearance.py` | `FAIL test_every_unread_constant_is_justified: … MIN_RADIUS_M (tools/blender/clearance.py)` + `FAIL test_the_name_from_this_task_is_gone` |
| KN-2 | martwy **słownik** `MARTWE_PROGI_M` — poza starym, węższym zasięgiem | `FAIL test_every_unread_constant_is_justified: … MARTWE_PROGI_M (tools/blender/clearance.py)` |
| KN-3 | wpis na liście, który nie opisuje już martwej stałej | `FAIL test_no_justification_outlives_the_constant_it_describes: … NIE_MA_TAKIEJ` + `FAIL test_the_justification_names_the_file_it_talks_about` |
| KN-4 | stała czytana **wyłącznie** ze skryptu CI | bez odczytu w `.sh`: `FAIL … PROG_TYLKO_DLA_CI_M`; **po** dopisaniu odczytu w `.sh`: zielono |

KN-2 jest tu warta osobnego zdania: pokazuje, że szerszy zasięg z §2 nie jest ozdobą —
przy węższym ten słownik przeszedłby w milczeniu. KN-4 jest **parą**, nie jedną próbą:
sam FAIL dowodziłby tylko, że bramka coś zgłasza; dopiero zniknięcie tego FAIL-a po
dopisaniu odczytu **w powłoce** dowodzi, że ścieżka pozapythonowa naprawdę jest czytana.

Dwie dalsze kontrole nie są jednorazowe — **są testami** i chodzą przy każdym
przebiegu: że przypisanie nie liczy się jako odczyt (gdyby się liczyło, każda definicja
czytałaby się sama i bramka nie zgłosiłaby **nigdy niczego** — zielona z tego samego
powodu, z którego zielone było `python3 <moduł>.py` przed 6.D25) i że `M.NAZWA` jest
odczytem.

## 6. Weryfikacja

```
$ python3 tools/tests/test_dead_constants.py
  6/6 przeszło
  RAZEM 4.010 s, 6 testów, 1 modułów
kod: 0
```

(Uruchomienie pojedynczego modułu tą drogą istnieje od 6.D25 — do wczoraj to polecenie
kończyłoby się kodem 0, nie wykonawszy ani jednego testu.)

## 7. Czego świadomie nie zrobiono

- **Funkcji i klas nieużywanych** — pole „Poza zakresem". Wymagałoby rozstrzygnięcia,
  czym jest publiczne API modułu; ta pozycja dotyczy przypisań modułowych.
- **Usunięcia `LOCATION_STATION`** — pole „Poza zakresem". To nie ciężar, tylko
  brakujący element wyliczenia GTFS, i jego usunięcie pogorszyłoby plik.
- **Nie tknięto zasięgu poza `tools/` i `src/`.** Stałe w `godot/` i w `tests/`
  (C#) nie są objęte; C# ma na to własne narzędzia kompilatora, a `godot/` nie było
  mierzone i wpisywanie go tu bez pomiaru byłoby zgadywaniem zasięgu.
