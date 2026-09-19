# 6.D287 · Ten sam czytnik, cały katalog `docs/` — i przesłanka, która się nie potwierdziła

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `b14f5fe`

## 1. O co pytała pozycja

6.D169 zmierzyło jeden plik, bo tylko o nim mówiła tamta pozycja. Blok 6.D287
stawia tezę: kryterium „zdanie o konkretnej maszynie ma nieść datę w swoim akapicie"
nie jest własnością `docs/23-environment.md`, tylko **własnością dokumentacji** —
a `docs/` ma kilkanaście innych plików, w tym `docs/06-worked-example.md`
i `docs/PLAYABILITY.md`, „pisane tą samą ręką i w tym samym czasie teraźniejszym".

Pozycja żądała tabeli po całym `docs/`, liczby zbiorczej i osobnej dla
`docs/23-environment.md`, żeby było widać, ile z tego znał już 6.D169.

## 2. Czytnik POŻYCZONY, nie napisany drugi raz

Brief zwiadowczy mówił, że czytnika z 6.D169 w drzewie nie ma i trzeba go odtworzyć.
To przestało być prawdą **wczoraj wieczorem**: 6.D285 postawiło
`tools/tests/test_machine_paragraphs.py`, którego `akapity(sciezka)`
i `akapity_o_maszynie(sciezka)` przyjmują ścieżkę **argumentem** — napisałem je
z tą myślą, bo 6.D281 zmierzyło, co się dzieje, gdy czytnik bierze korpus ze stałej
modułowej. Pomiar tej pozycji stoi więc na tamtym czytniku, a nie na jego kopii.

Wzorzec wąski — dokładnie ten z pola „Weryfikacja" 6.D169 — dołożony obok, żeby
dało się zmierzyć OBOMA i pokazać różnicę, zamiast wybierać jeden.

## 3. Wynik

| plik | sitem szerokim (6.D285) | bez daty | wzorcem wąskim (6.D169) | bez daty |
|---|---|---|---|---|
| `docs/23-environment.md` | dziewięć | dwa | osiem | jeden |
| `docs/TASKS.md` | sześć | dwa | sześć | dwa |
| pozostałe dwadzieścia cztery pliki | zero | zero | zero | zero |
| **razem** | **piętnaście** | **cztery** | **czternaście** | **trzy** |

## 4. Przesłanka pozycji się NIE POTWIERDZIŁA i to jest główny wynik

Blok twierdzi, że zjawisko jest własnością dokumentacji rozlaną po `docs/`.
Zmierzone: siedzi w **dwóch plikach z dwudziestu sześciu**. Co więcej, **oba pliki
wymienione w bloku z nazwy** — `docs/06-worked-example.md` i `docs/PLAYABILITY.md` —
mają **zero** akapitów mówiących o maszynie, którymkolwiek z dwóch sit.

Teza „pisane tą samą ręką i w tym samym czasie teraźniejszym" jest prawdziwa jako
opis stylu, ale nie przenosi się na to, o czym te pliki mówią: o maszynie mówi
dokument o środowisku i kolejka zadań, a nie dokumentacja projektowa.

## 5. Kontrola przyrządu zdana co do cyfry

Pole „Weryfikacja" żądało, żeby czytnik puszczony po samym `docs/23-environment.md`
odtworzył osiem zdań i jedno bez daty. Wąski wzorzec 6.D169 daje dokładnie to.

To rozstrzyga napięcie, które wpisałem do przewidywań **przed** pomiarem: 6.D285
zmierzyło na tym samym pliku dziewięć i dwa. Obie pary są prawdziwe i **nie są ze
sobą sprzeczne** — różnica jest własnością wzorca, opisaną w module bramki. Osiem
to liczba wzorca 6.D169; dziewięć to liczba wzorca szerszego o formę „u mnie".

## 6. Jednostka „akapit" załamuje się na `docs/TASKS.md`

Wiersze tabeli kolejki nie mają między sobą pustych wierszy, więc **cały blok tabeli
jest jednym akapitem**: najdłuższy liczy trzysta trzydzieści trzy wiersze i niesie
sześć różnych form naraz. Liczba dla `TASKS.md` nie jest więc porównywalna z liczbą
dla `23-environment.md` i nie należy ich sumować bez tego zastrzeżenia — sumę podaję
wyżej wyłącznie dlatego, że żądało jej pole „Wyjście".

