# T-212 · Pierwsza stacja typowa

**Zmierzone na commicie:** `a5356f0` (baza gałęzi `t212-stacja-typowa` po przebazowaniu;
pomiar wykonany na drzewie tej gałęzi, czyli na bazie plus jej jedynym commicie)

Stan: **2026-09-04**. Wyjście: `tools/track/station_components.py`,
`tools/blender/station_kit.py` (`--component`), `tools/tests/test_station_components.py`,
`docs/21-measured-vs-assumed.md` §4e.
Zależy od: T-211 (zrobione), T-210 (zrobione), R-007 (zrobione).

---

## 1. Co zrobiłem

Zespół dostępu nad peronem — **schody, winda, antresola, korytarz i portal** — budowany
proceduralnie z kilometrażu peronu i z profilu komory. Wybór elementów przez
`--component`, zgodnie z Issue #18.

Podział jest ten sam, co w całym paśmie geometrii i nie jest kosmetyczny: **cała
matematyka siedzi w `tools/track/station_components.py`, w którym nie ma ani jednej
linii `bpy`**. Dzięki temu każdy wymiar i każde położenie da się sprawdzić bez Blendera,
a `station_kit.py` tylko zamienia gotową listę brył na siatki. Ten moduł ma 22 testy;
przed T-212 warstwa brył stacji nie miała ani jednego.

## 2. Decyzje właściciela, na których to stoi

| pytanie | odpowiedź |
|---|---|
| zakres | pełny zestaw z Issue #18: schody, winda, antresola, korytarz, portal (03.09.2026) |
| długość peronu | **95,0 m** (04.09.2026, zmiana z 110 m — §7) |
| głębokość | zostać na Z = 0, wariant `flat-preview`; wysokości względem peronu (03.09.2026) |

**Skąd 95,0 m.** Wartość nie jest okrągła dla wygody i nie jest wybrana wewnątrz pustego
przedziału. R-007 §5 pkt 2 zostawia długość peronu jako `unknown` w danych i daje
generatorowi **jawny parametr**; ta liczba jest tym parametrem i siedzi w kodzie jako
`SC.DESIGN_PLATFORM_LENGTH_M`, nie w wywołaniu z terminala:

- **94,0 m** to długość składu M7 (`data/vehicle/m7-spec.json`, status `spec`) — dolna
  granica udowodniona w R-007 §4: peron krótszy od składu jest sprzeczny z ruchem bez
  selektywnego otwierania drzwi, którego STIB nie stosuje;
- **1,00 m zapasu**, po 0,50 m z każdej strony, to **3,2×** największy zmierzony błąd
  zatrzymania autopilota na pakiecie A (0,307 m, `reports/T-401-line-run.md` §2);
- 95,0 m mieści się w rozrzucie peronów OSM z R-007 §4 (26 z 28 w 94,76 ± 0,78 m, czyli
  do 95,54 m) **i w obrysie każdej stacji pakietu A**, razem z najciaśniejszym — Parc,
  109,1 m.

**Czego 95,0 m NIE zmienia w tej geometrii, i to jest sprawdzone, nie założone.**
Wznoszenie schodów wychodzi z profilu komory i z wysokości peronu (5,30 m + 0,40 m płyty
− 1,03 m = 4,67 m), a nie z długości peronu. Liczba stopni (**27**) i wysokość stopnia
(**0,1730 m**) są więc takie same jak przy 110 m — wypisane niżej z rzeczywistego
przebiegu. Od długości peronu zależy tylko **kilometraż**, na którym zespół staje:
`to_m − 4,0 m` odsunięcia, i dalej w stronę malejącego kilometrażu.

## 3. Co wynika z rachunku, a nie z wyboru

**Antresola nie mieści się wewnątrz komory.** Profil `station` ma strop na 5,30 m,
peron na 1,03 m, więc nad peronem zostaje **4,27 m**. Płyta 0,40 m i dolny poziom 2,60 m
w świetle zostawiają górnemu **1,27 m** — poniżej wzrostu człowieka. Antresola idzie
więc **nad stropem komory**, jako osobna skrzynia: podłoga 5,70 m, sufit 8,30 m.
Wznoszenie schodów wychodzi z tego samo: **4,67 m**.

**Wysokość stopnia nie jest nominalna.** 4,67 m przy nominalnych 0,17 m daje 27,47
stopnia. Zaokrąglenie w dół zostawiłoby 8 cm progu na górze, w górę — 9 cm w dół.
Liczba stopni jest więc całkowita (**27**), a wysokość stopnia wyliczona z podziału
(**0,1730 m**): schody muszą dojść tam, gdzie dochodzą.

