# Skrajnia M7 na rzeczywistych łukach pakietu A

Kontrola, której nie dało się wykonać wcześniej: dopiero po T-220 (#14) i T-210 (#12)
w repozytorium są jednocześnie geometria pojazdu i rzeczywisty przebieg osi. Nie jest to
osobne zadanie z ROADMAP — jest to weryfikacja wynikająca z reguły „jeżeli skrajnia
nie przechodzi, nie zmniejszaj pociągu".

- narzędzie: `tools/blender/clearance.py` (czysty Python, bez bpy)
- testy: `tools/tests/test_clearance.py`
- odtworzenie: `python3 tools/blender/clearance.py --alignment data/track/L1_A.json --profile box_double`
- w CI: `tools/ci/tunnel_alignment.sh` (job `tunnel-alignment`)

## 1. Model

Sztywne pudło członu opiera się na łuku cięciwą, więc jego środek wchodzi do wnętrza
łuku o strzałkę cięciwy `v = R − √(R² − (ℓ/2)²)`. Zapas skrajni liczony jest przez
**inflację skrajni pojazdu** o `v` i ponowne sprawdzenie `profiles.fits_gauge` —
nigdy przez zmianę szerokości M7. Pilnuje tego test
`test_clearance_never_shrinks_the_train_to_make_it_fit`.

Wejścia:

| wielkość | wartość | status |
|---|---|---|
| długość składu | 94,0 m | **spec** (`data/vehicle/m7-spec.json`) |
| liczba członów | 6 | **spec** |
| szerokość pudła | 2,70 m | **spec** |
| cięciwa jednego członu | 15,667 m | pochodna równego podziału — `design_assumption` z T-220 |
| profile tunelu | `box_double` 9,40 × 5,90 m, `bore_single` R 3,05 m | `source_level: design` — **nie** pomiar STIB |

## 2. Promień nie jest daną — są widełki

Promień mierzony jest **na cięciwie długości pudła**, nie na trójce sąsiednich
wierzchołków: trójka daje promień szumu digitalizacji, a nie łuku, po którym faktycznie
stanie człon (test `test_clearance_radius_is_measured_on_the_car_body_chord`).

Nawet wtedy wynik zależy od tego, jak potraktować łamaną:

| wariant | jak mierzony | R min | chainage | P05 | strzałka |
|---|---|---|---|---|---|
| `pessimistic` | skomitowana łamana 15 m — ostre wierzchołki zaniżają promień | **50,87 m** | 2518,6 m | 78,82 m | 606,7 mm |
| `optimistic` | krzywa zagęszczona (Catmull-Rom 5 m) — wygładza wierzchołki | **85,94 m** | 2518,8 m | 137,50 m | 357,7 mm |

Prawdziwy tor leży gdzieś pomiędzy i **nie da się tego rozstrzygnąć z dostępnych źródeł** —
geometria STIB to linia trasy handlowej, nie oś toru z pomiaru. Werdykt zapada na wariancie
pesymistycznym: profil, który przechodzi dopiero po wygładzeniu osi, nie jest profilem,
na którym można polegać.

Najciaśniejszy łuk wypada na chainage ~2519 m, czyli między Comte de Flandre (2054,9 m)
a Sainte-Catherine (2721,0 m) — na zakręcie w stronę Pentagonu.

## 3. Wynik

| profil | statyczny zapas | zapas `pessimistic` | zapas `optimistic` | werdykt |
|---|---|---|---|---|
| `box_double` | 1,078 m | **+0,471 m** | +0,720 m | mieści się |
| `station` | 1,497 m | **+0,890 m** | +1,139 m | mieści się |
| `bore_single` | 0,495 m | **−0,112 m** | +0,137 m | **nie mieści się** |

**Znalezisko: projektowy profil `bore_single` nie ma zapasu na łuki tej ostrości.**

Pakiet A jest tunelem dwutorowym (`box_double`), więc nie blokuje to T-210. Ale
`bore_single` jest w `profiles.py` przewidziany dla tuneli drążonych jednotorowych,
a te w Brukseli występują — na łuku R = 51 m 94-metrowy skład przekroczyłby jego
obrys o 11 cm.

Zgodnie z regułą z #14 **nie zwężam pociągu ani nie zmieniam profilu w tym PR**.
Problem leży po stronie **placeholderowego profilu**, nie geometrii M7:

- `bore_single` ma promień 3,05 m i `source_level: design` — nie pochodzi z żadnego
  przekroju STIB;
- jego statyczny zapas 0,495 m jest ponad dwukrotnie mniejszy niż `box_double`;
- korekta wymaga albo źródła (R-005 / #17 — ground truth infrastruktury torowej),
  albo świadomej decyzji właściciela o zmianie wymiaru projektowego.

Test `test_clearance_committed_axis_fits_the_double_box_but_not_the_single_bore`
utrwala oba wyniki, żeby zmiana profilu lub osi nie przeszła po cichu.

## 4. Czego ten model NIE liczy

- **wychylenia zewnętrznego końców składu** — wymaga rozstawu czopów skrętu, którego
  nie ma w `data/vehicle/m7-spec.json`; T-220 świadomie nie wymyślił wózków (#14).
  Zwis końcowy działa w przeciwną stronę niż strzałka i na skrajnych członach może być
  większy od niej, więc **rzeczywisty zapas jest mniejszy niż tu policzony**;
- przechyłki, ugięcia zawieszenia, zużycia kół, tolerancji toru i tolerancji budowlanej tunelu;
- rozjazdów, odcinków przejściowych i krzywych przejściowych (klotoid);
- profilu pionowego — T-112 (#10) zablokowane.

Wynik jest więc **warunkiem koniecznym**, nie pełną skrajnią kinematyczną. Ujemny zapas
oznacza „na pewno się nie mieści"; dodatni oznacza „na tym poziomie modelu się mieści".

## 5. Co z tego wynika dla kolejnych zadań

- R-005 (#17) powinien dostarczyć albo rzeczywisty przekrój tunelu drążonego, albo
  potwierdzenie, że linia 1/5 go nie używa;
- T-211 (#18) — element peronu i jego odsunięcie od osi toru muszą uwzględniać strzałkę
  na łukach stacyjnych, inaczej peron na łuku wejdzie w skrajnię;
- pełna skrajnia kinematyczna wymaga rozstawu czopów skrętu M7, czyli danej, której
  dziś nie ma z żadnego dopuszczalnego źródła.
