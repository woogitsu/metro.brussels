# 6.D271 — było ich trzynaście, a bramka zabraniała własnego lekarstwa

**Data:** 18.09.2026 · **Gałąź:** `claude/6d271-siedem-liczb` · **Baza:** `5139ed5`

## 1. Nie siedem, a trzynaście

Pozycja miała poprawić **siedem** nieprawdziwych liczb z listy `ROZJAZDY_POKRYTE_ZBIEGIEM`.
W tym samym module stało ich **trzynaście**, i to jest pierwsze znalezisko:
**lista miała siedem wpisów, bo tyle złapały KOTWICE, a nie bo tyle było fałszywych.**

| miejsce | co twierdziła proza | drzewo | jak było widziane |
|---|---|---|---|
| `:66` deklaracji razem | 389 | **396** | na liście |
| `:83` `const` | 304 | **307** | na liście |
| `:83` `static readonly` | 85 | **89** | na liście |
| `:83` razem w rozkładzie | 389 | **396** | na liście |
| `:84` bez modyfikatora | 43 | **45** | na liście |
| `:91` bez modyfikatora | 43 | **45** | na liście |
| `:91` zostaje po odjęciu | 346 | **351** | na liście |
| `:66` stara podłoga niżej o | 189 | **196** | **żadna kotwica** |
| `:66` udział w populacji | 48,6 % | **49,5 %** | **żadna kotwica** |
| `:68` gałąź `static readonly` zabiera | 85 | **89** | **niepogrubione** |
| `:68` po wycięciu zostaje | 304 | **307** | **niepogrubione** |
| `:70` równość w nawiasie | `== 389` | **396** | **niepogrubione** |
| `:72` i `:75` zapas nad sumą | 59 | **66** | wprost WYKLUCZONE z listy przy 6.D268 |

Trzy z sześciu niewidzianych są **niepogrubione**, więc census z 6.D268 nie mógł
ich zobaczyć; dwóch nie obejmowała żadna kotwica; jedną — „Zapas 59" — sam
wykluczyłem przy 6.D268 jako pochodną sumy, i było to złe rozstrzygnięcie:
pochodna też się starzeje.

**Poprawienie samej siódemki zepsułoby akapit.** Zdanie na `:66` było spójnym
rachunkiem historycznym: 389 populacji minus stara podłoga 200 daje 189, czyli
48,6 %. Podmiana 389 → 396 czyni 189 i 48,6 % fałszywymi, a zdanie zaczyna mieszać
dzisiejszą populację z wczorajszą arytmetyką. Wszystkie trzynaście poprawione razem.

## 2. Bramka z 6.D268 ZABRANIAŁA WŁASNEGO LEKARSTWA

Drugie znalezisko i poważniejsze. `test_ROZJAZDY_nadal_sa_rozjazdami` liczyło
`naprawione` ze **wszystkich** wierszy, które zwraca `rozjazdy_z_drzewa()`, bez
sprawdzenia, czy wiersz nadal stoi na liście. Po wykonaniu **obu** kroków, których
sama żądała — poprawka plus zdjęcie wpisu — zapalała się dalej:

```
oba kroki wykonane  ->  FAIL test_ROZJAZDY_nadal_sa_rozjazdami_i_lista_nie_zostala_z_tylu:
                        te twierdzenia przestaly byc rozjazdami — zdejmij je z
                        `ROZJAZDY_POKRYTE_ZBIEGIEM` … (a były już zdjęte)
                        11/12
```

Jest to kształt 6.D27 **odwrócony**: nie bramka, która milczy na zepsutym, ale
bramka, która czerwienieje na pracy poprawnej — i taka idzie do wyłączenia, nie
do poprawienia. Żyła jedną pozycję. Poprawka to jeden warunek:
`if v[0] == v[1] and k in ROZJAZDY_POKRYTE_ZBIEGIEM`.

## 3. Kontrole — wszystkie trzy kierunki ruchu

Przewidywania spisane przed przebiegami, na kopii PEŁNEGO drzewa, z czyszczonym
`__pycache__`, każda z asercją że mutacja wylądowała.

