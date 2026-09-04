# T-113 · Rozkład jazdy i służby

**Zmierzone na commicie:** `e2c32e9`

Stan: **2026-09-01**. Wyjście: `tools/track/timetable.py`, `tools/physics/schedule_envelope.py`,
`tools/tests/test_timetable.py`, `tools/tests/test_schedule_envelope.py`.
Zależy od T-110 (zrobione) i — dla odległości — od osi z T-210.

---

## 1. Co zrobiłem

Wyciągnąłem z oficjalnego GTFS STIB takt, rozpiętość służby, liczbę kursów naraz,
rozkładowy czas postoju i rozkładowy czas jazdy między stacjami. Czasy jazdy złączyłem
po `stop_id` z chainage osi z T-210, więc odcinek dostał **zmierzoną długość**, a nie
tylko parę nazw. Na tym zestawieniu skonfrontowałem rozkład z modelem fizyki z T-310/T-311.

Feed: `stib_gtfs.zip`, 14,5 MB, 1 554 901 wierszy `stop_times`, 75 696 kursów,
338 kalendarzy, 571 wyjątków kalendarzowych. Dzień odniesienia: **2026-09-02, środa**.
Archiwum pobiera `tools/track/fetch_gtfs.py` (z rejestru źródeł, z hashem i manifestem);
w repo nie leży — to 14,5 MB do `build/`, a reguła 8 zabrania commitowania takich plików.

## 2. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/track/timetable.py --gtfs build/gtfs/stib_gtfs.zip --out build/timetable.json \
    --date 2026-09-02 --axis data/track/L1_A.json --axis data/track/L1_B.json \
    --axis data/track/L2_E.json --axis data/track/L5_C.json --axis data/track/L5_D.json \
    --axis data/track/L6_F.json

[ROZKŁAD] 20260902 (wednesday): 72 kalendarzy kursowania (+0 / -15 z wyjątków), 1383 kursów metra
[ROZKŁAD] linia 1 kier. 0:  184 kursów, 05:15:09–24:30:37, takt mediana 5:10, szczyt 5:10, naraz 7 kursów o 06:44:37
[ROZKŁAD] linia 1 kier. 1:  177 kursów, 04:58:00–24:04:51, takt mediana 5:10, szczyt 5:10, naraz 6 kursów o 06:57:36
[ROZKŁAD] linia 5 kier. 0:  184 kursów, 05:11:28–24:23:09, takt mediana 5:10, szczyt 5:10, naraz 8 kursów o 06:24:01
[ROZKŁAD] linia 5 kier. 1:  180 kursów, 05:06:44–24:12:23, takt mediana 5:10, szczyt 5:10, naraz 8 kursów o 06:58:28
[ROZKŁAD] linia 6 kier. 0:  166 kursów, 05:14:51–24:19:39, takt mediana 5:40, szczyt 5:40, naraz 7 kursów o 06:51:51
[ROZKŁAD] linia 6 kier. 1:  167 kursów, 05:06:24–24:20:10, takt mediana 5:40, szczyt 5:40, naraz 7 kursów o 06:52:08
[ROZKŁAD] linia 2 kier. 0:  162 kursów, 05:32:54–24:24:20, takt mediana 5:40, szczyt 5:40, naraz 5 kursów o 06:22:55
[ROZKŁAD] linia 2 kier. 1:  163 kursów, 05:20:03–24:22:40, takt mediana 5:42, szczyt 5:40, naraz 5 kursów o 06:52:34
[SŁUŻBY] najwięcej kursów naraz w całym metrze: 48 — tyle składów jest w danej chwili w ruchu
[SŁUŻBY] obiegów pojazdów (block_id): 71, naraz w służbie 56 o 07:06:44, kursów na obieg 6–35, czas w służbie mediana 13 h 27 min
[ROZKŁAD] odcinków międzystacyjnych: 210, z odległością wzdłuż osi: 90
[POSTÓJ] linia 1 kier. 0: pośrednich 3450/3450 niezerowych (100.0 %), min 15 s, mediana 20 s, maks 45 s
[POSTÓJ] linia 1 kier. 1: pośrednich 3399/3399 niezerowych (100.0 %), min 15 s, mediana 19 s, maks 36 s
[POSTÓJ] linia 5 kier. 0: pośrednich 4652/4652 niezerowych (100.0 %), min 15 s, mediana 19 s, maks 45 s
[POSTÓJ] linia 5 kier. 1: pośrednich 4619/4619 niezerowych (100.0 %), min 12 s, mediana 19 s, maks 36 s
[POSTÓJ] linia 6 kier. 0: pośrednich 3983/3983 niezerowych (100.0 %), min 15 s, mediana 24 s, maks 34 s
[POSTÓJ] linia 6 kier. 1: pośrednich 3957/3957 niezerowych (100.0 %), min 15 s, mediana 24 s, maks 34 s
[POSTÓJ] linia 2 kier. 0: pośrednich 2738/2738 niezerowych (100.0 %), min 15 s, mediana 24 s, maks 34 s
[POSTÓJ] linia 2 kier. 1: pośrednich 2756/2756 niezerowych (100.0 %), min 15 s, mediana 24 s, maks 34 s
[ROZKŁAD] zapisano build/timetable.json
```

```
$ python3 tools/tests/test_all.py
  450/450 przeszło
