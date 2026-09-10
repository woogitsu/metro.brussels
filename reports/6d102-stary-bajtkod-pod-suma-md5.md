# 6.D102 — `md5sum -c` mówi o pliku, a wykonuje się bajtkod

**Zmierzone 10.09.2026 na:** `f0cd51c`, kontener tej sesji, CPython 3.11.
**Przyrząd:** laboratorium w katalogu tymczasowym (moduł + skrypt importujący),
rzeczywista bramka `tools/tests/test_reference_snapshot.py` na
`tools/physics/reference.py`, `tools/tests/test_bytecode_staleness.py` (nowy),
trzy pary przebiegów całego zestawu dla pomiaru kosztu.

---

## 1. Pułapka odtworzona, i działa w obie strony

CPython uznaje `.pyc` za ważny po parze **(mtime źródła w sekundach, rozmiar
w bajtach)**. Podmiana `248900.0` → `251389.0` ma tę samą długość, więc gdy trafi
w tę samą sekundę co poprzedni zapis, żadne z tych pól nie drgnie.

**Kierunek (a) — przywrócenie niewidoczne. To jest przypadek z 6.D86:**

```
--- mutacja, przebieg, przywrócenie w tej samej sekundzie ---
   baza=248900.0  mutacja=251389.0  po przywróceniu=251389.0
--- przyrząd mówi, że plik jest przywrócony ---
mod.py: OK
   treść pliku: F0_N = "248900.0"
```

**Kierunek (b) — mutacja niewidoczna, i ten jest groźniejszy:**

```
   baza=248900.0  mutacja=248900.0   -> kontrola negatywna wyszłaby ZIELONA
```

Kierunek (a) daje wynik czerwony, ale nie z tego powodu, co trzeba — widać, że coś
jest nie tak. Kierunek (b) daje wynik **zielony**, który czyta się jako „bramka tego
nie łapie", i nie zostawia żadnego śladu.

## 2. To samo na rzeczywistej bramce, nie tylko w laboratorium

`tools/physics/reference.py`, mutacja `F0_N` w tej samej sekundzie co przebieg bazowy:

```
PRÓBA 1 — bez procedury
   baza:     ('5/5 przeszło', 0)
   mutacja:  ('5/5 przeszło', 0)  <- MA być czerwona

PRÓBA 2 — z czyszczeniem __pycache__ przed mutacją
   baza:     ('5/5 przeszło', 0)
   mutacja:  ('1/5 przeszło', 1)  <- prawda

tools/physics/reference.py: OK
```

Suma MD5 dawała `OK` przez cały czas.

## 3. Rozstrzygnięcie: zmienna nie wystarcza — ale w czystym katalogu działa

Pole „Wyjście" żąda rozstrzygnięcia pomiarem. Zmierzone, przy `.pyc` **już leżącym**
z wcześniejszego zwykłego przebiegu i mutacji w tej samej sekundzie:

| procedura | baza | mutacja | wynik |
|---|---|---|---|
| bez niczego | 248900.0 | 248900.0 | **stary bajtkod** |
| `PYTHONDONTWRITEBYTECODE=1` na kontroli | 248900.0 | 248900.0 | **stary bajtkod** |
| `python3 -B` (to samo, inna droga) | 248900.0 | 248900.0 | **stary bajtkod** |
| czyszczenie `__pycache__` | 248900.0 | 251389.0 | prawda |

**Zmienna zabrania bajtkod PISAĆ, a pułapkę robi CZYTANIE tego, który już leży.**

**Skąd bierze się przekonanie, że zmienna wystarcza.** Ustawiona **od pierwszego**
przebiegu — czyli w pomiarze zrobionym w czystym katalogu — działa: `.pyc` nie powstaje
nigdy i mutacja jest widoczna. Nie opisuje to jednak życia, w którym zestaw chodził
godzinę wcześniej. Obie połowy są przybite osobnymi testami, bo pojedynczy test na
jedną z nich opisywałby co innego, niż mówi. **Moja pierwsza wersja bramki mierzyła
tylko tę korzystną połowę i przez to zaprzeczała pomiarowi** — złapał to jej własny
komunikat awarii, nie lektura.

