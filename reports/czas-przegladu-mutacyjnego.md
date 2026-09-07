# Gdzie idzie czas przeglądu mutacyjnego jednego modułu

**Zmierzone 06.09.2026 na commicie:** `08d12b689b5a03b6f307ba46b4eb5134d89b882f`
**Maszyna:** 4 rdzenie, obciążenie przed pomiarem 0,46 — pomiar szedł na maszynie
wolnej, żeby nie mierzyć cudzego przebiegu (to jest warunek z pozycji 6.B17).
**Metoda:** nie pełny przegląd, tylko CZĘŚCI osobno. Suma części kontra obserwowana
całość.

> **Adnotacja z 6.B20 (07.09.2026, `reports/reszta-czasu-przegladu.md`).** Liczby
> niżej ZOSTAJĄ — to jest datowany pomiar na maszynie wolnej (obciążenie 0,46) i się
> go nie przelicza. Ale metoda z §6 (suma OSOBNO zmierzonych części) jest dokładnie
> to, czego 6.B20 nie powtarza: tamta pozycja zmierzyła te same fazy JEDNEGO ciągłego
> przebiegu i suma zgodziła się z całością co do 0,001 s. Na maszynie współdzielonej
> (obciążenie 1,8–6,9) sonda pokrycia z §5 dokończyła się w całości i zajęła
> **416,7–426,6 s** — **1,53–1,57×** więcej niż ekstrapolacja „~272 s" niżej, która
> była policzona z przebiegu UCIĘTEGO po 210 s na maszynie czterokrotnie mniej
> obciążonej. Różnica jest więc obciążeniem maszyny i ekstrapolacją, nie błędem tego
> pomiaru — obie liczby są prawidłowe dla swoich warunków, tylko warunki są inne.
> Pełny przebieg dwóch mutacji (kalibracja + sonda + robotnicy, workers=1/2/4) dał
> **534,3–600,3 s (8,9–10,0 min)**, wobec sumy „~6,2 min" z §6 niżej — bo ta suma
> sumowała OSOBNE uruchomienia, a jeden ciągły przebieg tego nie robi. Nadal zostaje
> 10–11 minut do historycznej obserwacji „ponad 20 minut", nazwane w 6.B20 jako
> niepotwierdzona hipoteza, nie wynik.

## 1. Pytanie

Dwie mutacje `tools/blender/lod_paths.py` przy dwóch robotnikach nie domknęły się
w ponad dwudziestu minutach, przy obciążeniu maszyny 1,04 — czyli bez współbieżności.
Jeden przebieg zestawu trwa rząd minuty. Różnica jest dwudziestokrotna i pozycja pyta,
z czego się bierze.

## 2. Co robi przebieg, zanim policzy pierwszą mutację

Wyczytane z `tools/tests/mutation_sweep.py`, nie z obserwacji:

| krok | ile razy na przebieg | co kosztuje |
|---|---|---|
| `unreachable_modules` — próbny import modułu | raz na plik przebiegu | jeden podproces |
| kalibracja wyroczni — zestaw w drzewie BEZ mutacji | **raz na przebieg** | pełny zestaw |
| sonda pokrycia — zestaw z licznikiem wierszy | **raz na przebieg** | pełny zestaw **z licznikiem** |
| `add_worktree` | 1 (baza) + 1 (sonda) + 1 **na robotnika** | patrz §3 |
| zestaw pod mutacją | raz na mutację | pełny zestaw |

To odpowiada wprost na pytanie z wiersza kolejki „czy sonda pokrycia liczy się raz czy
za każdym razem": **raz na przebieg**. Wołana jest w `main`, przed pętlą robotników,
a nie w `worker` ani w `check_one`. Drzewo robocze też **nie** powstaje na mutację —
powstaje na robotnika. Obie podpowiedzi z opisu pozycji okazały się fałszywe i poniżej
są zmierzone liczby, które je wykluczają.

## 3. Część pierwsza: utworzenie drzewa roboczego

```
=== CZESC 1: git worktree add --detach --quiet (3 probki)
  worktree add #1: .111167450 s
  worktree remove #1: .011399475 s
  worktree add #2: .106971684 s
  worktree remove #2: .010252437 s
  worktree add #3: .089606652 s
  worktree remove #3: .010472563 s
```

**0,10 s.** Przy dwóch robotnikach cały budżet na drzewa robocze to cztery utworzenia,
czyli **0,4 s** — cztery dziesiąte sekundy z ponad tysiąca dwustu. Hipoteza „`git clean`
i checkout w tym repozytorium nie są tanie" jest **obalona liczbą**: to repozytorium
ma na tyle mało plików, że `git worktree add` mieści się w jednej dziesiątej sekundy.

## 4. Część druga: zestaw w drzewie ciepłym kontra świeżym

```
  ciepla #1: 64.999521156 s  rc=0    1709/1709 przeszło
```

```
worktree_add=.095692995 s
pycache w swiezym worktree: 0 katalogow
zimna_1=50.886377744 s rc=0 ::   1645/1645 przeszło
```

Zestaw w **świeżym** drzewie, bez ani jednego katalogu z prekompilowanym bajtkodem,
poszedł **szybciej** niż w drzewie ciepłym: 50,9 s wobec 65,0 s. Druga hipoteza —
„w świeżym drzewie nie ma prekompilowanego bajtkodu, a każdy moduł idzie przez
przepisanie drzewa składniowego, więc jest wielokrotnie drożej" — jest również
**obalona liczbą**, i to obalona w drugą stronę.

