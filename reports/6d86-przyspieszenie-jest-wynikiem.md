# Deklarowane maksimum przyspieszenia nie zgadzało się z modelem (6.D86)

**Zmierzone 09.09.2026, odtworzone 10.09.2026 na:** `71d8085`, kontener tej sesji.
**Przyrząd:** `tools/physics/reference.py` (ten sam model, którym liczy gra),
`python3 tools/tests/test_all.py`, cztery kontrole negatywne z `md5sum -c`
po każdym przywróceniu.

---

## 1. Rachunek, odtworzony co do szóstej cyfry

```
a(0) = (F0 − Davis(0)) / (m · 1,08)

AW0   (248 900 − 2 502) N / (170 000 · 1,08) kg  =  1,342044 m/s²
AW2   (248 900 − 3 266) N / (221 940 · 1,08) kg  =  1,024782 m/s²
```

Tabela w `docs/02-simulation.md` deklarowała **1,10 m/s²** ze statusem `design_model`.
**Nie jest to żadna z dwóch wartości modelu** — leży między nimi.

**Sufit przyczepnościowy nie wiąże**, i to też jest częścią tezy:
`μ·m·(4/6)·g` daje **277,9 kN** (AW0) i **362,7 kN** (AW2) wobec `F0 = 248,9 kN`,
więc o przyspieszeniu rozstrzyga siła rozruchowa, a nie tarcie.

## 2. Dlaczego to pozycja o dokumencie, a nie o fizyce

Liczba 1,10 **nie występuje w kodzie ani w danych pojazdu**, żaden test jej nie czytał,
a w modelu nie ma obcięcia, które by ją egzekwowało — sprawdzone przejściem po
`tools/physics/`, `src/Sim/` i `tools/tests/`.

Ryzyko jest **przyszłe**: ktoś weźmie tablicę referencyjną za kontrakt i dopisze sufit,
którego dziś nie ma — a wtedy **zmieni fizykę, sądząc, że poprawia opis**. Dlatego
poprawka idzie w wiersz tabeli, a nie w `TrainController`.

## 3. Poprawka

Wiersz mówi teraz wielkość **wynikową** dla obu obciążeń i nazywa ją pochodną, nie
sufitem; obok stoi wyprowadzenie z liczbami i zdanie o tym, że obcięcia w kodzie nie ma
i ta pozycja go nie wprowadza. Wartość projektowa jest w `data/vehicle/m7-spec.json`
wpisana wprost jako nieznana (`unknown_parameters`: „source-backed maximum
acceleration"), więc jej wybór jest **decyzją właściciela**, a nie skutkiem ubocznym
poprawki w dokumencie — tak stoi w polu „Poza zakresem".

## 4. Bramka odróżnia zmianę modelu od zmiany opisu — i to jest POKAZANE

Pole „Skończone, gdy" żąda tego wprost. Są więc dwa testy, nie jeden:

- **`test_the_start_acceleration_in_the_table_is_the_one_the_model_produces`** liczy
  przyspieszenie **przez `reference.traction_N` i `reference.davis_N`**, a nie przez
  wzór przepisany do testu, i porównuje z wierszem tabeli;
- **`test_the_gate_tells_a_changed_model_apart_from_a_changed_description`** przybija
  stronę **modelu** do liczb zmierzonych dziś, więc zmiana `F0_N`, mas albo
  współczynników Davisa zapala właśnie jego — z komunikatem o modelu.

Że to nie są dwie kopie jednego testu, widać w kontrolach: zmiana **dokumentu** zapala
tylko pierwszy, zmiana **modelu** zapala oba, a drugi mówi wprost
„MODEL się zmienił … to inna fizyka".

## 5. Cztery kontrole negatywne, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | przywrócony wiersz `1,10 m/s² \| design_model` | **czerwona** 4/5 — „wiersz zniknął albo zmienił kształt" |
| KN-2 | `F0_N` większe o 1 % (zmiana MODELU) | **czerwona** 1/5 — w tym test o modelu i dwa istniejące o parytecie C# |
| KN-3 | wiersz zachowany, liczba 1,300 zamiast 1,342 | **czerwona** 4/5 — „tabela podaje 1.300, a model liczy 1.342044" |
| KN-4 | wiersz podaje tylko AW0 | **czerwona** 4/5 — „tabela podaje dla ['AW0'], a model liczy dla obu" |

Trzy różne komunikaty dla trzech różnych sposobów zepsucia dokumentu, i czwarty —
o modelu — dla zepsucia modelu.

## 6. Kontrole KN-3 i KN-4 trzeba było powtórzyć, i powód jest wart zapisania

Za pierwszym razem obie zgłosiły `F0_N: 251389.0`, czyli wartość z **poprzedniej**
mutacji, mimo że `md5sum -c` na źródle dawał `OK`. Przyczyną był **nieświeży
`__pycache__`**: przywrócenie pliku przez `cp` nastąpiło w tej samej sekundzie co
mutacja, a podmieniany napis miał **dokładnie tę samą długość** (`248900.0` →
`251389.0`), więc para `(mtime w sekundach, rozmiar)` — po której CPython sprawdza
ważność bajtkodu — nie zmieniła się i interpreter wczytał skompilowaną **mutację**.

Kontrola sumą MD5 na źródle nie umie tego wykryć: ona mówi o pliku `.py`, a import
poszedł z `.pyc`. Po `find . -name __pycache__ -exec rm -rf` obie kontrole dały wynik
prawidłowy: 4/5 z komunikatem o dokumencie, bez śladu zmiany modelu.

**Jest to pułapka ogólna, nie incydent tej pozycji**: każda kontrola negatywna na
module Pythona, która podmienia napis o tej samej długości i przywraca go w tej samej
sekundzie, może przebiegać na starym bajtkodzie — i wyglądać jak wynik.

## 7. Czego NIE zrobiłem

**Nie dopisałem obcięcia w kodzie** — pole „Wyjście" mówi „żadnego obcięcia" wprost,
a wartość projektowa jest decyzją właściciela (pole „Poza zakresem").
**Nie tknąłem wiersza o hamowaniu**, choć też podaje 1,10 m/s²: to jest `b_service`,
inna wielkość z innego miejsca modelu, i jest w kodzie egzekwowana.
**Nie ruszałem `data/vehicle/m7-spec.json`** ani odczytem poza sprawdzeniem
`unknown_parameters`.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py test_reference_snapshot.py
  -> 5/5 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 99,990 s, 2146 testów, 113 modułów, kod 0
```

Zestaw urósł z **2144** do **2146**: dwa nowe testy.
