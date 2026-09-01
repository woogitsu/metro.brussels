# Gdzie sieć naprawdę biegnie w tunelu — dwa źródła zamiast jednego

Stan: **2026-09-01**. Narzędzie: `tools/track/surface_sections.py`.
Wejście: sześć osi z `data/track/`, warstwa UrbIS `bm_public_transport:Metro` (CC0)
i tagi `railway=subway` z OpenStreetMap (ODbL 1.0, snapshot Overpassa
`timestamp_osm_base = 2026-09-01T16:37:11Z`, 448 way'ów, 2920 odcinków).

Ten raport rozstrzyga pytanie zostawione otwarte w `reports/packages-BF-alignment.md`
§9: **czy `niveau = 0` znaczy „poza tunelem"**. Wtedy odpowiedzi nie było, bo
`data/network/sources.json` mówi wprost, że pola poziomu w UrbIS wymagają
interpretacji, a dataset nigdzie nie definiuje tego pola. Jedno źródło bez definicji
pola nie jest podstawą do twierdzenia o terenie — więc doszło drugie.

---

## 1. Wynik

**Tak, `niveau = 0` znaczy „poza tunelem".** Na 2032 punktach osi, gdzie oba źródła
mają zdanie, zgadzają się w **94,7 %**. Ale zgodność nie rozkłada się równo i to jest
właściwa treść tego raportu:

| | OSM: tunel | OSM: poza tunelem |
|---|---:|---:|
| **UrbIS: `niveau ≠ 0`** | **1746** | **81** |
| **UrbIS: `niveau = 0`** | 27 | **178** |

- **81 razy UrbIS mówi „tunel", a OSM przeczy.** To kierunek niebezpieczny: tam
  zbudowalibyśmy zamkniętą rurę na odcinku, którego nie ma. **Wszystkie 81 leżą
  w pakietach D (48) i F (33).** W pakietach A, B, C i E nie ma **ani jednego**
  takiego punktu.
- **27 razy UrbIS zawyża odcinek poza tunelem.** Kierunek bezpieczny — odrzucilibyśmy
  poprawną rurę.

Kontrola sensowności dopasowania: najdalszy way metra od osi wynosi **3,5–16,4 m**
zależnie od pakietu. OSM mapuje tory pojedynczo, więc kilka metrów to połowa rozstawu,
a nie błąd. Gdyby dopasowanie łapało inną linię, ta liczba szłaby w setki metrów.

## 2. Metoda

Trzy rzeczy, które odróżniają to od policzenia trafień w poligony:

1. **Drugie źródło jest niezależne.** OSM taguje `railway=subway` polem `tunnel`
   (i `layer`) — inni ludzie, inny proces, inne przesłanki. Zgodność dwóch
   niezależnych źródeł jest argumentem; jedno źródło nim nie jest.
2. **Bierzemy najbliższy odcinek, nie „jakiś w okolicy".** W rejonie Beekkant
   w jednym kwadracie 260 × 260 m leży osiem way'ów na czterech poziomach. Punkt
   dalej niż **60 m** od jakiegokolwiek way'a jest zapisany jako `nieznane`, a nie
   przypisany na siłę.
3. **Rozbieżność jest wynikiem, nie powodem do wybrania strony.** Narzędzie nie
   uśrednia i nie „poprawia" — zapisuje macierz i listę sprzeczności.

```bash
python3 tools/track/surface_sections.py --alignment data/track/L2_E.json \
    --out build/L2_E-surface.json --osm-file build/osm-subway.json --skip-osm
```

### Droga awaryjna, gdy Overpass leży

W dniu pomiaru Overpass odpowiadał `Dispatcher_Client::request_read_and_idx::timeout`
przez ponad godzinę na czterech instancjach (`overpass-api.de`, `kumi.systems`,
`private.coffee`, `osm.jp`). Dlatego narzędzie ma też tryb **sondowania** przez
`api.openstreetmap.org/api/0.6/map` — małe kwadraty 260 × 260 m wokół wybranych
kilometraży:

```bash
python3 tools/track/surface_sections.py --alignment data/track/L2_E.json \
    --out build/L2_E-surface.json --osm-dir build/osm --step-inside-m 40
```

Sondowanie dało na tych samych osiach 90,6 % zgodności na 138 sondach — czyli ten sam
wniosek jakościowy, ale **gorsze liczby i gubione odcinki**: 60-metrowy odcinek
pakietu E w kilometrażu 8556–8616 m nie trafił się żadnej sondzie. Tryb sondowania
jest drogą awaryjną, nie równorzędną metodą, i tak jest opisany w kodzie.

Przy sondowaniu okazało się jeszcze jedno, warte zapamiętania: pierwsza wersja
trafiała w **pierwszy punkt po wejściu w przedział**, czyli tuż za portal, i wszystkie
trzy ówczesne rozbieżności wypadły w kilometrażu 688–704 m — kilkanaście metrów od
granicy. Sondy w promieniu 60 m od granicy są teraz oznaczane jako `portal` i liczone
osobno, a środek każdego przedziału jest sondowany zawsze.

## 3. Per pakiet — pełne pokrycie

| pakiet | punktów | porównywalnych | zgodność | UrbIS `niveau = 0` | OSM: poza tunelem | UrbIS zawyża tunel |
|---|---:|---:|---:|---:|---:|---:|
| A — Pień 1/5 | 447 | 369 | 97,3 % | 4,0 % | **1,8 %** | **0** |
| B — Wschód 1 | 340 | 314 | **100 %** | 0,0 % | **0,0 %** | **0** |
| C — Zachód 5 | 361 | 361 | **100 %** | 8,6 % | 8,6 % | **0** |
| D — Wschód 5 | 258 | 208 | 75,0 % | 37,6 % | **69,8 %** | 48 |
| E — Pierścień 2/6 | 603 | 485 | 99,8 % | 2,0 % | **2,7 %** | **0** |
| F — Północ 6 | 299 | 295 | 84,7 % | 15,7 % | 22,7 % | 33 |

Przedziały kilometrażu, na których **OSM** nie widzi tunelu:

| pakiet | przedziały [m] | razem |
|---|---|---:|
| A | 45–135; 840 (pojedynczy punkt) | ~90 m |
| B | — | 0 m |
| C | 4937–5386 | 449 m |
| D | 60–539; 764–1258; 1422–1916; 2230–3398 | ~2645 m |
| E | 7762–7867; 7897–7927; **8556–8616** | ~195 m |
| F | 60–568; 763–972; 3530–3784 | ~972 m |

### Co z tego wynika dla każdego pakietu

- **B — w całości w tunelu.** 314 punktów, 314 razy `tunnel = yes`, zero poligonów
  `niveau = 0`, zero rozbieżności. Jedyny pakiet, któremu żadne z dwóch źródeł nie
  zarzuca ani metra poza tunelem.
  **Uwaga:** `data/network/lines.json` przypisuje pakietowi B `unlocks: odcinki
  naziemne`. Dwa niezależne źródła temu przeczą. Nie zmieniam `lines.json` — `data/`
  jest tylko do odczytu — ale to jest wpis do rozstrzygnięcia przez właściciela.
- **A — 90 m, nie 240 m.** Poligon „Tunnel STIB Beekkant – Gare de l'Ouest" ma jedno
  pole `niveau = 0` na całe 800 m i obejmuje **oba** stany naraz: kilometraż 45–135 m
  jest poza tunelem, a 690–840 m jest w tunelu na **`layer = -4`** — dziesięć
  z jedenastu punktów tego przedziału ma `tunnel = yes`, zgadza się dopiero ostatni,
  w 839,6 m, czyli przy samym portalu. To nie jest błąd UrbIS, tylko granulacja:
  `niveau` opisuje
  **poligon**, nie punkt. Liczba „240 m pakietu A poza tunelem" z
  `reports/packages-BF-alignment.md` §9 i `reports/L1_A-geometry.md` jest zawyżona
  o 150 m; rzeczywisty odcinek to **90 m z 6686 m, czyli 1,3 %**.
- **E — 195 m, w trzech kawałkach, w tym jeden, którego UrbIS nie zna.** Odcinek
  Delacroix – Clemenceau (7762–7927 m) ma w OSM `layer = 1`, czyli biegnie **nad**
  terenem, nie po nim. Do tego **8556–8616 m** — 60 m tuż za Gare de l'Ouest, bez
  żadnego poligonu UrbIS. To ten sam fizyczny odcinek co 45–135 m pakietu A, widziany
  z drugiej linii. Licząc od Gare de l'Ouest (kilometraż 8512,7 m na osi E): odcinek
  wypada **43,6–103,5 m** za stacją, wobec **45–135 m** w pakiecie A. Dwie niezależne
  osie, zbudowane z dwóch różnych wariantów trasy, wskazują ten sam odcinek — to jest
  kontrola, nie zbieg okoliczności.
- **C — 449 m, oba źródła co do punktu tak samo.** Rejon Erasme, do końca osi.
  Zgodność 361/361 — pod względem jakości danych pakiet C jest **najczystszy ze
  wszystkich sześciu**. Ma tylko dużo dłuższy odcinek poza tunelem i to jest jedyny
  powód, dla którego nie budujemy go teraz jako zamkniętej rury.
- **D — model zamkniętej rury jest niewłaściwy, i to dwa razy bardziej, niż mówił
  UrbIS.** OSM nie widzi tunelu na **69,8 %** punktów wobec 37,6 % z `niveau = 0`.
  48 punktów to miejsca, gdzie UrbIS mówi „tunel", a OSM przeczy — czyli miejsca,
  w których samo UrbIS wprowadziłoby nas w błąd.
- **F — 22,7 % poza tunelem i 33 punkty sprzeczne.** UrbIS wskazuje 60–748 m, OSM widzi
  tunel na `layer = -1` już od 568 m, za to dokłada 3530–3784 m, o którym UrbIS milczy.
  Granica portalu jest tu sporna między źródłami na 180 m.

## 4. Czego ten raport NIE rozstrzyga

- **Nie mówi, co budować zamiast rury.** Estakada, wykop otwarty, nasyp — to jest
  decyzja projektowa i osobne dane, których nie ma ani w `data/`, ani w `docs/`.
  Reguła 1 z `CLAUDE.md` zabrania zgadywania tu tak samo jak przy głębokości stacji.
- **Nie daje niwelety.** `layer` w OSM to porządek rysowania, nie rzędna. T-112
  pozostaje zablokowane brakiem publicznych rzędnych główki szyny (T-901).
- **Nie lokalizuje portali z dokładnością do metra.** Punkty osi stoją co 7,6–22,4 m,
  więc granica przedziału jest znana z tą samą dokładnością.
- **Nie zmienia żadnego pliku w `data/`.** Sprzeczność `lines.json` ↔ pomiar
  (pakiet B) i zawyżenie odcinka pakietu A są zgłoszone, nie „poprawione".

## 5. Wejście dla E1.2

Do generacji jako zamknięta rura kwalifikują się **B** (0,0 % poza tunelem, zero
rozbieżności) i **E** (2,7 %, trzy krótkie odcinki na końcu pakietu) — ten drugi na
tej samej zasadzie co już zbudowany pakiet A z jego 1,8 %. W żadnym z tych trzech
pakietów nie ma ani jednego punktu, w którym UrbIS zawyżałby tunel.

Pakiet **C** ma najlepszą jakość danych ze wszystkich sześciu, ale 449 m poza tunelem
to 8,6 % osi — próg, którego nie przekraczam bez decyzji właściciela. **D** i **F**
czekają na model odcinka poza tunelem.
