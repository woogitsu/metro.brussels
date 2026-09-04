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

---

## 2. Czy `|nx| = 0,9` to ściana?

Ten sam warunek, druga składowa. Zmierzone: najbliższa krawędź to `bore_single` z
`|nx| = 0,922287`, czyli **0,0223 powyżej progu** — dwa razy dalej niż przypadek stropu.

Warto przy okazji odnotować, że kolejność warunków jest tu **bez znaczenia** i to jest
dowodliwe: dla wektora jednostkowego `|ny| >= 0,9` i `|nx| >= 0,9` nie mogą zajść naraz,
bo `0,9² + 0,9² = 1,62 > 1`. Każda krawędź trafia więc do dokładnie jednej etykiety
niezależnie od tego, w jakiej kolejności się pyta.

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

---

## 10. Pasmo doboru dołków: 50 mm

`DEFAULT_REFINE_BAND_M = 0.050`. Zmierzone: doszlifowanie obniża minimum o 3,194 mm,
czyli **15 razy mniej** niż szerokość pasma. Pasmo jest więc z zapasem — pytanie, czy
zapas ma być taki, czy wyliczony z czegoś (np. dziesięciokrotność zmierzonego zysku).

Wąskie pasmo jest szybsze, ale ryzykuje przeoczenie dołka, który na siatce zgrubnej
wygląda niepozornie. Szerokie jest wolniejsze i bezpieczne.

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

## 13. `CONVEXITY_EPS` ma dziś DWIE przeciwne konwencje na granicy — którą ujednolicić?

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