```

## 3. Postój: pomyliłem się i pomiar mnie poprawił

Pisząc narzędzie założyłem w docstringu, że feed STIB ma `arrival_time == departure_time`
i postoju nie da się z niego wyodrębnić. Pomiar to obalił, więc docstring poszedł do
przepisania, a nie liczba do naciągnięcia.

Pierwszy pomiar dał „93–95 % zatrzymań z niezerowym postojem". Ta liczba była **moja,
nie STIB-owska**: rozcieńczały ją krańce kursów, które w GTFS mają `arrival == departure`
z definicji i nie są postojem zerowym, tylko brakiem postoju w tym kursie. Po rozdzieleniu:

| | zatrzymań | z niezerowym postojem |
|---|---:|---:|
| pośrednie | 29 554 | **29 554 (100,0 %)** |
| krańce kursów | 2 766 | 870 |

**Każde pośrednie zatrzymanie metra tego dnia ma rozkładowy postój.** Rozkład postoju:

| postój | udział skumulowany |
|---:|---:|
| 12 s | 0,0 % (jedno zatrzymanie w całym dniu) |
| 15 s | 17,2 % |
| 19 s | 40,8 % |
| 20 s | 45,5 % |
| 25 s | 83,2 % |
| 30 s | 94,9 % |
| 45 s | 100,0 % |

Mediana zależy od linii: 19–20 s na L1/L5, 24 s na L2/L6.

## 4. Co to odblokowuje w T-312

T-312 świadomie **nie wpisało** czasu wymiany pasażerów i `DoorCycle` nie ma z tego powodu
konstruktora bezargumentowego. Rozkład tej liczby nadal nie podaje, ale ją **ogranicza**:

```
postój rozkładowy = cykl drzwi (8,5 s, T-312) + wymiana pasażerów + ewentualna rezerwa
```

Stąd **górne** ograniczenie wymiany pasażerów, bo rezerwy z postoju nie da się wyodrębnić:

| przypadek | postój | wymiana ≤ |
|---|---:|---:|
| najkrótszy postój w sieci | 12 s | 3,5 s |
| pierwszy kwartyl (15 s) | 15 s | 6,5 s |
| mediana L1/L5 (19 s) | 19 s | 10,5 s |
| mediana L2/L6 (24 s) | 24 s | 15,5 s |
| najdłuższy postój | 45 s | 36,5 s |

Osobno wynika z tego kontrola spójności T-312: **cykl 8,5 s mieści się nawet w najkrótszym
rozkładowym postoju 12 s**, z zapasem 3,5 s. Gdyby wyszedł dłuższy niż 12 s, oznaczałoby to,
że fazy z `docs/02-simulation.md` są nie do pogodzenia z rozkładem STIB — nie wyszedł.

To nadal **nie jest** liczba do wpisania do `DoorCycle`. Jest to przedział, w którym musi
leżeć, i jest to pierwszy zmierzony przedział, jaki repo ma dla tej wielkości.

## 5. Koperta prędkości liniowej — najważniejszy wynik

W repo **nie ma źródła na prędkość dopuszczalną na torze**. `speed_limits` w każdej z sześciu
osi z T-210 jest pustą listą, a `max_speed_kmh` = 80 w rejestrze M7 ma `status: design_model`
i `source_id: null` — jest to prędkość konstrukcyjna pojazdu przepisana z legacy symulatora.

Rozkład pozwala tę dziurę ograniczyć od dołu. Dla odcinka o zmierzonej długości `L`
i rozkładowym czasie jazdy `T` szukamy najmniejszej prędkości szczytowej `v`, przy której
profil rozpęd–jazda–hamowanie mieści się w `T`. Ponieważ

```
czas_fizyczny(v_rzeczywista)  ≤  czas_rzeczywisty  ≤  T_rozkładowy
```

a `czas_fizyczny` maleje z `v`, **każda prędkość niższa od znalezionej nie zdążyłaby**.

```
$ python3 tools/physics/schedule_envelope.py --timetable build/timetable.json \
    --out build/schedule-envelope.json

