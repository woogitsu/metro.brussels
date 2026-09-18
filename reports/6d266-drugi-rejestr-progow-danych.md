# 6.D266 — drugi rejestr, a „nie pilnuje ich nic" było prawdą o KLASYFIKATORZE, nie o drzewie

**Data:** 18.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `61b9784`

## 1. Rozstrzygnięcie właściciela i to, czego nie zawierało

**Wariant (b): drugi rejestr dla progów danych, z własnymi klasami.** `ZAPADKA` zostaje
przy znaczeniu „próg bramki". Pozycja przepasmowana z D na M.

**Decyzja nazwała wariant, ale nie nazwała klas, i to jest zapisane, a nie przemilczane.**
Podział tematyczny (geometria / wiarygodność / artefakt) byłby oceną estetyczną, a
`CLAUDE.md` §8 każe się wtedy zatrzymać. Klasy są więc wyprowadzone z czegoś
**mierzalnego i czytelnego z AST**: jaką **drogą** próg dociera do kodu produkcyjnego.
Próg bywa używany kilkoma drogami naraz, więc klasą jest **zbiór** dróg — wybieranie
„ważniejszej" byłoby tym samym gustem tylnymi drzwiami.

## 2. Pięć dróg, zmierzonych, nie wymyślonych

| droga | co znaczy | które progi |
|---|---|---|
| `odrzuca` | porównanie, którego gałąź podnosi wyjątek | `MAX_MARKS` |
| `zglasza` | porównanie zasilające listę usterek, bez wyjątku | `MAX_GAP_M`, `MAX_TWIST_DEG`, `MAX_PLAUSIBLE_VERTICES`, `MIN_PLAUSIBLE_VERTICES` |
| `orzeka` | porównanie w wyrażeniu zwracanym, decyzja u wołającego | `MIN_AXIS_POINTS`, `MIN_CENTERLINE_POINTS` |
| `domyslny` | dociera **wyłącznie** jako wartość domyślna argumentu | `MAX_ECEF_RESIDUAL_M`, `MINIMUM_ARTEFACT_BYTES` |
| `odciecie` | granica wycinka — nie odrzuca, tylko **ucina** | `MAX_SEED_WAYS` |
| `arytmetyka` | tylko liczenie albo treść komunikatu | `MAX_AXIS_LENGTH_M`, `MIN_SENSIBLE_STEP_M` |

`MAX_MARKS` ma dwie drogi (`odrzuca` i `arytmetyka`), bo jest **pochodną**
`MAX_AXIS_LENGTH_M` przez `MIN_SENSIBLE_STEP_M`. Jego wartości nie przybijam —
rusza się razem ze składnikami i to jest w rejestrze zapisane.

**Dwie drogi są mocniejsze niż nazwa progu obiecuje:** `domyslny` znaczy, że wołający,
który poda własną wartość, omija próg po cichu; `odciecie` znaczy, że dane ponad próg
**znikają bez śladu**, zamiast zostać odrzucone. Nazwa `MAX_` obiecuje granicę; te
dwie drogi jej nie dotrzymują.

## 3. Pole „Weryfikacja" tej pozycji twierdzi nieprawdę — zmierzone

Pole mówi: „ruszenie któregokolwiek z dwunastu progów w zakazaną stronę ma zapalić
bramkę — **dziś nie zapala żadnej**".

Zmierzone na drzewie **sprzed** tej pozycji (kompletna kopia **razem z `.git`**),
każdy próg ruszony osobno w stronę luźniejszą:

```
PRZED ta pozycja zapala sie na 9 z 11 progow; NIE zapala na 2
  zapala:     MAX_AXIS_LENGTH_M, MAX_ECEF_RESIDUAL_M, MAX_GAP_M, MAX_PLAUSIBLE_VERTICES,
              MAX_TWIST_DEG, MIN_AXIS_POINTS, MIN_CENTERLINE_POINTS,
              MIN_PLAUSIBLE_VERTICES, MIN_SENSIBLE_STEP_M
  nie zapala: MAX_SEED_WAYS, MINIMUM_ARTEFACT_BYTES
```

Zdanie „nie pilnuje ich NIC" z 6.D262 było prawdą o **klasyfikatorze zapadek** — te
nazwy naprawdę są dla niego niewidzialne, bo docierają przez `moduł.NAZWA`. Nie było
prawdą o **drzewie**: dziewięć z jedenastu jest przybitych zwykłymi testami
(`test_thresholds_have_the_values_the_gate_was_designed_around`,
`test_minimum_centerline_points_is_pinned` i dalej). Brakowało im **rejestru i klasy**,
a nie strażnika.

**Dwa progi naprawdę niepilnowane to dokładnie te dwa, które klasyfikator dróg wskazał
jako najsłabsze** — `MAX_SEED_WAYS` (`odciecie`) i `MINIMUM_ARTEFACT_BYTES`
(`domyslny`). Dwa niezależne pomiary — droga do produkcji i pokrycie strażnikiem —
wskazały ten sam zbiór. Tego nie planowałem i nie jest to konstrukcja: klasy powstały
z AST, a pokrycie z przebiegów mutacyjnych.