**Otwór w antresoli wynika z obrysu tego, co ma przez niego przechodzić** — schodów
i szybu windy — powiększonego o 0,30 m. Nie jest wymyślony i nie jest wycięty operacją
boolowską: płyta jest dzielona na odcinki wzdłuż osi, a przy otworze zostają pasy z boku.

## 4. Weryfikacja — rzeczywiste wyjście

Blender **5.2.1 LTS** (`BLENDER_BIN=/opt/blender/blender-5.2.1-linux-x64/blender`; goły
`blender` w PATH to 4.0.2 z apt, czyli legacy EEVEE i wynik nieporównywalny z baseline'em
— `CLAUDE.md` §9).

```
$ python3 tools/track/station_layout.py --axis data/track/L1_A.json \
    --platform-length-m 95.0 --platform-gap-m 0.08 --out build/L1_A-platforms.json
[PERONY] L1_A: 12 peronów po 95.00 m na osi 6686.7 m
[PERONY] wysokość 1.03 m (spec), cięciwa członu 15.667 m
[PERONY] minimalne odsunięcie krawędzi 1.3503–1.5748 m (pół szerokości 1.35 m + strzałka na łuku)
[PERONY] 2 peronów przyciętych do końca osi
[RAPORT] build/L1_A-platforms.json

$ $BLENDER_BIN --background --python tools/blender/station_kit.py -- \
    --axis data/track/L1_A.json --layout build/L1_A-platforms.json \
    --platform-gap-m 0.08 --only-station "Parc|Park" --out build/T212-parc.glb \
    --metrics build/T212-parc-metrics.json
[PERON] profil station: ściana 7.60 m od osi, tory [-2.1, 2.1], wysokość peronu 1.03 m (spec)
[STACJA] poziomy: peron 1.03 m, strop komory 5.30 m (w świetle 4.27 m), antresola 5.70–8.30 m, wznoszenie schodów 4.67 m
[STACJA] elementy: platform, edge, stairs, lift, mezzanine, corridor, portal
[STACJA] peron: decyzja właściciela 95.0 m (skład M7 94,0 m + 1,0 m zapasu), kontrola R-007: obrys stacji 109.1 m (Parc)
[STACJA] założenia projektowe T-212 (18): ..., DESIGN_ACCESS_SETBACK_M=4.0, DESIGN_VOID_MARGIN_M=0.3, DESIGN_PLATFORM_LENGTH_M=95.0
[PERON] Parc|Park: 4028.2–4123.2 m, krawędź 1.4374 m od toru (minimum 1.3574 + szczelina 0.080)
[PERON] 37 brył, 596 wierzchołków, 522 ścian -> build/T212-parc.glb
[STACJA] brył per element: corridor=1, edge=2, lift=1, mezzanine=2, platform=2, portal=1, stairs=28
[RAPORT] build/T212-parc-metrics.json
```

Peron stoi teraz na **4028,2–4123,2 m** (było 4020,7–4130,7 m przy 110 m), a bryła ma
596 wierzchołków wobec 644 — krótszy peron to mniej pierścieni zamiatania. **37 brył
i podział na elementy się nie zmieniły**, bo zespół dostępu nie zależy od długości peronu.

Podział wznoszenia, wypisany z modułu, żeby liczba stopni była wynikiem, a nie zapewnieniem:

```
$ python3 -c "... station_components.stair_flights(4.67) ..."
odcinki: [('flight', 14, 4.06), ('landing', 0, 1.2), ('flight', 13, 3.77)]
stopni: 27 wysokość stopnia: 0.173
rzut schodów: 9.03
```

```
$ python3 tools/tests/test_all.py
  1455/1455 przeszło
```

Cztery nowe testy wobec wersji z 03.09.2026, wszystkie o długości peronu:
`test_components_platform_length_stays_within_the_tightest_station_footprint`,
`test_components_platform_length_is_the_train_plus_a_metre`,
`test_components_the_test_platform_is_the_decided_one`,
`test_components_footprint_control_refuses_degenerate_input`.

### Kontrole negatywne

Każda wykonana na zacommitowanym drzewie: mutacja skryptem, który sprawdza
`tekst.count(stare) == 1`, przywrócenie plikiem z indeksu.

**1. peron znów 110 m** (`DESIGN_PLATFORM_LENGTH_M = 95.0` → `110.0`) — wywraca trzy testy
naraz, w tym samą kontrolę R-007:

```
  FAIL test_components_platform_length_is_the_train_plus_a_metre: (110.0, 94.0)
  FAIL test_components_platform_length_stays_within_the_tightest_station_footprint: (110.0, 109.1)
  FAIL test_components_the_test_platform_is_the_decided_one: {'name': 'T', 'from_m': 100.0, 'to_m': 195.0, 'length_m': 110.0}
  1452/1455 przeszło
```

