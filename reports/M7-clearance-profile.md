# Profil luzu M7 wzdłuż całego pakietu A i zamiatana obwiednia składu

**Zmierzone na commicie:** `51fd842` · **data:** 2026-09-01

`reports/M7-in-tunnel.md` zmierzył luz w **jednym** punkcie — automatycznie wybranym
najciaśniejszym łuku (chainage 2518,8 m, R = 85,94 m, luz 0,9447 m na torze +2,10 m).
Ten raport odpowiada na pytanie, którego tamten pomiar nie zadaje: **jak luz wygląda
wzdłuż całych 6,7 km**, czy 0,94 m to dołek odosobniony i gdzie jeszcze robi się ciasno.

Odpowiedź w jednym zdaniu: **nie, 0,9447 m nie było minimum.** Minimum na pakiecie A
wynosi **0,8999 m** — o 45 mm mniej — i wypada przy ustawieniu składu o 38 m wcześniej
(czoło na 2433,5 m zamiast 2471,8 m), w innej bryle: na skrajnym `M7_car_6` zamiast
środkowego `M7_car_2`. Tor 0, o którym poprzedni pomiar mówił, że wiąże go strop
(1,1000 m), ma własne minimum ścienne **0,9189 m**, 267 m dalej wzdłuż trasy.

- narzędzia: `tools/blender/clearance_profile.py` (matematyka, czysty Python)
  + `tools/blender/profile_vehicle.py` (bpy: wierzchołki z GLB, siatka obwiedni, eksport)
- testy: `tools/tests/test_clearance_profile.py` (28 testów, bez Blendera)
- odtworzenie: `bash tools/ci/vehicle_clearance.sh` (~122 s, w tym ~60 s na profil)
- wynik maszynowo: `build/t220clearance/profile_t0.json`, `…/profile_t1.json`

## 1. Metoda

Skład jest przesuwany wzdłuż osi krokiem `step`, a dla każdej pozycji zapisywane są:
chainage czoła, minimalny luz, bryła i punkt, w którym wypadł, oraz **co wiąże** —
ściana, strop, podłoga czy ścięcie naroża stropu. Pomiar samego luzu jest dokładnie
ten sam, co w `place_vehicle.py`: każde pudło i każdy mieszek na własnej cięciwie,
offsety wierzchołka względem lokalnej ramki osi, odległość od obrysu profilu.

Pozycje idą od chainage 0 (czoło na początku osi) do `długość osi − 94 m` (koniec
składu na końcu osi), więc **suma pozycji pokrywa całą oś bez dziury**: pilnuje tego
`coverage_gaps`, a CI wywala się, gdy pojawi się luka albo gdy skrajna pozycja nie
wypada dokładnie na końcu.

### Krok i jego uzasadnienie

| parametr | wartość | status |
|---|---|---|
| krok skanu zgrubnego | **5,0 m** | `design_assumption` |
| krok doszlifowania | **0,25 m** | `design_assumption` |
| pasmo wyboru dołków do doszlifowania | min + **50 mm** | `design_assumption` |
| połowa okna doszlifowania | max(krok, 4 m) | `design_assumption` |
| szerokość pasma X kandydatów | **0** = pasma dokładne | `design_assumption` |
| kierunki podparcia obwiedni | **32** | `design_assumption` |
| zakres zamiatanej obwiedni | **± 150 m** wokół minimum | `design_assumption` |
| progi raportowania | 1,000 / 0,950 / 0,900 / 0,500 / **0,300** / 0,000 m | `design_assumption`, poza 0,300 m |

Krok 5 m nie jest przypadkiem: oś źródłowa STIB to łamana o kroku ~15 m, zagęszczana
Catmull-Romem do pierścieni **co 5 m**. Poniżej 5 m geometria nie zawiera już własnej
informacji, tylko interpolację. Ale sam krok 5 m **nie wystarcza do znalezienia dołka**
i nie udajemy, że wystarcza — dlatego po skanie zgrubnym idzie doszlifowanie krokiem
0,25 m w oknach wokół każdej pozycji nie gorszej niż `minimum + 50 mm`.

Ile to zmienia, zmierzone, a nie oszacowane:

| tor | minimum na siatce 5 m | po doszlifowaniu 0,25 m | zysk |
|---|---|---|---|
| 0 | 0,919787 m | **0,918851 m** | 0,936 mm |
| 1 | 0,903142 m | **0,899948 m** | 3,194 mm |