## 4. Czy zestaw ma to robić sam: nie, i powód nie jest ten, który stał we wpisie

Pole „Poza zakresem" wyklucza „wyłączanie cache'a na stałe w CI, **gdzie zysk czasowy
jest realny**". Zysk zmierzony — trzy pary przebiegów całego zestawu:

| | 1 | 2 | 3 | średnia |
|---|---|---|---|---|
| zimny (`__pycache__` wyczyszczony) | 126,27 s | 125,65 s | 127,47 s | **126,46 s** |
| ciepły (bajtkod leży) | 127,17 s | 127,49 s | 125,25 s | **126,64 s** |

Różnica **0,18 s na 126 s**, przy rozrzucie między przebiegami rzędu 2 s — czyli
**zysku nie ma**. Powód jest strukturalny: moduły testowe i tak kompilują się ze
źródła przez `assertion_gate.load_instrumented`, więc z 77 plików `.pyc` powstałych
w jednym przebiegu tylko 10 pochodzi z `tools/tests/`.

**Zestaw mimo to nie czyści katalogu sam**, bo czyszczenie w każdym przebiegu BYŁOBY
wyłączeniem cache'u na stałe także w CI, a to pole „Poza zakresem" wyklucza wprost.
Przesłanka tego wykluczenia jest po tym pomiarze fałszywa; sama decyzja należy do
właściciela i tu jej nie podejmuję.

**W CI pułapki i tak nie ma:** `actions/checkout` robi `git clean -ffdx` (CLAUDE.md §9),
`__pycache__` stoi w `.gitignore` (wiersz 3), więc każdy przebieg CI zaczyna zimno.
Żaden workflow nie cache'uje bajtkodu — siedem wywołań `actions/cache` w drzewie dotyczy
Blendera, Godota i .NET. **To jest zagrożenie lokalne, dla agenta i dla właściciela.**

## 5. Gdzie stoi procedura

`CLAUDE.md` §5 dostał osobny podrozdział „Kontrola negatywna na module Pythona —
czyść bajtkod" z poleceniem i z obiema połowami rozstrzygnięcia;
`docs/06-worked-example.md` — pełny opis z liczbami, jako czwarty wzorcowy przypadek
obok trzech istniejących. Pole „Skończone, gdy" żąda dokumentu, nie raportu, i tego
pilnują dwa testy nowej bramki.

**Bramka odtwarza pułapkę, a nie sprawdza napisu.** Gdyby CPython przeszedł na bajtkod
z sumą źródła (PEP 552, `CHECKED_HASH`) domyślnie, pierwszy test zapali się na zdrowej
maszynie — i to będzie sygnał, że zdanie w obu dokumentach przestało być prawdą, a nie
że bramka jest zepsuta. Komunikat awarii mówi to wprost.

## 6. Kontrole negatywne — wykonane, nie opisane

Każda przez `cp` kopii na bok i `md5sum -c` po przywróceniu, na trzech plikach naraz;
**`__pycache__` czyszczony przed każdym przebiegiem** — czyli tą samą procedurą, którą
ta pozycja wprowadza.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | polecenie czyszczące znika z `CLAUDE.md` | **5/6** |
| KN-2 | z dokumentu znika nazwa zmiennej, która nie wystarcza | **5/6** |
| KN-3 | sekwencja czyści bajtkod tam, gdzie miała go zostawić | **4/6**, dwa testy |
| KN-4 | zmienna ustawiona wszędzie zamiast tylko na kontroli | **5/6** |
| KN-5 | laboratorium nie startuje (przyrząd ma paść, nie milczeć) | **2/6**, cztery testy |
| KN-6 | napisy mutacji **różnej długości** | **4/6**, dwa testy |