**2. kontrola przepuszcza wszystko** (`return length_m <= footprint_m + 1e-9` → `return True`):

```
  FAIL test_components_platform_length_stays_within_the_tightest_station_footprint: 110 m przekracza obrys Parc o 0,9 m, a kontrola tego nie widzi
  1454/1455 przeszło
```

**3. obrys wzięty z drugiej najciaśniejszej stacji** (`TIGHTEST_STATION_FOOTPRINT_M`
109,1 → 125,0, czyli Gare Centrale zamiast Parc):

```
  FAIL test_components_platform_length_stays_within_the_tightest_station_footprint: 125.0
  1454/1455 przeszło
```

**4. granica przestaje należeć do peronu** (`<= footprint_m + 1e-9` → `< footprint_m - 1e-9`):

```
  FAIL test_components_platform_length_stays_within_the_tightest_station_footprint: peron równy obrysowi stacji jeszcze się w nim mieści
  1454/1455 przeszło
```

**5. zdjęta straż przed zdegenerowanym wejściem** (`if length_m <= 0.0:` → `if False:`):

```
  FAIL test_components_footprint_control_refuses_degenerate_input: przyjęte: peron 0.0 m, obrys 109.1 m
  1454/1455 przeszło
```

**6. kontrola w generatorze — sprawdzona WYKONANIEM, nie mutacją.** Wołanie
`platform_fits_the_station()` w `station_kit.py` siedzi w `main()` za `bpy`, więc żaden
test Pythona go nie dosięgnie. Sprawdzone więc tak, jak działa: layout policzony na 110 m
i podany generatorowi.

```
$ python3 tools/track/station_layout.py --axis data/track/L1_A.json \
    --platform-length-m 110.0 --platform-gap-m 0.08 --out build/L1_A-platforms-110.json
[PERONY] L1_A: 12 peronów po 110.00 m na osi 6686.7 m

$ $BLENDER_BIN --background --python-exit-code 7 --python tools/blender/station_kit.py -- \
    --axis data/track/L1_A.json --layout build/L1_A-platforms-110.json \
    --platform-gap-m 0.08 --only-station "Parc|Park" --out build/T212-parc-110.glb
BŁĄD: peron Parc|Park ma 110.0 m, a najciaśniejszy obrys stacji pakietu A to 109.1 m
      (Parc, R-007) — peron dłuższy niż obrys stacji jest na pewno błędny
kod wyjścia: 1
$ ls build/T212-parc-110.glb
ls: cannot access 'build/T212-parc-110.glb': No such file or directory
```

Generator staje **przed** zapisem GLB, więc nie zostawia po sobie pliku, który przeszedłby
bramki wyglądu tak samo dobrze jak plik poprawny.

## 5. Co widać na renderach

`renders/T212-dostep_{iso,side,inside}.png`, kadr **4082,5–4124,5 m** osi pakietu A
(okno przesunięte razem z peronem: przy 110 m było 4090–4132 m). Ten sam kadr
wyrenderowany dodatkowo w 1600 px do obejrzenia szczegółów — opis niżej jest z obu.

**`_iso`** — kadr NIE jest pusty i geometria nie jest zwinięta w punkt: z lewego górnego
narożnika w głąb kadru biegną **cztery równoległe pasy** — dwie płyty peronowe i dwa pasy
ostrzegawcze przy krawędziach. W prawej połowie leży **skrzynia antresoli**, widziana
z góry jako duża płyta, a w niej **prostokątny otwór**, przez który widać **serrację
stopni** i mniejszą bryłę szybu windy. Otwór dochodzi do krawędzi płyty po stronie
zespołu, czyli jest to klatka schodowa przy ścianie, a nie dziura w środku płyty.
W poprzek osi, w stronę lewego dolnego narożnika, wychodzi **korytarz** zakończony
osobnym **blokiem portalu**. Perony wystają poza antresolę w prawo — bo antresola ma
24,0 m, a peron 95,0 m.

**`_side`** — jednostki się zgadzają i profil pionowy jest ten, co w liczbach: peron jest
niskim pasem na ~1 m, skrzynia antresoli pasem wysoko nad nim (5,7–8,3 m), a **stosunek
tych wysokości w pikselach odpowiada 1,03 m do 8,3 m** — gdyby gdzieś wszedł centymetr
za metr, ten render byłby albo płaski, albo poza kadrem. **Schody dochodzą do poziomu
antresoli**: serracja stopni startuje z peronu, idzie w górę w prawo i **kończy się na
wysokości spodu antresoli, w otworze, a nie pod płytą** — widać ją na tle pustego
kadru na całym górnym odcinku, czyli tam, gdzie płyty już nie ma. W połowie biegu jest
**płaska przerwa spocznika**, między serracją 14 i 13 stopni. Szyb windy stoi obok,
sięga wyżej niż spód antresoli. Płyta **wisi bez podpór** — słupów nie ma i są wypisane
w `not_modelled`.