Rozstrzygnięcie podjąłem **przed** policzeniem i tak je zapisuję: wiersz tabeli
zostaje częścią akapitu, bo dzielenie go osobno wymagałoby czytnika Markdowna,
którego ta pozycja nie zamawia, a wynik i tak trzeba opatrzyć zastrzeżeniem.

## 7. Przewidywania wobec pomiaru

| co | przewidziane | zmierzone |
|---|---|---|
| plików `docs/*.md` | dwadzieścia sześć | **dwadzieścia sześć** |
| akapitów o maszynie w całym `docs/` | dwadzieścia dwa | **piętnaście** |
| z tego bez daty | dziewięć | **cztery** |
| `23-environment.md` wąskim wzorcem | osiem i jeden | **osiem i jeden** |
| inny plik ma zdanie bez daty | tak, podejrzewałem `06-worked-example.md` i `PLAYABILITY.md` | **tak, ale to `TASKS.md`; oba podejrzane mają zero** |
| `TASKS.md` zdominuje populację | tak | **nie, sześć wobec dziewięciu** |

Trzy trafione, trzy nietrafione. Nietrafione konsekwentnie w jedną stronę:
spodziewałem się zjawiska szerszego, niż jest.

## 8. Kontrola negatywna

Na **kompletnej kopii drzewa** z `.git`; do `docs/06-worked-example.md` — pliku,
który dziś ma zero — dopisany akapit „Na tej maszynie X działa" bez daty.
Przewidywanie spisane przed przebiegiem: kolumna tego pliku z zera na jeden, suma
szeroka o jeden w górę, `docs/23-environment.md` nietknięte.

```
plik                                       szer   sz.bez     wask    w.bez
06-worked-example.md                          1        1        1        1
23-environment.md                             9        2        8        1
TASKS.md                                      6        2        6        2
RAZEM                                        16        5       15        4
```

Zgodne co do każdej cyfry. Wąski wzorzec 6.D169 też go łapie, bo akapit używa formy
„na tej maszynie" — przewidziane i potwierdzone. Liczby dla `docs/23-environment.md`
nie drgnęły, więc kontrola mierzy dopisanie, a nie przebieg czytnika.

Drzewo robocze w tym czasie: te same liczby, co w §3.

## 9. Czego świadomie nie zrobiłem

- **Nie dopisałem ani jednej daty.** Pole „Dlaczego bez decyzji" mówi wprost, że
  werdykt „dopisać datę" nie jest automatyczny — 6.D169 pokazało, że zdanie
  o maszynie DOWOLNEJ daty dostać nie powinno.
- **Nie ruszyłem pola „Weryfikacja" żadnej pozycji**, w tym tej, której liczba
  „osiem" mogłaby wyglądać na nieaktualną po 6.D285. Nie jest nieaktualna: opisuje
  wzorzec, którym ją zmierzono.
- **Nie postawiłem bramki.** Pole „Wyjście" żąda raportu z tabelą, a nie sita
  w drzewie; tak samo 6.D286 i 6.D282.
- **Nie rozbiłem `docs/TASKS.md` na wiersze tabeli** — patrz §6.

## 10. Co zauważyłem, a czego nie tknąłem

- Dwa akapity `TASKS.md` bez daty mówią o konkretnej maszynie w blokach pozycji
  (w. 5974 i 6022): „`libEGL.so.1` na tej maszynie było" oraz „lista musi wyjść
  z pomiaru na tej maszynie". Oba są opisami zadań, nie twierdzeniami dokumentacji,
  i żaden nie ma daty w swoim akapicie — data stoi gdzie indziej w bloku.
  Czy blok pozycji ma podlegać temu samemu kryterium co akapit dokumentu, jest
  rozstrzygnięciem, którego ta pozycja nie zamawia.
- Bramka z 6.D285 pilnuje wyłącznie `docs/23-environment.md`. Po tym pomiarze
  wiadomo, że drugim plikiem z populacją jest `docs/TASKS.md` — i że nikt go nie
  pilnuje.

## 11. Weryfikacja

```
$ python3 tools/tests/test_all.py
  2662/2662 przeszło
  RAZEM 351.662 s, 2662 testów, 139 modułów
EXIT=0
```

Liczba testów nie urosła, bo bramki nie przybyło — czytnik został pożyczony
z modułu, który postawiło 6.D285, a pomiar stoi w tym raporcie.
