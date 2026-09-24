# T-113 → LineCore: brak danych pojedynczych kursów w wersjonowanym wejściu

**Audyt 24.09.2026 na `d583065`** (plus lokalny raport `72d7551`), następnie pomiar
24.09.2026 na `a1cefb5` z archiwum GTFS identycznym bajtowo z manifestem.

## Znalezione archiwum i projekcja L1_A

Archiwalna kopia z [gtfs.flatturtle.cloud](https://gtfs.flatturtle.cloud/stib-mivb/stib-mivb-gtfs_2026-09-01.zip)
ma **14 543 732 B** i SHA-256
`28c2fba48783e278d20f8f703759e3f729b72608d015e00d0f8215fa3b278bb6` —
dokładnie tyle samo co `data/network/gtfs-manifest.json` dla feedu STIB
`2_20_20260831_010702`. Oficjalny [opis zbioru STIB](https://stibmivb.opendatasoft.com/explore/dataset/gtfs-files-production/information/?flg=en-gb)
potwierdza, że obejmuje rozkładowe godziny zatrzymań. ZIP i wygenerowane JSON leżą
wyłącznie w lokalnym cache poza repozytorium. Identyczność jest potwierdzona odciskiem
całego ZIP, a nie podobieństwem daty lub rozmiaru.

Tryb `--project-trips` w `tools/track/timetable.py` odmawia niezgodnego SHA i złącza kursy z osią
po oficjalnych `stop_id`. Dla środy **02.09.2026** generator znajduje 1383 aktywne
kursy metra, a projekcja **357 rozkładowych przejazdów L1_A**: 173 L1 od Gare de
l'Ouest, 4 L1 od Beekkant, 3 L5 od Gare de l'Ouest i 177 L5 od Beekkant, wszystkie
do Merode. Należą do 39 `block_id`; maksimum rozkładowo jednocześnie na tej osi,
licząc od odjazdu pierwszej stacji pakietu do przyjazdu Merode, to **6**. Siedem
innych kursów zawiera tylko Merode — pojedynczy wspólny przystanek nie jest
przejazdem pakietu. Wynik jest **projekcją rozkładu**, nie symulacją 357 pociągów w
LineCore i nie określa polityki dyspozytora lub nawrotu.

Odtworzenie: uruchomić `tools/track/timetable.py --project-trips` z `--gtfs` wskazującym
archiwum o podanym SHA, `--date 2026-09-02`, `--axis data/track/L1_A.json` oraz
`--out` w katalogu poza `data/`. Testy syntetyczne wiążą identyfikator kursu, obieg,
czas wejścia i kolejność stacji, a także odrzucają kurs dotykający jednego peronu.

## Co jest w repozytorium

`data/network/gtfs-manifest.json` identyfikuje feed STIB `2_20_20260831_010702`, jego SHA-256 i listę tabel, ale **nie zawiera rekordów** `trips.txt` ani `stop_times.txt`. `reports/T-113-timetable.md` zapisuje agregaty: takt 5:10 dla L1/L5, 48 kursów sieciowo jednocześnie, 71 obiegów w dobie. `reports/service-day.md` zapisuje weryfikację 71 obiegów i 56 pojazdów jednocześnie w służbie. Test `tools/tests/test_timetable.py` tworzy mały **syntetyczny** GTFS w pamięci; nie jest próbką rzeczywistego rozkładu STIB.

`tools/track/timetable.py` podczas generowania widzi rzeczywiste `trip_id`, `route_id`, `direction_id`, `block_id` i sekwencję `(stop_id, arrival, departure)` z GTFS. **W chwili pierwotnego audytu** do `build/timetable.json` zapisywał jednak tylko `duties.rows[].trip_windows` jako pary `[start, end]`, bez identyfikatora kursu i trasy, `lines[]` jako statystyki taktu, a `segments[]` jako statystyki czasów między stacjami. Dodane później `trip_records` zachowuje relację kurs → kierunek → przystanki; sam `build/timetable.json` nie jest wersjonowany i nie leżał lokalnie w chwili audytu.

## Dokładny brak do adaptera jednej osi

Dla każdego rzeczywistego kursu trzeba znać co najmniej: `trip_id`, `block_id`, linię i kierunek, uporządkowane `stop_id` z godzinami przyjazdu/odjazdu oraz identyfikatory stacji granicznych L1_A. Z tego można dopiero wyznaczyć moment wejścia na oś (`releaseStep`), docelowy koniec przejazdu oraz powiązanie kolejnych kursów tego samego pojazdu. Obecne `trip_windows` podaje tylko początek i koniec **całego kursu**; nie mówi, czy ani kiedy przejeżdża Gare de l'Ouest i Merode. `ServiceDay` potrafi z nich policzyć służbę, ale nie może ich bez zgadywania przekazać do `LineCore.Add`.

Archiwum o wymaganym `content_sha256` jest teraz dostępne lokalnie. Generator zapisuje
`trip_records`, a osobny skrypt deterministycznie wybiera kursy przecinające pakiet A.
Następny etap może użyć tej projekcji jako wejścia do LineCore i porównać symulowane
wyjazdy z GTFS. Polityka dyspozytora i adapter LineCore nadal nie są zaimplementowane.

## Sprawdzenie

Audyt opiera się na schemacie w `tools/track/timetable.py` i spisie plików śledzonych przez Git. Lokalnie wykonano testy parsera GTFS oraz bramkę higieny raportów; nie pobierano feedu i nie uruchamiano gry.