**`_inside`** — kamera na poziomie toru, patrzy wzdłuż osi. Perony po obu stronach kadru,
na właściwej wysokości i odsunięciu. **Spód antresoli czyta się jako powierzchnia pełna**
— nie widać „przez" nią ani tła, ani brył za nią, czyli normalne są na zewnątrz i żadna
ściana nie znika. W prawej części sufitu jest **otwór, a przez niego schody widziane od
dołu** — pełna serracja stopni z ich spodu, plus pionowa bryła windy przy krawędzi otworu.
Poza otworem sufit jest ciągły aż do końca kadru.

**To NIE jest pierwsza wersja tej geometrii.** Pierwsza miała antresolę jako zamkniętą
płytę i render `_side` pokazał to natychmiast: schody dobijały do jej spodu i kończyły
się sufitem. Metryki bryły były wtedy bez zarzutu — 36 brył, 640 wierzchołków, zamknięte
siatki, dobre normalne. Żadna liczba tego nie łapała.

## 6. Czego świadomie nie zrobiłem

- **Komory stacyjnej nie ma w tym pliku.** `station_kit.py` buduje peron i zespół
  dostępu; rura komory powstaje z `tunnel_sweep.py` z profilem `station`. Rendery
  pokazują więc wyposażenie stacji bez otaczającego je tunelu;
- **słupów, balustrad, sufitów podwieszanych, bramek i kas** — wypisane w `not_modelled`
  metryk i w audycie;
- **rzutu żadnej brukselskiej stacji.** Układ jest **kanoniczny**: jeden zespół przy
  końcu peronu, antresola nad komorą, jeden korytarz, jeden portal. STIB nie publikuje
  rzutów (R-007), a obrysy z UrbIS mówią tylko, ile miejsca stacja zajmuje.

## 7. Decyzja: 110 m → 95,0 m (04.09.2026)

Pierwsza wersja tego zadania stała na peronie **110 m** i zapisywała w §7 konflikt tej
wartości z R-007. Konflikt został rozstrzygnięty przez właściciela: **peron ma 95,0 m**.

| kontrola z R-007 | liczba | 110 m | 95,0 m |
|---|---:|---|---|
| obrys stacji **Parc** — najciaśniejszy w pakiecie A | 109,1 m | **przekroczony o 0,9 m** | mieści się z zapasem 14,1 m |
| drugi najciaśniejszy obrys (Gare Centrale) | 125,0 m | mieści się | mieści się |
| perony OSM, 26 z 28 | 94,76 ± 0,78 m (do 95,54 m) | o ~15 m dłuższe | **mieści się** |
| długość składu M7 (dolna granica) | 94,0 m | mieści | mieści, z 1,00 m zapasu |

**Co się przez to zmieniło w kodzie, a nie tylko w opisie.** Przy 110 m liczba mieszkała
w wywołaniu generatora z terminala i w komentarzu raportu — czyli w miejscu, którego nic
nie porównuje z niczym. Teraz:

- `SC.DESIGN_PLATFORM_LENGTH_M = 95.0` jest jawnym parametrem T-212, wpisanym do
  `DESIGN_ASSUMPTIONS`, do metryk bryły i do `docs/21-measured-vs-assumed.md` §4e;
- `SC.TIGHTEST_STATION_FOOTPRINT_M = 109.1` **nie jest** założeniem projektowym i stoi
  poza `DESIGN_ASSUMPTIONS`: to pomiar obrysu Parc z UrbIS (poligony `MS`, CC0, R-007 §4);
- `SC.platform_fits_the_station()` **wykonuje** kontrolę z R-007 §5 pkt 3 i jest wołane
  przez `station_kit.py`, zanim postawi zespół dostępu — generator staje z komunikatem,
  zamiast zbudować peron dłuższy niż stacja;
- `test_components_platform_length_stays_within_the_tightest_station_footprint` pilnuje
  tego z obu stron granicy, a mutacja `95.0 → 110.0` go wywraca (§4).

**Co pozostaje otwarte, tak samo jak przy 110 m.** Peron OSM w Schuman ma 111,6 m
z `source=knowledge` (R-007 §5 pkt 4), więc jest albo prawdą o dłuższym peronie, albo
błędem mapowicza; 95,0 m niczego w tej sprawie nie rozstrzyga. Sama długość peronu
zostaje w danych `unknown` — 95,0 m jest parametrem generatora, nie daną o sieci.
