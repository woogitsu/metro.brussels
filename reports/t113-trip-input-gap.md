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
`trip_records`, a jego tryb `--project-trips` deterministycznie wybiera kursy przecinające pakiet A.
Projekcja jest już wejściem dla `LineEntrySchedule`, a ograniczona bramka
`LineEntryGate` rejestruje pojedyncze wjazdy na wskazanej stacji i w dniu służby.
Pełna polityka dyspozytora i przejście tego samego pojazdu między kolejnymi kursami
nie są zaimplementowane; nie wykonano porównania 357 symulowanych kursów z GTFS.

## Granica obecnego LineCore wobec 357 kursów (24.09.2026, `9280d3b`)

Pomiar na tej samej projekcji i tym samym SHA GTFS: **176** kursów wchodzi na L1_A od
Gare de l'Ouest (`stop_id` 8733, kilometraż 0), a **181** od Beekkant (`stop_id`
8742, kilometraż 509,73 m). `LineCore.Add(trainId, releaseStep)` przyjmuje tylko
identyfikator i krok wyjazdu. Faza wjazdu tworzy `LineDrive` dla całej osi i rejestruje
każdy skład w `_entryChainageM = axis.Stations[0].ChainageM`. Podanie wszystkich 357
kursów przez to API umieściłoby 181 składów na **złej stacji**. Nie jest to różnica
zaokrąglenia czasu, tylko inna pozycja wejścia.

W 357 kursach jest **39 różnych `block_id`**, każdy występuje wielokrotnie (najwięcej
17 kursów jednego obiegu). Żadne dwa kolejne przejazdy pakietu A w tym samym obiegu
nie nakładają się; najmniejsza przerwa po przyjeździe do Merode do następnego
odjazdu z pierwszej stacji pakietu wynosi **2993 s**. To nie jest czas nawrotu na
Merode: pomiędzy tymi przejazdami pojazd jedzie także poza pakietem A. `LineCore`
ma jeden stały `ReleaseStep` na `LineTrain`, a jego nawrót ponownie wpuszcza ten sam
skład po lokalnym czasie, bez przypisania następnego `trip_id` i jego godziny.
Zgłoszenie każdego `trip_id` jako oddzielnego składu zgubiłoby tożsamość pojazdu;
zgłoszenie jednego `block_id` nie zaplanowałoby kolejnych kursów.

Ruch w tym samym czasie nie jest tu przeszkodą samą w sobie: rozkład osiąga maksimum
**6** przejazdów równocześnie na osi, a `LineCore` obsługuje N składów na jednym
zegarze i blokach. **W chwili pomiaru** brakowało wejścia w środku osi oraz
przeniesienia tego samego pojazdu między kursami według GTFS. Późniejszy
`AddAtStation` rozwiązuje pierwszy brak, a `LineEntrySchedule` wiąże krok wejścia
z dniem służby; `EnteredAtStep` nadal pokazuje faktyczny wjazd, który zajęty blok
może opóźnić. **Przeniesienie pojazdu między kursami i pełna polityka ruchowa
pozostają otwarte.** Nie należy twierdzić, że LineCore odtworzył 357 kursów.
Nie zmieniono automatycznego nawrotu ani polityki dyspozytora.

**Kontrola ciągłości obiegów po dodaniu planu wejść.** `BlockContinuity` używa
`block_id` wyłącznie jako klucza tego samego obiegu pojazdu; GTFS nie nadaje tu
numeru jednostki taboru. Dla każdego kursu sprawdza czas wejścia i wyjścia oraz
stacje graniczne. Odrzuca nakładanie się dwóch kursów jednego obiegu, ale nie
uznaje samej przerwy czasowej za dowód przejazdu poza pakietem.

