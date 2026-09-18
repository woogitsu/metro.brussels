# 6.D273 — ciasne podłogi zostają, a przesłanka wariantu (b) była nieprawdziwa

**Data:** 18.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `e41ce06`

## 1. Rozstrzygnięcie właściciela

**Wariant (c): zostawić ciasne podłogi, bez równości.** Pozycja jest zamknięta.

Klasy trzech podłóg w rejestrze `ZAPADKI` zostają **WOLNE** — przy (c) nic ich nie
przestawia. `MINIMUM_DEKLARACJI` nietknięte.

## 2. Liczba, której żądało pole „Wyjście" — policzona

Pole żądało liczby **przed** decyzją: ile deklaracji C# przybywa na rewizję, czyli
jak często równość żądałaby korekty. Decyzja już zapadła, więc liczba nie jest
wejściem do niej — ale bez niej zamknięcie byłoby samym „właściciel zdecydował".

Zmierzone na **155** rewizjach dotykających `src/` albo `tests/`, każda porównana
ze **swoim pierwszym rodzicem**:

| | ile |
|---|---|
| rewizji, w których rozkład C# się zmienia | **86** ze 155, czyli **55 %** |
| rewizji z przyrostem sumy deklaracji | **84**, łącznie **+402** |
| mediana przyrostu, gdy przybywa | **3**, największy pojedynczy **31** |
| **ile razy równość na którejkolwiek z trzech gałęzi żądałaby korekty** | **86** |

Wariant (a) kosztowałby więc korektę w **ponad połowie** rewizji dotykających C#.
Wariant (c) kosztuje tyle, ile 6.D270 już policzyło: podłoga zapala się wyłącznie
na spadku gałęzi.

## 3. Przesłanka wariantu (b) jest w zapisanej postaci NIEPRAWDZIWA

Pozycja opisuje wariant (b) słowami: równość tylko na gałęzi `bez modyfikatora
dostępu`, „która przez 572 rewizje **nie ruszyła się ani razu**".

Zmierzone na pełnej historii:

| gałąź | ruszyła się | wzrost | spadek |
|---|---|---|---|
| `const` | **73** | 72 | 1 |
| `static readonly` | **50** | 49 | 1 |
| `bez modyfikatora` | **24** | 24 | **0** |

Gałąź `bez modyfikatora` **ruszyła się dwadzieścia cztery razy**. Prawdziwe jest
zdanie węższe: **nie spadła** ani razu. Różnica nie jest słowna — równość zapala się
na ruchu w **obie** strony, więc wariant (b) kosztowałby **24** korekty, a nie zero.
Decyzja właściciela o (c) ma pod sobą liczbę, której pozycja nie miała.

Denominatory są różne i to też trzeba powiedzieć: 6.D232 liczyło na **572** rewizjach
(cała historia repozytorium w tamtym dniu), a ten pomiar na **155** rewizjach
dotykających `src/` albo `tests/`. Rewizja, która C# nie dotyka, nie może ruszyć
żadnej gałęzi, więc węższy mianownik jest tu właściwy — ale liczb z obu pomiarów
nie wolno zestawiać wprost.

## 4. Kontrola negatywna — wariant (c) ma łapać SPADEK gałęzi

Mutacja na kompletnej kopii drzewa (215 plików `.py`, 154 pliki `.cs`): jedna
deklaracja `const` przepisana na `static readonly`, czyli **przesunięcie** przy
sumie bez zmian.

```
FAIL test_kazda_galaz_wzorca_ma_wlasna_podloge: galaz `const` daje 306 przy progu 307
     (rozklad: {'const': 306, 'static readonly': 90, 'bez modyfikatora': 45})
14/15 przeszło
```

Suma się nie ruszyła — złapała to wyłącznie ciasna podłoga gałęzi, dokładnie tak,
jak zaprojektowało to 6.D270.

**Czego ta kontrola NIE pokazuje, i to jest treść wariantu (c):** dziura PRZYROSTU
W ZŁEJ GAŁĘZI zostaje otwarta. Stała dopisana jako `static readonly` tam, gdzie
konwencja żąda `const`, podnosi jedną gałąź i nie zapala niczego. Decyzja brzmi:
ta dziura zostaje, bo jej zamknięcie kosztowałoby 86 korekt na 155 rewizji.

## 5. Przewidywania — trzy z sześciu nietrafione

Przewidziałem **200–400** rewizji dotykających C# (jest **155**) i że rozkład zmienia
się na **10–25 %** z nich (jest **55 %**). Drugi błąd ma nazwę: pomyliłem mianownik —
„większość pracy idzie w `tools/`" jest prawdą o całej historii, a nie o rewizjach,
które `src/` w ogóle dotykają.

Trafiona jest mediana przyrostu (**3**), rząd kosztu równości i przewidywanie,
że gałąź `bez modyfikatora` mogła **urosnąć**, choć nie spadła — i to ostatnie
okazało się głównym znaleziskiem.

## 6. Czego ta pozycja nie ruszała

Żadnej podłogi nie zamieniłem na równość. Klasy w `ZAPADKI` zostają WOLNE.
`MINIMUM_DEKLARACJI` nietknięte. Nie zmieniłem ani jednej deklaracji C# w `src/`
ani `tests/` — kontrola negatywna szła wyłącznie na kopii.

## 7. Co zauważyłem przy okazji, a czego nie tknąłem

1. **Dwa spadki gałęzi w historii są realne i nikt ich nie opisał.** `const` spadła
   raz, `static readonly` raz. Przy dzisiejszych ciasnych podłogach każdy taki spadek
   zapaliłby bramkę — czyli koszt wariantu (c) na tej historii to **dwa** zapalenia,
   a nie zero. Jest to ta sama liczba, którą 6.D270 podało jako cenę ciasnych podłóg,
   ale tam wyszła z innego pomiaru i na innym mianowniku; że obie drogi dają dwa,
   jest zbieżnością wartą odnotowania, a nie potwierdzeniem.
2. **Największy pojedynczy przyrost to 31 deklaracji w jednej rewizji.** Przy równości
   taka rewizja żądałaby korekty progu w tym samym commicie — co samo w sobie jest
   wykonalne, ale pokazuje, że „jedna linijka korekty" bywa optymistycznym opisem.