Po każdej: `md5sum -c` → `OK` na wszystkich trzech plikach.

KN-6 jest tu najważniejsza: dowodzi, że przesłanka „ta sama długość" jest **nośna**.
Z napisami różnej długości rozmiar pliku się zmienia, para `(mtime, rozmiar)` drga
i pułapka znika — czyli bramka mierzy ten mechanizm, a nie jakiś inny.

## 7. Czego świadomie nie zrobiłem

- **Nie kazałem zestawowi czyścić `__pycache__`**, mimo że pomiar zdejmuje jedyny
  argument przeciw — pole „Poza zakresem" wyklucza wyłączanie cache'u na stałe w CI,
  a to jest dokładnie to.
- **Nie zmieniałem sposobu liczenia testów** (to samo pole).
- **Nie ruszałem `reports/6d86-przyspieszenie-jest-wynikiem.md`** — tamten raport
  opisuje pomiar z tamtego dnia i jest poprawny.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

- **`mutation_sweep.py` mutuje pliki i uruchamia zestaw w pętli**, czyli robi dokładnie
  tę sekwencję, w której pułapka żyje. Nie sprawdziłem, czy sweep czyści bajtkod między
  próbami — jeśli nie, część „przeżytych" mutacji może być mutacjami niewidocznymi.
  To jest pytanie o wyrocznię mutacyjną, a nie o procedurę kontroli negatywnej, i na
  osobną pozycję.
- **Pułapka nie ogranicza się do kontroli negatywnych.** Zwykła edycja modułu narzędziowego
  i natychmiastowy przebieg zestawu mają ten sam kształt: ta sama sekunda, ta sama
  długość — i ten sam stary bajtkod. Dokumenty mówią o kontroli negatywnej, bo tam
  wyszło; zakres zjawiska jest szerszy.

## 9. Uzupełnienie kolejki w tym samym commicie — wymuszone arytmetyką

Domknięcie 6.D102 zbija kolejkę z dwunastu pozycji na **jedenaście**, czyli poniżej
progu `MINIMUM_READY_ITEMS`. `CLAUDE.md` §8 mówi wprost, że wtedy **pierwszym zadaniem
jest jej uzupełnienie**, a `tools/tests/test_backlog.py` tego pilnuje — commit z samym
domknięciem zostawiłby drzewo czerwone:

```
FAIL test_the_queue_holds_at_least_a_day_of_work: kolejka ma 11 pozycji przy progu 12
FAIL test_the_documented_shortfall_is_written_down_while_it_lasts: zapas 11 przy progu 12
```

Dopisane sześć pozycji, **6.D113 … 6.D118**, kolejka z 11 na **17**,
`MINIMUM_DETAIL_BLOCKS`, podniesiona ze stu osiemdziesięciu pięciu, stoi dziś na 191. Wszystkie sześć wyszło z pomiarów zrobionych przy
6.D97, 6.D99, 6.D100, 6.D101 i 6.D102 i zapisanych tam jako „zauważone i nietknięte" —
żadnej nie wymyśliłem pod pustą kolejkę, czego `CLAUDE.md` §8 zabrania wprost.

Jedna z nich, **6.D114**, wyszła nie z lektury: wołając `test_all.py` z czterema
modułami naraz dostałem wynik jednego i wziąłem go za wynik czterech. Zestaw czyta
`sys.argv[1]` i o reszcie milczy.

**6.D113 jest bezpośrednim następstwem tej pozycji** i dlatego stoi w kolejce, a nie
w zakresie: `mutation_sweep.py` robi tę samą sekwencję maszynowo i tysiące razy, więc
jeśli nie czyści bajtkodu, „mutacja PRZEŻYŁA" znaczy czasem „mutacji nie wykonano".
Liczby dziś nie znam i pozycja ma ją policzyć, a nie odziedziczyć po tym raporcie.
