# `seen >= 500` przy 1466 trafieniach — podłoga przeliczana i bramka pokrycia (6.D58)

**Zmierzone 09.09.2026 na:** `c8fb583`, kontener tej sesji.
**Przyrząd:** przejście po `reports/` wzorcem `PATH_TOKEN` (pełnym i zawężanym) oraz
`python3 tools/tests/test_all.py test_report_hygiene.py`.

---

## 1. Co było zepsute — zapas 966 i próg, który słabł sam

Bramka „każda ścieżka wymieniona w raporcie rozwiązuje się w drzewie" kończyła się
podłogą `assert seen >= 500`, przy komentarzu mówiącym, że próg „stoi niżej, żeby nie
trzeba go było ruszać przy każdym nowym raporcie". Pomiar:

```
raportow (checked): 162
trafien wzorca (seen): 1466
obecna podloga: 500  -> zapas: 966
udzial, ktory moglby zniknac: 65.9 %
```

Do tego stała **słabła z każdym raportem**: 500 to dziś 3,09 ścieżki na raport, przy
300 raportach byłoby 1,67, przy 500 — jedna. Podłoga wpisana w trafieniach mierzy
katalog z dnia, w którym ją wpisano.

## 2. Dlaczego stosunek, a nie zapadka równościowa — odstępstwo od pola „Wyjście"

Pole **Wyjście** pozycji 6.D58 żądało zapadki **równościowej** na `seen`, wzorem
zapadki, którą 6.D45 wprowadziła dla stałej `MIN_REPORTS`. Nie zrobiłem tego,
i powód jest zmierzony, nie wygodny:

- `MIN_REPORTS` rusza się, gdy **dochodzi raport** — raz na zadanie. I nawet w tym
  kształcie wymusiło **siedem** podniesień w ciągu jednego wieczoru (153 → 162).
- `seen` rusza się przy **każdej wzmiance o pliku w prozie dowolnego raportu**, czyli
  przy edycji, która z tą bramką nie ma nic wspólnego. Równość na `seen` byłaby
  tripwire'em na niepowiązanej pracy, a bramka zapalająca się na poprawnej zmianie
  zostaje wyłączona (6.D27).

W drzewie stoi więc `seen >= checked * SCIEZEK_NA_RAPORT_MIN`. Podłoga rośnie razem
z katalogiem i nie ma w niej liczby, która mogłaby zostać z tyłu. Druga strona pary
już była: `checked >= MIN_REPORTS` przypina liczbę **czytanych** raportów do stanu
katalogu, więc równoczesny spadek `seen` i `checked` — czyli skan, który przestał
czytać pliki — nie utrzyma stosunku.

## 3. Boksowanie stałej — oba brzegi liczone z drzewa

`test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami` nie przechowuje ani jednej
liczby z pomiaru; przelicza brzegi przy każdym przebiegu.

| brzeg | co mówi | dziś |
|---|---|---|
| od dołu | podłoga musi zaczerwienić **zawężenie kontrolne** wzorca (zdjęcie `.md`) | 972 > 905 |
| od góry | podłoga musi stać co najmniej **jedną pełną ścieżkę na raport** pod dzisiejszym stosunkiem, `seen >= checked * (K + 1)` | 1466 ≥ 1134 |
| różnica | nowa podłoga żąda więcej niż zastąpiona stała | 972 > 500 |

Kontrola przyrządu stoi wewnątrz testu: gdyby `ROZSZERZENIE_KONTROLNE` przestało mieć
trafienia, brzeg od dołu porównywałby podłogę z **niezmienionym** stosunkiem i byłby
zielony nad każdą wartością stałej. Bez tej asercji cały brzeg byłby ozdobą.

### Trzy kierunki — wykonane, każdy z czyszczeniem `__pycache__`

