# 6.D329 · Dwukrotna różnica między korpusami to RÓŻNICA POPULACJI, nie dyscypliny — a osiem z pięćdziesięciu dziewięciu milczących ma jednostkę w nazwie

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `3bdc353`

6.D320 §3 zmierzyło, że klasa „milcząca" liczy **26 ze 188** w `src/` (14 %) i **59
z 209** w `tools/` (28 %), i zapisało tę dwukrotność jako miejsce, w którym siedzi
różnica między korpusami. Tamta pozycja żądała listy imiennej **tylko dla `src/`**.
Ta pozycja czyta pięćdziesiąt dziewięć z `tools/` — **czyta i klasyfikuje**, niczego
nie przemianowuje i żadnej bramki nie stawia.

Klasyfikator, cztery listy rdzeni i obie poprawki z 6.D320 §2 przeniesione **bez
zmian**; `znajdz` z `tree_walk.py` **pożyczony**, tak jak każe pole.

---

## 1. Kontrola przyrządu ZDANA co do jedynki

```
=== KONTROLA PRZYRZADU (6.D310) ===
   MIN_SECTION_HEIGHT_M     -> JEDNOSTKA W NAZWIE
   sagitta_m                -> JEDNOSTKA W NAZWIE
   SEARCH_CEILING_KMH       -> JEDNOSTKA W NAZWIE

=== SZESC LICZB ===
  src/    JEDNOSTKA W NAZWIE 148 | KONWENCJA DZIEDZINY  14 | MILCZACA  26 | SUMA 188
  tools/  JEDNOSTKA W NAZWIE 137 | KONWENCJA DZIEDZINY  13 | MILCZACA  59 | SUMA 209
```

Pole żądało **137 / 13 / 59** i tyle wyszło. Przewidywanie W1 trafione — i jest to
pierwsza kontrola przyrządu w tej sesji, która przechodzi co do jedynki, po czterech
kolejnych, które nie przeszły (6.D319, 6.D323, 6.D326, 6.D328).

**To, że przyrząd odtwarza swój własny wynik, nie znaczy jednak, że klasy mówią
prawdę.** §3 pokazuje, że nie mówią o dziewięciu nazwach z pięćdziesięciu dziewięciu.

## 2. GŁÓWNE ZNALEZISKO: dwukrotność jest własnością MIANOWNIKA, a nie dyscypliny

Pole ostrzegało, żeby nie przyjąć bez pomiaru, że dwukrotna różnica znaczy gorszą
dyscyplinę w `tools/`, i wskazywało na progi i tolerancje jako możliwe wytłumaczenie.
**Wytłumaczenie jest inne i prostsze: obie populacje nie zawierają tego samego.**

Rozbiłem populację `tools/` po ZASIĘGU nazwy — moduł czy ciało funkcji:

```
=== tools/ : 209 nazw wedlug ZASIEGU i KLASY ===
zasieg       JEDNOSTKA W NAZWIE    KONWENCJA DZIEDZINY   MILCZACA     SUMA
modul                       133                      3         25      161
funkcja                       4                     10         34       48
RAZEM                       137                     13         59      209
```

**Trzydzieści cztery z pięćdziesięciu dziewięciu milczących to zmienne LOKALNE
w funkcji**, a osiemnaście z nich to inicjalizacja akumulatora `= 0.0` (`suma`,
`worst`, `widest`, `najdluzsza`, `previous`, `rozpietosc`, `area2`, `station`, …).
Zmienna, która startuje od zera i bierze jednostkę od tego, co się do niej dodaje,
milczy z innego powodu niż stała.

Po stronie `src/` tego zjawiska nie ma prawie wcale. Zmierzyłem głębokość klamer
w tej samej populacji:

```
=== src/: populacja wedlug GLEBOKOSCI KLAMER ===
   cialo metody (glebokosc>=2)      8   (w tym MILCZACYCH 2)
   skladowa (glebokosc<=1)        227   (w tym MILCZACYCH 27)
MILCZACE z ciala metody w src/ (2): demand, t0
```