## 4. Kontrola negatywna — jedenaście przebiegów, nie jeden

Każdy z jedenastu przybitych progów ruszony **osobno** w stronę luźniejszą, na
kompletnej kopii drzewa (216 plików `.py`, 401 raportów), `__pycache__` czyszczony
przed każdym przebiegiem:

```
MAX_AXIS_LENGTH_M        40000.0 -> 80000.0     CZERWIEN
MAX_ECEF_RESIDUAL_M      1.0     -> 2.0         CZERWIEN
MAX_GAP_M                0.001   -> 0.002       CZERWIEN
MAX_PLAUSIBLE_VERTICES   500000  -> 1000000     CZERWIEN
MAX_SEED_WAYS            8       -> 16          CZERWIEN
MAX_TWIST_DEG            5.0     -> 10.0        CZERWIEN
MINIMUM_ARTEFACT_BYTES   1024    -> 1023        CZERWIEN
MIN_AXIS_POINTS          2       -> 1           CZERWIEN
MIN_CENTERLINE_POINTS    2       -> 1           CZERWIEN
MIN_PLAUSIBLE_VERTICES   1000    -> 999         CZERWIEN
MIN_SENSIBLE_STEP_M      1.0     -> 0.5         CZERWIEN

zapalilo sie na 11 z 11 progow
```

Wartość dodana tej pozycji to więc **dwa progi**, których nie pilnowało nic, plus
**jedno miejsce**, w którym stoją wszystkie dwanaście razem z klasą — a nie
jedenaście nowych strażników.

## 5. Pierwsza kontrola przeciwna była NIEWAŻNA i zostaje zapisana

Pierwszą kontrolę „przed pozycją" zrobiłem na kopii **bez `.git`**. Dała **55**
czerwieni, z których żadna nie miała związku z mutacją: `git ls-files` zwracał kod 128,
brakowało `global.json`, `README` i połowy plików, których testy szukają. Kopia
niekompletna czyta się dokładnie jak oczekiwana czerwień — to jest pułapka, którą
projekt złapał już cztery razy, i złapała mnie piąty.

**Wyszła z niej mimo to rzecz prawdziwa**, i dlatego ją tu zapisuję zamiast wyrzucić:
w tym szumie stała jedna czerwień o właściwej treści —
`test_thresholds_have_the_values_the_gate_was_designed_around: 0.002` — i to ona
kazała mi sprawdzić, czy „nie zapala żadnej" jest w ogóle prawdą. Nie było.

## 6. Kontrola przyrządu

Czytnik dróg sprawdzony na **wejściu syntetycznym**, w którym te same pięć dróg stoi
obok siebie: porównanie z `raise`, wartość domyślna argumentu, porównanie zasilające
listę, granica wycinka i samo mnożenie. Bez tego sito mogłoby zwracać jedną klasę dla
wszystkiego i **zgadzać się z rejestrem, w którym ta klasa stoi** — czyli być zgodne
samo ze sobą i ślepe (6.D276).

Drugi rejestr porównywany jest z `POZA_ZASIEGIEM_KLASYFIKATORA` **w obie strony**
i z `ZAPADKI` na przecięcie: nazwa w obu rejestrach naraz znaczyłaby, że jedno z dwóch
pojęć przestało być sobą.

## 7. Czytnik poprawił mnie na dwóch progach

Wpisałem do rejestru `orzeka` dla `MAX_PLAUSIBLE_VERTICES` i `MIN_PLAUSIBLE_VERTICES`;
czytnik powiedział `zglasza`. Sprawdziłem w źródle: `m7_report.py` ma
`if not MIN < ... < MAX: problems.append(...)`, czyli **gałąź zasilającą listę**.
Czytnik miał rację, wpis był mój i błędny — poprawiłem rejestr do pomiaru,
a nie pomiar do rejestru.

## 8. Czego ta pozycja nie ruszała

Rejestru `ZAPADKI` nie rozszerzyłem — to wariant (a), odrzucony. Nie zmieniłem
**ani jednej** z dwunastu wartości progu. `POZA_ZASIEGIEM_KLASYFIKATORA` zostaje
nietknięte i jest odtąd porównywane z nowym rejestrem w obie strony.

## 9. Co zauważyłem przy okazji, a czego nie tknąłem

1. **`MAX_SEED_WAYS` nie odrzuca nadmiaru, tylko go ucina** — `ways[:MAX_SEED_WAYS]`.
   Import OSM z większą liczbą dróg zasiewu dostanie po cichu obcięty wynik zamiast
   błędu. Czy to jest zamierzone, czy przeoczone, z kodu nie widać: nie ma tam ani
   komentarza, ani wypisu. To jest pytanie do właściciela o dane, nie o czytnik,
   więc nie rozstrzygam go tutaj.
2. **`MAX_ECEF_RESIDUAL_M` i `MINIMUM_ARTEFACT_BYTES` docierają do porównania wyłącznie
   jako wartość domyślna.** Wołający z własną wartością omija próg, a rejestr o tym
   mówi dopiero od tej pozycji. Ilu jest takich wołających, nie policzyłem.
