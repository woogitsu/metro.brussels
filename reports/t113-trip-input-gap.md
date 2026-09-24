# T-113 → LineCore: brak danych pojedynczych kursów w wersjonowanym wejściu

**Audyt 24.09.2026 na `d583065`** (plus lokalny raport `72d7551`), bez sieci i bez źródłowego archiwum GTFS.

## Co jest w repozytorium

`data/network/gtfs-manifest.json` identyfikuje feed STIB `2_20_20260831_010702`, jego SHA-256 i listę tabel, ale **nie zawiera rekordów** `trips.txt` ani `stop_times.txt`. `reports/T-113-timetable.md` zapisuje agregaty: takt 5:10 dla L1/L5, 48 kursów sieciowo jednocześnie, 71 obiegów w dobie. `reports/service-day.md` zapisuje weryfikację 71 obiegów i 56 pojazdów jednocześnie w służbie. Test `tools/tests/test_timetable.py` tworzy mały **syntetyczny** GTFS w pamięci; nie jest próbką rzeczywistego rozkładu STIB.

`tools/track/timetable.py` podczas generowania widzi rzeczywiste `trip_id`, `route_id`, `direction_id`, `block_id` i sekwencję `(stop_id, arrival, departure)` z GTFS. **W chwili pierwotnego audytu** do `build/timetable.json` zapisywał jednak tylko `duties.rows[].trip_windows` jako pary `[start, end]`, bez identyfikatora kursu i trasy, `lines[]` jako statystyki taktu, a `segments[]` jako statystyki czasów między stacjami. Dodane później `trip_records` zachowuje relację kurs → kierunek → przystanki; sam `build/timetable.json` nie jest wersjonowany i nie leżał lokalnie w chwili audytu.

## Dokładny brak do adaptera jednej osi

Dla każdego rzeczywistego kursu trzeba znać co najmniej: `trip_id`, `block_id`, linię i kierunek, uporządkowane `stop_id` z godzinami przyjazdu/odjazdu oraz identyfikatory stacji granicznych L1_A. Z tego można dopiero wyznaczyć moment wejścia na oś (`releaseStep`), docelowy koniec przejazdu oraz powiązanie kolejnych kursów tego samego pojazdu. Obecne `trip_windows` podaje tylko początek i koniec **całego kursu**; nie mówi, czy ani kiedy przejeżdża Gare de l'Ouest i Merode. `ServiceDay` potrafi z nich policzyć służbę, ale nie może ich bez zgadywania przekazać do `LineCore.Add`.

Następny wymagany input offline to archiwum STIB o **tym samym** `content_sha256`, który stoi w manifeście, lub wersjonowana projekcja jego rekordów dla L1_A, zachowująca wymienione pola i pochodzenie. Generator zapisuje już osobne `trip_records` z `trip_id`, `block_id`, linią, kierunkiem i pełną sekwencją godzin przystanków, gdy ma źródłowy feed. Bez archiwum o zweryfikowanym odcisku nie da się jednak wytworzyć rzeczywistych rekordów ani zmierzyć zgodności z GTFS. Po otrzymaniu danych można napisać deterministyczny wybór kursów przecinających pakiet A i test porównujący wyjazdy z GTFS. Do tego czasu adapter używający agregatów byłby wymyślonym rozkładem. Nie dodano go, ani polityki dyspozytora.

## Sprawdzenie

Audyt opiera się na schemacie w `tools/track/timetable.py` i spisie plików śledzonych przez Git. Lokalnie wykonano testy parsera GTFS oraz bramkę higieny raportów; nie pobierano feedu i nie uruchamiano gry.
