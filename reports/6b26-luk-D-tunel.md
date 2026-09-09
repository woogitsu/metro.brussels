# Czy najciaśniejszy łuk pakietu D biegnie w tunelu — cztery klasy źródeł, jedna odpowiedź (6.B26)

**Zmierzone 09.09.2026 na:** `eb70a26`, kontener tej sesji.
**Przyrząd:** `tools/track/crosscheck_alignment.py --osm-source osm-api`,
`tools/track/surface_sections.py` na snapshotach lokalnych, oraz trzy pobrania:
warstwa UrbIS `bm_public_transport:Metro`, warstwa UrbIS Topo `bm_urbis_topo:tunnel_line`
i INSPIRE Rails `TN.RailTransportNetwork.gml`.

---

## 1. Odpowiedź

**Na dostępnych danych rozstrzygnąć się nie da**, i to jest wynik, nie unik.
Przy kilometrażu **1916,2 m** osi `data/track/L5_D.json` — tam leży najciaśniejszy
łuk pakietu, R = 82,28 m — werdykt o tunelu ma **dokładnie jedno** źródło z czterech
klas hierarchii `docs/07-open-data-research.md`, i jest nim OpenStreetMap, czyli
klasa **4**. Trzy klasy wyżej milczą, a `reports/surface-vs-tunnel.md` §2 mówi
wprost: „Zgodność dwóch niezależnych źródeł jest argumentem; jedno źródło nim nie
jest".

Do tego punkt leży **wewnątrz strefy portalu** w rozumieniu przyrządu, który tę
strefę zdefiniował: `PORTAL_HALO_M = 60,0 m` w `tools/track/surface_sections.py`,
z komentarzem „przy portalu oba źródła mają prawo różnić się o kilkanaście metrów
i taka rozbieżność **nic nie mówi** o tym, czy odcinek biegnie w tunelu". Tunel
Delta – Beaulieu zaczyna się według UrbIS na **1976,0 m**, czyli **59,8 m** za
łukiem, a według OSM na **1931,1 m**, czyli **14,9 m** za nim. Oba dystanse są
w halo. Reguła projektu odmawia tu werdyktu **własnym progiem**, nie moją oceną.

W konsekwencji zapasy skrajni policzone na tym łuku są **warunkowe** i tak
oznaczone w `reports/promien-luku-szesc-osi.md` — wszystkie trzy, nie tylko
`box_double` z treści pozycji (§5).

## 2. Przejście po hierarchii — co która klasa mówi w punkcie 1916,2 m

| klasa | źródło | co mówi w 1916,2 m |
|---|---|---|
| 1 | STIB Open Data (shapefiles, GTFS, Stop Details) | **nie publikuje atrybutu tunel/powierzchnia w ogóle** — daje przebieg, przystanki i rozkład; sama oś `L5_D` z tego źródła pochodzi |
| 2 | UrbIS `bm_public_transport:Metro` | **milczy** — punkt leży w 194,5-metrowej dziurze pokrycia, 2,2 m od poligonu `Tunnel STIB Delta - Beaulieu` |
| 2 | UrbIS Topo `bm_urbis_topo:tunnel_line` (BR04L, CC0) | **milczy o metrze** — najbliższa linia tunelowa jest 238,7 m dalej, i to samo dotyczy odcinka, na którym metro jest w tunelu na pewno |
| 3 | INSPIRE Rails (Belgian Mobility) | **nie ma atrybutu tunelu** — zero wystąpień `tunnel`, `level`, `bridge`, `elevation` w 3 370 178 znakach GML-a |
| 4 | OpenStreetMap `railway=subway` | **jedyny werdykt**: 13 kolejnych way'ów na 1422,2–1916,2 m bez tagu `tunnel`, `bridge` i `layer`; tunel pojawia się na 1931,1 m (way 475856296, `tunnel=yes`, `layer=-1`) |

### 2.1 Klasa 2, warstwa Metro: dziura pokrycia nie jest zdaniem o terenie

