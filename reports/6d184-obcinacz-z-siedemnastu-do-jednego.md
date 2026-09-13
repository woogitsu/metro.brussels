# 6.D184 — obcinacz z siedemnastu miejsc do jednego, i nic się przez to nie ruszyło

**13.09.2026**, na `439a745`. Wejście: `tests/Game.Tests/UiTextTests.cs`,
`src/Game/FirstRun.cs`, `reports/6d182-uciete-literaly.md`.

## 1. Miejsc było siedemnaście, nie dziesięć

Wpis pozycji mówił o **dziesięciu** miejscach wywołania, zmierzonych 12.09.2026.
Dziś jest ich **siedemnaście**. Siedem doszło od tamtego dnia i **doszły z mojej
ręki** — przy 6.D182, 6.D183, 6.D155 i 6.D180, czyli w tej samej sesji, która potem
tę pozycję wzięła.

Rozkład po odbiorcy: **cztery** karmią `Literaly`, **trzy** karmią `SlowaWKodzie`,
**dziesięć** trafia do zmiennej i jest używane dalej.

## 2. Na dzisiejszym korpusie obcinacz nie zmienia NICZEGO

Zmierzone na korpusie `ZrodlaGry` (21 plików), obie drogi porównane plik po pliku:

| | z obcinaczem | bez obcinacza | plików z różnicą |
|---|---:|---:|---:|
| literały (`Literaly`) | **480** | **480** | **0** |
| zgłoszenia (`SlowaWKodzie`) | **347** | **347** | **0** |

Powód jest strukturalny, nie przypadkowy: `SlowaWKodzie` iteruje po `Literaly(kod)`,
więc **oba** czytniki dziedziczą po nim obsługę komentarzy — a `Literaly` pomija
komentarze sam, leksykalnie, od 6.D182. Obcinacz stał przed czytnikiem, który już
niczego od niego nie potrzebował.

## 3. A szkodzić potrafi — pokazane liczbą, nie zdaniem

Wejście syntetyczne: napis surowy o czterech wierszach, którego drugi wiersz zaczyna
się od `//`.

| | długość literału |
|---|---:|
| czytnik sam | **33** znaki |
| po obcinaczu | **18** znaków |

Obcinacz usuwa piętnaście znaków ze **środka** napisu, po cichu, bez żadnego
zgłoszenia. Drzewo takiego napisu dziś nie ma — i właśnie dlatego wejście musiało
być syntetyczne: na korpusie obie drogi są nierozróżnialne, więc bramka stojąca na
nim byłaby zielona niezależnie od tego, czy obcinacz gdziekolwiek wrócił.

## 4. ZOSTAJE W JEDNYM MIEJSCU, i to jest wynik pomiaru, nie wyjątek

Pierwsze podejście zdjęło obcinacz ze wszystkich siedemnastu miejsc. Zestaw poszedł
na czerwono w jednym teście:

```
Assert.AreEqual failed. Expected:<521>. Actual:<861>.
stary czytnik daje dziś 861 pozycji wobec zmierzonych 521
```

`PozycjiStaregoCzytnika` opisuje **stary czytnik** — dawny wzorzec regularny,
trzymany wyłącznie jako **wejście kontroli negatywnej**. Bez obcinacza łapie on
cudzysłowy w komentarzach i daje 861 pozycji zamiast 521.

Obcinacz zostaje więc **w jednym miejscu**: karmi `StaryCzytnik`. Obcinanie literału
jest tam nieszkodliwe — ten czytnik ma być zły, o to w nim chodzi. Nazwa zmieniona
na `KodBezKomentarzyDlaStaregoCzytnika`, żeby jego jedyna rola stała w nazwie.

**Szesnaście zdjętych, jedno zostaje z powodem.** Żadna przybita liczba się nie
ruszyła: 480, 362 i 521 są takie same przed i po.

## 5. Co pilnuje powrotu

Dwie bramki, bo jedna by nie wystarczyła:

- **na wejściu syntetycznym** — obcinacz tnie literał z 33 na 18 znaków, a czytnik
  nie tnie; gdyby obcinacz przestał ciąć albo czytnik zaczął, obie strony zapalają;
- **zapadka równościowa na liczbę wystąpień nazwy** — trzy: definicja, wejście
  `StaryCzytnik` i wejście kontroli. Czwarte wywołanie wymaga rozstrzygnięcia,
  a nie przechodzi samo. Bez tej drugiej bramki obcinacz mógłby wrócić na drogę
  żywego czytnika **bez ani jednej czerwonej liczby**, bo na dzisiejszym korpusie
  obie drogi dają to samo.

Bramka wycina ze skanu **własną metodę**: stoją w niej wzorce, które tę nazwę
wymieniają, więc licząc siebie dawała **4 zamiast 3**. Ta sama konstrukcja, co
wycięcie własnej sekcji przy 6.D161 — i ten sam powód.

## 6. Kontrole negatywne

Baza: **249/249**. Po każdej `cp` z kopii roboczej i `md5sum -c: OK`.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | obcinacz wraca na drogę żywego czytnika | **248/249** | zapadka na wystąpienia łapie powrót |
| KN-2 | obcinacz przestaje ciąć (zwraca źródło) | **247/249** | zapala dwie: kontrolę i starego czytnika |
| KN-3 | własna metoda nie jest wycięta ze skanu | **248/249** | liczba 4 zamiast 3 jest zmierzona |
| KN-4 | obcinacz wstawiony do wnętrza `Literaly` | **247/249** | czytnik pod obcinaczem zapala obie bramki |

## 7. Czego nie zrobiono

- **Nie tknięto `src/Game/`** — „Poza zakresem".
- **Nie zmieniono czytnika `Literaly`** — „Poza zakresem".
- **Nie zdjęto obcinacza z ostatniego miejsca** — punkt 4 mówi, czym by to było:
  przeliczeniem historycznego porównania bez powodu.

## 8. Co zauważone przy okazji, nietknięte

Liczba miejsc wywołania urosła z dziesięciu na siedemnaście **w ciągu jednej doby**,
i wszystkie siedem dopisałem ja, przy czterech kolejnych pozycjach. Wpis pozycji
podawał liczbę zmierzoną dzień wcześniej i nikt jej nie odświeżał — to ta sama
rodzina, co ranga otwarta z 6.D163: liczba w prozie opisuje dzień, w którym ją
zmierzono, a wygląda jak liczba bieżąca.
