# Najciaśniejszy łuk na każdej z sześciu osi — i skrajnia M7 punkt po punkcie

**Zmierzone 06.09.2026 na commicie:** `7842878`

Pozycja 6.B5. `reports/M7-curve-clearance.md` zmierzył i opisał metodę na jednym
pakiecie; tu jest zastosowana do wszystkich sześciu osi z `data/track/`. Nie dochodzi
ani jedna nowa liczba o sieci: wejściem są te same osie, ta sama specyfikacja
`data/vehicle/m7-spec.json` i te same trzy profile z `tools/blender/profiles.py`.

- narzędzie: `tools/blender/clearance.py` (czysty Python, bez `bpy`), z dopisanym
  przebiegiem **punkt po punkcie** (`--scan`)
- testy: `tools/tests/test_curve_radius_axes.py` — wyłącznie na to, czym B-F różni się od A
- odtworzenie: `python3 tools/blender/clearance.py --alignment data/track/L5_D.json
  --profile box_double --scan --report-only`

Metody nie powtarzam — jest w `reports/M7-curve-clearance.md` §1 i §2. Powtarzam
za to jej granicę, bo bez niej cała ta tabela czyta się jak fakt o metrze: promień
jest mierzony na **cięciwie długości pudła członu**, a nie na trójce sąsiednich
wierzchołków, i jest własnością skomitowanej łamanej, nie łuku zbudowanego w Brukseli.

---

## 1. Najciaśniejszy łuk każdej z sześciu osi

Wariant `pessimistic` liczony na skomitowanej łamanej, `optimistic` na tej samej osi
zagęszczonej Catmull-Romem co 5 m. Werdykt zapada na pesymistycznym.

| pakiet | oś | R min [m] | kilometraż [m] | gdzie to jest | P05 [m] |
|---|---|---:|---:|---|---:|
| A — Pień 1/5 | `data/track/L1_A.json` | **50,87** | 2518,6 | Comte de Flandre +463,8 m, przed Sainte-Catherine | 78,82 |
| B — Wschód 1 | `data/track/L1_B.json` | 73,97 | **30,0** | Montgomery +30,0 m | 98,55 |
| C — Zachód 5 | `data/track/L5_C.json` | 52,94 | 2543,6 | Veeweyde +477,2 m, przed Bizet | 82,87 |
| D — Wschód 5 | `data/track/L5_D.json` | **82,28** | 1916,2 | Delta +208,7 m, przed Beaulieu | 96,75 |
| E — Pierścień 2/6 | `data/track/L2_E.json` | 59,13 | 4285,7 | Trône +58,3 m, przed Porte de Namur | 95,64 |
| F — Północ 6 | `data/track/L6_F.json` | 74,02 | 1286,2 | Pannenhuis +567,4 m, przed Bockstael | 91,04 |

Ten sam pomiar na osi zagęszczonej:

| pakiet | R min [m] | kilometraż [m] | ten sam łuk co wyżej? |
|---|---:|---:|---|
| A | 85,94 | 2518,8 | tak, +0,2 m |
| B | 119,54 | 30,0 | tak, 0,0 m |
| C | 90,05 | 2543,7 | tak, +0,1 m |
| D | 132,59 | **1242,6** | **nie — 673,6 m dalej**, Pétillon +594,7 m |
| E | 95,56 | 4285,8 | tak, +0,1 m |
| F | 118,53 | **4262,4** | **nie — 2976,2 m dalej**, Heysel +360,3 m |

Najciaśniejszy łuk całej szóstki leży w pakiecie **A**, czyli w tym już zbudowanym.
Ten sam wniosek, inną drogą, ma `reports/clearance-BE.md` §1 — tam mierzony luzem
na siatce w Blenderze na trzech pakietach, tu promieniem czystym Pythonem na sześciu.

## 2. Skrajnia punkt po punkcie

`evaluate` woła `profiles.fits_gauge` **raz**, w minimum promienia. Wystarcza to do
werdyktu tylko przy założeniu, że zapas jest monotoniczny względem promienia. Przebieg
`--scan` woła `fits_gauge` osobno w każdym punkcie osi, czyli tego nie zakłada, i podaje
dwie rzeczy, których minimum podać nie umie: **ile** punktów nie przechodzi i **gdzie**.

### 2.1 Profil `box_double` — sześć osi na sześć przechodzi