```
=== SCIEZEK_NA_RAPORT_MIN = 5
  FAIL test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami: po zdjęciu `.md` ze wzorca zostaje 905 trafień, czyli 5.59 na raport, a podłoga żąda 5 — zawężenie PRZESZŁOBY. […]
  17/18 przeszło
kod: 1
=== SCIEZEK_NA_RAPORT_MIN = 7
  18/18 przeszło
kod: 0
=== SCIEZEK_NA_RAPORT_MIN = 8
  18/18 przeszło
kod: 0
=== SCIEZEK_NA_RAPORT_MIN = 9
  FAIL test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami: drzewo daje 9.05 ścieżki na raport przy podłodze 9 — zapas zszedł poniżej jednej pełnej ścieżki (1466 trafień wobec 1620 wymaganych) […]
  17/18 przeszło
kod: 1
```

`md5` modułu przed mutacjami i po przywróceniu: `fd81c6d1dabb6daab0bd4ebee813d292`.

**Kierunek w dół daje FAIL, równo jest zielono, a kierunek w górę — nie daje FAIL,
i to jest wynik pomiaru, nie luka w boksowaniu.** Pole „Skończone, gdy" żądało trójki
FAIL/zielono/FAIL, bo było pisane dla zapadki **równościowej**, która z definicji pada
w obie strony. Podłoga stosunkowa ma jeden brzeg twardy (dołem) i jeden z zapasem
(górą); przedział mieszczący się w obu to **{6, 7, 8}**. Zgłaszam to jako drugie
odstępstwo od treści pozycji, razem z rachunkiem niżej, a nie jako spełniony warunek.

## 4. Dlaczego 6, a nie 8 — pomiar trwałości

„Bierz najmocniejszą wartość z przedziału" byłoby tu błędem, bo **raporty z ostatnich
dni są chudsze od średniej katalogu**:

| próbka | raportów | ścieżek na raport (średnia) | mediana |
|---|---:|---:|---:|
| pierwsze 50 dodanych | 50 | 15,14 | 8,0 |
| ostatnie 50 dodanych | 50 | 7,26 | 4,0 |
| ostatnie 20 dodanych | 20 | 6,15 | 3,0 |
| 07.09.2026 (największa próbka jednego dnia) | 59 | 5,47 | 3,0 |
| 02.09.2026 (najchudszy dobrze obsadzony dzień) | 9 | 5,11 | 5,0 |

Średnia całego katalogu (9,05) jest niesiona przez ogon starych, gęstych raportów —
maksimum to 102 ścieżki w jednym pliku, a **92 raporty ze 162 mają mniej niż siedem**.
Ile nowych raportów o gęstości 5,11 zniesie która podłoga, licząc z dzisiejszego
zapasu:

| podłoga | zapas trafień | raportów do zaczerwienienia |
|---:|---:|---:|
| 6 | 494 | **555** |
| 7 | 332 | 175 |
| 8 | 170 | 58 |

58 raportów to w tym projekcie około trzech dni. Podłoga 8 byłaby więc bramką, która
zaświeci bez żadnej usterki, zanim ktokolwiek o niej zapomni — czyli dokładnie
materiałem na wyłączenie (6.D27). Stąd 6.

## 5. Podłoga stosunkowa łapie 2 zawężenia z 12 — i to jest jej granica

Tu pomiar obalił moje własne założenie z pola „Wyjście": stosunek **nie jest** dobrym
detektorem zawężenia wzorca. Trafienia po rozszerzeniach i to, co zostaje po zdjęciu
każdego z nich:

| rozszerzenie | trafień | `seen` po zdjęciu | ścieżek/raport | podłoga 6 |
|---|---:|---:|---:|---|
| `py` | 597 | 869 | 5,36 | **CZERWONA** |
| `md` | 561 | 905 | 5,59 | **CZERWONA** |
| `cs` | 157 | 1309 | 8,08 | zielona |
| `json` | 107 | 1359 | 8,39 | zielona |
| `sh` | 22 | 1444 | 8,91 | zielona |
| `csproj` | 9 | 1457 | 8,99 | zielona |
| `txt` | 7 | 1459 | 9,01 | zielona |
| `csv` | 4 | 1462 | 9,02 | zielona |
| `tscn` | 2 | 1464 | 9,04 | zielona |
| `yml`, `yaml`, `geojson` | 0 | 1466 | 9,05 | zielona |