Na projekcji dnia 20260902 z archiwum STIB SHA-256
`28c2fba48783e278d20f8f703759e3f729b72608d015e00d0f8215fa3b278bb6`
walidator odczytał 357 odcinków kursów, 39 obiegów i 318 par sąsiednich odcinków
tego samego obiegu **w projekcji L1_A**. Projekcja nie zawiera pełnych kursów
poza osią, więc sąsiedztwo w niej nie dowodzi sąsiedztwa w całym GTFS. Nie było
nakładek widocznych odcinków. **Wszystkie 318 par mają niewyjaśnioną
trasę między granicami pakietu:** poprzedni kurs kończy się w Merode (`8072`),
a następny zaczyna w Gare de l'Ouest (`8733`, 163 przypadki, przerwy 2993–3594 s)
lub Beekkant (`8742`, 155 przypadków, przerwy 4248–4708 s). To są tylko odstępy
między odcinkami w pakiecie A; bez pełnej trasy między kursami nie można określić
przejazdu technicznego, nawrotu ani chwili ponownego użycia składu w `LineCore`.

**Bramka pojedynczego wjazdu.** `LineEntryGate.QueueDue` przyjmuje typowany kurs
tylko wtedy, gdy `releaseStep` jest bieżącym krokiem LineCore, i przekazuje jego
`trip_id` oraz indeks stacji do `AddAtStation`. Samo zgłoszenie nie oznacza fizycznego
wjazdu: `LineCore.Step` sprawdza zajętość bloków i ustawia `EnteredAtStep` dopiero
po wejściu. Test na dwóch kursach o tym samym czasie i peronie pokazuje opóźnienie
drugiego składu. Bramka odmawia drugiego kursu tego samego `block_id`, ponieważ
nie ma jeszcze reguły przekazania tożsamości pojazdu między kursami. Jej użycie
nie jest dyspozyturą dla 357 kursów ani modelem przejazdu między krańcami osi.
Gdy dwa kursy mają ten sam `releaseStep` i peron, pierwszy zgłoszony dostaje
pierwszą próbę wjazdu; GTFS nie ustala tu priorytetu przy konflikcie, więc
kolejności zgłoszeń nie należy przedstawiać jako oficjalnej decyzji ruchowej.

**Remisy rozkładowe.** W tej samej zweryfikowanej projekcji 20260902 wszystkie
357 wartości `release_s` są różne; najmniejszy odstęp między dwoma wjazdami to
55 s, czyli 6600 kroków przy 120 Hz. `LineEntrySchedule` porządkuje dane po
`(releaseStep, trip_id)`, co daje stabilny porządek także dla przyszłego feedu
z remisem; test syntetyczny go sprawdza. Jest to porządek techniczny, nie
uprawnienie do pierwszeństwa na torze. `BlockContinuity` pokazuje przejścia
posortowane po `block_id`, a wewnątrz obiegu po czasie wejścia i przy remisie
po `trip_id`. Wywołujący bramkę powinien brać kursy w kolejności planu, lecz
rozstrzygnięcie konfliktu wjazdów wymaga osobnej polityki ruchowej.

**Kontrola pominiętych wjazdów.** Sama `QueueDue` odmawiała kursowi
zgłoszonemu po jego `releaseStep`, ale nie mogła wykryć kursu, którego nikt
w ogóle nie zgłosił. Bramka z przekazanym `LineEntrySchedule` ma teraz `Step()`:
zatrzymuje zegar przed każdym krokiem, dla którego istnieje niezgłoszony kurs,
i wymaga porządku planu przy jednakowym czasie. Nie tworzy składów automatycznie.
Kontrola obowiązuje tylko wtedy, gdy wywołujący używa `LineEntryGate.Step()`
zamiast bezpośredniego `LineCore.Step()`; API rdzenia nadal pozostaje dostępne
do innych scenariuszy. Wjazd już zgłoszonego składu może zostać opóźniony przez
zajęte bloki, co nadal mierzy `EnteredAtStep`.

## Sprawdzenie

Audyt opiera się na schemacie w `tools/track/timetable.py` i spisie plików śledzonych przez Git.
Archiwum pobrano do lokalnego cache, sprawdzono jego SHA-256 i wykonano pomiar projekcji;
testy parsera GTFS oraz pełna bramka narzędzi przeszły na połączonym commicie.