I kontrola odwrotna: przebieg z krokiem **2 m** (3298 pozycji zamiast 1320) po
doszlifowaniu daje na torze 1 **to samo minimum 0,899948 m** — czyli gęstsza siatka
zgrubna nie znajduje niczego, czego nie znajduje 5 m + doszlifowanie, a kosztuje 2,5×
dłużej. Stąd 5 m jako domyślne.

Próg 0,300 m **nie jest nowym założeniem**: to `profiles.CLEARANCE_M`, projektowy luz
skrajni pojazdu, który jest w repozytorium od T-010. Pozostałe progi to okrągłe pasma
do czytania profilu i nie mają statusu wymiaru projektowego.

### Koszt obliczeń i skąd się bierze

Naiwny pomiar to ~5,4 tys. wierzchołków pojazdu × ~1,35 tys. ramek osi **na każdą
pozycję** — 0,42 s za pozycję, czyli ponad 9 minut na tor. Trzy redukcje, każda
z dowodem, sprowadzają to do 6,6–8,2 ms:

1. **Pasma X i otoczka wypukła.** Wierzchołki o tym samym X pojazdu leżą w jednym
   przekroju prostopadłym do bryły, więc mają tę samą ramkę osi, a luz jest funkcją
   **afiniczną** (Y, Z) — minimum leży na otoczce wypukłej rzutu pasma. ~5,4 tys. → **1306
   kandydatów** w 336 pasmach.
2. **Współczynniki afiniczne na pasmo.** Iloczyny skalarne ramki liczone raz na pasmo,
   nie raz na wierzchołek. Ramka jest jednak wybierana **osobno dla każdego
   wierzchołka**, spośród 3 ramek wokół pasma: jedna wspólna ramka na pasmo gubiła na
   łuku pakietu A 3,7 mm, bo sąsiednie pierścienie są 5 m od siebie i widzą inny
   fragment krzywej.
3. **Luz jako minimum półpłaszczyzn.** Wszystkie profile w `profiles.py` są wypukłe,
   a dla punktu wewnątrz wielokąta wypukłego odległość od brzegu = minimum odległości
   od prostych podpierających. Zamiast sześciu odległości od odcinków — sześć iloczynów
   skalarnych. Test `test_clearance_profile_halfplane_clearance_matches_distance_to_boundary`
   pilnuje, że obie drogi dają tę samą liczbę do 1e-9 dla wszystkich trzech profili.

Dowód, że redukcja nie gubi minimum, jest **liczbowy i w CI**: `--verify-full` przelicza
wybrane pozycje (w tym zawsze najgorszą) naiwnie — po wszystkich wierzchołkach i przez
`placement.local_offsets` + `placement.distance_to_boundary`:

```
[PROFIL] kontrola redukcji na 3 pozycjach (1.41 s):
[PROFIL]   czoło  2433.50 m: redukcja 0.899948 m, pełny przebieg 0.899948 m, rozjazd 0.0000 mm
[PROFIL]   czoło  2509.75 m: redukcja 0.900821 m, pełny przebieg 0.900821 m, rozjazd 0.0000 mm
[PROFIL]   czoło  3383.50 m: redukcja 0.950845 m, pełny przebieg 0.950845 m, rozjazd 0.0000 mm
```

Kubełkowanie X po 0,5 m byłoby o 40 % szybsze (794 kandydatów), ale na torze 0 gubi
0,78 mm, a po 1,0 m — 3,4 mm. Dlatego domyślnie liczymy pasma dokładne. To jest cena
za to, żeby liczba w raporcie nie zależała od parametru wydajnościowego.

Zmierzony czas (Blender 4.0.2, jeden rdzeń na tor):

| etap | tor 0 | tor 1 |
|---|---|---|
| skan zgrubny 1320 pozycji | 9,2 s | 9,2 s |
| doszlifowanie (646 / 817 pozycji) | 4,5 s | 5,4 s |
| zamiatana obwiednia 300 m | 11,7 s | 10,1 s |
| **razem na tor** | **27,9 s** | **29,3 s** |

Oba tory idą równolegle, więc cały nowy etap kosztuje ~30 s ściany. Cały
`vehicle_clearance.sh` to **119–122 s** wobec ~22 s przed tym zadaniem.

## 2. Profil luzu — liczby

Percentyle liczone **wyłącznie na siatce równomiernej** (1320 pozycji, krok 5 m).
Doszlifowanie zagęszcza próbki tylko w dołkach, więc wrzucone do jednego worka
przesunęłoby P05 i medianę i statystyka opisywałaby rozkład próbek, nie rozkład luzu.