**Dwa z dwunastu.** Stara podłoga `>= 500` nie łapała ani jednego. Dlatego doszła
druga bramka — **pokrycie rozszerzeń, bez żadnego progu**: każde pilnowane
rozszerzenie musi mieć w raportach żywe trafienie albo jawny wpis w
`ROZSZERZENIA_BEZ_TRAFIEN` z powodem. Łapie **9 z 12** zawężeń; trzech ostatnich nie
łapie nic, bo i dziś nie mają trafień, i to stoi wypisane przy wpisach.

Bramka pokrycia zamyka też własną pułapkę, i to jest w niej najważniejsze. Lista
rozszerzeń **nie może** być czytana z samego wzorca — zmierzone na wzorcu z `.md`
zdjętym:

```
A) lista rozszerzen CZYTANA ZE WZORCA -- pulapka, ktorej NIE uzyto:
   lista: ('py','cs','json','sh','yml','yaml','txt','csproj','tscn','geojson','csv') (11 pozycji, 'md' JUZ NIE MA)
   bez pokrycia: [] -> ZIELONA nad defektem

B) lista PRZYPIETA w kodzie -- to, co jest w drzewie:
   lista: ('py','cs','md','json','sh','yml','yaml','txt','csproj','tscn','geojson','csv') (12 pozycji)
   bez pokrycia: ['md'] -> CZERWONA
```

Zdjęcie rozszerzenia ze wzorca zdjęłoby je także z listy do sprawdzenia. To **czwarty
raz z rzędu** — po 6.D54, 6.D55 i 6.D56 — kiedy świeżo napisana bramka byłaby zielona
nad usterką, którą ma łapać, i pierwszy, w którym wyszło to przed napisaniem, a nie po.
Cena kopii listy jest znana z 6.D44 i zapłacona: zgodność kopii ze wzorcem pilnuje
asercja **równościowa** w `test_zestaw_rozszerzen_w_kodzie_i_we_wzorcu_JEST_TEN_SAM`.

## 6. Kontrole negatywne — wszystkie wykonane

### KN-1: zawężenie kontrolne — stara podłoga zielona, nowa czerwona

Tego żądało pole „Weryfikacja", i to **liczbą**:

```
=== WZORZEC ZAWĘŻONY: usunięte 'md|'
  checked=162 seen=905 stosunek=5.59
  STARA podloga  seen >= 500              -> ZIELONA
  NOWA  podloga  seen >= checked*6 (972)  -> CZERWONA
  FAIL test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie: wzorzec znalazł 905 ścieżek w 162 raportach, czyli 5.59 na raport przy wymaganych 6 […]
  FAIL test_kazde_pilnowane_rozszerzenie_ma_zywe_trafienie_albo_jawny_wyjatek: rozszerzenia ['md'] nie mają w 162 raportach ani jednego trafienia […]
  FAIL test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami: zawężenie kontrolne zdejmuje `.md`, a to rozszerzenie nie ma dziś ani jednego trafienia […]
  FAIL test_zestaw_rozszerzen_w_kodzie_i_we_wzorcu_JEST_TEN_SAM: kopia listy rozszerzeń rozjechała się ze wzorcem […]
  14/18 przeszło
```

### KN-2: zawężenie, którego podłoga stosunkowa nie widzi

```
=== WZORZEC ZAWĘŻONY: usunięte '|csv'
  checked=162 seen=1462 stosunek=9.02
  STARA podloga  seen >= 500              -> ZIELONA
  NOWA  podloga  seen >= checked*6 (972)  -> ZIELONA
  FAIL test_kazde_pilnowane_rozszerzenie_ma_zywe_trafienie_albo_jawny_wyjatek: rozszerzenia ['csv'] nie mają w 162 raportach ani jednego trafienia […]
  FAIL test_zestaw_rozszerzen_w_kodzie_i_we_wzorcu_JEST_TEN_SAM: kopia listy rozszerzeń rozjechała się ze wzorcem […]
  16/18 przeszło
```

**Obie podłogi zielone, pada wyłącznie pokrycie i zgodność kopii.** Ta kontrola jest
całym uzasadnieniem drugiej bramki: bez niej zmiana sprawdzałaby więcej tylko
o dwa rozszerzenia z dwunastu.