[KOPERTA] 55 odcinków, masa AW0 170000 kg, hamulec 1.10 m/s², zryw 0.75 m/s³
[KOPERTA] L5_D BEAULIEU → DEMEY:   886.7 m, rozkład  69.0 s, bez ograniczenia  58.7 s, wymaga  57.65 km/h
[KOPERTA] L2_E RIBAUCOURT → YSER:   900.7 m, rozkład  70.0 s, bez ograniczenia  59.3 s, wymaga  57.47 km/h
[KOPERTA] L1_A SCHUMAN → MERODE:  1219.0 m, rozkład  90.0 s, bez ograniczenia  70.6 s, wymaga  57.41 km/h
[KOPERTA] L5_C AUMALE → SAINT-GUIDON:   737.2 m, rozkład  60.0 s, bez ograniczenia  52.9 s, wymaga  57.03 km/h
[KOPERTA] L1_B ROODEBEEK → VANDERVELDE:   810.6 m, rozkład  65.0 s, bez ograniczenia  55.8 s, wymaga  56.46 km/h
[KOPERTA] L6_F BOCKSTAEL → STUYVENBERGH:   831.2 m, rozkład  68.0 s, bez ograniczenia  56.6 s, wymaga  54.11 km/h
...
[KOPERTA] L1_A MAELBEEK → SCHUMAN:   314.9 m, rozkład  45.0 s, bez ograniczenia  33.1 s, wymaga  29.71 km/h
[KOPERTA] dolne ograniczenie prędkości liniowej dla sieci: 57.65 km/h (wiąże BEAULIEU → DEMEY)
```

Dwa wyniki:

**Zero odcinków nierealizowalnych.** Model fizyki z T-310/T-311 dowozi **każdy** z 55
odcinków w rozkładowym czasie, z rezerwą 4,3 s (najciaśniej) do 45,3 s (najluźniej),
mediana 10,7 s. Gdyby model był za wolny, wyszłoby to tutaj na konkretnym odcinku
z nazwami stacji — nie wyszło. Jest to pierwsza konfrontacja fizyki M7 z czymkolwiek
zewnętrznym; dotąd testy sprawdzały tylko parytet C# z referencją Pythona.

**Sześć pakietów zbiega się do tej samej liczby.** Najbardziej wymagający odcinek
każdego pakietu, liczony niezależnie:

| pakiet | odcinków | wymagana prędkość |
|---|---:|---:|
| L5_D | 6 | 57,65 km/h |
| L2_E | 16 | 57,47 km/h |
| L1_A | 11 | 57,41 km/h |
| L5_C | 8 | 57,03 km/h |
| L1_B | 8 | 56,46 km/h |
| L6_F | 6 | 54,11 km/h |

Sześć niezależnych fragmentów sieci, trzy różne linie, rozrzut 3,5 km/h. To wygląda jak
konstrukcja rozkładu wokół jednej prędkości projektowej, ale **tego nie twierdzę** —
zbieżność jest obserwacją, a nie dowodem, i równie dobrze może wynikać z tego, że rozkłady
wszystkich linii układa ten sam zespół tą samą metodą.

Dla składu obciążonego (AW2, 221 940 kg) ograniczenie rośnie do **61,42 km/h**
(wiąże Aumale → Saint-Guidon).

### Czego to nie dowodzi

Ograniczenie jest **warunkowe względem modelu**, a model jest w całości `design_model`:
krzywa trakcyjna z T-310 i hamulec służbowy 1,10 m/s² z `docs/02-simulation.md`. Gdyby M7
rozpędzał się mocniej, ta sama rozkładowa jazda wyszłaby przy niższej prędkości szczytowej.
Liczba mówi „przy tym modelu nie da się wolniej", a nie „tak jeździ metro w Brukseli".

Ponieważ rozkład zawiera rezerwę, prędkość rzeczywista jest **wyższa** niż 57,65 km/h —
ograniczenie jest zachowawcze i po tej stronie.

## 6. Odległości i prędkości średnie

90 z 210 odcinków rozkładowych dostało odległość wzdłuż osi; po odrzuceniu tego samego toru
obsługiwanego przez dwie linie (pień 1/5, pierścień 2/6) zostaje **55 różnych odcinków toru**.
Pozostałe 120 to pary stacji rozdzielone między dwa pakiety albo leżące poza sześcioma osiami.

**Pary międzypakietowe świadomie nie dostają odległości.** Chainage każdego pakietu liczy się
od jego własnego zera, więc odjęcie ich od siebie dałoby liczbę wyglądającą jak metry i nie
będącą metrami. Ciągłość chainage między pakietami zamyka T-112, nie to zadanie. Test
`test_timetable_refuses_distance_across_two_packages` przypina to zachowanie.

Skrajne prędkości średnie rozkładowe: **25,2 km/h** (Maelbeek → Schuman, 315 m) do
**48,8 km/h** (Schuman → Merode, 1219 m). Krótki odcinek jest wolniejszy w średniej, bo
rozpęd i hamowanie zajmują na nim cały czas jazdy — to nie jest ograniczenie prędkości,
tylko geometria profilu.

## 7. Służby

`services_active` = 72 to **kalendarze kursowania GTFS**, nie służby drużyn — narzędzie
początkowo wypisywało „72 służb" i było to nazwanie czegoś, czym ta liczba nie jest.
Poprawione.

Obiegi pojazdów **są w feedzie**. Napisałem najpierw, że nie ma w nim `block_id`, i było to
zgadywanie zamiast sprawdzenia: `trips.txt` ma tę kolumnę i ma ją wypełnioną dla wszystkich
1383 kursów metra. `block_id` wiąże kursy wykonywane po kolei tym samym pojazdem, więc obiegi
są **odczytem**, a nie oszacowaniem z taktu i czasu obrotu.

```
[SŁUŻBY] najwięcej kursów naraz w całym metrze: 48 — tyle składów jest w danej chwili w ruchu
[SŁUŻBY] obiegów pojazdów (block_id): 71, naraz w służbie 56 o 07:06:44, kursów na obieg 6–35,
         czas w służbie mediana 13 h 27 min