| wielkość | tor 0 (−2,10 m) | tor 1 (+2,10 m) |
|---|---|---|
| pozycji na siatce 5 m | 1320 | 1320 |
| minimum (z doszlifowaniem) | **+0,9189 m** | **+0,8999 m** |
| P05 | 1,0366 m | 1,0108 m |
| mediana | 1,1000 m | 1,1000 m |
| P95 | 1,1000 m | 1,1000 m |
| maksimum | 1,1000 m | 1,1000 m |
| pozycji poniżej 1,000 m | 33 (2,5 %) | 57 (4,3 %) |
| pozycji poniżej 0,950 m | 28 (2,1 %) | 34 (2,6 %) |
| pozycji poniżej 0,900 m | 0 | 0 |
| pozycji poniżej 0,500 / 0,300 / 0,000 m | 0 | 0 |
| pozycji, w których wiąże **strop** | 1228 (93 %) | 1161 (88 %) |
| pozycji, w których wiąże **ściana** | 92 (7 %) | 159 (12 %) |

Trzy rzeczy warte odczytania z tej tabeli:

- **Mediana i P95 są dokładnie równe 1,1000 m** — czyli 4,70 m stropu minus 3,60 m
  dachu. Na 88–93 % trasy o luzie decyduje **wysokość**, nie szerokość, a wysokość nie
  zależy od promienia. Profil luzu na pakiecie A to płaska linia 1,100 m z kilkoma
  wcięciami na łukach, a nie ciągle zmienna krzywa.
- **Luz nigdzie nie jest ujemny** i nigdzie nie spada poniżej 0,90 m. Gdyby spadł,
  byłoby to wynikiem do zaraportowania, nie do zamiecenia — CI wywala się na ujemnym
  luzie i wypisuje, ile pozycji go ma.
- **Dołek nie jest jeden.** Poniżej 1,000 m wypadają trzy różne miejsca na torze 1
  i jedno na torze 0.

## 3. Miejsca krytyczne

Grupowane po chainage punktu styku, nie po pozycji składu: jeden ciasny łuk widziany
z kilkuset pozycji pociągu to **jedno miejsce w tunelu**, a nie kilkaset wpisów.

| tor | chainage | luz | wiąże | bryła | gdzie |
|---|---|---|---|---|---|
| 1 | **2521,1 m** | **0,8999 m** | ściana | `M7_car_6` | 200 m przed Sainte-Catherine \| Sint-Katelijne, między Comte de Flandre a Sainte-Catherine |
| 1 | 3405,6 m | 0,9147 m | ściana | `M7_car_6` | 275 m za De Brouckère, między De Brouckère a Gare Centrale |
| 1 | 946,4 m | 0,9910 m | ściana | `M7_car_6` | 437 m za Beekkant, między Beekkant a Étangs Noirs \| Zwarte Vijvers |
| 0 | **2786,2 m** | **0,9189 m** | ściana | `M7_car_6` | 65 m za Sainte-Catherine \| Sint-Katelijne, między Sainte-Catherine a De Brouckère |

Poniżej progu 0,950 m zostają tylko dwa miejsca na torze 1 (2521 m i 3406 m) i jedno
na torze 0 (2786 m). Poniżej 0,900 m — żadne.

Co z tego wynika, a czego pomiar w jednym punkcie nie pokazywał:

- **Minimum globalne jest o 45 mm gorsze od dotąd raportowanego.** 0,8999 m wobec
  0,9447 m. Punkt styku (chainage 2521 m) leży blisko poprzedniego (2496 m), ale przy
  ustawieniu składu z czołem na 2433,5 m zamiast 2471,8 m — czyli **wybór pozycji
  „skład wyśrodkowany na najmniejszym promieniu" nie jest wyborem najgorszej pozycji**.
- **Wiążąca bryła to `M7_car_6`, nie `M7_car_2`.** Oba skrajne człony są dłuższe
  (15,12 m wobec 14,57 m), więc mają większą strzałkę cięciwy; przy odpowiednim
  ustawieniu to one wypadają na najciaśniejszym łuku.
- **Na torze 0 wiąże ściana, nie strop.** Poprzedni raport zapisał dla toru 0 luz
  1,1000 m wiązany stropem i to była prawda — ale wyłącznie dla tamtego jednego
  chainage. 265 m dalej ten sam tor ma minimum ścienne 0,9189 m.
- **Łuk przy De Brouckère (3405 m) nie pojawił się w żadnym wcześniejszym raporcie**,
  bo nie jest najciaśniejszy — jest drugi w kolejności.

