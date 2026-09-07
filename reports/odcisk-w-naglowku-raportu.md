# Raport przeglądu identyfikował pomiar samym commitem (6.B42)

**Zmierzone 07.09.2026 na commicie:** `5ae1b52d99b3ed1cd5c1f0e874e706ac5380f685`
**Dotyczy:** `tools/tests/mutation_sweep.py`, `tools/tests/test_mutation_sweep.py`
**Poprzedni etap:** 6.B32 (wpis dziennika), 6.B40 (nazwa pliku), 6.D3 (higiena raportów)

## 1. Trzeci raz to samo zdanie, o trzecim miejscu

Commit nie odróżnia dwóch przebiegów na tym samym commicie. To zostało zmierzone
najpierw dla **wpisu** dziennika (6.B32), potem dla **nazwy pliku** (6.B40), a nagłówek
raportu mówił nadal `**Snapshot na commicie:** {commit}` i nic więcej — więc raport
z przebiegu `--dirty` był **nieodróżnialny** od raportu z drzewa czystego, choć liczby
dotyczyły innej treści.

6.D3 postawiło bramkę na to, żeby każdy `reports/*.md` mówił, na jakim commicie
powstały jego liczby. Ten raport commit podawał — i to było za mało dokładnie o tyle,
o ile za mało go było w dzienniku.

## 2. Pomiar, którego żądało pole „Wyjście", i on rozstrzygnął postać

Pole pozostawiało wybór: jeden odcisk całego przebiegu (krótki, ale nie mówi, który
moduł się różni) albo tabela moduł → odcisk (dokładna, ale przy 63 modułach zajmuje
ekran). Miał go rozstrzygnąć pomiar: „ile modułów ma typowy przebieg z `reports/`".

**Najpierw trzeba było odsiać prozę od komend** — ta sama pułapka, którą 6.A31 nazwało
dla ścieżek `bin/`, i mój pierwszy licznik w nią wpadł:

```
wierszy z napisem mutation_sweep.py, ktore NIE sa komenda (proza):  99
prawdziwych wywolan:                                                66
```

Naiwny `grep` dałby więc **165** i utopił sygnał w wzmiankach typu
„`tools/tests/mutation_sweep.py` (`report`, wywołanie w `main`)".

Rozkład prawdziwych wywołań po liczbie objętych modułów:

| ile modułów obejmuje wywołanie | ile wywołań |
|---|---|
| **1** | **54** |
| 2 | 1 |
| 0 (umyślna atrapa `nie-ma-takiego-pliku`) | 4 |
| **63** (bez `--only`) | **7** |

Średnia ważona: **7,5** modułu na wywołanie — liczba, która sama nic nie mówi, bo
rozkład jest dwugarbny.

**Założenie pozycji jest POTWIERDZONE**: „jeżeli triaż chodzi po jednym module naraz,
tabela jest darmowa" — w **82 %** wywołań (54 z 66) tabela ma **jeden wiersz**.

## 3. Rozstrzygnięcie: jedno ORAZ drugie, z progiem z pomiaru

Nie „jedno z dwojga". Nagłówek niesie **odcisk zbiorczy** (zawsze, krótki) **oraz**
tabelę moduł → odcisk, dopóki modułów jest najwyżej `MAX_ODCISKOW_W_RAPORCIE = 8`.
Próg nie jest okrągły z gustu: przepuszcza **każdy** zmierzony przebieg triażowy
(najszerszy z zawężeniem to `sweep.py` z dwoma modułami) i odsiewa te **7** pełnych,
gdzie tabela zajęłaby 63 wiersze.

Powyżej progu zostaje sam odcisk zbiorczy **i zdanie o tym, ile modułów pominięto** —
nie milczenie. Raport, który nie mówi, że czegoś nie mówi, jest gorszy od raportu
krótszego.

Odcisk zbiorczy bierze `odcisk_przebiegu` z 6.B40, a nie własne składanie tej samej
listy: dwa czytniki jednej rzeczy rozjeżdżają się po cichu (6.B28). To jest ten drugi
rozmówca, dla którego tamta funkcja została **wydzielona osobno** — i dlatego ta
pozycja nie dodaje ani jednej linii arytmetyki.

## 4. Skończone, gdy — WYKONANE, oba nagłówki wklejone

Ten sam commit, ten sam moduł, dwie treści:

```
=== A: raport z drzewa CZYSTEGO ===
# Przegląd mutacyjny bramek

**Snapshot na commicie:** `5ae1b52`

**Odcisk treści przebiegu:** `ebd663d489861bb7` (1 moduł(ów))

| moduł | odcisk treści |
|---|---|
| `tools/blender/lod_paths.py` | `fcb923b7000e0dca` |

=== B: jeden znak zmieniony, przebieg --dirty ===
# Przegląd mutacyjny bramek

**Snapshot na commicie:** `5ae1b52`

**Odcisk treści przebiegu:** `7d1ed5ecd86fd947` (1 moduł(ów))

| moduł | odcisk treści |
|---|---|
| `tools/blender/lod_paths.py` | `634df59defe0ec2a` |
```

`diff` obu nagłówków pokazuje dokładnie dwa wiersze różnicy i ani jednego więcej —
commit jest w obu ten sam, co jest sedno sprawy.

## 5. Weryfikacja

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  1927/1927 przeszło
  RAZEM 72.782 s, 1927 testów, 101 modułów
kod: 0
```

Zestaw **1922 → 1927**, moduł `test_mutation_sweep.py` **99 → 104**.

## 6. Cztery kontrole negatywne — WYKONANE, każda na innym zbiorze

**KN-1 — odciski zdjęte z nagłówka w całości** → wszystkie pięć nowych testów, `99/104`.

**KN-2 — odcisk zbiorczy podmieniony na STAŁĄ.** To jest kontrola, dla której ta
czwórka w ogóle istnieje: napis w raporcie **jest**, zależności od treści **nie ma**.
Test sprawdzający tylko obecność frazy przeszedłby.

```
FAIL test_dwie_tresci_daja_ROZNE_naglowki_przy_tym_samym_commicie:
     **Odcisk treści przebiegu:** `0000000000000000` (1 moduł(ów))
FAIL test_naglowek_raportu_niesie_odcisk_tresci_a_nie_tylko_commit
FAIL test_powyzej_progu_tabela_ustepuje_ZDANIU_a_nie_milczeniu
  101/104 przeszło
```

To ta sama klasa usterki, którą ta sesja tropiła cały dzień: **asercja na obecność
czegoś dobrego zamiast na zależność** (6.A32, 6.A29, 6.A25, 6.A26, 6.A27) — i tym
razem została przewidziana, a nie znaleziona po fakcie.

**KN-3 — próg `<=` zmieniony na `<`** (remis na granicy) → dokładnie **jeden** test,
`103/104`. Para „na progu tabela jeszcze jest" / „powyżej progu ustępuje zdaniu"
pilnuje granicy z obu stron, więc przesunięcie progu musi być świadome.

**KN-4 — powyżej progu MILCZENIE zamiast zdania** → dokładnie **jeden** test,
`103/104`.

Plik przywrócony po każdej z czterech i sprawdzony przez `cmp`.

## 7. Czego świadomie nie zrobiłem

- **Nie przeliczyłem `reports/mutation-sweep.md` ani `reports/mutation-drift.md`** —
  są pomiarami z datą i dostały **adnotację** mówiącą, czego w nich brakuje
  (`docs/04-conventions.md`, pole „Poza zakresem" pozycji).
- **Nie tknąłem formatu samych sekcji raportu** — pole „Poza zakresem". Zmienił się
  wyłącznie nagłówek.
- **Nie dodałem ani jednej linii arytmetyki odcisków.** `odcisk_przebiegu` istnieje
  od 6.B40 i został tam wydzielony osobno **właśnie na tego rozmówcę**.

## 8. Zauważone przy okazji, nietknięte

- **Średnia 7,5 modułu na wywołanie jest liczbą bezużyteczną i dlatego stoi obok
  rozkładu.** Rozkład jest dwugarbny (54 wywołania po 1 module, 7 po 63), więc średnia
  nie opisuje ani jednego prawdziwego przebiegu. Zapisuję, bo sama średnia w raporcie
  wyglądałaby jak wynik.
- **`reports/mutation-sweep.md` niesie nagłówek `**Snapshot na commicie:** `66b8301`
  (`main`, 04.09.2026)`** — czyli commit **i** datę **i** nazwę gałęzi w jednym
  wierszu, inaczej niż wzór z 6.D3. Bramka higieny to przepuszcza, bo szuka SHA
  w grawisach. Nie tknięte: to jest kształt nagłówka, nie brak informacji.