| pakiet | punktów (łamana / zagęszczona) | punktów bez skrajni | najmniejszy zapas [m] | @ kilometraż |
|---|---:|---:|---:|---:|
| A | 401 / 1331 | **0 / 0** | +0,4713 | 2518,6 |
| B | 319 / 1016 | **0 / 0** | +0,6621 | 30,0 |
| C | 331 / 1076 | **0 / 0** | +0,4953 | 2543,6 |
| D | 238 / 762 | **0 / 0** | +0,7043 † | 1916,2 |
| E | 545 / 1792 | **0 / 0** | +0,5568 | 4285,7 |
| F | 273 / 875 | **0 / 0** | +0,6624 | 1286,2 |

Profil `station` przechodzi tak samo, z zapasem od +0,8903 m (A) do +1,1233 m (D) †.

**† zapas WARUNKOWY.** Najciaśniejszy łuk pakietu D leży w 1916,2 m, a czy na tym
kilometrażu jest ściana tunelu, **nie da się rozstrzygnąć na dostępnych danych**:
werdykt ma tam jedno źródło z czterech klas hierarchii i jest nim OSM, a punkt leży
w strefie portalu (59,8 m przed tunelem według UrbIS, 14,9 m według OSM), której
`PORTAL_HALO_M = 60 m` z `tools/track/surface_sections.py` odmawia werdyktu.
Pełne przejście po hierarchii: `reports/6b26-luk-D-tunel.md`. Liczba jest poprawna
dla modelu; warunkowy jest model, nie arytmetyka.

### 2.2 Profil `bore_single` — trzy osie na sześć NIE przechodzą

To jest ta część wyniku, którą trzeba nazwać wprost razem z liczbą.

| pakiet | zapas [m] | punktów bez skrajni | przedziały kilometrażu bez skrajni |
|---|---:|---:|---|
| **A** | **−0,1117** | **11 z 401** | 2488,7–2533,6; 2773,5–2848,4; 3403,0 |
| **C** | **−0,0877** | **5 z 331** | 2513,7–2573,5 |
| **E** | **−0,0262** | **4 z 545** | 4255,8–4285,7; 8586,3 |
| B | +0,0791 | 0 z 319 | — |
| D | +0,1213 † | 0 z 238 | — |
| F | +0,0794 | 0 z 273 | — |

**Pakiety A, C i E nie mieszczą się w projektowym `bore_single`** — odpowiednio
o **111,7 mm**, **87,7 mm** i **26,2 mm** na najciaśniejszym łuku. Na osi zagęszczonej
przechodzą wszystkie sześć, więc jest to dokładnie ten przypadek, przed którym
`reports/M7-curve-clearance.md` ostrzega: profil, który przechodzi dopiero po
wygładzeniu osi, nie jest profilem, na którym można polegać.

Znalezisko z pakietu A nie jest więc ani własnością jednego pakietu, ani całej sieci.
Granica jest policzalna z samego profilu: strzałka cięciwy 15,667 m zjada cały statyczny
zapas 0,495 m dokładnie przy **R = 62,2 m**. Trzy osie, które nie przechodzą, mają łuk
poniżej tej wartości (50,87 · 52,94 · 59,13 m), trzy pozostałe powyżej
(73,97 · 74,02 · 82,28 m) — i to jest cała reguła, bez ani jednego wyjątku.

