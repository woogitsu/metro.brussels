# 6.D320 · Sześć liczb — a klasa „milcząca" spadła ze 157 do 26 przez DWIE usterki mojego przyrządu

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `15ce9bf`

6.D310 §4 zmierzyło, że siedem z ośmiu wypadków, w których jednostka w ogóle pada przy
tolerancji względnej, to **identyfikator**, a w komentarzu nie pada ani razu. Ta pozycja
pyta, jak to wygląda na całym `src/` i całym `tools/`. **Liczy, nie ocenia** — niczego
nie przemianowuje i żadnej bramki nie stawia.

Sześć liczb stoi w §3. Ale wynik, dla którego warto było tę pozycję wziąć, jest inny:
**klasa „milcząca" w `src/` spadła ze 157 do 26 po dwóch poprawkach przyrządu — i obie
poprawki znalazło ostrzeżenie zapisane w polu, zanim cokolwiek policzyłem.**

---

## 1. K0 — jednostki PRZECZYTANE, i pole myli się co do formy zapisu

Pole „Wejście" żąda przeczytania „tabeli jednostek" z `docs/04-conventions.md`,
wprost zastrzegając: **nie zgadnięcia**. Przeczytałem — i **tabeli tam nie ma**:

```
K0: wierszy tabeli w docs/04-conventions.md: 0
```

Cały zapis jednostek to **dwa punkty listy** (wiersze 3–4): jednostka sceny = metr,
prędkość m/s, masa kg, czas s, pochylenie %. Pięć jednostek, dwa wiersze, zero tabel.

Zapisuję ten rozjazd, zamiast go przemilczeć, bo **jest tego samego rodzaju co
niespełnialna kontrola z 6.D317**: pole opisuje wejście kształtem, którego wejście nie
ma. Gdybym zaufał polu zamiast przeczytać, szukałbym tabeli i albo bym jej nie znalazł,
albo — gorzej — dopisał brakujące jednostki z głowy. **Reguła wymiarowości w tej pozycji
stoi więc na tych pięciu jednostkach, a nie na żadnej tabeli.**

## 2. DWIE USTERKI MOJEGO PRZYRZĄDU, obie przewidziane przez pole

Pole ostrzega: klasa „milcząca", która nie odróżnia wielkości wymiarowej od
bezwymiarowej, **policzy przede wszystkim bezwymiarowe i wyjdzie z liczbą bez treści**.
Wyszła dokładnie taka i mówię to zamiast poprawić po cichu.

**Przebieg pierwszy — 157 milczących w `src/`.** W klasie stały metody (`Clamp`, `Dot`,
`Compare`, `ApplyNeutralMaterial`) i **kody wyjścia** (`ExitCabMissing`,
`ExitMissingAssets`, jedenaście sztuk). Żadne z tego nie jest nazwą wielkości.
Przyczyna: mój wzorzec łapał deklaracje z nawiasem (czyli metody) i typy całkowite
(czyli liczniki i kody).

**Poprawka pierwsza** — tylko `double`/`float`/`decimal`, bez metod: **157 → 59**.

**Przebieg drugi — 59, i wśród nich `_brakeWorkJ`, `_emergencyBrakeMps2`,
`_entryChainageM`, `_jerkMps3`, `_topSpeedMps`.** Te nazwy **mają jednostkę w nazwie**,
a klasyfikator ich nie widział. Przyczyna jest w `docs/04-conventions.md`, czyli w tym
samym dokumencie, który pole kazało przeczytać: **`_camelCase` to konwencja prywatnego
pola C#**, a mój rozbijacz nazw brał wiodący znak `_` za separator `snake_case`
i zwracał jeden człon `brakeworkj` zamiast `["brake","work","j"]`.

**Poprawka druga** — zdjęcie wiodących `_` przed wyborem sposobu rozbicia: **59 → 26**.

**To jest TRZECI raz w tej rodzinie pozycji, gdy klasyfikator myli się na CZŁONIE
NAZWY.** 6.D310 i 6.D312 miały błąd przedrostka, 6.D317 wciągnęło trzy nazwy angielskie
do klasy polskiej przez przedrostki `Minimum` i `Plan`. Tam były to pojedyncze nazwy;
tutaj człon zdecydował o **sto trzydziestu jeden** z nich.

## 3. SZEŚĆ LICZB, których żądało pole

Populacja: nazwy wielkości **zmiennoprzecinkowych** — w `src/` deklaracje `double`,
`float`, `decimal` poza metodami, w `tools/` nazwy przypisane literałowi `float`.
Wielkości bezwymiarowe z nazwy (`count`, `ratio`, `index`, `id`, …) do populacji
**nie wchodzą**, bo pole ostrzega, że inaczej liczba nie ma treści.