**Ta tabela liczy WYSTĄPIENIA, a 6.D320 liczyło NAZWY** — dlatego suma jest 235,
a nie 188. Mówię to zamiast podać samą liczbę, bo mianownik jest tu dokładnie tym,
o co chodzi. Dla nazw liczba milczących z ciała metody w `src/` wynosi **dwie**:
`demand` i `t0`.

Porównanie na populacjach, które zawierają to samo:

```
tools/, tylko poziom MODUŁU:      25 / 161 = 16 %
src/,   tylko poziom SKŁADOWEJ:   24 / 186 = 13 %
```

**Dwukrotna różnica (28 % wobec 14 %) znika: zostaje 16 % wobec 13 %.** Przyczyną
nie jest gorsza dyscyplina w `tools/`, tylko to, że po stronie Pythona przyrząd
łapie zmienne lokalne, a po stronie C# prawie nie — bo lokalne w C# pisze się
zwykle `var`, a mój wzorzec wymaga słowa `double`/`float`/`decimal`.

**Przewidywanie W6 jest OBALONE CO DO LITERY i spełniam warunek spisany przed
pomiarem.** W6 mówiło, że po odjęciu progów udział w `tools/` spadnie **poniżej
14 %**; spadł do 16 %, czyli nie spadł poniżej — i spadł z zupełnie innego powodu
niż progi. Mówię więc wprost, **co zostaje**: po zrównaniu populacji zostaje
różnica trzech punktów procentowych, 16 wobec 13, i tej różnicy nie tłumaczę
niczym — jest mniejsza niż wpływ dziewięciu błędów klasyfikatora z §3.

## 3. Klasyfikator myli się na DZIEWIĘCIU z pięćdziesięciu dziewięciu — trzeci raz na CZŁONIE NAZWY

Przewidywanie W4 trafione, i to ilościowo. **Osiem nazw ma jednostkę wypisaną
w nazwie**, a klasyfikator ich nie widzi, bo listy jednostek z 6.D320 nie zawierają
`mm`, `us` ani `px`:

| nazwa | jednostka w nazwie |
|---|---|
| `FORMULA_GUARD_MM`, `FORMULA_MAX_SLACK_MM` | milimetry |
| `PIXEL_BUDGET_LENS_MM`, `PIXEL_BUDGET_SENSOR_MM`, `SENSOR_MM` | milimetry |
| `PIXEL_BUDGET_TOLERANCE_PX` | piksele |
| `NIEMIERZALNY_US`, `ODRZUCONY_MIERZALNY_US` | mikrosekundy |

Dziewiąta, `area2`, wypada z innego powodu: rdzeń `area` **jest** na liście konwencji
dziedziny, ale rozbijacz nazw daje z `area2` jeden człon `area2`, a nie `["area","2"]`.
**To jest ten sam rodzaj usterki co obie poprawki z 6.D320 §2 i co jednoliterowy człon
z 6.D327** — klasyfikator myli się na CZŁONIE, nie na regule.

**Liczba 59 jest więc o dziewięć za duża**, a prawdziwa liczba milczących w `tools/`
wynosi **50**. Nie poprawiam przez to 6.D320: tamten raport zapisuje pomiar swoim
przyrządem i ten przyrząd odtwarzam co do jedynki (§1). Zapisuję poprawkę tutaj,
razem z listą imienną, żeby dało się ją sprawdzić bez czytania mojego kodu.

## 4. LISTA IMIENNA — trzy klasy z pola sumują się do 50, a nie do 59

Pole żądało trzech klas sumujących się do 59. **Nie sumują się do 59 i nie zmuszę
ich do tego** — dziewięć nazw z §3 do żadnej z trzech nie należy, bo jednostkę mają.
Podaję cztery liczby, z których trzy są klasami z pola:

```
  BEZWYMIAROWE                                    13
  JEDNOSTKA PRZEZ KONWENCJĘ DZIEDZINY             11
  MILCZĄCE NAPRAWDĘ                               26
                                                 ---
  SUMA TRZECH KLAS Z POLA                         50
  BŁĄD KLASYFIKATORA (jednostka JEST w nazwie)     9
                                                 ---
  RAZEM                                           59   ZGADZA SIĘ
```

**BEZWYMIAROWE (13)** — milczenie nie jest brakiem:

| nazwa | co to jest |
|---|---|
| `BACKFACE_LUMA`, `BACKGROUND_TOLERANCE` | luminancja i jej tolerancja, 0…1 |
| `LEVEL_DOT_LIMIT`, `UP_PARALLEL_EPS` | iloczyn skalarny |
| `M7_BODIES` | liczba członów składu (6) |
| `MIERZALNOSC_MIN` | stosunek CPU do ściany |
| `NIEMIERZALNY_ROZSTEP`, `NIEMIERZALNY_ROZSTEP_DRUGI`, `ODRZUCONY_MIERZALNY_ROZSTEP` | rozstęp w procentach |
| `t0` | parametr krzywej Catmull-Rom |
| `nx`, `ny`, `nz` | składowe normalnej Newella |

`t0` wpada tu **z tego samego powodu i pod tą samą nazwą co `t0` w `src/`** (6.D320
§5). Ta sama nazwa, dwa języki, jedna klasa — i żaden z dwóch przyrządów jej nie
rozpoznał sam.

**JEDNOSTKA PRZEZ KONWENCJĘ DZIEDZINY, której lista rdzeni NIE OBJĘŁA (11):**

| nazwa | konwencja |
|---|---|
| `G` | przyspieszenie ziemskie, m/s² |
| `a`, `a_brake` | `a` = przyspieszenie, m/s² |
| `s` | `s` = droga, m |
| `t` | `t` = czas, s |
| `v` | `v` = prędkość, m/s |
| `chord` | cięciwa — długość, m |
| `station`, `station_at` | `station` = chainage w terminologii kolejowej, m |
| `h` | przyrost współrzędnej geograficznej, stopnie |
| `worst_beta` | `β` = kąt, radiany |

**Siedem z jedenastu to JEDNOLITEROWE symbole fizyki.** Lista rdzeni 6.D320 nie ma
jak ich objąć: `a`, `s`, `t`, `v` są w `JEDN_KROTKIE` jako **jednostki**, a nie jako
**wielkości**, więc `a` jako nazwa zmiennej jest dla klasyfikatora „amperem na
ostatnim członie", tyle że przy jednym członie ta gałąź nie działa (`len(cz) > 1`).

**MILCZĄCE NAPRAWDĘ (26):**

| gdzie | nazwy |
|---|---|
| moduł (7) | `CONVEXITY_EPS` (m²), `TOLERANCE` (m), `VERTEX_EPS` (m), `INCYDENT_DOCKER_CPU`, `INCYDENT_DOCKER_SCIANA`, `KONTENER_11_09_CPU`, `KONTENER_11_09_SCIANA` (s) |
| funkcja (19) | `below`, `between`, `corner`, `krok`, `najdluzsza`, `pad`, `previous`, `rozpietosc`, `short`, `static`, `step`, `suma`, `threshold`, `value`, `widest`, `worst`, `z`, `z_rzedna` (m) oraz `slow` (m/s) |

**Dwie nazwy polskie są milczące dlatego, że lista rdzeni jest angielska:**
`rozpietosc` to `span`, a `z_rzedna` to `elevation` — oba rdzenie **są** na liście
6.D320, tylko po angielsku. To nie jest brak dyscypliny piszącego, to jest granica
klasyfikatora w projekcie pisanym w dwóch językach.

## 5. Drugie pytanie pola: ile milczących naprawdę to PROGI BRAMEK