Powód różnicy jest widoczny w mianownikach: **1709** testów w drzewie ciepłym wobec
**1645** w drzewie roboczym. Drzewo robocze dostaje zaślepkę zamiast testów samego
narzędzia mutacyjnego, więc liczy o 64 testy mniej — i to one, a nie bajtkod, robią
te czternaście sekund. Przepisanie drzewa składniowego kosztuje tyle samo w obu
drzewach, bo licznik asercji kompiluje ze źródła za każdym razem; prekompilowany
bajtkod nie ma tu czego przyspieszyć.

## 5. Część trzecia: sonda pokrycia

Sonda robi jeden pełny przebieg zestawu z licznikiem wierszy wstrzykniętym przez
`sitecustomize` do KAŻDEGO procesu przebiegu, także do podprocesów. Przebieg z licznikiem
uciąłem po 210 s, żeby zmieścić się w czasie sesji, i policzyłem, ile testów zdążył:

```
sonda_z_licznikiem: czas=210.009126667 s rc=124 (124 = uciety przez timeout 210 s)
testow wykonanych do ucięcia: 1271 z 1645
```

**1271 testów w 210 s to 6,05 testu na sekundę.** Bez licznika ten sam zestaw w tym samym
drzewie roboczym zrobił 1645 testów w 50,9 s, czyli **32,3 testu na sekundę**. Licznik
wierszy spowalnia zestaw **5,3-krotnie**, a pełny przebieg sondy to w tym tempie
**około 272 s, czyli 4,5 minuty**.

Zastrzeżenie do tej liczby, wypisane, bo zmienia jej wagę: (1) ekstrapolacja z 1271 na
1645 testów zakłada, że pozostałe testy są średnio tak samo drogie jak wykonane, czego
nie sprawdziłem; (2) przez pierwsze kilkadziesiąt sekund tego pomiaru dobiegał jeszcze
poprzedni pomiar z §4, więc 272 s jest **górnym** oszacowaniem, nie środkiem.

Sonda ma własny, hojniejszy limit czasu — czterokrotność limitu mutacji — więc 4,5 minuty
mieści się w nim swobodnie i sonda nigdy nie zgłasza, że czegoś nie zdążyła. Kosztuje po
cichu.

## 6. Rachunek: z czego składa się przebieg dwóch mutacji

Dla przypadku z pozycji — **dwie mutacje, dwóch robotników**:

| składnik | ile | skąd |
|---|---|---|
| 4 × utworzenie drzewa roboczego (baza, sonda, 2 robotniki) | 0,4 s | §3, zmierzone |
| kalibracja wyroczni — zestaw bez mutacji | 50,9 s | §4, zmierzone |
| sonda pokrycia | ~272 s | §5, zmierzone z ekstrapolacją |
| zestaw pod mutacją, 2 mutacje na 2 robotnikach równolegle | ~51 s | §4, zmierzone |
| **suma części** | **~374 s ≈ 6,2 min** | |

**Narzut, który przebiega ZANIM policzona zostanie pierwsza mutacja, to 323 s, czyli
5,4 minuty — i 272 s z tego, czyli 84 %, to sonda pokrycia.** Arytmetyka z opisu pozycji
(„dwie mutacje razy minuta, przez dwóch robotników") liczyła ten narzut jako zero i myli
się o te 323 s — przy dwóch mutacjach o **sześciokrotność**.

**I to nadal nie jest dwadzieścia minut.** Suma zmierzonych części daje 6,2 minuty,
a w najgorszym wariancie — gdyby obie mutacje wisiały aż do limitu czasu mutacji zamiast
kończyć zestaw — 10,4 minuty. Obserwowane było ponad dwadzieścia. **Zostaje co najmniej
dziesięć minut, których ten pomiar NIE wyjaśnia**, i uczciwa odpowiedź pozycji brzmi:
sonda pokrycia jest największą pojedynczą częścią narzutu i jest o rząd większa, niż
zakładała arytmetyka, ale sama nie domyka rachunku. Dwie hipotezy, które opis pozycji
stawiał na pierwszym miejscu — koszt `git worktree add` i brak prekompilowanego bajtkodu
w świeżym drzewie — są **obalone** (§3 i §4) i tej dziury nie zapełnią; szukać trzeba
gdzie indziej.

## 7. Czego ten pomiar nie obejmuje

- **Nie zmierzyłem liczby mutacji na minutę przy 1, 2 i 4 robotnikach**, której żąda
  pole „Wyjście" pozycji. Na to nie starczyło czasu w tej sesji. Z części wyżej wynika
  ona rachunkiem, ale rachunek to nie pomiar i nie jest tu podany jako pomiar.
- **Nie mierzyłem przebiegu pełnego** ani razu — cała metoda polegała na tym, żeby go
  nie odpalać, bo to on się nie domyka.

## 8. Co zauważone obok, a nie tknięte

- Przyspieszenie samego zestawu jest poza zakresem tej pozycji (to 6.D11), tak samo
  zmiana limitu czasu mutacji — limit jest wyrocznią dla mutacji dających pętlę
  nieskończoną.