## 4. Kontrola krzyżowa wobec wzoru

### 4.1 Zgodność dwóch implementacji tego samego pomiaru

Zanim wzór: profil i `place_vehicle.py` muszą dawać tę samą liczbę tam, gdzie mierzą
to samo. CI sprawdza to w dwóch punktach:

```
[KONTROLA] tor 0: pozycja odniesienia — profil 1.1000 m, place_vehicle 1.1000 m, rozjazd 0.000 mm
[KONTROLA] tor 1: pozycja odniesienia — profil 0.9446 m, place_vehicle 0.9447 m, rozjazd 0.060 mm
[KONTROLA] w globalnym minimum: profil 0.8999 m, place_vehicle 0.9000 m, rozjazd 0.052 mm
```

0,05–0,06 mm to różnica kolejności działań zmiennoprzecinkowych (rozwinięcie afiniczne
wobec `transform_point` + `dot`), nie różnica modelu. Próg w CI: 0,5 mm.

### 4.2 Wzór na strzałkę cięciwy w pozycji odniesienia

Przepisany 1:1 z istniejącego `vehicle_clearance.sh`: rzeczywista cięciwa bryły,
w której wypadło minimum, razy promień w środku składu, próg rozjazdu **10 mm**.

```
[KONTROLA] odniesienie: cięciwa 14.553 m, promień 85.94 m -> strzałka 308.6 mm,
           luz statyczny do ściany 1.2500 m, przewidziany 0.9414 m, rozjazd 3.2 mm
```

**3,2 mm** — czyli nowe narzędzie odtwarza zgodność 3,9 mm z `reports/M7-in-tunnel.md`
(różnica bierze się z cięciwy 14,553 m zamiast 14,567 m w tamtej wersji bryły).

Na torze 0 ta sama kontrola daje 182,4 mm — i **nie jest progowana**, bo minimum wiąże
tam **strop**, a wzór na strzałkę cięciwy opisuje wyłącznie ścianę na łuku. Porównywanie
przewidywanej odległości od ściany ze zmierzoną odległością od stropu nie mierzy
niczego. Liczba jest wypisywana, żeby nikt nie musiał zgadywać, czemu jej nie ma.

### 4.3 Wzór w globalnym minimum — tu robi się ciekawie

„Promień" nie jest jedną liczbą: zależy od tego, gdzie i na jakiej cięciwie się go
mierzy. Dla najgorszej pozycji na torze 1 (czoło 2433,50 m, `M7_car_6`, cięciwa
15,0985 m, zmierzony luz 0,8999 m):

| promień podany wzorowi | R | strzałka | przewidziany luz | rozjazd | wzór jest |
|---|---|---|---|---|---|
| lokalny, w środku bryły | 93,99 m | 303,7 mm | 0,9463 m | **46,4 mm** | optymistyczny |
| najmniejszy na osi, cięciwa rzeczywista | 85,12 m | 335,4 mm | 0,9146 m | **14,6 mm** | optymistyczny |
| najmniejszy na osi, cięciwa nominalna 94/6 | 85,94 m | 357,7 mm | 0,8923 m | **7,7 mm** | zachowawczy |

Do tego liczba, której wzór nie zna: **rzeczywiste odchylenie osi od cięciwy bryły
wynosi 320,5 mm**, mierzone bez założenia o łuku okręgu (`chord_deviation_m`).

Co z tego wynika:

- Wzór `v = R − √(R² − (ℓ/2)²)` zakłada, że oś między końcami bryły jest **łukiem
  okręgu**. Oś pakietu A nim nie jest — to łamana STIB o zmiennej krzywiźnie. W punkcie
  minimum promień z trójki punktów (93,99 m) przewiduje strzałkę 303,7 mm, a naprawdę
  jest 320,5 mm; stąd 46 mm rozjazdu przy promieniu lokalnym.
- Podanie wzorowi **najmniejszego promienia na całej osi** zamiast lokalnego zbija
  rozjazd do 14,6 mm, a wariant nominalny z `reports/M7-curve-clearance.md` (cięciwa
  15,667 m, R 85,94 m) przewiduje **0,8923 m wobec zmierzonych 0,8999 m** — czyli
  **model analityczny myli się o 7,7 mm i myli się w stronę bezpieczną**.