```

Trzy różne liczby, każda o czym innym:

| liczba | co znaczy |
|---:|---|
| **71** | obiegów w ciągu doby — tyle pojazdów wyjeżdża, licząc te wychodzące tylko na szczyt |
| **56** | obiegów jednocześnie w służbie o 07:06:44 — z pojazdami stojącymi na obrocie |
| **48** | kursów jednocześnie w ruchu — bez stojących na obrocie |

Różnica 56 − 48 = 8 to pojazdy stojące w tej chwili na krańcu. Suma maksimów per kierunek
wynosi 53, więcej niż sieciowe 48, bo maksima linii wypadają o różnych porach — dlatego
liczy się je jednym przemiataniem po całej sieci, a nie sumowaniem.

Obieg trwa od 3 h 36 min do 19 h 45 min, mediana 13 h 27 min, i wykonuje od 6 do 35 kursów.
Rozkład jest dwugarbny: 26 obiegów po 6–13 kursów (wyjazdy szczytowe) i 45 obiegów po 15–35
kursów (całodzienne). **Żadna para kursów w tym samym obiegu się nie nakłada** — narzędzie
to sprawdza, bo obieg z nakładką jest obiegiem, którego żaden pojazd nie wykona.

Nadal nie jest to **wielkość floty**: 71 to pojazdy w ruchu w dniu roboczym, bez rezerwy
i bez naprawy. Dla porównania `data/network/lines.json` podaje 36 dostarczonych M7, 21 M6
i 217 wagonów MX — przy sześciu wagonach na skład jest z czego wystawić 71 obiegów.

Dzień tygodnia zmienia takt bez zmiany rozpiętości służby:

| dzień | kursów metra | takt L1 | takt L2 |
|---|---:|---:|---:|
| środa | 1383 | 5:10 | 5:40 |
| sobota | 1054 | 7:30 | 7:30 |
| niedziela | 928 | 10:00 | 10:00 |

## 8. Czego świadomie nie zrobiłem

- **Nie wpisałem czasu wymiany pasażerów do `DoorCycle`.** Rozkład daje przedział, nie liczbę,
  a decyzja T-312 o niewpisywaniu liczby bez źródła nadal obowiązuje.
- **Nie dopisałem `speed_limits` do osi.** `data/` jest tylko do odczytu (reguła 6),
  a 57,65 km/h jest ograniczeniem warunkowym względem modelu, nie prędkością dopuszczalną.
  Wpisane do osi wyglądałoby dokładnie tak samo jak prawdziwe ograniczenie ze źródła STIB.
- **Nie liczyłem odległości między pakietami** — patrz §6.
- **Nie modelowałem obrotu na krańcu.** Czas obrotu wychodzi z `block_id` jako przerwa między
  kursami jednego pojazdu, ale nie da się z niego odróżnić obrotu technicznego od postoju
  regulacyjnego. Do T-320, gdzie ta różnica zaczyna mieć znaczenie.
- **Nie napisałem trzeciej implementacji fizyki.** `schedule_envelope.py` składa rozpęd
  z zamrożonej referencji parytetu T-310 i hamowanie z zamkniętych wzorów T-311; własnego
  całkowania nie ma.

## 9. Co zauważyłem, ale nie tknąłem

- **Linia 2 kier. 0 w sobotę kończy o 18:27:16**, przy 24:24:20 w środę i niedzielę.
  Wygląda na rozbicie służby na dwa `route_id` albo na sobotni wariant trasy. Nie ruszałem —
  do sprawdzenia przy T-320, gdzie rozpiętość służby zaczyna mieć znaczenie.
- **870 z 2766 krańców kursu ma niezerowy „postój"** — to postój przed odjazdem na krańcu
  początkowym, nie wymiana pasażerów w biegu. Raportowane osobno, żeby nie wpadło do
  rozkładu postoju.
- **Rezerwa rozkładowa nie jest stała**: od 4,3 s (Gare Centrale → Parc) do 45,3 s
  (Eddy Merckx → Erasme). Odcinki przy krańcach i zajezdniach mają wyraźnie większą
  rezerwę. Może to być zapas przed obrotem, może ograniczenie prędkości przy zajezdni —
  z rozkładu nie da się rozstrzygnąć.
- **Feed ma `shapes.txt` z 41 kształtami dla metra.** Nie użyłem ich: oś z T-210 pochodzi
  z UrbIS i INSPIRE, a kształt GTFS jest przebiegiem rysowanym dla pasażera, nie geometrią
  toru. Zestawienie jednego z drugim byłoby osobnym zadaniem kontrolnym i nie należy do T-113.