Pole żądało tej liczby **także gdy zero**. Nie jest zero, ale jest mała, i zależy od
odczytu, więc podaję **oba**:

* **Odczyt wąski** — próg wewnątrz klasy „milczące naprawdę": **4 z 26**
  (`CONVEXITY_EPS`, `TOLERANCE`, `VERTEX_EPS`, `threshold`). Pozostałe **22** to
  wielkości fizyczne: długości, czasy, jedna prędkość.
* **Odczyt szeroki** — dowolna z 59, która jest własną liczbą jakiejś bramki,
  niezależnie od klasy: **21 z 59** (cztery wyżej plus `MIERZALNOSC_MIN`, trzy
  `*_ROZSTEP`, dwa `*_US`, cztery `INCYDENT_*`/`KONTENER_*`, `BACKGROUND_TOLERANCE`,
  `BACKFACE_LUMA`, `LEVEL_DOT_LIMIT`, `UP_PARALLEL_EPS`, `FORMULA_GUARD_MM`,
  `FORMULA_MAX_SLACK_MM`, `PIXEL_BUDGET_TOLERANCE_PX`).

**W żadnym z dwóch odczytów progi nie tłumaczą różnicy między korpusami** — bo
w odczycie wąskim jest ich cztery, a w szerokim większość i tak ma jednostkę
w nazwie albo jest bezwymiarowa. Tłumaczy ją mianownik z §2.

## 6. Przewidywania — dwa trafione, cztery obalone

| # | przewidywanie | wynik |
|---|---|---|
| W1 | kontrola odtworzy 137/13/59 co do jedynki | **trafione** (§1) |
| W2 | większość z 59 to progi i tolerancje | **OBALONE**: 4 z 26 wąsko, 21 z 59 szeroko (§5) |
| W3 | udział bezwymiarowych wśród 59 większy niż 54 % z `src/` | **OBALONE**: 13 z 50, czyli 26 % — ponad dwa razy MNIEJ |
| W4 | klasyfikator pomyli się co najmniej na jednej nazwie | **trafione**, na dziewięciu (§3) |
| W5 | wielkości fizycznych naprawdę milczących mniej niż dziesięć | **OBALONE**: 22 |
| W6 | po odjęciu progów udział w `tools/` spadnie poniżej 14 % | **OBALONE** co do litery: 16 %, i z innego powodu (§2) |

Cztery obalenia z sześciu. Trzy z nich (W2, W5, W6) wynikały z **jednego** błędnego
założenia, które zapisałem przed pomiarem: że milczące w `tools/` to przede wszystkim
progi bramek. Są przede wszystkim **zmiennymi lokalnymi w ciele funkcji**.

## 7. Czego świadomie nie zrobiłem

Nie przemianowałem ani jednej nazwy, nie dopisałem przyrostka, nie postawiłem bramki
na nazwach, nie tknąłem `docs/04-conventions.md`, `src/` ani `data/` — wszystko to
stoi w polu „Poza zakresem".

**Nie poprawiłem list jednostek w przyrządzie 6.D320 o `mm`, `us` i `px`**, mimo że
§3 pokazuje, że ich brakuje. Przyrząd tamtej pozycji jest w katalogu roboczym, a nie
w drzewie; poprawianie go tutaj dałoby liczbę, której nie da się porównać z żadną
zapisaną. Zapisuję brakujące jednostki imiennie, żeby następna pozycja z tej rodziny
zaczęła od nich, a nie od zera.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

`tools/physics/reference.py` pisze `v=s=t=0.0` i `a=min(decel,a+V["jerk"]*dt)`
w jednym wierszu, bez spacji wokół operatorów — jedyne takie miejsce w populacji.
Nie jest to usterka i nie pilnuje tego żadna bramka; zapisuję, bo przy czytaniu
pięćdziesięciu dziewięciu deklaracji rzuciło się w oczy jako jedyne odstępstwo
od reszty drzewa.