- To jest realna, mierzalna wartość poprzedniego raportu: jego zachowawczość
  (~50 mm z tytułu cięciwy nominalnej, o której pisał §3 `reports/M7-in-tunnel.md`)
  niemal dokładnie kompensuje optymizm wynikający z traktowania osi jak łuku okręgu.
  Zbieg okoliczności, ale zbieg okoliczności, który teraz jest **zmierzony**, a nie
  domniemany.

W CI progowany jest wariant „najmniejszy promień na cięciwie rzeczywistej", bezpiecznikiem
100 mm. To nie jest ocena dokładności wzoru — to wykrywacz regresji: rozjazd powyżej
100 mm znaczyłby, że rozjechał się model, a nie krzywizna osi.

## 5. Zamiatana obwiednia składu

**To nie jest to samo, co `--envelope-out` z `m7_shell.py`.** Tamta bryła jest statyczną
skrajnią prostego składu stojącego na prostej — pryzma 94 × 3,0 × 3,7 m. Ta jest
objętością, którą skład **rzeczywiście zajmuje przejeżdżając odcinek**: suma pozycji
wszystkich pudeł na wszystkich zmierzonych ustawieniach pociągu.

Konstrukcja: każdy kandydat wnosi swoje offsety do pierścienia osi, w którym wypadł
(do dwóch otaczających, nie do najbliższego — inaczej obwiednia miałaby prążki
niedomiaru na szwach). Przekrój pierścienia jest **przekrojem 32 półpłaszczyzn
podparcia**, czyli otoczką wypukłą z nadmiarem. Nadmiar jest wyborem, nie
niedopatrzeniem: do pytania „czy coś wstawionego do tunelu wchodzi w drogę składu"
niedomiar byłby niebezpieczny, nadmiar jest tylko zachowawczy.

| wielkość | tor 0 | tor 1 |
|---|---|---|
| zakres chainage | 2636,2–2936,2 m | 2371,1–2671,1 m |
| pozycji składu, które wniosły wkład | 725 | 611 |
| pierścienie × kierunki | 63 × 32 | 62 × 32 |
| wierzchołki / ściany siatki | 2016 / 1986 | 1984 / 1954 |
| bbox | 204,54 × 190,98 × **2,65** m | 213,19 × 175,54 × **2,65** m |
| GLB | 148 660 B | 143 576 B |
| luz obwiedni wobec profilu tunelu | +0,918851 m | +0,899948 m |
| minimum ze skanu w tym zakresie | 0,918851 m | 0,899948 m |
| wierzchołków pojazdu poza obwiednią | 0 z 75 684 | 0 z 64 484 |

Wysokość 2,65 m to spód pudła 0,95 m do dachu 3,60 m — obwiednia nie rośnie w pionie,
bo pojazd nie zmienia wysokości. Szerokość rośnie: na renderze przekroju obwiednia ma
**3,06 m** wobec 2,70 m szerokości pudła, i to jest cała różnica między bryłą statyczną
a zamiataną.

Dwa niezmienniki pilnowane automatycznie: obwiednia **zawiera** skład w każdej
zmierzonej pozycji (0 wierzchołków poza) i jej luz jest **nie większy** niż minimum ze
skanu w tym zakresie (jest nadzbiorem). Do tego round-trip przez `glb_roundtrip.py`:

```
[ROUNDTRIP] obiekty=1 wierzcholki=3858 sciany=4028
[ROUNDTRIP] bbox_m: [204.5442, 190.978, 2.65]
[ROUNDTRIP] OK
[ROUNDTRIP] obiekty=1 wierzcholki=3711 sciany=3964
[ROUNDTRIP] bbox_m: [213.1907, 175.5384, 2.65]
[ROUNDTRIP] OK
```

### Dlaczego zakres, a nie cała trasa

Domyślnie obwiednia powstaje dla **± 150 m wokół minimum**, nie dla całych 6,7 km.
Wariant pełnej trasy jest zaimplementowany i zmierzony (`--swept-from 0 --swept-to 6690`):

| | ± 150 m | cała trasa |
|---|---|---|
| pierścienie | 62 | 1349 |
| GLB | 144 KB | **3 505 324 B (3,5 MB)** |
| czas przebiegu | 29,3 s | **54,0 s** |
| luz obwiedni | +0,899948 m | +0,899948 m |