| mutacja | przewidziane | zmierzone |
|---|---|---|
| poprawka BEZ zdjęcia wpisu | czerwień „zdejmij je z…" | `FAIL … te twierdzenia przestaly byc rozjazdami`, 11/12 |
| oba kroki (stan końcowy) | zielono | `12/12 przeszło` — po poprawce bramki; PRZED nią `11/12` |
| zdjęcie wpisu BEZ poprawki | czerwień „lista rozjechała się" | `FAIL … zmierzone [(…'const'), (304, 307))], wpisane []` |
| **regresja poprawionej liczby** (307 → 304) | czerwień — dziś nic tego nie łapie | `FAIL … zmierzone [(… 'const'), (304, 307))], wpisane []` |
| **regresja figury NOWO objętej kotwicą** (196 → 189) | czerwień — godzinę temu nie łapało nic | `FAIL … [(… 'stara podloga nizej o'), (189, 196))]` |

Dwie ostatnie są zyskiem trwałym: liczba, której przed tą pozycją nie pilnowało
nic, zapala się dziś **z nazwy**.

## 4. Zapadka pokrycia: zmierzona, nie podniesiona

Pole „Wyjście" pytało, czy poprawienie przesunie liczby ze `zbiegu` do
`bez pokrycia` i o ile ruszy `MAX_POGRUBIONYCH_BEZ_POKRYCIA`. Zmierzone:
poprawienie trzynastu figur zostawia **175** bez zmian, więc zapadki **nie
podniesiono** — a podnieść górnej i tak nie wolno.

Jedna liczba musiała jednak stracić pogrubienie i powód jest inny niż zwykle:
w komentarzu o zawężeniu kotwicy napisałem `` `(zostaje **307**)` `` jako **cytat
wzorca**, nie twierdzenie o pomiarze — a sito liczy pogrubienie, nie intencję.
Populacja bez pokrycia poszła na 176 i wróciła na 175 po przepisaniu tego zdania.
Nie jest to obejście bramki: zdanie nie ogłaszało pomiaru.

Census z 6.D268 zapalił się na tej pozycji trzeci raz z rzędu, bo pogrubiłem trzy
figury wcześniej niepogrubione: pokrytych zbiegiem jest **54**, w tym module **12**,
grupa A **26**. Census zaktualizowany.

## 5. Kotwica, która stała się dwuznaczna

Dołożenie kotwicy `(zostaje **307**)` zrobiło starą kotwicę `zostaje \*\*(\d+)\*\*`
dwuznaczną — dopasowywała **dwa** zdania, a czytnik zwracał wtedy `None` i
porównanie przechodziło cicho. Złapała to
`test_kotwice_zdan_o_deklaracjach_lapia_PO_JEDNYM_zdaniu`, czyli dolne ostrze
dopisane razem z kotwicami przy 6.D268 — bramka istniejąca dokładnie na ten
wypadek, zadziałała przy pierwszym przebiegu po rozszerzeniu. Kotwica zawężona
do `deklaracje, zostaje \*\*(\d+)\*\*`.

## 6. Trzeci raz ta sama pomyłka na kopii drzewa

`DRZEWA` tego modułu to `("src", "tests")`, a ja **trzy razy** w tej serii
skopiowałem `tools/` i liczyłem na wynik. Za każdym razem kopia dawała liczby
bezsensowne (`const` 117 zamiast 307, potem `(45, 0)`) i za każdym razem czytało
się to jak zapalenie bramki na mutacji. Kopia musi nieść
`tools + src + tests + docs + reports + CLAUDE.md + .gitignore`; zapisane tutaj,
bo trzy powtórzenia to nie pomyłka, a nawyk.

## 7. Czego świadomie nie zrobiono

`MINIMUM_DEKLARACJI` nietknięte — podłoga sumy jest poprawna, zmieniły się tylko
zdania o niej. Pozostałych **14** pozycji grupy A z 6.D268 nie sprawdzano: każda
wymaga wskazania czytnika, którego w tekście nie ma. Okna, wzorca pogrubienia ani
zapadki górnej nie ruszano (6.D259).

Podłoga sumy jest w nowych kotwicach czytana **ze źródła jako tekst**, a nie brana
przez `DCS.MINIMUM_DEKLARACJI`, i powód jest zmierzony: sięgnięcie po symbol daje
tej zapadce drugie użycie i zapala bramkę z 6.D254, która wtedy żąda zmierzenia
jej klasy mutacją. Przy 6.D268 ta sama kolizja kosztowała zdjęcie wiersza z listy;
tu wiersz był potrzebny, więc kosztowała zmianę sposobu odczytu.