```
  src/    JEDNOSTKA W NAZWIE 148 | KONWENCJA DZIEDZINY  14 | MILCZACA  26 | SUMA 188
  tools/  JEDNOSTKA W NAZWIE 137 | KONWENCJA DZIEDZINY  13 | MILCZACA  59 | SUMA 209
```

**Jednostka w nazwie jest w `src/` normą, a nie wyjątkiem: 148 ze 188, czyli 79 %.**
W `tools/` jest nią tak samo — 137 z 209, czyli 66 %. Konwencja, o której mówi tytuł
pozycji, jest więc **realnie stosowana po obu stronach drzewa**, mimo że nie pilnuje
jej żadna bramka. To jest odpowiedź mocniejsza niż sama liczba: konwencja bez bramki
nie jest tu konwencją martwą.

**Różnica między korpusami siedzi w klasie MILCZĄCEJ, nie w klasie z jednostką:**
26 na 188 w `src/` (14 %) wobec 59 na 209 w `tools/` (28 %) — dwukrotnie.

## 4. Kontrola przyrządu — ZDANA dla wszystkich trzech nazw

```
   MIN_SECTION_HEIGHT_M     -> JEDNOSTKA W NAZWIE
   sagitta_m                -> JEDNOSTKA W NAZWIE
   SEARCH_CEILING_KMH       -> JEDNOSTKA W NAZWIE
```

Trzy z siedmiu wypadków zmierzonych przy 6.D310, i wszystkie trzy w klasie, której
żądało pole — także **przed** obiema poprawkami z §2, co znaczy, że poprawki nie
zostały dobrane pod kontrolę.

## 5. LISTA IMIENNA MILCZĄCYCH z `src/` — 26 nazw, PRZECZYTANYCH, nie sklasyfikowanych automatem

Przy dwudziestu sześciu pozycjach reguła przedrostkowa jest droższa niż czytanie
(lekcja 6.D317). Przeczytałem deklarację każdej z nich i ich użycie.

**BEZWYMIAROWE — milczenie NIE jest brakiem (14):**

| nazwa | co to jest |
|---|---|
| `Adhesion`, `DesignAdhesionDry`, `DesignAdhesionWet` | współczynnik przyczepności |
| `DesignSurfaceResistanceMultiplier`, `DesignTunnelResistanceMultiplier`, `_surfaceMultiplier`, `_tunnelMultiplier` | mnożniki oporu |
| `EffectiveThrottle` | nastawa 0…1 |
| `RelativeResidual` | reszta **względna**, nazwa mówi to wprost |
| `ColinearSine` | sinus |
| `DesignAw2Passengers` | liczba pasażerów |
| `MeanWaiting` | „średnia liczba składów czekających" — z komentarza przy deklaracji |
| `t0` | parametr krzywej Catmull-Rom |
| `heading` | **znak kierunku**, nie kąt — komentarz mówi „mniejsze od zera znaczy jazdę w stronę malejącego chainage" |

**`heading` jest tu najważniejsze i dlatego stoi w tabeli, a nie w przypisie.** Moja
lista rdzeni konwencji dziedziny wciągnęłaby je jako kąt — nazwa mówi „kurs". Kod mówi
co innego: to mnożnik ±1. **Czytanie pobiło klasyfikowanie na dokładnie tej nazwie,
na której automat był najpewniejszy.**

**JEDNOSTKA PRZEZ KONWENCJĘ DZIEDZINY, której moja lista NIE OBJĘŁA (5):**

`DesignDavisB`, `DesignDavisC`, `_a`, `_b`, `_c` — współczynniki równania Davisa.
Ich jednostki (`N`, `N·s/m`, `N·s²/m²`) są ustalone przez **samo równanie**, a nazwy
biorą się z nazwiska i z pozycji w wzorze. Jest to konwencja dziedziny w najczystszej
postaci — i moja zamknięta lista rdzeni (`chainage`, `speed`, `radius`, …) jej nie
objęła, bo szukała **nazw wielkości**, a nie **nazw miejsc we wzorze**.

**MILCZĄCE NAPRAWDĘ — wymiarowe i bez jednostki w nazwie (7):**

| nazwa | plik | jednostka wyczytana z użycia |
|---|---|---|
| `Jitter` | `src/Game/RunPlan.cs` | s — „nierówność czasów klatek" |
| `_jitter` | `src/Game/FirstRun.cs` | s |
| `JitterFrequency` | `src/Game/RunPlan.cs` | Hz |
| `_carry` | `src/Sim/Physics/StepAccumulator.cs` | s — reszta kroku |
| `_start` | `src/Sim/Train/LineDrive.cs` | m — przypisane z `_stations[0].ChainageM` |
| `_trigger` | `src/Sim/Train/LineDrive.cs` | m/s² — iloczyn ułamka i `ServiceBrakeMps2` |
| `demand` | `src/Sim/Signalling/TrainProtection.cs` | m/s² — żądanie hamowania |