Decyzja: **zakres**, z trzech powodów. (1) Pełna obwiednia w jednym GLB to dokładnie
ten kształt pliku, który T-210 odrzucił dla tunelu — streaming w Godocie potrzebuje
chunków i manifestu, a nie jednego monolitu; obwiednia całej trasy należy do tego samego
podziału i ma powstać per chunk, kiedy będzie do czegoś potrzebna. (2) 3,5 MB to plik,
którego i tak nie wolno commitować (`CLAUDE.md` §4.8), a jego treść w 95 % to prosty
tunel, gdzie obwiednia jest trywialnym pryzmatem. (3) Interesująca jest ta część, gdzie
luz jest najmniejszy — i tam gęstość pozycji jest największa dzięki doszlifowaniu.
`--swept-from` / `--swept-to` pozwalają wygenerować dowolny odcinek bez zmiany kodu.

## 6. Obejrzane rendery

Zestaw kamer `clearance` (`gap`, `approach`, `flank`), po dwa komplety: `M7_WORST`
(pojazd w znalezionym minimum, czoło na 2433,5 m) i `M7_SWEPT` (zamiatana obwiednia
w tunelu). Kamery `gap` i `flank` mają `wire: true` w manifeście — bez overlaya siatki
scena złożona z pojazdu i tunelu jest jednolicie szara.

### `M7_WORST_gap` — przekrój w najgorszym punkcie

Widać obrys `box_double` z oboma ścięciami naroży stropu, a w nim przekrój pudła M7
wyraźnie przesunięty w prawo. Odczyt z obrazu przy kadrze 12 m na 960 px, czyli
**80 px/m** (skala potwierdzona samym obrazem: krawędzie tunelu na 98,5 i 850,5 px,
czyli 752 px = **9,400 m**, dokładnie szerokość `box_double`):

| co | odczyt z pikseli | wartość zmierzona |
|---|---|---|
| szerokość otworu tunelu | 752 px = 9,400 m | 9,40 m (profil) |
| dach pojazdu do stropu (kolumna x = 648 px) | 88 px = **1,100 m** | 1,1000 m |
| poziom podłogi pudła | y = 345,5 px → z = 1,031 m | 1,03 m (spec) |
| poziom posadzki tunelu | y = 523,5 px → z = −1,194 m | −1,20 m (profil) |
| szczelina do prawej ściany na z = 1,15 m | 78,5 px = 0,981 m | — |
| szczelina do prawej ściany na z = 2,60 m | 74,5 px = **0,931 m** | 0,8999 m w punkcie minimum |

Odczyt szczeliny (0,93–0,98 m) jest o 30–80 mm większy od zmierzonego minimum
0,8999 m i to jest zrozumiałe: linie overlaya siatki mają 8–12 px grubości, a ich środek
leży o pół grubości (~0,06 m) wewnątrz pudła, więc pomiar „środek grupy pikseli"
systematycznie zawyża szczelinę; do tego kadr o głębi 3 m sumuje kilka przekrojów,
a punkt minimum leży na samej krawędzi płata. **Wartości pionowe, gdzie grubość linii
znosi się po obu stronach, zgadzają się co do milimetra** — 1,100 m luzu do stropu,
1,031 m podłogi, −1,194 m posadzki.

### `M7_WORST_flank` — elewacja odcinka 30 m

Poziomy pas tunelu z widoczną grubą triangulacją, a w nim skorupa M7: po lewej
zwężający się koniec z kabiną (gęsty pęk pionowych krawędzi z 0,20-metrowych stacji
ścięcia czoła), dalej regularny rząd prostokątnych otworów drzwiowych. Nad pasem
pojazdu i pod nim zostaje wyraźny pas tunelu — pudło jest w środku otworu, nie na
jego krawędzi.

### `M7_WORST_approach` — widok z toru

Kadr wypełnia ściana tunelu widziana z bliska, z niewielkim prześwitem w prawej części.
W odróżnieniu od `M7_GAP_approach` (gdzie na końcu zakrętu widać wyłaniające się czoło
składu z otworami drzwiowymi) ten kadr **jest mało czytelny**: oko stoi 32 m przed
czołem, w miejscu, gdzie tunel skręca ostro, więc bliższa ściana zasłania perspektywę.
Kamera `approach` nie ma overlaya siatki, więc dwie szare bryły nie odróżniają się od
siebie. Zapisuję to jako ograniczenie kadru, nie jako wynik.

### `M7_SWEPT_gap` — przekrój zamiatanej obwiedni

Ten sam obrys tunelu, a w nim **ścięty prostokąt obwiedni**, wyraźnie szerszy od pudła
z poprzedniego kadru: lewa krawędź na 533,5 px zamiast 558 px, prawa na 778,5 px
zamiast ~776 px. Odczyt:

