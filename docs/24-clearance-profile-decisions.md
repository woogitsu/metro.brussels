# Jedenaście progów w `clearance_profile.py`, które nie są niczyją decyzją

**Data:** 2026-09-03
**Dotyczy:** `tools/blender/clearance_profile.py`
**Poprzedni etap:** `reports/mutation-triage-clearance.md` (PR #128), 72 → 66 ocalałych
**Do czego to jest:** żeby dało się na to odpowiedzieć, a potem przypiąć odpowiedź testem.

## Po co ten dokument

Przegląd mutacyjny znalazł w tym module **72 ocalałe mutacje na 77** — 94 %, najwyższy
udział w całym repozytorium. Pierwszy przebieg triażu (`reports/mutation-triage-clearance.md`,
PR #128) zszedł do **66**, domykając strażniki geometrii zdegenerowanej, i tam się
zatrzymał — bo reszty nie da się ruszyć bez odpowiedzi na pytania, których nie ma
w żadnym dokumencie: gdzie dokładnie przebiega granica między „mieści się" a „nie mieści",
i którą krawędź tunelu uznajemy za strop, a którą za ścięcie naroża.

Tamten raport policzył, ile takich pozycji jest — **jedenaście „progów klasyfikacji"
i dziewięć „remisów przy minimum"** — ale ich nie wypisał. Ten dokument je wypisuje,
każdą ze zmierzoną konsekwencją obu odpowiedzi.

Mogę napisać testy przypinające to, co kod robi **dziś**. Byłoby to jednak zabetonowanie
zachowania, którego nikt nie wybrał: test przestaje wtedy sprawdzać projekt i zaczyna
sprawdzać przypadek, a każda późniejsza próba poprawki wygląda jak regres.

Dlatego zamiast testów jest ta lista. Każde pytanie ma **zmierzoną** konsekwencję obu
odpowiedzi, nie opis. Po odpowiedziach triaż tego modułu rusza od razu.

## Jak czytać

Każda pozycja ma: co robi kod dziś, co zmienia druga odpowiedź, i **liczbę** — na
prawdziwych danych pakietu A albo na prawdziwych profilach z `profiles.py`. Tam, gdzie
liczby nie da się dziś zmierzyć, jest to napisane wprost.

Wszystkie te progi mają dziś status `design_assumption`, ale — w odróżnieniu od
np. długości chunka — **nikt ich nie wybierał**. Wzięły się z pisania kodu.

### Co z liczbami po #86 (dopisane 04.09.2026)

Dokument jest z 03.09.2026, a #86 (`4a03982`) przeliczyło kilometraże stacji na
wszystkich sześciu osiach. Pytanie, czy liczby w tym dokumencie nadal obowiązują,
jest zasadne i **zmierzone**, a nie odpowiedziane z pamięci:

```
punkty osi identyczne: True
length_m: 6686.35 -> 6686.35
stacji ze zmienionym kilometrażem: 11 z 12
  Beekkant: 509.74 -> 509.73   (-0.010 m)
  ...
  Merode:   6686.99 -> 6686.35 (-0.640 m)
```

**Łamana osi nie ruszyła się ani o mikrometr** — #86 poprawiło wyłącznie kilometraże
stacji, o najwyżej 0,640 m. Wynika z tego:

- pozycje **1, 2, 9, 10, 11** stoją na profilach z `profiles.py` i na geometrii osi,
  więc są nietknięte;
- pozycja **6** liczy tolerancję na długości osi, a ta jest identyczna — nietknięta;
- pozycje **3, 4, 5, 7, 8** dotyczą kilometraży, ale jako pytania o KONWENCJĘ, nie
  o wartość, więc treść pytania się nie zmienia.

**Jedna rzecz zostaje otwarta** i jest tu zapisana, żeby nikt jej nie przeoczył:
minimum luzu 0,899948 m z pozycji 3 zostało zmierzone przy starych kilometrażach.
Skan przełącza profil na granicy stacji (`between_stations`), więc gdyby minimum
leżało bliżej niż 0,640 m od takiej granicy, przesunięcie mogłoby zmienić, który
profil w tym punkcie obowiązuje — a wtedy i samą liczbę. Ten dokument nie zapisuje
kilometrażu minimum, więc bez ponownego skanu nie da się tego rozstrzygnąć, a skan
wymaga tunelowego i pojazdowego GLB, czyli Blendera **5.2.1** z przypięcia
(`tools/ci/blender-version.txt`). Lokalnie stoi 4.0.2, który renderuje legacy EEVEE,
więc zgodnie z `CLAUDE.md` §2 pomiaru tu nie wykonuję. Do zrobienia w CI, przy
odpowiedzi na pozycję 3.

Wniosek praktyczny: **52 µm z pozycji 3 traktuj jako rząd wielkości, nie jako
przypięty pomiar.** Sedno pytania jest od tej liczby niezależne — chodzi o to, że
minimum potrafi wypaść dowolnie blisko progu, a nie o to, jak blisko wypadło tego dnia.

---

## 1. Czy krawędź o `|ny| = 0,9` to strop, czy ścięcie naroża?

```python
if ny <= -0.9:  return ROOF
if ny >= 0.9:   return FLOOR
if abs(nx) >= 0.9: return WALL
return CHAMFER
```

**To jest najpilniejsze pytanie z całej listy**, bo próg 0,9 stoi tuż obok prawdziwej
krawędzi prawdziwego profilu.

Zmierzone na wszystkich trzech profilach z `profiles.py`:

| profil | `\|ny\|` krawędzi |
|---|---|
| `box_double` | 0,0000 · 0,8087 · 1,0000 |
| `station` | 0,0000 · 0,7526 · 1,0000 |
| `bore_single` | 0,0221 … **0,8922** · 0,9608 · 0,9956 · 1,0000 |

Krawędzie 12 i 17 profilu `bore_single` mają `|ny| = 0,892173`, czyli **0,0078 poniżej
progu**. Dziś są etykietowane jako *ścięcie naroża stropu*. Próg 0,89 zamiast 0,90
przeniósłby je do *stropu* — a etykieta trafia wprost do raportu luzu jako odpowiedź na
pytanie „co ogranicza skrajnię w tym miejscu".

- **Zostawić 0,9:** okrągły tunel ma 4 krawędzie stropowe i 2 ścięcia w górnej strefie.
- **Zmienić na 0,89:** 6 krawędzi stropowych, 0 ścięć. Raport zmienia treść, geometria nie.
- **Trzecia droga:** etykieta z **kąta**, nie z progu na składowej — np. „strop" to
  krawędź w granicach 25° od poziomu. `arccos(0,9) = 25,84°`, więc dzisiejszy próg jest
  prawie tym samym, tylko wyrażonym mniej czytelnie.

**Czego to NIE zmienia:** liczonego luzu. Etykieta jest opisem, nie wymiarem.


### ROZSTRZYGNIĘTE 04.09.2026 — zostaje 0,9, ale z pomiarem

Właściciel przekazał wybór mnie. **Wartość bez zmian**, bo pomiar mówi, że wybór
jest tu nieczuły w szerokim zakresie, a każda zmiana byłaby ruszeniem liczby bez
powodu. Zmierzone na trzech profilach `profiles.py`, 42 krawędzie łącznie — ile
krawędzi zmienia etykietę wobec dzisiejszego progu:

| próg | krawędzi zmieniających etykietę |
|---|---|
| 20,00° | 0 |
| 25,00° | 0 |
| **25,84°** (dzisiejsze 0,9) | **0** |
| 26,00° | 0 |
| 27,00° | 2 |
| 30,00° | 2 |
| 35,00° | 2 |

Te dwie krawędzie to `bore_single` o `|ny| = 0,892173` — „ścięcie naroża stropu"
przechodzi w „strop". Leżą **0,0078 pod progiem**, czyli najbliżej granicy z całej
sieci krawędzi, i to jest jedyna liczba, która o tym progu cokolwiek mówi.

Trzecia droga z tej pozycji — zapis jako kąt — **odrzucona**: `arccos(0,9)` daje
25,84°, liczbę tak samo nieokrągłą jak 0,9, tylko z dodatkowym wywołaniem trygonometrii
przy granicy. Zapis kątowy byłby czytelniejszy, gdyby próg był okrągły w kątach; nie jest.

---

## 2. Czy `|nx| = 0,9` to ściana?

Ten sam warunek, druga składowa. Zmierzone: najbliższa krawędź to `bore_single` z
`|nx| = 0,922287`, czyli **0,0223 powyżej progu** — dwa razy dalej niż przypadek stropu.

Warto przy okazji odnotować, że kolejność warunków jest tu **bez znaczenia** i to jest
dowodliwe: dla wektora jednostkowego `|ny| >= 0,9` i `|nx| >= 0,9` nie mogą zajść naraz,
bo `0,9² + 0,9² = 1,62 > 1`. Każda krawędź trafia więc do dokładnie jednej etykiety
niezależnie od tego, w jakiej kolejności się pyta.


### ROZSTRZYGNIĘTE 04.09.2026 — razem z pozycją 1

Ten sam próg, ta sama os, ta sama decyzja: **0,9 zostaje**, a uzasadnieniem jest
pomiar wypisany w pozycji 1 (20°–26° daje etykiety identyczne co do krawędzi).
Rozstrzygane łącznie, bo rozdzielenie tych dwóch progów dałoby profil, w którym
krawędź pod 26° do poziomu jest stropem, a pod 26° do pionu już nie jest ścianą.

---

## 3. Czy luz **dokładnie równy** progowi jest naruszeniem?

```python
below = [r for r in records if r["clearance_m"] < threshold_m]
```

Dziś: **nie** — równość mieści się. Zmierzone na pakiecie A: minimum luzu wynosi
**0,899948 m**, a jeden z progów raportowania to **0,900 m**. Różnica: **52 µm**.

Gdyby minimum wypadło o te 52 µm wyżej, dokładnie na progu, dzisiejszy kod **nie
zgłosiłby go w ogóle** — a jest to najciaśniejsze miejsce na całym pakiecie.

- **Zostawić `<`:** próg znaczy „poniżej tego jest źle".
- **Zmienić na `<=`:** próg znaczy „tyle to już za mało".

Nie ma tu odpowiedzi lepszej z natury; jest odpowiedź, którą trzeba wybrać, bo w tym
module jest **niespójna z sąsiednim warunkiem** (pozycja 4).

### ROZSTRZYGNIĘTE 04.09.2026 — ani `<`, ani `<=`

**Odpowiedź właściciela: żadne z dwóch.** Zamiast wybierać stronę operatora,
granica staje się nazwanym **pasmem, które się RAPORTUJE**. Luz w odległości
najwyżej jednego milimetra od progu nie jest ani po cichu w porządku, ani po cichu
naruszeniem — jest zgłaszany jako `at_threshold`. To zamyka też pozycję 4: obie
strony czytają teraz jednakowo.

Dlaczego jeden milimetr, a nie liczba wzięta z powietrza: ten moduł **zapisuje**
progi z dokładnością milimetra — `round(threshold_m, 3)` w `critical_places`
i `f"{t:.3f}"` w `statistics`. Poniżej milimetra w wyjściu nie ma informacji, po
której stronie progu leży wartość, więc rozstrzyganie tam operatorem jest
rozstrzyganiem o czymś, czego raport i tak nie odnotowuje. Równość tolerancji
z rozdzielczością zapisu jest przybita testem, żeby zmiana jednej strony bez
drugiej nie przeszła po cichu.

**Pasmo liczy się w milimetrach CAŁKOWITYCH, i to nie jest szczegół.** Pierwsza
wersja porównywała floaty (`abs(v - t) <= 0.001`) i przywracała dokładnie to pytanie,
które tolerancja miała usunąć, tylko o poziom niżej. Zmierzone:

```
  luz 0.899   |v-0.900| = 0.0010000000000000009    <= 0.001 ? False
  luz 0.9005  |v-0.900| = 0.0004999999999999449    <= 0.001 ? True
```

Milimetr **pod** progiem z pasma wypadał, pół milimetra **nad** nim wpadało —
granicę rozstrzygała reprezentacja binarna, nie decyzja. Liczby całkowite tego
problemu nie mają i mówią wprost, co pasmo znaczy: „w odległości najwyżej jednego
zapisanego milimetra".

Co się NIE zmieniło: `below_threshold` dalej znaczy **ściśle poniżej** progu, bo
czyta je `profile_vehicle.py` i przybijają je testy. Pasmo doszło jako osobny klucz
`at_threshold`. Rozszerzenie zakresu `critical_places` nie może wywrócić CI —
`vehicle_clearance.sh` te wpisy wypisuje, a do listy `problems` ich nie dodaje,
i jest to sprawdzone w kodzie bramki, nie założone.

---

## 4. Dobór dołków do doszlifowania używa `<=`, a raportowanie `<`

```python
floor_value = min(...) + band_m
picked = [... if r["clearance_m"] <= floor_value]
```

Ta sama wielkość, ta sama jednostka, przeciwna konwencja na granicy. Jedna z nich jest
przypadkiem — pytanie, która.

Zmierzone: pasmo doboru to 50 mm, a doszlifowanie obniża minimum o **3,194 mm**. Zmiana
`<=` na `<` wyrzuciłaby z doboru wyłącznie pozycje o luzie **równym co do bitu**
`min + 0,050`, czyli w praktyce żadną. **Konsekwencja liczbowa: zerowa.** To pytanie jest
o spójność, nie o wynik.

**ROZSTRZYGNIĘTE 04.09.2026 razem z pozycją 3:** oba warunki używają teraz tego samego
pasma (`at_or_below_threshold`), więc niespójność znika, a konsekwencja liczbowa
zostaje zerowa — dokładnie jak zmierzono wyżej.

---

## 5. Czy przerwa **dokładnie** 25 m to jedno miejsce, czy dwa?

```python
if record["chainage_m"] - runs[-1][-1]["chainage_m"] <= gap_m:
```

`CRITICAL_CLUSTER_GAP_M = 25,0` — dobrane jako „nieco więcej niż cięciwa najdłuższej
bryły M7 (15,12 m)". Uzasadnienie dotyczy rzędu wielkości, nie samej liczby: 20 m i 30 m
spełniają je tak samo dobrze.

Pytanie właściwe brzmi: **czy ta liczba ma być pochodną czegoś**, na przykład długości
składu (94,0 m, `spec`) albo cięciwy bryły (15,12 m), czy zostaje okrągłą wartością do
czytania raportu.


### ROZSTRZYGNIĘTE 04.09.2026 — krotność kroku skanu, nie geometria pudła

Właściciel przekazał wybór mnie. **Liczba zostaje 25,0 m, uzasadnienie się zmienia** —
i to jest cała treść rozstrzygnięcia, bo dotychczasowe uzasadnienie było nieprawdziwe.

Zmierzone na pakiecie A, tor 1, próg 1,000 m, z doszlifowaniem:

```
najwieksze LUKI chainage miedzy sasiednimi rekordami pod progiem:
  [1524.584, 844.529, 5.01, 5.001, 4.894, 4.724, 4.525, 3.89, ...]
```

Dwie pierwsze dzielą **prawdziwie różne miejsca**. Trzecia i dalsze leżą wewnątrz
jednego miejsca i największa z nich to **5,01 m — czyli krok skanu**. Wielkością, od
której ta stała naprawdę zależy, jest więc gęstość próbkowania, a nie cięciwa pudła.
Cięciwa jest zresztą 15,1167 m, nie 15,12 jak mówił komentarz.

Zmierzony zakres nieczułości i to, co go łamie:

| odstęp | wpisów przy 1,000 m | przy 0,950 | przy 0,900 |
|---|---|---|---|
| 5,0 m | **5** | 2 | 2 |
| 15,0985 m (cięciwa) | 3 | 2 | 2 |
| 15,667 m (cięciwa nominalna) | 3 | 2 | 2 |
| **25,0 m** | **3** | **2** | **2** |
| 50,0 m | 3 | 2 | **1** |
| 94,0 m (długość składu) | 3 | 2 | **1** |

Odstęp równy krokowi **rozbija trzy miejsca na pięć**. Odstęp wyprowadzony z długości
składu **scala dwa miejsca w jedno** przy progu 0,900 m, czyli traci wpis z raportu —
to jedyna z rozważanych wartości, która zmienia wyjście, i zmienia je na gorsze.

W kodzie stoi `CLUSTER_GAP_STEPS = 5` i `cluster_gap_m(step_m)`, a `profile_vehicle.py`
woła to z FAKTYCZNYM krokiem. Krotność, nie liczba, bo `--step 25` znaczy, że osi nie
da się rozróżnić drobniej niż 25 m, i wtedy scalanie miejsc 30 m od siebie jest
**poprawne**, a nie stratą.

---

## 6. Tolerancja `1e-6` przy kontroli pokrycia osi

```python
if b - a > step_m + 1e-6:
    problems.append(...)
```

Metr osi ma tu tolerancję mikrometra. Przy realnych chainage **`1e-6` nie jest
reprezentowalne dokładnie**, a różnica wypada raz nad progiem, raz pod nim — zależnie
od podstawy:

```
1e-6 przy  400,0 m  ->  1e-06                    (dokładnie)
1e-6 przy 1500,0 m  ->  9.999999974752427e-07    (MNIEJ niż próg)
1e-6 przy 6700,0 m  ->  1.0000003385357559e-06   (WIĘCEJ niż próg)
```

Znaczy to, że warunek „przerwa większa niż krok o dokładnie tolerancję" nie zachodzi
nigdy, a po której stronie granicy wypadnie konkretny przypadek, decyduje kilometraż.
To dokładnie ta pułapka, która w `test_lod.py` sprawiła, że test napisany pod cztery
mutacje zabijał dwie (`reports/mutation-triage-lod.md`).

- **Zostawić `1e-6`:** trzeba pamiętać, że przy dużym chainage granica jest rozmyta.
- **Zmienić na potęgę dwójki** (`2**-20 ≈ 9,54e-7`): granica jest granicą przy każdej
  podstawie i da się ją przypiąć testem.

Rekomendacja techniczna jest jednoznaczna (potęga dwójki), ale to zmiana wartości
progu, więc pytam.


### ROZSTRZYGNIĘTE 04.09.2026 — milimetry całkowite

**Odpowiedź właściciela: przejść na milimetry całkowite** — tą samą drogą, którą
poszła decyzja 1 o pasmie progu, czyli jedno wyprowadzenie rozdzielczości na cały
moduł zamiast dwóch. `coverage_gaps` porównuje teraz `_millimetres(...)`, a nie floaty.

Zmierzone po zmianie — ten sam warunek przy trzech podstawach:

| podstawa | przerwa 5,0004 m | przerwa 5,0006 m |
|---|---|---|
| 0,0 m | 5000 mm, nie dziura | 5001 mm, **dziura** |
| 5,0 m | 5000 mm, nie dziura | 5001 mm, **dziura** |
| 6700,0 m | 5000 mm, nie dziura | 5001 mm, **dziura** |

Nie ma już „strony granicy zależnej od kilometrażu". Cena jest jawna: tolerancja
rośnie z mikrometra do milimetra, tysiąckrotnie. Oś ma pierścienie co 5 m i chainage
zapisany z dokładnością do centymetra, więc milimetr jest wciąż o rząd drobniejszy
niż wszystko, co ta oś potrafi rozróżnić.

#### Jedno ograniczenie, którego nie obchodzę doborem liczb

Granica wypada **poniżej połowy** milimetra, nie na milimetrze, bo `_millimetres`
zaokrągla do najbliższego. I jest jeden punkt, w którym niezależność od kilometrażu
**nie zachodzi**: różnica dokładnie pół milimetra rozstrzyga się parzystością licznika,
bo `round()` w Pythonie zaokrągla połowę do liczby parzystej. Zmierzone:

| podstawa | mm | mm(+0,5 mm) | różnica | licznik |
|---|---|---|---|---|
| 0,0 | 0 | 0 | 0 | parzysty |
| 5,0 | 5000 | 5000 | 0 | parzysty |
| 1500,000 | 1500000 | 1500000 | 0 | parzysty |
| 1500,001 | 1500001 | 1500002 | **1** | NIEPARZYSTY |
| 6592,739 | 6592739 | 6592740 | **1** | NIEPARZYSTY |
| 6592,740 | 6592740 | 6592740 | 0 | parzysty |

Znalazł to **mój własny test**, który celował dokładnie w połowę milimetra i padł na
końcu zakresu pakietu A (6592,739 m = 6686,739 − 94,0). Zapisuję to, a nie tylko
przesuwam próbki na 0,4 i 0,6 mm, bo bez tego zdania łatwo napisać w raporcie
„granica jest teraz dokładna przy każdym kilometrażu" — co jest prawdą o 0,4 i 0,6 mm,
a nieprawdą o 0,5 mm. Przypięte testem
`test_clearance_profile_coverage_exactly_half_a_millimetre_depends_on_parity`.

Konsekwencja praktyczna jest żadna: chainage w `data/track/` jest zapisany z dokładnością
do centymetra, więc różnica dokładnie pół milimetra nie powstaje z danych — powstaje
z testu, który ją skonstruuje.

Kontrola na prawdziwych danych: pakiet A, oba tory, przed i po zmianie —
`coverage_problems` puste w obu przypadkach, minimum `0,918851` / `0,899948` m
bez zmian, wpisy miejsc krytycznych identyczne.

---

## 7. Czy skład **dokładnie** tak długi jak oś mieści się na niej?

```python
last = axis_length_m - train_length_m
if last <= 0.0:
    raise ValueError(f"skład {train_length_m} m nie mieści się na osi {axis_length_m} m")
```

Dziś `last == 0` jest **odmową**. Skład o długości równej osi ma dokładnie jedną
dopuszczalną pozycję — czoło w zerze — i ta pozycja jest sensowna: zajmuje całą oś.

Zmierzone na `data/track/`: najkrótszy pakiet to **L5_D, 3847,23 m**, a skład M7 ma
94,0 m, więc **dziś ten przypadek nie zachodzi na żadnym pakiecie** — najciaśniejszy
stosunek to 41:1. Zachodzi natomiast dla krótkiego wycinka osi podanego ręcznie, co jest
normalnym trybem pracy przy badaniu jednego łuku.


### ROZSTRZYGNIĘTE 04.09.2026 — jedna pozycja, czoło w zerze

**Odpowiedź właściciela: równość NIE jest odmową.** Strażnik to teraz `last < 0.0`.

Powodem jest nieciągłość zmierzona wprost:

```
os 94.0 m, sklad 93.999 m -> 2 pozycji: [0.0, 0.001]
os 94.0 m, sklad 94.0   m -> [0.0]                     (bylo: ValueError)
os 94.0 m, sklad 94.001 m -> ValueError: sklad 94.001 m nie miesci sie na osi 94.0 m
```

Poprzednio było: dwie pozycje / **odmowa** / odmowa — czyli wynik dobrze określony
(skład zajmuje dokładnie całą oś) był odrzucany. Kontrola negatywna po drugiej stronie
jest przybita razem z tym: skład dłuższy od osi choćby o milimetr nadal jest odmową,
bo inaczej „poluzowałem strażnika" nie dałoby się odróżnić od „usunąłem strażnika".

Poprzedni test przypinał odmowę i mówił wprost: „gdyby właściciel chciał, żeby równość
była dopuszczalna, zmienia się strażnik i ten test razem z nim". Jest **przepisany**,
nie dopisany obok.

---

## 8. Punkt **dokładnie** na kilometrażu stacji: przed nią czy za nią?

```python
if value <= chainage_m:
    before = station
```

Dziś: punkt na kilometrażu stacji jest **za** nią. Blok sygnalizacyjny w tym samym
repozytorium ma konwencję odwrotną — półotwartą `[start, end)`, w której granica należy
do bloku **następnego** (`docs/15-classic-signalling.md`).

Dwie różne konwencje na tę samą sytuację w jednym projekcie to koszt, który ktoś kiedyś
zapłaci. Pytanie, którą ujednolicić.


### SKREŚLONE 04.09.2026 — pozycja stała na MOJEJ pomyłce

Sprzeczności nie ma i mówię to wprost, bo to ja ją tu wpisałem. Sprawdzone w kodzie
obu stron, nie z pamięci:

```csharp
// src/Sim/Signalling/Block.cs
public bool Contains(double chainageM) => chainageM >= StartM && chainageM < EndM;
```

```python
# clearance_profile.between_stations
if value <= chainage_m:
    before = station
```

Punkt na kilometrażu stacji **S** dostaje `after: S, before: następna`, czyli wpada
w przedział `[S, następna)`. Blok stały robi to samo: punkt na granicy należy do bloku,
który się w niej **zaczyna**. **Obie konwencje wkładają punkt graniczny do przedziału
zaczynającego się w nim** — to jest ta sama konwencja, nie przeciwna. Sprawdzone na
wszystkich dwunastu stacjach pakietu A, dla `c`, `c − 1e-9` i `c + 1e-9`.

Skąd wzięła się pomyłka: `docs/15` opisuje półotwartość zdaniem „chainage dokładnie
na granicy należy już do bloku **następnego**", a „następny" znaczy tam „następny wobec
tego, który się w tej granicy kończy". Przeczytałem to jako „następny wobec granicy",
czyli o jeden przedział dalej.

Zgodność jest przybita testem, wybranym przez właściciela — bo dokument poprawiony bez
testu to znów liczba w komentarzu, której nic nie porównuje. Test wprost porównuje
`between_stations` z regułą `[start, end)` na tej samej granicy.

---

## 9. Pasma kandydatów: dokładne czy kubełkowane?

`CANDIDATE_BUCKET_M = 0.0` — dziś dokładne. Zmierzone w `reports/M7-clearance-profile.md`:

| tryb | kandydatów | czas | błąd minimum |
|---|---|---|---|
| dokładny (0,0) | 1306 | odniesienie | 0 |
| kubełki 0,5 m | 794 | −40 % | **0,78 mm** |
| kubełki 1,0 m | — | — | **3,4 mm** |

To jedyna pozycja na tej liście, w której odpowiedź kupuje czas CI za dokładność.
Przy minimum 0,899948 m błąd 0,78 mm to 0,09 % — pytanie, czy to jest cena, którą chcemy
płacić za 40 % krótszy przebieg.


### ROZSTRZYGNIĘTE 04.09.2026 — zostają dokładne, a tabela wyżej ma poprawkę

Właściciel przekazał wybór mnie. **Zostają dokładne (0,0)**, i decyduje o tym nie
procent, a sekundy. Zmierzone z doszlifowaniem, oba tory, Blender 5.2.1:

| tryb | kandydatów | czas tor 0 | czas tor 1 | błąd tor 0 | błąd tor 1 |
|---|---|---|---|---|---|
| dokładny (0,0) | 1306 | 9,50 s | 10,52 s | odniesienie | odniesienie |
| kubełki 0,5 m | 794 | 5,36 s | 5,61 s | **+0,779 mm** | 0,000 mm |
| kubełki 1,0 m | 630 | 4,49 s | 4,54 s | **+0,779 mm** | **+0,873 mm** |

Dokumentowe „−40 %" jest prawdą w procentach i **niczym w sekundach**: cały zakup to
około 4 s na tor, a tory idą równolegle. Cena to 0,78 mm na pomiarze, który rozstrzyga,
czy M7 mieści się w tunelu. Nie ma tu wymiany, którą warto zrobić.

**Poprawka do tabeli powyżej:** 0,78 mm dla kubełków 0,5 m **potwierdza się** (tor 0,
z doszlifowaniem). Zapisanego tam **3,4 mm dla kubełków 1,0 m nie odtworzyłem** —
z doszlifowaniem wychodzi +0,779 mm (tor 0) i +0,873 mm (tor 1), a bez doszlifowania
+3,090 mm (tor 0) i 0,000 mm (tor 1). Liczba 3,4 mm nie wyszła w żadnym z tych czterech
przebiegów; nie wiem, w jakich warunkach powstała, i dlatego jej nie zostawiam bez tej
adnotacji zamiast po cichu podmienić.

---

## 10. Pasmo doboru dołków: 50 mm

`DEFAULT_REFINE_BAND_M = 0.050`. Zmierzone: doszlifowanie obniża minimum o 3,194 mm,
czyli **15 razy mniej** niż szerokość pasma. Pasmo jest więc z zapasem — pytanie, czy
zapas ma być taki, czy wyliczony z czegoś (np. dziesięciokrotność zmierzonego zysku).

Wąskie pasmo jest szybsze, ale ryzykuje przeoczenie dołka, który na siatce zgrubnej
wygląda niepozornie. Szerokie jest wolniejsze i bezpieczne.


### ROZSTRZYGNIĘTE 04.09.2026 — 50 mm zostaje, ale uzasadnienie było ODWROTNE

Właściciel przekazał wybór mnie. **Wartość zostaje**, a zdanie wyżej („pasmo jest
z zapasem", „15 razy mniej niż szerokość pasma") jest **nieprawdziwe** i to jest
najważniejsza część tego rozstrzygnięcia. Zmierzone, pakiet A, tor 1:

| pasmo | okien | pozycji | min po doszlifowaniu | zysk mm | sekundy |
|---|---|---|---|---|---|
| 0,001 m | 2 | 95 | 0,900821 | 2,321 | 0,41 |
| 0,003 m | 2 | 114 | 0,900821 | 2,321 | 0,52 |
| 0,005 m | 2 | 114 | 0,900821 | 2,321 | 0,55 |
| 0,010 m | 2 | 114 | 0,900821 | 2,321 | 0,55 |
| **0,050 m** | **6** | **817** | **0,899948** | **3,194** | **3,93** |
| 0,100 m | 7 | 1349 | 0,899948 | 3,194 | 6,36 |
| 0,200 m | 1 | 25052 | 0,899948 | 3,194 | 122,56 |

Przy 10 mm globalne minimum **0,899948 m zostaje przeoczone** — raport pokazałby
0,900821 m, czyli o 0,873 mm za wysoko, i najciaśniejsze miejsce pakietu przestałoby
być najciaśniejszym. 50 mm nie jest więc piętnastokrotnym zapasem nad zyskiem
3,194 mm; jest wartością **niedaleko od tej, przy której dołek przestaje się znajdować**.
Wiązanie pasma z zyskiem — trzecia rozważana droga — jest zresztą sprzężeniem zwrotnym,
nie uzasadnieniem: zysk sam zależy od pasma, co ta tabela pokazuje w kolumnie „zysk mm".

Nie poszerzam do 100 mm, choć daje to samo minimum: przy 200 mm okna zlewają się
w jedno i czas rośnie z 3,93 s do 122,56 s, czyli trzydziestokrotnie. Skoro sufit jest
tak blisko, poszerzanie „na zapas" kupowałoby ryzyko przekroczenia go przy pierwszym
pakiecie z płaskim dnem profilu — a to jest ryzyko czerwonego CI, nie ryzyko pomiaru.

---

## 11. `CONVEXITY_EPS = 1e-9` — kiedy obrys przestaje być wypukły?

```python
if turn < -CONVEXITY_EPS:
    raise ValueError("obrys profilu nie jest wypukły")
```

Cały pomiar luzu stoi na wypukłości: dla punktu wewnątrz wielokąta wypukłego odległość
od brzegu równa się minimum odległości od półpłaszczyzn. Dla wielokąta niewypukłego ta
równość **nie zachodzi** i wynik przestaje być odległością.

`1e-9` przepuszcza więc obrysy „prawie wypukłe". Zmierzone: żaden z trzech profilów
w `profiles.py` nie zbliża się do tego progu — wszystkie są wypukłe z dużym zapasem.
Pytanie dotyczy profilu, który dopiero powstanie: czy odchyłka rzędu nanometra ma być
tolerowana, czy odrzucana, skoro konsekwencją jest cichy błąd pomiaru, a nie brzydka
geometria.


### ROZSTRZYGNIĘTE 04.09.2026 — 1e-9 zostaje, z wypisanym zakresem bezpiecznym

Właściciel przekazał wybór mnie. **Wartość bez zmian**, bo pytanie nie było o wartość,
tylko o to, że nie wiadomo, skąd się wzięła. Zmierzone, oba końce zakresu:

**Od góry — najmniejszy PRAWDZIWY niezerowy `turn` na trzech profilach:**

| profil | najmniejszy \|turn\| | ile to razy EPS |
|---|---|---|
| `bore_single` | 6,060260e-02 | 6,1·10⁷ |
| `box_double` | 3,025000e+00 | 3,0·10⁹ |
| `station` | 4,640000e+00 | 4,6·10⁹ |

**Od dołu — szum zmiennoprzecinkowy, ten sam obrys przesunięty o stałą:**

| przesunięcie | największy dryf `turn` | ile to razy EPS |
|---|---|---|
| 0 m (współrzędne lokalne) | **0,0 dokładnie** | 0 |
| 1 m | 7,6e-16 | 7,6·10⁻⁷ |
| 1000 m | 1,3e-12 | 1,3·10⁻³ |
| 10⁶ m | 1,3e-09 | **1,3** |

Współrzędne Lambert 72 dla Brukseli to ~1,5·10⁵ m, czyli dryf rzędu 1e-11 — około
**0,01 × EPS**. Próg ma więc **10² zapasu do szumu i 6·10⁷ do najbliższej prawdziwej
krawędzi**; mieści się w przedziale bezpiecznym rozpiętym na siedem rzędów wielkości
po każdej stronie i nie ma w tym przedziale wartości lepszej z natury.

Zaostrzenie do 1e-12 **odrzucam z pomiaru, nie z ostrożności**: leży poniżej szumu
przy współrzędnych Lamberta, więc obrys zbudowany ze współrzędnych absolutnych mógłby
zostać odrzucony za sam szum zaokrągleń. Rozluźnienia do 1e-6 też nie robię — toleruje
wklęsłość rzędu 0,3 µm na profilu 3 m, a konsekwencją niewypukłości jest **cichy błąd
pomiaru** (luz przestaje być odległością od brzegu), nie brzydka geometria.

Odchyłka, którą 1e-9 jeszcze przepuszcza, to około **0,3 nanometra** na profilu 3 m.

---

## 12. Czy pierścień o polu **dokładnie zero** to obrys? — ROZSTRZYGNIĘTE 04.09.2026

Pozycja dopisana po tej liście, bo pytanie wyszło z triażu (#196), nie z tego
dokumentu. **Odpowiedź właściciela: `halfplanes` ma taki pierścień ODRZUCAĆ,
z nazwanym błędem, tak samo jak odrzuca zerową krawędź.** Wdrożone.

Dlaczego to było pytanie: mutacja `area2 > 0.0` -> `>= 0.0` w wyznaczaniu orientacji
przeżywała przegląd. Rozstrzyga się wyłącznie na pierścieniu o polu zerowym, a tam
luz jest identyczny w 1681 punktach na 1681 — różni się sama etykieta wiążącej
krawędzi, w 41 punktach.

### Strażnik jej NIE ZABIŁ, i to trzeba zapisać wprost

Pierwsza wersja tej pozycji twierdziła, że odmowa zamyka tamtą mutację. Nie zamyka.
Przegląd po dodaniu strażnika, na `f6058f9`:

```
[MUTACJE] rozstrzygniętych 78/78, zabitych 29, ocalałych 49, nierozstrzygniętych 0
  w.188  '<=' -> '<'      ZABITA — test granicy progu
  w.190  '>'  -> '>='     OCALAŁA
```

Strażnik czyni ją **nieosiągalną**, a nie zabitą: różnicę między `>` i `>=` widać
wyłącznie przy `area2 == 0.0`, a takie wejście jest już odrzucone wyżej. Z „ocalałej,
bo nie wiadomo co robi" zrobiła się „ocalała, bo dowodliwie równoważna" — postęp, ale
nie ten, który obiecywałem.

Zostawienie jej byłoby zostawieniem progu, który niczego nie rozstrzyga, w module,
którego progi są tematem całego tego dokumentu. Porównanie zastąpione więc
wyrażeniem **bez progu**:

```python
orientation = math.copysign(1.0, area2)
```

Zmierzone: 0 różnic wobec starego wyrażenia na 200 000 wejściach z `area2 != 0`.
Dla dokładnego zera wyniki się różnią (+1,0 kontra -1,0), ale tam nie dochodzi już
wykonanie. Pomiar końcowy, `c82157f`:

| | main przed zmianą | strażnik sam | strażnik + `copysign` |
|---|---:|---:|---:|
| mutacji | 77 | 78 | **76** |
| zabitych | 28 | 29 | **28** |
| ocalałych | **49** | 49 | **48** |

Tabelę trzeba czytać uczciwie: zabitych jest tyle samo co przed zmianą, bo skład się
wymienił — odszedł zabity `0.0` -> `0.001` z wiersza orientacji, doszedł zabity
`<=` -> `<` z nowego strażnika. **Ocalałych jest o jedną mniej, i nie dlatego, że
doszedł test, który ją zabija, ale dlatego, że zniknął próg, którego żaden test nigdy
nie mógłby zabić.** To jest mniej efektowne niż „+1 zabita" i dlatego stoi tu wprost.

### Próg jest istniejący, nie nowy — i to jest zmierzone

Naturalne `area2 == 0.0` byłoby **dekoracją**. Zmierzone 04.09.2026 na 200 000
losowych trójkach współliniowych:

```
prób: 200000, area2 != 0.0 w 126915 przypadkach (63.46 %)
największe |area2| dla wejścia współliniowego: 2.183e-11
```

Dokładne porównanie z zerem przepuszczałoby **prawie dwie trzecie** prawdziwie
zdegenerowanych wejść. Strażnik porównuje więc z `CONVEXITY_EPS = 1e-9`, czyli
z progiem, który w tym module **już był** — a nie z dwunastą stałą. Rozdzielenie
zmierzone z obu stron:

| wejście | \|area2\| | względem progu |
|---|---:|---|
| trójki współliniowe (200 000 prób, maksimum) | 2,183e-11 | 1,7 rzędu **poniżej** |
| trójkąt 0,5 mm — najmniejszy, który zestaw każe przyjąć | 2,5e-07 | 2,4 rzędu **powyżej** |
| `bore_single` | 56,53 | 10,8 rzędu powyżej |
| `box_double` | 110,48 | 11,0 rzędu powyżej |
| `station` | 196,48 | 11,3 rzędu powyżej |

### Nowy próg dostał od razu przybitą granicę

Bez tego pozycja 12 tworzyłaby pozycję 13. Granica **jest osiągalna**: trójkąt
o przyprostokątnych 1e-5 i 1e-4 daje `area2` dokładnie `1e-09`, i tak samo cztery
inne pary (1e-9 x 1, 1e-4 x 1e-5, 2e-5 x 5e-5, 1 x 1e-9). Na progu obrys jest
**odrzucany** (`<=`), tak samo jak przy zerowej krawędzi; 1e-5 m na 1e-4 m to
0,01 mm na 0,1 mm i nie jest to profil tunelu przy żadnym czytaniu.

Warte zapamiętania, bo dotyczy metody, nie tej jednej pozycji: **300 000 losowych
obrysów o skali rozłożonej logarytmicznie trafiło w ten próg dokładnie ZERO razy.**
Samo próbkowanie orzekłoby więc, że `<=` i `<` są nierozróżnialne — a mutacja
`<=` -> `<` wywraca test. W taki próg się nie wpada losowo, tylko się go
konstruuje, i to jest cała różnica między „zmierzyłem równoważność" a „nie
znalazłem różnicy".

---

## 13. `CONVEXITY_EPS` miał DWIE przeciwne konwencje na granicy — ROZSTRZYGNIĘTE 04.09.2026

Pozycja dopisana 04.09.2026 po triażu reszty ocalałych mutacji; pytanie wyszło
z pomiaru, nie z tej listy. Nie rozstrzygam jej sam, bo jest tym samym rodzajem
pytania, co pozycja 4: **ta sama stała, ta sama jednostka, przeciwna konwencja
na granicy** — tylko tu obie strony są w jednej funkcji.

`halfplanes` używa `CONVEXITY_EPS = 1e-9` dwa razy, o osiemnaście wierszy od siebie:

```python
if abs(area2) <= CONVEXITY_EPS:          # w. 239 — pole obrysu
    raise ValueError("obrys profilu ma zerowe pole")
...
if turn < -CONVEXITY_EPS:                # w. 262 — wypukłość obrysu
    raise ValueError("obrys profilu nie jest wypukły")
```

Odchyłka **dokładnie równa tolerancji** trafia w tych dwóch miejscach po przeciwnych
stronach granicy, i oba przypadki są osiągalne CO DO BITU — zmierzone, nie oszacowane:

| miejsce | wejście na progu | co robi kod dziś |
|---|---|---|
| w. 239, pole | trójkąt 1e-5 x 1e-4 m -> `area2` DOKŁADNIE `1e-09` | **ODRZUCA** (`<=`) |
| w. 262, wypukłość | obrys CCW z zakrętem DOKŁADNIE `-1e-09` | **PRZYJMUJE** (`<`) |

Konstrukcja drugiego wejścia, żeby dało się to powtórzyć:

```
ring   = [(0,0), (1,0), (2,-1e-9), (3,0), (3,2), (0,2)]
area2  = 12.000000002                    (11 rzędów powyżej progu, obrys jest obrysem)
zakręty = [-1e-09, 2e-09, 2.0, 6.0, 6.0, 2.0]
najmniejszy zakręt == -1e-9 co do bitu: True
oryginał    : PRZYJĄŁ, 6 półpłaszczyzn
mutacja `<=`: ODMÓWIŁ — „obrys profilu nie jest wypukły"
```

**Odpowiedź właściciela: ujednolicić na „odrzuć na progu".** Zakręt dokładnie równy
`-CONVEXITY_EPS` jest teraz odmową (`turn <= -CONVEXITY_EPS`), tak samo jak pole
dokładnie równe progowi. Jedna stała, jedna konwencja.

Warunek, który postawiłem przed wdrożeniem: zaostrzenie nie może odrzucić prawdziwego
profilu. Zmierzone przed zmianą, wszystkie trzy profile z `profiles.py`:

```
profil             najmniejszy zakret     zapas nad -EPS
bore_single       0.06060260000000016          6.06e+07x
box_double          3.024999999999999          3.02e+09x
station             4.639999999999999          4.64e+09x
```

Wszystkie **dodatnie** i najbliższy progu leży 6·10⁷ razy nad nim, więc zaostrzenie
nie ma jak dotknąć prawdziwego obrysu. Tolerancja na szum zaokrąglenia zostaje:
obrys z zakrętem `-1e-10`, czyli dziesięć razy bliżej zera niż próg, nadal przechodzi
i jest to przybite osobnym testem — inaczej nie dałoby się odróżnić „zaostrzyłem
granicę" od „zjadłem całą tolerancję".

Granica w. 239 została przybita testem w #197 (decyzja z pozycji 12: na progu
**odrzucać**). Granica w. 262 nie jest przybita niczym, a mutacja `<` -> `<=`
przeżywa przegląd właśnie dlatego, że nikt nie powiedział, co ma się stać
na progu. Przypięcie jej testem **bez odpowiedzi** zabetonowałoby zachowanie,
którego nikt nie wybrał — a to jest dokładnie zarzut ze wstępu tego dokumentu.

- **Ujednolicić „na progu odrzucamy" (`turn <= -EPS`):** obie strony czytają tak samo,
  „odchyłka równa tolerancji jest już odchyłką". Cena: obrys o zakręcie dokładnie
  `-1e-9` przestaje przechodzić, czyli tolerancja robi się o jeden bit ciaśniejsza.
- **Ujednolicić „na progu przyjmujemy" (`abs(area2) < EPS`):** wymagałoby zmiany
  decyzji z pozycji 12, więc jest to pytanie o cofnięcie tamtej odpowiedzi, nie
  o nową.
- **Trzecia droga, ta z pozycji 3:** zamiast wybierać stronę operatora, zgłaszać
  pasmo. Tu jednak wyjściem jest odmowa, a nie liczba w raporcie, więc „obrys
  prawie wypukły" nie ma gdzie zostać zgłoszony — pasmo dałoby trzeci stan
  w funkcji, która dziś ma dwa.

**Czego to NIE zmienia i to jest zmierzone:** żadnego prawdziwego profilu. Najmniejszy
zakręt w `profiles.py` to `bore_single` z **0,0606** — 7,8 rzędu POWYŻEJ progu:

| profil | najmniejszy zakręt | względem progu |
|---|---:|---|
| `bore_single` | 0,0606026 | 7,8 rzędu powyżej |
| `box_double` | 3,025 | 9,5 rzędu powyżej |
| `station` | 4,640 | 9,7 rzędu powyżej |

Pytanie jest więc o **spójność i o profil, który dopiero powstanie**, nie o dzisiejszy
wynik — tak samo jak pozycja 11, z którą łączy je ta sama stała. Konsekwencja liczbowa
dla pakietu A: **zerowa.**

## Czego na tej liście nie ma

Nie ma tu **wartości progów raportowania** (1,000 · 0,950 · 0,900 · 0,500 · 0,300 · 0,0).
Te są opisane w `reports/M7-clearance-profile.md` jako pasma do czytania profilu, a 0,300
pochodzi z `profiles.CLEARANCE_M`, czyli z wartości, która już jest w repozytorium.
Zmiana tamtych liczb to osobna rozmowa i nie blokuje triażu.

Nie ma też pytań, na które umiem odpowiedzieć sam i już to zrobiłem — na przykład czy
krawędź zerowej długości ma być odmową (ma, i jest przypięta testem).
