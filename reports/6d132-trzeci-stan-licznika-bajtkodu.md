# 6.D132 — licznik starego bajtkodu miał dwa stany, a stany są trzy

**11.09.2026**, na `e6a7c74`. Pozycja pytała, czy dorobić trzeci stan, czy pokazać
pomiarem, że wznowień z dziennikiem sprzed 6.D113 nie ma i mieć nie będzie.
**Pomiar mówi, że są osiągalne** — więc trzeci stan.

## 1. Czego dotyczy

Wypis przed poprawką:

```
[MUTACJE] mutacji zapisanych pod ważnym starym bajtkodem: 0
          (sweep kasuje go przed każdym przebiegiem, więc żadna nie poszła na nim)
```

Liczba powstaje z `[r for r in results if r.get("stary_bajtkod")]`. Wpis sprzed 6.D113
tego pola nie ma, `dict.get` zwraca `None`, `None` jest fałszywe — wpis wpada do tej
samej kupki, co wpis **zmierzony z wynikiem `False`**, i nie zostawia śladu. Zdanie
w nawiasie mówi tymczasem o **wszystkich** mutacjach przebiegu.

## 2. Czy to jest w ogóle osiągalne — zmierzone, nie wywnioskowane

Wznowienie odrzuca dziennik na trzy sposoby: wpis z pliku spoza przebiegu, wpis
z innego `commit` (6.B19) i wpis o innym `odcisk` treści (6.B32). **Obie te poprawki
są starsze od 6.D113**, więc wpis sprzed 6.D113 wszystkie trzy odmowy przechodzi.

Zbudowany dziennik z jednym takim wpisem — `commit` i `odcisk` dzisiejsze, pola
`stary_bajtkod` brak — i przebieg na dwóch mutacjach `lod_paths`:

```
[MUTACJE] wznowienie z /tmp/mieszany2.jsonl: 1 z 2 już policzonych
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0, nierozstrzygniętych 0
[MUTACJE] mutacji zapisanych pod ważnym starym bajtkodem: 0
          (sweep kasuje go przed każdym przebiegiem, więc żadna nie poszła na nim)
```

Zero **z dwóch**, z których zmierzono **jedną**. Liczby `2` nie ma w wypisie nigdzie,
a słowo „żadna" dotyczy obu.

## 3. Po poprawce, ten sam dziennik, ten sam przebieg

```
[MUTACJE] mutacji zapisanych pod ważnym starym bajtkodem: 0 z 1 ZMIERZONYCH
          (sweep kasuje go przed każdym przebiegiem, więc żadna zmierzona nie poszła na nim)
[MUTACJE] wpisów BEZ tego pomiaru: 1 z 2 — dziennik sprzed 6.D113 pola `stary_bajtkod`
          nie ma, więc licznik wyżej o tych mutacjach nie mówi NIC
  BEZ POMIARU   tools/blender/lod_paths.py:28 operator `==` -> `!=`
```

Trzy zmiany, każda z własnym powodem:

* **mianownik** — „0 z 1", nie samo „0";
* **słowo „zmierzona"** w zdaniu w nawiasie, bo zdanie dotyczy tylko tych;
* **wiersz o niezmierzonych**, wypisywany **także gdy jest ich zero**. Jest to ta sama
  zasada, którą 6.D113 zapisało dla wiersza wyżej („zero jest wynikiem pomiaru,
  a milczenie byłoby nieodróżnialne od braku pomiaru"), plus powód nowy: bez tego
  wiersza mianownik nie ma z czym się różnić i czyta się jak ozdobnik.

`null` w polu — a ręcznie poprawiony dziennik taki bywa — liczy się jako **niezmierzony**,
nie jako `False`.

## 4. Kontrole negatywne

Baza `test_mutation_sweep.py`: **132/132** (było 126). `__pycache__` czyszczony przed
każdym przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK` na obu plikach.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | powrót do `bool(entry.get(...))`, dwa stany | **129/132**, trzy testy |
| KN-2 | wiersz o niezmierzonych tylko gdy niezerowy | **130/132**, dwa testy |
| KN-3 | mianownik liczony ze wszystkich wpisów | **131/132** |
| KN-4 | `main` składa wypis po swojemu | **131/132** |
| KN-5 | wiersze `BEZ POMIARU` zdjęte | **131/132** |
| KN-6 | niezmierzone wrzucone do kupki `False` | **130/132**, dwa testy |

KN-4 jest tu warta zdania: bez niej testy mierzyłyby funkcję, której przebieg nie woła —
czyli byłyby bramką meldującą sprawdzenie, którego nie zrobiła. Test czyta drzewo składni
`main` i żąda wywołania po nazwie, a osobno liczy, ile razy zdanie licznika stoi w kodzie
**poza docstringami**: docstring nowej funkcji cytuje to zdanie dwa razy, brzmieniem dawnym
i dzisiejszym, i cytat kopią reguły nie jest.

## 5. Weryfikacja

```
  132/132 przeszło       test_mutation_sweep.py   (było 126)
  2326/2326 przeszło, 122 moduły, KOD=0, RAZEM 164.968 s
```

Przebieg przeglądu na dzienniku mieszanym: **kod 0**, `rozstrzygniętych 2/2`.

## 6. Czego nie zrobiłem

* **Nie przepisałem żadnego dawnego dziennika** i nie zmieniłem formatu wpisu dla pól
  istniejących — oba wprost w „Poza zakresem".
* **Nie dodałem odmowy wznowienia przy wpisie bez pola.** Byłaby to czwarta odmowa obok
  trzech istniejących, a te trzy bronią przed podstawieniem **cudzego wyniku**; brak
  pomiaru bajtkodu niczego nie podstawia, więc odmowa kosztowałaby wznowienie, dając
  w zamian to, co dziś mówi wypis.
* **Nie policzyłem, ile dzienników sprzed 6.D113 leży dziś na dyskach.** Nie da się:
  domyślna nazwa niesie commit i odcisk, więc dziennik sprzed tamtej zmiany żyje tylko
  tam, gdzie ktoś podał `--journal` ręcznie.