**`_trigger` jest z tych siedmiu najciekawsze:** nazwa nie mówi nic o wielkości,
a wartość jest **przyspieszeniem**, i widać to dopiero w wierszu przypisania, dwie
setki wierszy dalej niż deklaracja.

## 6. ODPOWIEDŹ NA PYTANIE, KTÓRE POLE KAZAŁO ZADAĆ WPROST

Pole żąda powiedzieć, ile z milczących niesie jednostkę przez konwencję dziedziny,
i dopuszcza odpowiedź „wszystkie", bo wtedy milczenie nie jest brakiem.

**Nie brzmi „wszystkie". Z dwudziestu sześciu: 14 bezwymiarowych, 5 z konwencji
dziedziny, 7 milczących naprawdę.** Milczenie jest brakiem w **siedmiu** wypadkach
na 188 nazw `src/`, czyli w **3,7 %**.

**Nie znaczy to, że jest usterką** — pole zabrania tego wniosku i ma rację: `_start`
przypisane z `ChainageM` jest w metrach dla każdego, kto przeczyta następny wiersz.
Liczę, nie oceniam.

## 7. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| R1 | kontrola przyrządu przejdzie za pierwszym razem dla trzech nazw | trafione |
| R2 | w `src/` „jednostka w nazwie" będzie większością | trafione — 148 ze 188, 79 % |
| R3 | w `tools/` będzie **odwrotnie** | **OBALONE** — tam też większość, 66 % |
| R4 | milczących w `src/` mniej niż 20 | **OBALONE** — 26, więc rozbiłem klasę (§5) |
| R5 | odpowiedź nie brzmi „wszystkie" | trafione |
| R6 | moja lista rdzeni konwencji dziedziny okaże się niewyczerpująca | trafione — współczynniki Davisa |
| R7 | populacje `src/` i `tools/` różnią się co najmniej trzykrotnie | **OBALONE** — 188 wobec 209, czyli 1,11× |

**R3 i R7 obalone razem mówią jedno:** spodziewałem się, że `tools/` i `src/` to dwa
różne światy nazewnicze i dwie różne skale. Nie są. Populacje różnią się o jedenaście
procent, a rozkład klas jest w obu **ten sam co do kształtu** — jednostka w nazwie
dominuje, konwencja dziedziny jest marginesem, milczące są resztą. Przewidywanie
o różnicy było przewidywaniem o **moim wyobrażeniu o tych katalogach**, nie o nich.

**R1 zapisuję jako trafione, ale odnotowuję, co to znaczy:** kontrola przeszła także
przed obiema poprawkami z §2, więc **nie odróżniła przyrządu poprawnego od przyrządu
z usterką na stu trzydziestu jeden nazwach**. Kontrola żądana przez pole sprawdza trzy
nazwy i te trzy były w porządku przez cały czas.

## 8. Czego świadomie nie zrobiono

- **Nie przemianowano niczego i nie dopisano ani jednego przyrostka** — pole nazywa to
  decyzją właściciela, dotyczącą kodu w `src/`.
- **Nie postawiono bramki na nazwach.** §3 pokazuje, dlaczego byłaby przedwczesna:
  konwencja jest stosowana w 79 % bez żadnej bramki, a klasa milcząca to 3,7 % nazw.
- **Nie zmieniono `docs/04-conventions.md`**, mimo że §1 pokazuje rozjazd między polem
  a formą zapisu jednostek — pole zabrania wprost.
- **Nie uznano żadnej z siedmiu milczących za usterkę.**
- **Nie rozstrzygnięto jednostek pięciu współczynników Davisa** ponad to, co mówi
  równanie — nie ma tego w `docs/`, a zgadywanie byłoby wymyślaniem danych.
- **Nie tknięto `src/`, `data/` ani `docs/`.**

## 9. Zauważone przy okazji, nietknięte

1. **Kody wyjścia w `src/Game/FirstRun.cs` to jedenaście stałych całkowitych
   o wspólnym przedrostku `Exit`** — z punktu widzenia każdego skanu po nazwie
   zachowują się jak jedna rodzina i zaśmiecają każdą klasę, która nie odsiewa
   typów całkowitych. Zauważone, bo to one dały największy pojedynczy wkład do
   fałszywych 157 z §2.
2. **`docs/04-conventions.md` nie wymienia `J`, `N`, `W`, `Hz` ani `%` obok metra
   i kilograma**, a wszystkie cztery padają w nazwach `src/` jako przyrostki
   (`_brakeWorkJ`, `_startupForceN`, `_installedPowerW`, `JitterFrequency`).
   Konwencja jest więc **szersza niż jej zapis** — i nikt tego nigdzie nie odnotował.
3. **W `tools/` milczących jest dwa razy więcej niż w `src/`** (28 % wobec 14 %).
   Czym są, ta pozycja nie pyta — żądała listy imiennej tylko dla `src/`.
