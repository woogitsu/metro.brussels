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

## Czego na tej liście nie ma

Nie ma tu **wartości progów raportowania** (1,000 · 0,950 · 0,900 · 0,500 · 0,300 · 0,0).
Te są opisane w `reports/M7-clearance-profile.md` jako pasma do czytania profilu, a 0,300
pochodzi z `profiles.CLEARANCE_M`, czyli z wartości, która już jest w repozytorium.
Zmiana tamtych liczb to osobna rozmowa i nie blokuje triażu.

Nie ma też pytań, na które umiem odpowiedzieć sam i już to zrobiłem — na przykład czy
krawędź zerowej długości ma być odmową (ma, i jest przypięta testem).
