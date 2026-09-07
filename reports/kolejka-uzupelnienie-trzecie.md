# Trzecie uzupełnienie kolejki 07.09.2026 — pięć pozycji z „Zauważone przy okazji"

**Zmierzone 07.09.2026 na commicie:** `627d184e1b84a6ddc2488c0c8a9d16f34adedbe6`
**Dotyczy:** `docs/TASKS.md`, `tools/tests/test_backlog.py`
**Po co:** kolejka zeszła do dwunastu, czyli równo do progu — a próg osiągnięty jest
progiem przekroczonym przy następnym domknięciu.

## 1. Dlaczego teraz

Po scaleniu 6.D35 (#385) zapas to **12 pozycji**, czyli dokładnie
`MINIMUM_READY_ITEMS`. Bramka `test_the_queue_holds_at_least_a_day_of_work` używa
`>=`, więc jest zielona — i zapali się przy **pierwszym** następnym domknięciu, na
czerwonym zestawie w cudzym pull requeście. `CLAUDE.md` §8 mówi wtedy jedno:
pierwszym zadaniem jest uzupełnienie kolejki.

```
przed tym commitem:  12 pozycji do wzięcia, 106 bloków
po tym commicie:     17 pozycji do wzięcia, 111 bloków
```

To trzecie uzupełnienie tego dnia (po `reports/kolejka-uzupelnienie-drugie.md`)
i **dwa z trzech były wywołane wykonaniem pracy, nie zaniedbaniem** — licznik zapasu
opada, gdy zadania są domykane.

## 2. Skąd pięć pozycji: z sekcji „Zauważone przy okazji" dzisiejszych raportów

Zadania wymyślonego na miejscu nie bierze się nigdy (`CLAUDE.md` §8). Wszystkie pięć
wyszło z **pomiarów wykonanych przy dzisiejszych zadaniach** — z rzeczy, które ktoś
zobaczył i świadomie nie tknął, bo nie były jego pozycją:

| pozycja | skąd | liczba |
|---|---|---|
| **6.B45** | znalazł agent 6.B41, nie tknął | docstring mówi **9 z 44**, zmierzone **10 z 63** |
| **6.B46** | `reports/czas-modulu-mutacyjnego.md` §10 nazwał to osobną pozycją | świeże `collect()` to **0,224 s** za komplet 63 celów |
| **6.D36** | `reports/sciezka-dziennika-z-odciskiem.md` §9 | **3** obcięcia `hexdigest()` w drzewie: 2 przez stałą, **1 przez literał** |
| **6.D37** | `reports/pusty-zbior-listy.md` §9 | `--only ""` daje **2346 mutacji zamiast 2** — **1173×** więcej pracy, bez słowa |
| **6.D38** | `reports/odcisk-w-naglowku-raportu.md` §8 | nagłówek `mutation-sweep.md` niesie commit, gałąź i datę w jednym wierszu |

## 3. Pomiary, na których stoją nowe pozycje

### 3.1 6.B45 — docstring i próg

```
celow: 63   nieosiagalnych: 10
   dziewięć modułów tools/blender/… + tools/visual/capture_blender.py
```

Docstring mówi „9 z 44 modułów". **Jakościowa połowa zdania jest pilnowana** pętlą
`assert "bpy" in reason` i pozostaje prawdziwa — dziesiąty moduł też importuje `bpy`.
Liczbowa stoi na progu `len(unreachable) < len(targets()) // 2`, czyli **10 < 31**,
więc przechodzi przy 9, przy 10 i przy 30.

**Dlatego pozycja nie każe wpisać 10 i 63**: przybicie dokładnej liczby zapaliłoby
bramkę przy każdym dodanym module z `bpy`, czyli przy pracy normalnej. Repozytorium
ma wzorzec — liczbę się **wyprowadza** (6.D26 z listy pomiarów, 6.A31 z pliku
projektu) — i pole „Wyjście" żąda pomiaru, który z dwojga wybrać.

### 3.2 6.D36 — jedno obcięcie przez literał

```
obcięć hexdigest RAZEM: 3
  przez STALA:   mutation_sweep.py:444, :943   [:ODCISK_ZNAKOW]   (16)
  przez LITERAL: mutation_sweep.py:990         [:12]
```

`test_dead_constants.py` (6.B29) pilnuje stałej, **której nikt nie czyta**. Nic nie
pilnuje odwrotności — literału, który powinien być stałą. Przy **trzech** wystąpieniach
w całym drzewie bramka może być droższa od problemu, i pole „Wyjście" każe to
rozstrzygnąć liczbą, nie przekonaniem.

### 3.3 6.D37 — puste zawężenie

```
mutacji bez zawezenia:     2346
mutacji dla lod_paths.py:     2
stosunek:                  1173×
```

Pusty napis jest fałszywy dla `if args.only`, więc nie wchodzi ani filtr, ani wypis
„dopasowało N plików", ani odmowa z 6.B39. Ta sama rodzina co 6.B39, **odwrócona**:
tam zbiór był pusty i przebieg wychodził zerem wyglądając na poprawny; tu zbiór jest
pełny, a przebieg wygląda na zawężony.

## 4. Weryfikacja

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  1931/1931 przeszło
  RAZEM 71.118 s, 1931 testów, 101 modułów
kod: 0
```

Liczniki odczytane z bramki, nie policzone ręcznie:

```
open:   17 ['5.6', '6.A19', '6.A21', '6.A33', '6.B26', '6.B43', '6.B44', '6.B45',
            '6.B46', '6.C4', '6.D24', '6.D32', '6.D33', '6.D34', '6.D36', '6.D37',
            '6.D38']
blocks: 111   zapadka: 111
nowe bez bloku: []
```

## 5. Trzy kontrole negatywne — WYKONANE

**KN-1 — zapadka zostawiona na 106 przy 111 blokach:**

```
FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: bloków z kompletem
sześciu pól jest 111, a zapadka stoi na 106 — podnieś ją do 111 w tym samym commicie
  25/26 przeszło
```

**KN-2 — blok 6.D37 wycięty przy zapadce 111:**

```
FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: bloków jest 110 przy
zapadce 111 — któryś zniknął albo stracił jedno z sześciu pól
  25/26 przeszło
```

**KN-3 — jedno pole zdjęte z bloku (`Zależy od` w 6.D37).** Ta kontrola mierzy co
innego niż dwie pierwsze: czy zapadka liczy bloki **kompletne**, a nie nagłówki.
Padają **dwa** testy i drugi z nich nazywa dokładnie brakujące pole:

```
FAIL test_every_detail_block_carries_all_six_fields: 6.D37 bez pól: Zależy od
FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: bloków jest 110 przy
zapadce 111
  24/26 przeszło
```

Plik przywrócony po każdej z trzech i sprawdzony przez `cmp`.

## 6. Czego ten commit świadomie nie zrobił

- **Nie wykonał żadnej z pięciu pozycji.** To uzupełnienie zapasu, nie praca z niego.
- **Nie poprawił dwóch liczb w docstringu 6.B45**, choć poprawka jest dwuznakowa:
  pole „Wyjście" tamtej pozycji żąda najpierw pomiaru, czy liczbę wpisać, czy
  wyprowadzić — a wpisanie jej teraz przesądziłoby to bez pomiaru.
- **Nie obniżył progu.** `MINIMUM_READY_ITEMS` zostaje na 12.
- **Nie przeliczył żadnego cudzego pomiaru.** Trzy z pięciu pozycji przewidują dla
  raportów **adnotację**, nie poprawkę.

## 7. Zauważone przy okazji, nietknięte

**Trzy z pięciu nowych pozycji mają w polu „Wyjście" wariant „i nic".** To nie jest
niezdecydowanie: dzisiejsze 6.A32 i 6.D35 skończyły się dokładnie tym wynikiem, oba
po pomiarze, i oba dlatego, że przyrząd okazał się gorszy od problemu. Pozycja, która
z góry przesądza, że bramka ma powstać, zamienia pomiar w formalność — a `CLAUDE.md`
§4.1 zabrania dorabiania liczby do wniosku.