| co | odczyt z pikseli | wartość zmierzona |
|---|---|---|
| szerokość obwiedni | 245 px = **3,062 m** | pudło ma 2,70 m — obwiednia jest szersza o 36 cm |
| szczelina do prawej ściany | 72,0 px = **0,900 m** | 0,899948 m (`envelope_clearance`) |
| dach obwiedni do stropu | 88 px = 1,100 m | 1,1000 m |
| spód obwiedni | y = 351,5 px → z = 0,956 m | 0,95 m (spód pudła) |

**Szczelina 0,900 m odczytana z obrazu zgadza się ze zmierzoną 0,899948 m z dokładnością
do 0,1 mm** — i to jest ten sam odczyt na wszystkich trzech sprawdzonych wysokościach
(z = 1,15 / 1,60 / 2,60 m), bo bok obwiedni jest pionową płaszczyzną, a nie zbiorem
rozmytych przekrojów pudła. To najostrzejszy pomiar z obrazu w całym zadaniu.

### `M7_SWEPT_flank` — obwiednia z boku

Jednolity, **nieprzerwany** pas biegnący przez cały 30-metrowy kadr, z widoczną
triangulacją czworokątów między kolejnymi pierścieniami i trzema poziomymi krawędziami
(strop tunelu, góra obwiedni, posadzka). Brak otworów drzwiowych jest tu informacją,
nie usterką: obwiednia jest gładką rurą, bo zamiatana objętość nie ma drzwi. Brak
przerw między pierścieniami potwierdza, że przypisywanie wierzchołka do dwóch
sąsiednich pierścieni działa — przy przypisaniu do najbliższego byłyby prążki.

### `M7_SWEPT_approach` — obwiednia w tunelu, ukośnie

Oko 40 m przed punktem minimum, przesunięte 3 m w bok (na sąsiedni tor), patrzy ukośnie
w stronę zakrętu. Lewa połowa kadru to wnętrze tunelu: ściana z pionowym prążkowaniem
pierścieni, posadzka i strop uciekające w prawo za łuk. Prawa połowa to **bok zamiatanej
obwiedni** — płaska, jasna płaszczyzna z ostrą sylwetą, odcinająca się jaśniejszym
paskiem górnej krawędzi biegnącym do prawego górnego rogu. Widać z tego dokładnie jedną
rzecz, ale ważną: obwiednia stoi w tunelu jak ściana i zostawia wolny cały sąsiedni tor.
Kontrastu jest mało, bo `approach` nie ma overlaya siatki, a cała scena ma jeden materiał
kontrolny.

## 7. Kontrole automatyczne w `tools/ci/vehicle_clearance.sh`

| kontrola | próg | wynik |
|---|---|---|
| profil pokrywa oś bez dziur | brak luk > krok, końce dokładnie na 0 i `oś − 94 m` | OK |
| luz nigdzie ujemny | 0 pozycji | OK (0 na obu torach) |
| redukcja kandydatów nie gubi minimum | 0,001 mm wobec pełnego przebiegu | OK (0,0000 mm) |
| profil wobec `place_vehicle.py` w pozycji odniesienia | 0,5 mm | OK (0,000 / 0,052 mm) |
| profil wobec `place_vehicle.py` w globalnym minimum | 0,5 mm | OK (0,052 mm) |
| wzór na strzałkę w pozycji odniesienia | 10 mm | OK (3,2 mm; tor 0 nie progowany, wiąże strop) |
| wzór na strzałkę w globalnym minimum | 100 mm (bezpiecznik) | OK (14,6 / 4,4 mm) |
| determinizm drugiego przebiegu | raport identyczny co do bitu | OK (1354 pozycje) |
| obwiednia zawiera skład | 0 wierzchołków poza | OK |
| obwiednia jest nadzbiorem skanu | luz obwiedni ≤ minimum ze skanu | OK |
| bbox obwiedni sensowny | wszystkie osie > 0, pion ≥ 2 m | OK (2,65 m) |
| round-trip GLB obwiedni | `glb_roundtrip.py`, bbox ±0,01 m | OK |
| rendery niepuste i niejednolite | `compare.py`, progi z manifestu | OK (6 kadrów) |

Determinizm sprawdzany jest na siatce zgrubnej (krok 25 m), bo nie zależy od gęstości
siatki, a dwa pełne przebiegi to minuta CI za tę samą informację. Ścieżka kodu jest ta
sama: skan, doszlifowanie, obwiednia, kontrola redukcji.