### KN-3: skan czyta 3 raporty zamiast 162

```
  FAIL test_kazde_pilnowane_rozszerzenie_ma_zywe_trafienie_albo_jawny_wyjatek: bramka przeszła tylko 3 raportów, a w `reports/` jest ich co najmniej 162 […]
  FAIL test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami: bramka przeszła tylko 3 raportów, a w `reports/` jest ich co najmniej 162 […]
  16/18 przeszło
```

Mutacja dotyczy **zbieracza**, nie danych — obie nowe bramki mają własną podłogę
`checked >= MIN_REPORTS`, bo stosunek policzony z trzech raportów jest zielony tak
samo dobrze jak z stu sześćdziesięciu dwóch.

### KN-4: wyjątek od pokrycia, który zaczął chronić żywe rozszerzenie

```
  FAIL test_kazde_pilnowane_rozszerzenie_ma_zywe_trafienie_albo_jawny_wyjatek: `ROZSZERZENIA_BEZ_TRAFIEN` wymienia ['csv'], a trafienia już są ({'csv': 4}) — zdejmij wpis […]
  17/18 przeszło
```

Bez tej drugiej strony lista wyjątków gniłaby po cichu, dokładnie jak
`COMMIT_EXCEPTIONS` bez `test_lista_wyjatkow_nie_gnije`.

Po każdej mutacji `find tools -name __pycache__ -type d -exec rm -rf {} +` (6.D41),
a `md5` modułu po każdym przywróceniu: `fd81c6d1dabb6daab0bd4ebee813d292`.

## 7. Weryfikacja

```
$ python3 tools/tests/test_all.py test_report_hygiene.py
  18/18 przeszło
kod: 0
```

## 8. Czego świadomie nie zrobiłem

- **Nie zmieniłem `PATH_TOKEN`** — zabrania tego pole „Poza zakresem", i dotyczy to
  także martwego pola opisanego w §9.
- **Nie zrobiłem zapadki równościowej na `seen`** — powód w §2, zmierzony.
- **Nie wpisałem trzeciego brzegu na trwałość** (rachunek z §4 jako asercji). Wymagałby
  czytania dat dodania raportów z `git log` w czasie testu, czyli podprocesu w bramce
  higieny, i dawałby brzeg tak czuły, że sam byłby fałszywym alarmem. Rachunek stoi
  przy stałej i w §4; brzeg od góry (`K + 1`) chroni tę samą rzecz taniej.
- **Nie ruszyłem `MIN_REPORTS`, `COMMIT_EXCEPTIONS` ani żadnego raportu** — poza
  zakresem pozycji.

## 9. Zauważone przy okazji, nie tknięte

**`PATH_TOKEN` nie umie dopasować ani jednej ścieżki zaczynającej się kropką.** Token
musi się zaczynać znakiem z `[A-Za-z0-9_]`, więc **22 wzmianki w 15 raportach**
o plikach CI — wszystkie pod `.github/` — są dla bramki niewidzialne. Dziś wszystkie
22 rozwiązują się w drzewie, więc usterki nie ma; jest martwe pole przyrządu, i to
w bramce, której całym zadaniem jest łapanie odsyłaczy w puste miejsce. To także
powód, dla którego `yml` nie ma trafień: nie dlatego, że nikt o CI nie pisze.
Zmiana wzorca jest poza zakresem 6.D58, więc zgłoszone osobną pozycją **6.D59**.

**Istniejąca kontrola detektora nie zauważyła żadnego z dwóch zawężeń.**
`test_wzorzec_sciezki_lapie_to_co_ma_i_nie_lapie_prozy` przeszedł zarówno przy zdjętym
`.md`, jak i przy zdjętym `.csv` — jego cztery pary sprawdzają **kształt** tokena
(ukośnik, proza, przedrostki), a nie **zestaw rozszerzeń**. Nie jest to usterka tego
testu, bo nigdy nie obiecywał pokrycia rozszerzeń; jest to miejsce, w którym bramka
pokrycia z tej pozycji stanęła obok niego, a nie zamiast niego.