Wniosek co do przyczyny zostaje ten sam co przy pakiecie A i **nie jest tu rozstrzygany**: `bore_single` ma
`source_level: design` i promień 3,05 m, który nie pochodzi z żadnego przekroju STIB.
Korekta należy do R-005 (#17).

Przedziały wyżej są sklejane progiem `SPAN_GAP_M` = 25,0 m. Nie jest to okrągła liczba
z sufitu: największy odstęp między sąsiednimi wierzchołkami na sześciu osiach to
22,4 m, więc próg poniżej niego rozciąłby jeden dołek na kilka „miejsc" tam, gdzie oś
jest rzadziej próbkowana. Bez sklejania pakiet A miałby jedenaście miejsc zamiast trzech.

## 3. Czym pakiety B-F różnią się od A

Sześć różnic, każda przypięta osobnym testem w `tools/tests/test_curve_radius_axes.py`.
Liczba, która na wszystkich sześciu osiach wychodzi tak samo, testu tam nie ma.

### 3.1 W pakiecie B najciaśniejszy łuk leży 30 m od początku osi

W pozostałych pięciu najbliższy koniec osi jest dalej niż kilometr. Konsekwencja jest
praktyczna: 94-metrowy skład ustawiony na tym łuku **wystaje poza oś**, więc miary
liczone na całym składzie — te z `tools/blender/profile_vehicle.py` — nie mają tam
gdzie stanąć. Wzór na strzałkę cięciwy ma i dlatego tę liczbę w ogóle da się podać.
`reports/clearance-BE.md` §1 podaje dla pakietu B najciaśniejsze miejsce na
kilometrażu 27,6 m; to ten sam łuk, widziany drugą metodą.

### 3.2 W pakietach D i F oba warianty wskazują DWA RÓŻNE łuki

W A, B, C i E wariant pesymistyczny i optymistyczny trafiają w ten sam wierzchołek
co do decymetra, więc widełki są widełkami jednej liczby. W D rozjeżdżają się
o 673,6 m, w F o 2976,2 m. Tam „promień najmniejszego łuku" **nie ma jednego adresu**
i raport podający sam promień bez kilometrażu obu wariantów mówiłby o dwóch różnych
miejscach naraz. Dlatego tabela w §1 jest podwójna, a nie pojedyncza z kolumną widełek.

### 3.3 Najciaśniejszy łuk pakietu D leży POZA tunelem

`reports/surface-vs-tunnel.md` §3 podaje przedziały, na których OSM nie widzi tunelu.
Odległość najciaśniejszego łuku od najbliższego takiego przedziału:

| pakiet | wariant pesymistyczny | wariant optymistyczny |
|---|---:|---:|
| A | 1678,6 m | 1678,8 m |
| B | brak takich odcinków | brak takich odcinków |
| C | 2393,4 m | 2393,3 m |
| **D** | **0,2 m** | **0,0 m — wewnątrz odcinka 764–1258 m** |
| E | 3476,3 m | 3476,2 m |
| F | 314,2 m | 478,4 m |

Rozdzielenie jest ostre: w D oba warianty leżą w granicy dokładności, z jaką w ogóle
znana jest granica przedziału (punkty osi stoją co 7,6–22,4 m), w pozostałych pięciu
najbliższy odcinek poza tunelem jest o setki metrów dalej.

**Co to znaczy: zapas +0,7043 m z §2.1 jest w pakiecie D policzony wobec ściany,
o której NIE WIADOMO, czy tam jest.** Zdanie w tym miejscu brzmiało do 09.09.2026
„wobec ściany, której tam nie ma" — i było twierdzeniem o terenie mocniejszym niż
pomiar. 6.B26 przeszła całą hierarchię źródeł dla tego jednego kilometrażu
(`reports/6b26-luk-D-tunel.md`): STIB nie publikuje atrybutu tunelu, obie warstwy
UrbIS w tym punkcie milczą — a dziury w ich pokryciu zdarzają się także w tunelach,
które istnieją na pewno — INSPIRE Rails nie ma takiego atrybutu w ogóle, więc werdykt
zostaje wyłącznie OSM, czyli klasa 4 i jedno źródło. Liczba jest poprawna dla modelu
i bezużyteczna jako fakt o metrze
— dokładnie ta sama klasa zastrzeżenia co uwaga o kilometrażu 8584,1 m
w `reports/clearance-BE.md` §1, z tą różnicą, że tam dotyczyła jednego dołka luzu,
a tu najciaśniejszego łuku całego pakietu. Pakiet D jest zresztą jedynym z sześciu,
w którym `bore_single` przechodzi z największym zapasem i jednocześnie **nie wiadomo,
czy jakikolwiek profil tunelu jest tam właściwy**.

### 3.4 Pakiet A jest najciaśniejszy, D najluźniejszy

Rozpiętość promienia między pakietami to 50,87 m (A) do 82,28 m (D), czyli 1,62×.
Rozpiętość zapasu w `box_double` — od +0,4713 m do +0,7043 m † — jest w tej samej
kolejności i to nie jest osobna informacja: przy tej cięciwie zapas jest funkcją
samego promienia.

### 3.5 `bore_single` dzieli sześć osi na dwie połowy

§2.2. W pakiecie A ta sama metoda dała jedną odpowiedź i wyglądała jak własność
projektowego profilu; na sześciu osiach widać, że jest to własność **pary**
profil-promień, z policzalną granicą przy R = 62,2 m.

### 3.6 Ani jedna z tych sześciu liczb nie jest promieniem konstrukcyjnym

Wspólne wszystkim sześciu i dlatego wypisane osobno w §4.

## 4. Czego NIE DA SIĘ potwierdzić i co w związku z tym zostało zostawione

**Promienia łuku jako faktu konstrukcyjnego nie potwierdza żadne dostępne źródło.**
Nie jest to ostrożność redakcyjna — mówi to wprost pole `not_derived` we wszystkich
sześciu plikach prowieniencji, na przykład `data/track/L5_D.provenance.json`:

> „promienie łuków jako fakt konstrukcyjny — polilinia jest reprezentacją trasy"

Osie pochodzą z tras handlowych STIB, a nie z osi toru z pomiaru. Że to nie jest
formułka, widać na liczbach. W drzewie stoją **dwa** pomiary promienia tej samej osi:

| pakiet | `build_alignment.radius_stats` (trójka wierzchołków) | tu (cięciwa pudła) | iloraz |
|---|---:|---:|---:|
| A | 97,3 m | 50,87 m | 1,913 |
| B | 141,5 m | 73,97 m | 1,913 |
| C | 101,0 m | 52,94 m | 1,908 |
| D | 157,2 m | 82,28 m | 1,911 |
| E | 113,0 m | 59,13 m | 1,911 |
| F | 141,3 m | 74,02 m | 1,909 |

Iloraz jest **taki sam na wszystkich sześciu osiach**, choć same promienie różnią się
o 60 %. I jest przewidziany co do drugiego miejsca przez same długości: krok
digitalizacji osi (mediana 14,96–15,00 m) do połowy cięciwy członu (7,833 m) daje
1,915. Żaden z tych dwóch pomiarów nie mierzy więc łuku — oba czytają ten sam krok
digitalizacji, tylko z innym rozstawem próbek. Zagęszczenie osi podnosi promień jeszcze
raz — na czterech pakietach, w których oba warianty wskazują ten sam łuk, o 1,62–1,70× —
i jest to ta sama zależność, a nie nowa informacja o torze.

Praktyczny wniosek, który z tego wynika i którego nie wolno pominąć przy czytaniu §1:
zdanie „walidator osi dopuszcza tylko łuki powyżej 90 m" (`tools/tests/test_packages.py`)
**nie jest zdaniem o skrajni**. Wszystkie sześć osi ten warunek spełniają, a promień,
który widzi pudło członu, jest na każdej z nich mniejszy od 90 m.

Dlatego **nie podaję ani jednej liczby jako promienia projektowego łuku STIB** i nie
podstawiam w to miejsce liczby prawdopodobnej. Rozstrzygnięcie wymaga osi toru
z pomiaru albo dokumentacji konstrukcyjnej — jednego i drugiego dziś nie ma
w dopuszczalnych źródłach (`docs/07-open-data-research.md`).

Nie da się też potwierdzić:

- **wymiarów samych profili tunelu** — `box_double`, `station` i `bore_single` mają
  `source_level: design`, więc każdy zapas z §2 jest zapasem wobec projektu, nie
  wobec zmierzonego światła tunelu. Zakres pomiaru UrbIS i granica jego stosowalności
  są w `reports/M7-curve-clearance.md` §4; ta pozycja niczego tam nie zmienia;
- **wychylenia zewnętrznego końców składu** — wymaga rozstawu czopów skrętu, którego
  `data/vehicle/m7-spec.json` nie ma. Zwis końcowy działa przeciwnie do strzałki, więc
  rzeczywisty zapas jest **mniejszy** niż policzony tutaj;
- **przechyłki, krzywych przejściowych i rozjazdów** — nie ma ich w żadnym pliku
  wejściowym, więc nie ma ich i w tym modelu.

Wynik jest zatem **warunkiem koniecznym**, nie pełną skrajnią kinematyczną: ujemny
zapas znaczy „na pewno się nie mieści", dodatni znaczy „na tym poziomie modelu
się mieści".

## 5. Progu dopuszczalnego luzu ta pozycja NIE wybiera

Progu nie ma ani w `data/`, ani w `docs/` — `reports/clearance-BE.md` §6 mówi to
wprost. Zamiast wybierać, podaję zmierzony zapas i pasma, przy których zmienia się
odpowiedź. Pasma są te z `reports/M7-clearance-profile.md`; `docs/24-clearance-profile-decisions.md`
w sekcji „Czego na tej liście nie ma" zapisuje, że **nie są one decyzją właściciela**,
a 0,300 pochodzi z `profiles.CLEARANCE_M` = 0,30.

| próg | `box_double` przechodzi | `bore_single` przechodzi |
|---|---|---|
| 0,000 m | A B C D E F | B D F |
| 0,300 m | A B C D E F | — |
| 0,500 m | B D E F (A o 28,7 mm poniżej, C o 4,7 mm) | — |
| 0,700 m | D (o 4,3 mm powyżej) | — |
| 0,900 m | — | — |

Który z tych progów jest właściwy, zależy od normy, której w repozytorium nie ma.
**Ta pozycja go nie wybiera i nie proponuje.**

## 6. Wypis narzędzia — sześć osi

Wyjście skrócone o trzy powtarzające się wiersze `nieliczone`, identyczne w każdym
przebiegu. Pełne wypisy dla trzech profili leżą w `build/6b5/`.

```
$ python3 tools/blender/clearance.py --alignment data/track/L1_A.json --profile box_double --scan --report-only
[SKRAJNIA] oś=L1_A profil=box_double człon=15.667 m (6 x, 94.0 m)
[SKRAJNIA] statyczny zapas profilu: 1.078 m
[SKRAJNIA] pessimistic: Rmin 50.87 m @ 2518.6 m, P05 78.82 m, strzałka 606.7 mm, zapas +0.471 m -> MIEŚCI SIĘ
[SKRAJNIA] optimistic : Rmin 85.94 m @ 2518.8 m, P05 137.5 m, strzałka 357.7 mm, zapas +0.720 m -> MIEŚCI SIĘ
[PUNKT PO PUNKCIE] pessimistic: 401 punktów, nie przechodzi 0, najmniejszy zapas +0.4713 m @ 2518.6 m (R 50.87 m), niedobór brak
[PUNKT PO PUNKCIE] optimistic : 1331 punktów, nie przechodzi 0, najmniejszy zapas +0.7203 m @ 2518.8 m (R 85.94 m), niedobór brak

$ python3 tools/blender/clearance.py --alignment data/track/L1_B.json --profile box_double --scan --report-only
[SKRAJNIA] oś=L1_B profil=box_double człon=15.667 m (6 x, 94.0 m)
[SKRAJNIA] statyczny zapas profilu: 1.078 m
[SKRAJNIA] pessimistic: Rmin 73.97 m @ 30.0 m, P05 98.55 m, strzałka 415.9 mm, zapas +0.662 m -> MIEŚCI SIĘ
[SKRAJNIA] optimistic : Rmin 119.54 m @ 30.0 m, P05 171.01 m, strzałka 256.9 mm, zapas +0.821 m -> MIEŚCI SIĘ
[PUNKT PO PUNKCIE] pessimistic: 319 punktów, nie przechodzi 0, najmniejszy zapas +0.6621 m @ 30.0 m (R 73.97 m), niedobór brak
[PUNKT PO PUNKCIE] optimistic : 1016 punktów, nie przechodzi 0, najmniejszy zapas +0.8211 m @ 30.0 m (R 119.54 m), niedobór brak

$ python3 tools/blender/clearance.py --alignment data/track/L5_C.json --profile box_double --scan --report-only
[SKRAJNIA] oś=L5_C profil=box_double człon=15.667 m (6 x, 94.0 m)
[SKRAJNIA] statyczny zapas profilu: 1.078 m
[SKRAJNIA] pessimistic: Rmin 52.94 m @ 2543.6 m, P05 82.87 m, strzałka 582.7 mm, zapas +0.495 m -> MIEŚCI SIĘ
[SKRAJNIA] optimistic : Rmin 90.05 m @ 2543.7 m, P05 143.94 m, strzałka 341.3 mm, zapas +0.737 m -> MIEŚCI SIĘ
[PUNKT PO PUNKCIE] pessimistic: 331 punktów, nie przechodzi 0, najmniejszy zapas +0.4953 m @ 2543.6 m (R 52.94 m), niedobór brak
[PUNKT PO PUNKCIE] optimistic : 1076 punktów, nie przechodzi 0, najmniejszy zapas +0.7367 m @ 2543.7 m (R 90.05 m), niedobór brak

$ python3 tools/blender/clearance.py --alignment data/track/L5_D.json --profile box_double --scan --report-only
[SKRAJNIA] oś=L5_D profil=box_double człon=15.667 m (6 x, 94.0 m)
[SKRAJNIA] statyczny zapas profilu: 1.078 m
[SKRAJNIA] pessimistic: Rmin 82.28 m @ 1916.2 m, P05 96.75 m, strzałka 373.7 mm, zapas +0.704 m -> MIEŚCI SIĘ
[SKRAJNIA] optimistic : Rmin 132.59 m @ 1242.6 m, P05 169.37 m, strzałka 231.6 mm, zapas +0.846 m -> MIEŚCI SIĘ
[PUNKT PO PUNKCIE] pessimistic: 238 punktów, nie przechodzi 0, najmniejszy zapas +0.7043 m @ 1916.2 m (R 82.28 m), niedobór brak
[PUNKT PO PUNKCIE] optimistic : 762 punktów, nie przechodzi 0, najmniejszy zapas +0.8464 m @ 1242.6 m (R 132.59 m), niedobór brak

$ python3 tools/blender/clearance.py --alignment data/track/L2_E.json --profile box_double --scan --report-only
[SKRAJNIA] oś=L2_E profil=box_double człon=15.667 m (6 x, 94.0 m)
[SKRAJNIA] statyczny zapas profilu: 1.078 m
[SKRAJNIA] pessimistic: Rmin 59.13 m @ 4285.7 m, P05 95.64 m, strzałka 521.2 mm, zapas +0.557 m -> MIEŚCI SIĘ
[SKRAJNIA] optimistic : Rmin 95.56 m @ 4285.8 m, P05 173.52 m, strzałka 321.6 mm, zapas +0.756 m -> MIEŚCI SIĘ
[PUNKT PO PUNKCIE] pessimistic: 545 punktów, nie przechodzi 0, najmniejszy zapas +0.5568 m @ 4285.7 m (R 59.13 m), niedobór brak
[PUNKT PO PUNKCIE] optimistic : 1792 punktów, nie przechodzi 0, najmniejszy zapas +0.7564 m @ 4285.8 m (R 95.56 m), niedobór brak

$ python3 tools/blender/clearance.py --alignment data/track/L6_F.json --profile box_double --scan --report-only
[SKRAJNIA] oś=L6_F profil=box_double człon=15.667 m (6 x, 94.0 m)
[SKRAJNIA] statyczny zapas profilu: 1.078 m
[SKRAJNIA] pessimistic: Rmin 74.02 m @ 1286.2 m, P05 91.04 m, strzałka 415.6 mm, zapas +0.662 m -> MIEŚCI SIĘ
[SKRAJNIA] optimistic : Rmin 118.53 m @ 4262.4 m, P05 159.19 m, strzałka 259.1 mm, zapas +0.819 m -> MIEŚCI SIĘ
[PUNKT PO PUNKCIE] pessimistic: 273 punktów, nie przechodzi 0, najmniejszy zapas +0.6624 m @ 1286.2 m (R 74.02 m), niedobór brak
[PUNKT PO PUNKCIE] optimistic : 875 punktów, nie przechodzi 0, najmniejszy zapas +0.8189 m @ 4262.4 m (R 118.53 m), niedobór brak
```

Trzy osie, na których `bore_single` nie przechodzi — wypis z tym samym poleceniem
i innym `--profile`:

```
$ python3 tools/blender/clearance.py --alignment data/track/L1_A.json --profile bore_single --scan --report-only
[SKRAJNIA] statyczny zapas profilu: 0.495 m
[SKRAJNIA] pessimistic: Rmin 50.87 m @ 2518.6 m, P05 78.82 m, strzałka 606.7 mm, zapas -0.112 m -> NIE MIEŚCI SIĘ
[SKRAJNIA] optimistic : Rmin 85.94 m @ 2518.8 m, P05 137.5 m, strzałka 357.7 mm, zapas +0.137 m -> MIEŚCI SIĘ
[PUNKT PO PUNKCIE] pessimistic: 401 punktów, nie przechodzi 11, najmniejszy zapas -0.1117 m @ 2518.6 m (R 50.87 m), niedobór -0.1117 m
[PUNKT PO PUNKCIE] pessimistic: przedziały bez skrajni: 2488.7-2533.6 m; 2773.5-2848.4 m; 3403.0-3403.0 m
[PUNKT PO PUNKCIE] optimistic : 1331 punktów, nie przechodzi 0, najmniejszy zapas +0.1373 m @ 2518.8 m (R 85.94 m), niedobór brak
[SKRAJNIA] UWAGA: skrajnia M7 nie mieści się w bore_single na najciaśniejszym łuku (wariant pesymistyczny, zapas -0.112 m)

$ python3 tools/blender/clearance.py --alignment data/track/L5_C.json --profile bore_single --scan --report-only
[SKRAJNIA] pessimistic: Rmin 52.94 m @ 2543.6 m, P05 82.87 m, strzałka 582.7 mm, zapas -0.088 m -> NIE MIEŚCI SIĘ
[PUNKT PO PUNKCIE] pessimistic: 331 punktów, nie przechodzi 5, najmniejszy zapas -0.0877 m @ 2543.6 m (R 52.94 m), niedobór -0.0877 m
[PUNKT PO PUNKCIE] pessimistic: przedziały bez skrajni: 2513.7-2573.5 m
[PUNKT PO PUNKCIE] optimistic : 1076 punktów, nie przechodzi 0, najmniejszy zapas +0.1537 m @ 2543.7 m (R 90.05 m), niedobór brak

$ python3 tools/blender/clearance.py --alignment data/track/L2_E.json --profile bore_single --scan --report-only
[SKRAJNIA] pessimistic: Rmin 59.13 m @ 4285.7 m, P05 95.64 m, strzałka 521.2 mm, zapas -0.026 m -> NIE MIEŚCI SIĘ
[PUNKT PO PUNKCIE] pessimistic: 545 punktów, nie przechodzi 4, najmniejszy zapas -0.0262 m @ 4285.7 m (R 59.13 m), niedobór -0.0262 m
[PUNKT PO PUNKCIE] pessimistic: przedziały bez skrajni: 4255.8-4285.7 m; 8586.3-8586.3 m
[PUNKT PO PUNKCIE] optimistic : 1792 punktów, nie przechodzi 0, najmniejszy zapas +0.1734 m @ 4285.8 m (R 95.56 m), niedobór brak
```

## 7. Kontrole negatywne — wykonane, nie opisane

Cztery sabotaże `tools/blender/clearance.py`, każdy uruchomiony, wynik wklejony,
kod przywrócony:

```
=== SABOTAŻ 1: merge_spans '<=' -> '<' (granica progu sklejania) ===
FAIL test_curve_radius_span_merge_joins_neighbours_and_splits_a_real_gap

=== SABOTAŻ 2: SPAN_GAP_M 25.0 -> 5.0 ===
FAIL test_curve_radius_point_scan_names_where_bore_single_runs_out_of_room:
     [(2488.7, 2488.7), (2503.7, 2503.7), (2518.6, 2518.6), (2533.6, 2533.6), ...]
FAIL test_curve_radius_span_gap_is_above_the_largest_point_spacing_of_all_six_axes:
     (5.0, 22.396311682953638)

=== SABOTAŻ 3: scan przyjmuje każdy punkt (fits zawsze True) ===
FAIL test_curve_radius_point_scan_names_where_bore_single_runs_out_of_room:
     {... 'failing_samples': 0, 'fits_everywhere': True, 'min_margin_m': -0.1117 ...}
FAIL test_curve_radius_scan_reports_a_shortfall_on_an_arc_tight_enough_to_cause_one

=== SABOTAŻ 4: radii_along mierzy na trójce wierzchołków, nie na cięciwie pudła ===
FAIL 10 z 14 testów modułu, w tym:
     test_curve_radius_package_A_is_the_tightest_of_the_six
     test_curve_radius_variants_disagree_about_which_arc_is_tightest_in_D_and_F
     test_curve_radius_two_committed_measures_differ_by_the_digitisation_step
     test_curve_radius_tightest_arc_of_package_D_falls_outside_the_tunnel
```

Dopisanie `scan`, `margin_at` i `merge_spans` podniosło liczbę mutacji modułu z 11 na 12,
co złapała bramka `test_drift_report_mutation_count_is_the_one_the_tool_gives_today`.
Przebieg przeliczający wiersz w `reports/mutation-drift.md`, tym samym poleceniem
i tym samym zestawem klas co cały tamten audyt. Jako jedyny pomiar w tym raporcie
nie jest liczony na `7842878`, tylko na drzewie tej gałęzi — inaczej nie zobaczyłby
dopisanego kodu, czyli tego, o co w nim chodzi. Osie i specyfikacja są w obu
drzewach identyczne, więc liczb z §1-§4 to nie dotyczy:

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/clearance.py \
      --operators operator,prog --workers 4 --json build/6b5/clearance-mut.json
[MUTACJE] rozstrzygniętych 12/12, zabitych 6, ocalałych 6 (w tym 0 nieuruchomionych), nierozstrzygniętych 0
  OCALAŁA  tools/blender/clearance.py:51 prog `0.0` -> `0.001`
  OCALAŁA  tools/blender/clearance.py:51 operator `<=` -> `<`
  OCALAŁA  tools/blender/clearance.py:54 operator `>=` -> `>`
  OCALAŁA  tools/blender/clearance.py:74 operator `<` -> `<=`
  OCALAŁA  tools/blender/clearance.py:103 operator `<=` -> `<`
  OCALAŁA  tools/blender/clearance.py:105 prog `0.0` -> `0.001`
kod: 0
```

Nowa mutacja — granica sklejania przedziałów — jest **zabita**, a lista ocalałych to
co do pozycji ta sama szóstka co przed tą zmianą: liczba ocalałych zostaje 6, więc
kolumna Δ w audycie zostaje zerem. To jest ta sama granica, którą wykonał sabotaż 1;
przegląd mutacyjny potwierdza ją drugim, niezależnym narzędziem.

Sabotaż 3 pokazał przy okazji rzecz wartą zapisania: przy `box_double` żaden z sześciu
przebiegów go nie zauważa, bo tam nie ma ani jednego punktu bez skrajni. Wykrywa go
wyłącznie przebieg na `bore_single` i syntetyczny łuk R = 25 m — czyli te dwa wejścia,
w których w ogóle jest co odrzucać.

## 8. Czego świadomie nie zrobiłem

- **Nie wybrałem progu dopuszczalnego luzu** — §5. Nie ma go w repozytorium, a wybór
  należy do właściciela.
- **Nie zmieniłem `tools/blender/profiles.py`.** Trzy osie nie mieszczą się
  w `bore_single`; reguła z #14 mówi, że w takim razie nie zwęża się pociągu ani nie
  poprawia profilu w tym samym miejscu, w którym się mierzy. Wymiar jest projektowy
  i należy do R-005 (#17).
- **Nie zbudowałem ani jednej geometrii.** Blendera nie ma w tym środowisku, a cały
  pomiar jest z definicji bez `bpy` — ale to znaczy też, że **nie ma renderów**
  i wyniki §2 nie są tu potwierdzone drugą, siatkową drogą. Dla pakietów A, B i E
  taka droga istnieje w `reports/clearance-BE.md` i zgadza się co do wniosku;
  dla C, D i F nie istnieje, bo `tools/ci/vehicle_clearance.sh` liczy luz w tunelu,
  a tuneli tych trzech pakietów nikt nie zbudował (`reports/clearance-BE.md` §6).
- **Nie zapisałem niczego do `data/`.** Wyniki maszynowe leżą w `build/6b5/`.
- **Nie policzyłem profilu pionowego** — T-112 zablokowane brakiem publicznych
  rzędnych główki szyny. Wszystkie sześć osi ma `z = 0` na całej długości, więc
  promień jest tu promieniem w planie, nie w przestrzeni.

## 9. Co zauważyłem przy okazji, ale nie tknąłem

- `MIN_RADIUS_M` w `tools/blender/clearance.py` nie jest używane przez nic — ani
  w tym module, ani poza nim. Nazwa jest przy tym zajęta drugi raz, z inną wartością,
  w `tools/tests/test_packages.py`. Usunięcie martwej stałej jest zmianą poza zakresem
  tej pozycji.
- Kilometraż 8586,3 m pakietu E, na którym `bore_single` nie przechodzi, wypada
  w przedziale 8556–8616 m, o którym `reports/surface-vs-tunnel.md` mówi, że **nie
  jest tunelem**. To ten sam odcinek, który `reports/clearance-BE.md` §1 nazywa przy
  kilometrażu 8584,1 m. Trzeci pomiar, trzecia metoda, ten sam odcinek.