Uwaga na marginesie, zauważona przy okazji: **eksporter glTF nie jest powtarzalny co do
liczby wierzchołków**. Ta sama bryła M7 (2334 wierzchołki, 1862 ściany wg generatora)
eksportuje się w kolejnych buildach jako 5338, 5362, 5408 albo 5454 wierzchołki GLB —
rozszczepienie na szwach UV zależy od czegoś, czego generator nie kontroluje. **Zmierzone minimum nie
zależy od tego**: dwa niezależne buildy skorupy dały identyczne 0,918851 m i 0,899948 m.
Jest to znane i opisane w `sweep.py` przy okazji chunków, ale warto wiedzieć, że dotyczy
też pomiaru skrajni.

## 8. Czego ten pomiar NIE obejmuje

Wszystko z §5 `reports/M7-in-tunnel.md` obowiązuje dalej — profil wzdłuż osi nie usuwa
ani jednej z tamtych niepewności, tylko pokazuje je w większej liczbie punktów:

- **zwis czopów skrętu** — brak rozstawu w `data/vehicle/m7-spec.json`. Zwis końcowy
  działa w przeciwną stronę niż strzałka i na skrajnych członach może być od niej
  większy, więc **rzeczywisty luz jest mniejszy niż tu zmierzony**. To dotyczy zwłaszcza
  wyniku tego raportu, bo minimum wypada właśnie na skrajnym członie `M7_car_6`;
- **przechyłka, ugięcie zawieszenia, zużycie kół, tolerancje toru i budowlane tunelu** —
  żadna nie jest modelowana;
- **profil pionowy** — T-112 (#10) zablokowane, cała scena leży na Z = 0. Wszystkie luzy
  pionowe (1,100 m) są luzami na płaskim torze;
- **rozjazdy, odcinki przejściowe, krzywe przejściowe (klotoidy)** — oś jest ciągła
  i nie zawiera żadnego z nich;
- **szerokość otworu** — `box_double` 9,40 m to wymiar **projektowy**, nie pomiar;
  UrbIS daje 8,25–9,92 m (§4 `reports/M7-curve-clearance.md`). Przy P05 8,25 m ściana
  stoi 0,575 m bliżej toru, więc cały profil ścienny przesuwa się o tyle w dół
  i minimum wypadłoby ok. **0,32 m**;
- **rozstaw torów** — cały pomiar zakłada `track_offsets` ±2,10 m z `profiles.py`,
  czyli wartość bez źródła; INSPIRE Rails daje ±1,647 m
  (`reports/L1_A-track-spacing.md`), co działa w przeciwną stronę;
- **niepewność samego promienia** — oś to geometria linii handlowej STIB zagęszczona
  Catmull-Romem, nie oś toru z pomiaru. Na łamanej źródłowej najmniejszy promień to
  50,87 m zamiast 85,94 m i wtedy cały profil schodzi niżej;
- **profil zamiatanej obwiedni poza zakresem ±150 m** — policzony tylko na żądanie,
  domyślnie nie istnieje;
- **inne profile niż `box_double`** — stacje (`station`) i tunel drążony (`bore_single`)
  nie zostały przeskanowane; `bore_single` już w `reports/M7-curve-clearance.md` nie
  przechodził na najciaśniejszym łuku.

Wynik jest więc, tak jak poprzednio, **warunkiem koniecznym**, nie pełną skrajnią
kinematyczną — tyle że teraz sprawdzonym w 1320 punktach na tor zamiast w jednym.
Zanim ktokolwiek uzna 0,90 m za zapas, musi zostać domknięte R-005 (#17).

## 9. Co z tego wynika dla kolejnych zadań

- **Nie wolno cytować 0,9447 m jako minimum pakietu A.** Ta liczba jest poprawna, ale
  opisuje jedną pozycję składu, a nie trasę. Minimum trasy to 0,8999 m (tor 1)
  i 0,9189 m (tor 0).
- T-211 (#18) — peron na łuku: zamiatana obwiednia jest gotową bryłą do testu, czy
  krawędź peronu w nią nie wchodzi; wystarczy wygenerować ją dla chainage stacji
  (`--swept-from` / `--swept-to`).
- Trzecia szyna, wyposażenie tunelu, znaki i sygnalizatory — ta sama obwiednia,
  ten sam test. Dlatego przekrój jest zachowawczy (nadzbiór), a nie „dokładny".
- Jeżeli R-005 (#17) przyniesie węższy otwór albo mniejszy promień, profil trzeba
  przeliczyć **w całości**, a nie tylko w dotychczasowym punkcie kontrolnym — bo
  miejsce minimum zależy od geometrii i potrafi się przenieść o dziesiątki metrów.
