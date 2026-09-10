# 6.D107 — parametr bez strażnika, bo jego pochodzenie było za dobre

**Zmierzone 10.09.2026 na:** `bd00787`, kontener tej sesji.
**Przyrząd:** `tools/physics/braking.py` (`params`, `o_statusie`, `PARAMETRY`),
`tools/tests/test_tool_refusals.py`, `data/vehicle/m7-spec.json` — wyłącznie do
odczytu.

---

## 1. Rozstrzygnięcie, o które prosi wpis

Pole „Wyjście" żąda pomiaru: czy `empty_mass_kg` ma status pozwalający przejść przez
`design()`. **Nie ma** — i powód jest odwrotny do spodziewanego:

```
empty_mass_kg: {'value': 170000.0, 'unit': 'kg', 'status': 'spec',
                'approximate': True, 'source_id': 'stib_m7_2020_07_13',
                'notes': 'STIB states approximately 170 tonnes; …'}
```

Status to **`spec`**, czyli wartość z oficjalnego źródła, z `source_id` w rejestrze.
Pozostałe czternaście ma `design_model` — założenie tego projektu. Strażnik `design()`
żądał dosłownie `design_model`, więc parametr o pochodzeniu **mocniejszym** przez niego
nie przechodził.

To wyjaśnia, czemu był czytany wprost: nie z przeoczenia, tylko dlatego, że kontrola
napisana pod jeden status nie miała jak przyjąć drugiego. **Ominięto kontrolę zamiast
dobrać właściwą** — a brak kontroli nie zostawia śladu w żadnym wypisie.

## 2. Co się zmieniło

Oczekiwany status jest **argumentem**, nie stałą wpisaną w warunek: `o_statusie(
container, key, oczekiwany)`. Wszystkie piętnaście parametrów idzie tą samą drogą,
każdy ze swoim wymaganym statusem, a tabela `PARAMETRY` jest jedynym miejscem, w
którym stoi „ile ich jest" i „który jakiego statusu wymaga".

| | ile |
|---|---:|
| parametrów w `params()` | **15** |
| wymaga `design_model` | **14** |
| wymaga `spec` | **1** |

Czternaście plus jeden daje piętnaście, i tej arytmetyki pilnuje osobny test — tego
wprost żąda pole „Skończone, gdy".

**Wynik `params()` jest identyczny co do wartości** przed zmianą i po niej;
porównany słownik po słowniku, nie obejrzany.

## 3. Dlaczego tabela, a nie piętnaście wywołań obok siebie

Piętnaście linii `design(ref, "…")` nie dawało się przejść pętlą, więc bramka
sprawdzająca „każdy z piętnastu ma kontrolę" musiałaby trzymać **drugą** listę tych
piętnastu — i rozjechać się z pierwszą przy szesnastym parametrze. Tabela jest jedna,
`params` buduje z niej wynik, a test po niej chodzi.

Dokłada to drugą, mocniejszą bramkę: **wymagany status musi zgadzać się z rejestrem**.
Bez niej tabela mogłaby żądać statusu słabszego niż faktyczny i kontrola
przepuściłaby wartość, której pochodzenie się pogorszyło — albo żądać innego i model
nie zbudowałby się wcale.

## 4. Kontrole negatywne — wykonane, nie opisane

Każda przez `cp` dwóch plików na bok i `md5sum -c` po przywróceniu, z `__pycache__`
czyszczonym przed każdym przebiegiem (procedura z 6.D102).

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | `aw0_kg` wraca do czytania bez kontroli | **5/6** — zgłoszony po nazwie |
| KN-2 | tabela żąda `design_model` tam, gdzie rejestr ma `spec` | **5/6** |
| KN-3 | parametr zniknął z tabeli (czternaście zamiast piętnastu) | **4/6**, dwa testy |
| KN-4 | kontrola przyjmuje dowolny status | **4/6**, w tym **wszystkie piętnaście** wymienionych z nazwy |

Po każdej: `md5sum -c` → `OK` na obu plikach.

KN-4 jest tu najostrzejsza: pętla po wszystkich piętnastu wypisuje wszystkie
piętnaście nazw, więc widać, że bramka mierzy komplet, a nie jeden przypadek. KN-1
wypisuje dokładnie jedną nazwę — tę, która była bez strażnika do dziś.

## 5. Czego świadomie nie zrobiłem

- **Nie zmieniałem wartości ani statusów w `data/`** — pole „Poza zakresem" mówi to
  wprost, a `CLAUDE.md` §4.6 czyni `data/` katalogiem tylko do odczytu. Rejestry
  syntetyczne w testach powstają w pamięci.
- **Nie zmieniałem znaczenia `spec` ani `design_model`.** Tabela mówi, którego
  statusu który parametr wymaga; co te statusy znaczą, rozstrzyga
  `docs/02-simulation.md` (i, dla wymiarów geometrii, `docs/21` — patrz 6.D105).
- **Nie tknąłem `approximate: True` przy masie pustej.** „STIB states approximately
  170 tonnes" to fakt o źródle, nie usterka.

## 6. Co zauważyłem przy okazji, ale nie tknąłem

- **`approximate: True` nie jest przez nic czytane.** Model hamowania bierze
  `value` i nie wie, że liczba jest przybliżona; żaden wypis tego nie mówi. To jest
  pytanie o to, jak niepewność wchodzi do modelu — czyli osobna pozycja, i decyzja
  właściciela, a nie skutek uboczny tej zmiany.
- **Docstring `test_tool_refusals.py` cytuje `braking.py:65` jako miejsce jednego
  z trzech dawnych `assert`ów.** Numer wiersza opisuje stan z 6.D94 i po tej zmianie
  wskazuje co innego; zdanie jest w czasie przeszłym i jako zapis pomiaru zostaje,
  ale numer wiersza w takim zapisie starzeje się cicho.