To jest pomiar, który rozstrzyga o tej klasie, i wyszedł inaczej, niż zakładała treść
pozycji („UrbIS mówi tunel, a OSM przeczy"). W punkcie 1916,2 m **UrbIS nie mówi nic**:
poligonu tam nie ma. Przejście po całej osi pokazuje, gdzie pokrycie się zmienia:

```
  od   1601.8 m: MS Station Delta (niveau=-)
  od   1691.7 m: MT Tunnel STIB Delta - Beaulieu (niveau=-)
  od   1766.5 m: BRAK POKRYCIA
  od   1976.0 m: MT Tunnel STIB Delta - Beaulieu (niveau=-)
```

Oś **wychodzi z tego samego poligonu i wraca do niego** po 209,5 m. Odległość do jego
krawędzi w dziurze maleje monotonicznie: 3,5 → 3,4 → 3,3 → 3,1 → 2,6 → **2,2 (łuk)** →
1,7 → 1,1 → 0,6 → 0,0 m. Nigdzie nie przekracza **3,47 m**, a zmierzona odchyłka osi od
way'ów OSM na tym pakiecie ma medianę 1,04 m i maksimum 3,91 m — czyli dziura mieści się
w rozrzucie, z jakim te geometrie w ogóle się na siebie nakładają.

**Kontrola, która zamyka sprawę tej klasy: takie dziury są też w tunelach, które istnieją
na pewno.** Przejście po trzech osiach, ta sama metoda:

```
=== L5_D
          dziura [m]  dlugosc  punktow  dyst. min  dyst. maks  najblizszy poligon (w maks.)
    104.8–   374.3    269.5       19       0.06        1.42  MT Tunnel STIB Thieffry - Pétillon
   1766.5–  1961.0    194.5       14       0.64        3.47  MT Tunnel STIB Delta - Beaulieu
   2125.6–  2290.3    164.7       12       0.40        0.84  MT Tunnel STIB Delta - Beaulieu
=== L1_A
   4692.3–  5007.1    314.9       22       0.06        1.01  MT Tunnel STIB Arts-Loi - Maelbeek
   5576.9–  5741.8    164.9       12       0.67        2.43  MT Tunnel STIB Schuman - Merode
   5816.8–  6131.6    314.9       22       0.75        2.89  MT Tunnel STIB Schuman - Merode
```

Pakiet A ma zgodność źródeł 97,3 % i jest zbudowany jako zamknięta rura, a mimo to
UrbIS zostawia na nim dziury po **314,9 m** — w tunelach Arts-Loi – Maelbeek i Schuman
– Merode, o których nikt nie twierdzi, że ich nie ma. Dziura w pokryciu jest więc
artefaktem nakładania geometrii, **nie zdaniem „tu nie ma tunelu"**.

Że UrbIS ma czym powiedzieć „to nie tunel", widać na tej samej osi: robi to polem
`niveau = 0` **wewnątrz** poligonu, i używa go w czterech miejscach L5_D (703,6–1242,6;
1437,2–1452,1; 1512,0–1586,9; 2470,0–3143,6 m). W 1916,2 m nie ma ani poligonu
z `niveau = 0`, ani żadnego innego. Najbliższe **twierdzenie** UrbIS-u to `niveau = 0`
kończące się 329,3 m wcześniej i `niveau ≠ 0` zaczynające się 59,8 m później.

### 2.2 Klasa 2, warstwa tuneli topograficznych: milczy także tam, gdzie tunel jest

`docs/07-open-data-research.md` §„UrbIS Topo — linie tuneli" ostrzega, że to ogólna
warstwa tuneli i nie wolno jej brać za oś tunelu metra bez potwierdzenia zgodności
obiektu z siecią STIB. Pomiar pokazuje **mocniejszą** wersję tego ograniczenia:

```
   km [m]   najbliższa linia BR04L  dyst. [m]
   1916.2                  1818091     238.72     <- najciaśniejszy łuk
   1976.0                  1818091     205.81     <- UrbIS Metro: TUNEL, OSM: tunnel=yes
   2125.6                  1818091     107.13
```

Na odcinku 1976,0–2125,6 m **oba** źródła klasy 2 i 4 zgadzają się, że metro jest
w tunelu — a najbliższa linia BR04L jest 106–206 m dalej. Warstwa nie mapuje tego
tunelu metra wcale, więc jej milczenie w 1916,2 m nie mówi o metrze nic. Trzynaście
obiektów BR04L w wycinku to tunele drogowe okolicy Delty; ich brak przy osi jest
faktem o tej warstwie, nie o torze.

### 2.3 Klasa 3, INSPIRE Rails: atrybutu nie ma

Pobrane z URL-a z rejestru (`data/network/sources.json`, `belgian_mobility_inspire_rails`):
ZIP 378 482 B, w nim `TN.RailTransportNetwork.gml` o 3 370 178 znakach, 1689
`gml:featureMember`, 2116 `net:link`. Wyszukanie napisów: `tunnel` — **0**, `level` — 0,
`elevation` — 0, `bridge` — 0. Jedyne słowo z tej rodziny w pliku to `fictitious`
(1620 wystąpień, atrybut topologii sieci). Klasa 3 nie ma czym odpowiedzieć na to
pytanie i nie jest to kwestia dostępu — plik pobrał się bez przeszkód.

### 2.4 Klasa 4, OSM: jedyny werdykt, i jest nim BRAK TAGU

```
        way  tunnel  layer  bridge  punkty osi [m]
  209202545    None   None    None  1422.2–1571.9 (6 pkt)
  …
  209203334    None   None    None  1901.2 (1 pkt)
  209203895    None   None    None  1916.2 (1 pkt)   <- najciaśniejszy łuk, way 0,65 m od osi
  475856296     yes     -1    None  1931.1 (1 pkt)
```

Trzynaście różnych way'ów na 494 m, żaden z tagiem `tunnel`, żaden z `bridge`, żaden
z `layer`; czternasty, 14,9 m dalej, ma `tunnel=yes` i `layer=-1`.

**Na poziomie pakietu jest to mocny sygnał**, i tak go czyta
`reports/surface-vs-tunnel.md`: 494 m ciągu way'ów bez tagu, zamkniętych way'em
otagowanym jako tunel, plus 97 punktów `niveau = 0` w UrbIS — dwa źródła zgodne co do
kierunku. **Na poziomie jednego punktu jest to brak dowodu, a nie dowód braku**: w OSM
tunel taguje się dodatnio (`tunnel=yes`), a jego nieobecność jest wartością domyślną,
którą nosi także way, którego nikt nie sprawdził. Narzędzie zapisuje ten brak jako
`poza_tunelem`, bo musi coś zapisać — ale to konwencja przyrządu, nie zdanie mapy.

## 3. Co ten pomiar potwierdził z poprzedniego raportu

Dzisiejsze pobranie odtwarza `reports/surface-vs-tunnel.md` z 01.09.2026 co do liczby,
choć poszło **drogą zapasową** (Overpass odmówił: `Connection reset by peer`):

```
[POWIERZCHNIA] zgodność 75.0% na 208 punktach; OSM bez tunelu na 180 (69.8%),
  przedziały [[59.9, 538.9], [763.5, 1257.5], [1422.2, 1916.2], [2230.4, 3398.1]]
[POWIERZCHNIA]   urbis=tunel|osm=poza_tunelem: 48
[POWIERZCHNIA] najdalszy way metra od osi: 3.91 m
```

48 punktów sprzecznych, przedział 1422,2–1916,2 m — te same wartości co osiem dni
temu, na innym snapshotcie i inną drogą dostępu. To jest kontrola stabilności wejścia,
bez której dzisiejszy werdykt opierałby się na jednym pobraniu.

**Dopisane 09.09.2026 (6.D61): która to z dwóch liczb.** Wypis wyżej podaje jedną
zgodność, bo ścieżka pełnego pokrycia liczyła wtedy jedną. Dziś liczy dwie i ta sama
oś, na tym samym snapshotcie, daje:

```
[POWIERZCHNIA] zgodność 75.0% na 208 punktach; poza portalami 78.5% na 144;
  punktów w halo portalu (60.0 m): 69; RÓŻNICA dwóch liczb: 3.5 pkt
```

Wartość **75,0 %** zostaje w tym raporcie jako pomiar swojego dnia i **nie jest
błędna** — mówi tylko o czym innym, niż brzmi jej nazwa: liczy punkty w halo portalu
na równi z punktami ze środka odcinka. Dla werdyktu tego raportu to bez różnicy
i właśnie dlatego warto to wypisać: pakiet D ma **69 punktów w halo ze 258**, ponad
ćwierć osi, a odsianie ich podnosi zgodność tylko o **3,5 pkt**. Rozbieżność pakietu D
nie bierze się z portali.

## 4. Czego ten raport NIE zmienia

- **Wniosek pakietowy zostaje.** „Model zamkniętej rury jest dla D niewłaściwy" opiera
  się na 180 punktach OSM i 97 punktach `niveau = 0`, a nie na tym jednym punkcie.
  Nierozstrzygnięty jest **werdykt punktowy w 1916,2 m**, i to on jest podstawą liczby
  zapasu.
- **Nie mówi, co jest na tym odcinku zamiast tunelu.** Estakada, wykop, nasyp — to
  decyzja projektowa i osobne dane (`reports/surface-vs-tunnel.md` §4).
- **Nie rusza `data/`.** Ani osi, ani rejestru źródeł — `CLAUDE.md` §4.6.
- **Nie przelicza zapasów.** Liczby są poprawne dla swojego modelu; warunkowy jest
  **model**, nie arytmetyka.

## 5. Oznaczenie warunkowe — trzy liczby, nie jedna

Treść pozycji mówiła o zapasie `box_double` **+0,7043 m**. Pomiar pokazuje, że
najciaśniejszy łuk pakietu D leży w 1916,2 m dla **wszystkich** profili, więc warunkowe
są trzy liczby z `reports/promien-luku-szesc-osi.md`, a nie jedna:

| profil | zapas D | gdzie |
|---|---:|---|
| `box_double` | +0,7043 m | §2.1, tabela |
| `station` | +1,1233 m | §2.1, zdanie pod tabelą |
| `bore_single` | +0,1213 m | §2.2, tabela |

Wszystkie trzy dostały oznaczenie **†** z przypisem odsyłającym tutaj. **Wklejone
wyjścia przyrządu w §7 tamtego raportu zostały nietknięte** — zapis pomiaru nie jest
miejscem na adnotację, bo edycja wklejonego wyjścia fałszuje dowód (6.D49).

Poprawione zostało przy tym **za mocne zdanie z §3.3** tamtego raportu: mówiło, że
zapas jest „policzony wobec ściany, **której tam nie ma**". To twierdzenie o terenie,
którego żadne z czterech źródeł nie potwierdza — dzisiejszy pomiar mówi mniej i mówi
to dokładniej: nie wiadomo, czy ta ściana tam jest.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py
```

Wyjście w bloku ZROBIONE pozycji 6.B26 w `docs/TASKS.md`.

## 7. Zauważone przy okazji, nie tknięte

- **`data/network/sources.json` nie zna warstwy `bm_urbis_topo:tunnel_line`**, choć
  `docs/07-open-data-research.md` opisuje ją z metadanymi, typem `BR04L` i licencją CC0,
  a ta pozycja z niej korzystała. Rejestr maszynowy jest więc uboższy od dokumentu
  o źródło, którego już się w projekcie używa. `data/` jest tylko do odczytu, więc
  zgłaszam, nie dopisuję.
- **Overpass odmawia od co najmniej 08.09.2026** (`Connection reset by peer`), więc
  droga podstawowa z `docs/07-open-data-research.md` jest niedostępna, a każdy dzisiejszy
  pomiar OSM idzie drogą zapasową: 30 kafli, **66 137 965 B** transferu na jedną oś,
  wobec jednego zapytania Overpassa. Dla sześciu osi to 400 MB. Zgłoszone już jako
  droga zapasowa w `reports/osm-api-droga-zapasowa.md`; tutaj tylko liczba dla D.
