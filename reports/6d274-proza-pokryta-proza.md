# 6.D274 — trzy czwarte „pokrycia" nie ma z kodem nic wspólnego

**Data:** 18.09.2026 · **Gałąź:** `claude/6d274-proza-pokryta-proza` · **Baza:** `7822a10`

## 1. Trzy liczby z pola „Wyjście"

Z **54** liczb klasy `zbieg` (pokrytych zbiegiem cyfr, czyli bez przypisania stałej):

| klasa wierszy pokrywających | ile |
|---|---|
| **wyłącznie proza** — w oknie ani jednego wiersza kodu | **41** |
| wyłącznie kod | **11** |
| mieszane | **2** |
| **par wzajemnych** (A pokrywa B i B pokrywa A) | **9** |

6.D264 nazwało tę klasę „zbiegiem cyfr" i mierzyło ją względem **kodu**. Okno czyta
jednak WIERSZE PLIKU, nie odróżniając kodu od komentarza — więc w 41 przypadkach
na 54 wiersz pokrywający jest po prostu **innym zdaniem prozy** o tej samej liczbie.

## 2. Dziewięć par, które certyfikują się nawzajem

| para | |
|---|---|
| `test_dead_constants_csharp.py:66` **396** | ↔ `:83` **396** |
| `test_dead_constants_csharp.py:68` **89** | ↔ `:83` **307** |
| `test_dead_constants_csharp.py:68` **89** | ↔ `:83` **89** |
| `test_dead_constants_csharp.py:68` **307** | ↔ `:83` **307** |
| `test_dead_constants_csharp.py:68` **307** | ↔ `:83` **89** |
| `test_dead_constants_csharp.py:72` **66** | ↔ `:75` **66** |
| `test_dead_constants_csharp.py:84` **45** | ↔ `:91` **45** |
| `test_report_claims.py:1937` **35** | ↔ `:1949` **35** |
| `test_suite_runtime_budget.py:386` **0,992** | ↔ `:403` **0,992** |

Siedem par stoi w `test_dead_constants_csharp.py`, gdzie zjawisko zobaczyłem przy
6.D271 — ale **dwie stoją gdzie indziej**, więc nie jest to własność jednego pliku.
Dlatego bramka pilnuje rozkładu par PO PLIKACH, a nie samej sumy: 6.D267 zmierzyło,
że suma przesunięcia między członami nie widzi.

## 3. Klasyfikacja po PEŁNYM zbiorze, i to jest sprawdzone, a nie założone

Pierwsze podejście czytało pole `pokrywajace` z `pozycje_pokrycia`, które trzyma
tylko **dwa pierwsze** wiersze (`pokrywajace[:2]`) — na nim „wyłącznie proza"
znaczyłoby „obie zapamiętane są prozą", a trzeci wiersz w oknie mógłby być kodem.
Przeliczone od nowa po całym zbiorze daje **te same** 41 / 11 / 2. Różnicy nie ma,
ale teraz jest to zmierzone.

Klasa liczy się **w tym samym przebiegu**, co pokrycie — w pętli, która i tak
zbiera wiersze pokrywające. Drugi skan tych samych okien kosztowałby tyle, co cały
czytnik, a 6.D272 zmierzyło, ile taki drugi skan potrafi kosztować: **22 sekundy
za odpowiedź „zero"**. Suma po tej pozycji: 287,9 s przy 281,7 s przed nią.

## 4. Kontrola negatywna — przewidywanie SPRECYZOWANE przez pomiar

Na kopii pełnego drzewa (`tools`, `src`, `tests`, `docs`, `reports`, `data`,
`.github`, `.gitignore`, `CLAUDE.md`), z czyszczonym `__pycache__`, z asercją że
mutacja wylądowała. Mutacja: jedno zdanie pary wzajemnej
`test_report_claims.py:1949` przepisane tak, żeby liczby stały słownie.

Wybrałem parę **spoza** modułu, w którym zjawisko zobaczyłem — gdyby kontrola szła
na `test_dead_constants_csharp.py`, potwierdzałaby tylko to, co już wiadomo o tamtym
pliku.

```
przewidziane: par 9 -> 8, klasa „proza" maleje o 1, bez pokrycia rosnie o 1
zmierzone:    par 9 -> 8      ZGODNIE
              klasa „proza" 41 -> 39   (o DWA, nie o jeden)
              zbieg 54 -> 52
```

**Przewidywanie było co do kierunku trafne, a co do wielkości za ostrożne — i powód
jest tezą tej pozycji.** Para jest WZAJEMNA, więc usunięcie jednego zdania zabiera
pokrycie OBU liczbom naraz: nie ma już czym się podpierać w żadną stronę. Zapisuję
to jako sprecyzowanie, a nie jako trafienie, bo liczbę 1 wpisałem przed przebiegiem.

## 5. Kontrola przyrządu

Trzy kształty naraz, bo równość na trzech klasach przeszłaby także przy czytniku,
który wszystko wrzuca do jednej:

```
["#: liczba 41 stoi tu", "    # a tu 41"]  -> proza
["PROG = 41", "    x = 41"]                -> kod
["#: liczba 41", "PROG = 41"]              -> mieszane
```

Wcięcie jest tu treścią: komentarz w tym drzewie stoi wcięty razem z kodem, który
opisuje, więc `startswith("#")` bez `strip()` uznałby go za kod i cała klasa „proza"
zapadłaby się do zera przy zielonej bramce.

## 6. Trzy liczby przeszły ze `zbiegu` do `PRZYPISANIA` — i to jest poprawa

Dopisanie trzech stałych postawiło każdą z pogrubionych liczb obok tej, która
ją niesie: `POKRYTYCH_WYLACZNIE_PROZA` przy **41**, `POKRYTYCH_WYLACZNIE_KODEM`
przy **11**, `POKRYTYCH_MIESZANIE` przy **2**. `POKRYTYCH_PRZYPISANIEM` poszło
przez to z 15 na **18**, a 6.D264 nazwało ten kierunek poprawą wprost —
liczba stanęła obok swojej stałej — i tak go tu liczę.

## 7. Czego świadomie nie zrobiono

Okna, wzorca pogrubienia ani zapadki górnej nie ruszano — to 6.D259 i jej pole
„Poza zakresem". **Par wzajemnych nie rozdzielano**: każde rozdzielenie odbiera
pokrycie dwóm liczbom naraz i podnosi `MAX_POGRUBIONYCH_BEZ_POKRYCIA`, której
podnosić nie wolno — wynika to wprost z kontroli negatywnej wyżej, gdzie jedna
mutacja przesunęła dwie liczby. Rozdzielenie ich jest więc osobną pracą z własnym
kosztem, a nie porządkami przy okazji.

Adresy par stoją w tym raporcie, a nie w bramce: numer wiersza rusza się przy każdym
dopisanym akapicie powyżej, więc przybita jest LICZBA par i ich rozkład po plikach.
