# MB-05 — kabina wpięta, i jedna usterka złapana RACHUNKIEM, nie okiem

**14.09.2026**, na `d87f551`, gałąź `claude/mb05-kabina`. Wejście:
`tools/blender/m7_cab.py`, `m7_cab_build.py`, `src/Game/World/TrainView.cs`,
`FirstRun.PlaceEverything`, decyzja właściciela z 10.09.2026.

## 1. Dwa fakty startowe pozycji — sprawdzone, nie przyjęte

```
tools/blender/m7_cab.py        15949 B
tools/blender/m7_cab_build.py   3380 B
grep -rn 'M7_cab' --include=*.cs src/   -> ZERO trafień
```

Generator był zrobiony, scena o nim nie wiedziała. Zgadza się z opisem pozycji.

## 2. Co weszło

| plik | co |
|---|---|
| `src/Game/World/CabView.cs` | **nowy** — wczytanie brył i POLITYKA WIDOCZNOŚCI |
| `src/Game/World/TrainView.cs` | nowe `TrainLayout.PlaceWithRear` — ogon jako ARGUMENT |
| `src/Game/Scenes/FirstRun.tscn` | węzeł `Cab` **obok** `Train`, nie pod nim |
| `src/Game/FirstRun.cs` | wczytanie z odmową (`ExitCabMissing` = 14), ustawianie, widoczność |
| `tools/dev/prepare-playable.sh` | kabina w procesie generacji |
| `tools/release/package-playable.sh` | `M7_cab.glb` w paczce gracza |
| `tests/Game.Tests/CabPlacementTests.cs` | **nowy**, 6 metod, 15 asercji |

## 3. USTERKA, KTÓREJ NIE POKAZAŁA ŻADNA LICZBA W LOGU

Pierwsza wersja `CabView.PlaceAt` wołała `TrainLayout.Place` — tę samą metodę, co
skorupa. Wyglądało to na wybór najostrożniejszy z możliwych: jedna arytmetyka, zero
kopii. Było błędne.

`Place` liczy ogon jako **czoło − rozpiętość PRZEKAZANYCH BRYŁ**. Dla skorupy jest to
poprawne, bo skorupa JEST składem. Dla kabiny nie:

| zbiór | rozpiętość | dlaczego |
|---|---|---|
| skorupa M7 | **94,000 m** | to jest cały skład |
| kabiny | **93,300 m** | zaczynają się 0,35 m za czołem i kończą 0,35 m przed ogonem |

Przy czole na 2000,000 m:

```
szyba czołowa TERAZ      : 2000.350 m  (czyli  0.35 m od czoła)   <- PRZED czołem pudła
szyba czołowa POPRAWNIE  : 1999.650 m  (czyli -0.35 m od czoła)
przesunięcie             : 0.700 m
oko maszynisty           : 1998.200 m  (1.8 m za czołem)
```

**Kabina wystawała przodem przez czoło składu**, a oko maszynisty wypadało ZA OPARCIEM
FOTELA zamiast nad siedziskiem.

**Zdanie o szybie jest tu PRZEPISANE, a nie dopisane obok** (audyt 14.09.2026).
Poprzednia wersja mówiła, że „oko maszynisty zostawało ZA szybą zamiast przed nią",
i jest to **nieprawda wyprowadzona z tych samych liczb, co reszta akapitu**: usterka
przesuwa BRYŁY KABINY, a nie kamerę. Oko stawia `FirstRun.PlaceEverything` z kilometrażu
CZOŁA i stałej `DesignAssumptions.CabEyeSetbackM` = 1,80 m, więc przy czole na 2000,000 m
stoi na **1998,200 m w obu przypadkach** i nie rusza się ani o milimetr. Oko jest przez to
po TEJ SAMEJ stronie płaszczyzny szyby przed poprawką i po niej — zmienia się wyłącznie
odległość: **−1,450 m** poprawnie, **−2,150 m** z usterką.

Co usterka naprawdę robiła, widać na fotelu i na pulpicie:

| bryła kabiny wiodącej (lokalne X) | poprawnie | z usterką |
|---|---|---|
| siedzisko `cab_rear_seat_cushion` 92,10–92,55 | 1998,100–1998,550 m — **obejmuje oko** | 1998,800–1999,250 m |
| oparcie `cab_rear_seat_back` 92,00–92,10 | 1998,000–1998,100 m — **za okiem** | 1998,700–1998,800 m — **przed okiem** |
| pulpit `cab_rear_desk_body` 92,90–93,50 | bliższa krawędź **0,70 m przed okiem** | **1,40 m przed okiem** |

Maszynista siedział więc za oparciem własnego fotela, z pulpitem odsuniętym dwukrotnie.

**Dlaczego żadna liczba tego nie pokazała.** Wiersz `[KABINA]` podawał poprawną
rozpiętość. Wiersz `[SKŁAD]` poprawną długość. Porównanie telemetrii z rdzeniem przy
progu **0** wychodziło „identyczne co do bajtu" — bo kabina nie dotyka fizyki. Obie
liczby były poprawnymi rozpiętościami swoich zbiorów; błędne było zdanie, że jedna
z nich odpowiada na pytanie o drugą.

**Dlaczego nie pokazała tego też KLATKA. Ten akapit jest PRZEPISANY, a nie dopisany
obok** (audyt 14.09.2026). Poprzednia wersja wiązała brak ramy szyby z usterką („nie było
ramy szyby w ogóle, więc wyglądało to na kabinę bez okna, a nie na przesuniętą") — i ten
związek przyczynowy jest **fałszywy**. Ramy szyby nie ma w kadrze **ani przed poprawką,
ani po niej**, bo **kabina nie ma ramy szyby**: szesnaście brył z `M7_cab.json` to podłoga,
trzy części grodzi, pudło pulpitu, blat, siedzisko i oparcie — po osiem na koniec, zero
ścian i zero ram. Przesunięcie o 0,700 m nie mogło tego wywołać ani odwołać.

Klatka nie pokazała usterki z innego powodu: **w widoku kabinowym nie ma w kadrze ani
jednej bryły stojącej w układzie SKŁADU**. Skorupę chowa `FirstRun.ApplyView`
(`_train.Visible = view != ViewKind.Cab`), a jedyna pozostała geometria — tunel — nie
niesie żadnego znacznika, względem którego 0,700 m byłoby widoczne. „Pulpit dalej"
i „pulpit bliżej" to dwie klatki, z których żadna nie wygląda na błędną. Usterkę znalazł
rachunek z raportu generatora (`build/t400/M7_cab.json`), zestawiony z arytmetyką
`TrainLayout`.

**Poprawka:** `TrainLayout.PlaceWithRear` bierze ogon jako **argument**. Zbiór brył,
który nie jest całym składem, nie umie sam odpowiedzieć, gdzie skład się kończy.

## 4. Kabina nie zmienia fizyki ani telemetrii — przy progu ZERO

```
[PORÓWNANIE] wierszy=168 identyczne co do bajtu=TAK
[PORÓWNANIE] step         max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] chainage_m   max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] speed_mps    max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] próg = 0.000E+000
```

```
[SESJA] zaliczone (AllTargetsServed): 2/2 celów, 156.842 s, 1357.513 m, ATP 0/0/0 | 8742 obsłużony błąd -0.023 m | 8292 obsłużony błąd -0.387 m
```

Ten sam wiersz co do znaku co przy MB-02, MB-03 i MB-04.

## 5. Cztery klatki kontrolne z `render_check.py` — OBEJRZANE

Renderowane na **jednej** kabinie (`--end 0`), a nie na pliku z obiema, i to jest wynik
pierwszej próby: plik z obiema ma obwiednię **93,3 m**, więc kamera `_iso` kadruje całą
długość składu i każda kabina zajmuje w klatce kilkanaście pikseli. Obejrzałem najpierw
tamte i właśnie to na nich widać — dwa maleńkie skupiska brył na przeciwległych końcach
pustego kadru. Klatka, z której nie da się nic ocenić, nie jest weryfikacją.

| klatka | co widzę |
|---|---|
| `_iso` | płyta podłogi, wysoka ścianka grodzi z **prostokątnym otworem drzwiowym**, pudło pulpitu z blatem, siedzisko i oparcie. Osiem brył, zgodnie z wypisem generatora. Scena nie jest pusta, geometria nie jest zwinięta w punkt |
| `_side` | proporcje czytelne: podłoga jako cienka płyta, grodź od 1,09 do 3,14 m, pulpit do 2,04 m, oparcie do 2,12 m. Jednostki się zgadzają — przy pomyłce ×1000 nie byłoby czego oglądać |
| `_normals` | tło szare, trzy ciemnogranatowe prostokąty — to **tło świata** widziane przez otwór drzwiowy i obok krawędzi paneli, nie tylne ściany. `tylna_strona=0.00000`; wypis jest podłogą, nie oceną, i dlatego klatkę obejrzałem: **nie widzę odwróconych normalnych** |
| `_inside` | kamera stoi 1,4 m ZA bryłą (obwiednia 0,3–3,6 m, kamera na 5,0 m), bo `render_check.py` dobiera ją heurystyką osi tunelu i wypisuje `WARN no --centerline supplied; using bbox fallback`. Widać podłogę, nakładkę siatki i panele od tyłu. Klatka nie jest pusta, ale **dla zasobu kabiny mówi mniej niż dla tunelu** i jest to ograniczenie narzędzia, nie geometrii |

## 6. Prawdziwe klatki Godota

`--shot` wymaga `xvfb-run` i sterownika `opengl3`; pod samym `--headless` odmawia
nazwanym błędem (`[ZRZUT] --headless wyłącza renderer`), co jest zachowaniem poprawnym.

| klatka | co widzę |
|---|---|
| `MB05_cab_2000m` **przed poprawką** | pulpit nisko w kadrze, brak ramy szyby, tunel dokoła |
| `MB05_cab_2000m_po` **po poprawce** | pulpit szerszy i bliżej, zajmuje dolną trzecią część kadru; tor widoczny po obu jego stronach; HUD w całości czytelny **na** pulpicie |
| `MB05_cab_postoj` (kilometraż Beekkantu) | ta sama kompozycja co wyżej — pulpit **stoi nieruchomo względem kamery**, czyli kabina podąża za składem |
| `MB05_chase_2000m` | ośmiokątny tył pudła M7 w tunelu. **Kabiny nie widać ani śladu** — polityka widoczności działa w drugą stronę |

**Postój jest tu KILOMETRAŻEM, nie postojem, i tak to zapisuję.** `--shot` wymusza
przebieg skryptowy, więc HUD na tej klatce pokazuje **78,1 km/h**. Prawdziwej klatki
„na postoju, z otwartymi drzwiami" nie da się dziś zrobić — blokuje to ta sama otwarta
decyzja właściciela, którą zgłosiłem przy MB-03 (czy `--shot` ma działać w trybie
ręcznym). Nie obchodziłem tego.

## 7. Bramka i cztery kontrole negatywne — w tym TRZY, które wyszły ZIELONE

Najpierw napisałem trzy testy arytmetyczne na atrapach. Kontrole negatywne dały:

| KN | mutacja | czerwone |
|---|---|---|
| KN-1 | ogon liczony z rozpiętości kabiny | **0/292** |
| KN-2 | `_cabView.Visible = true` | **0/292** |
| KN-3 | `PlaceWithRear` przekierowane na `Place` | **0/292** |

**Zielona kontrola negatywna nie została załatana odruchem, tylko wyjaśniona pomiarem.**
Powód jest jeden i nie jest usterką tamtych testów: mutacje siedzą w `FirstRun.cs`
i `CabView.cs`, czyli w węzłach Godota, których `dotnet test` nie powoła. Testy
arytmetyczne sprawdzają RACHUNEK i robią to poprawnie — ale **miejsce wywołania jest
poza ich zasięgiem**, więc „arytmetyka się zgadza" i „scena jej używa" to dwa różne
zdania.

Odpowiedzią jest bramka **leksykalna**, ta sama droga co przy MB-03. Po jej dołożeniu:

| KN | mutacja | czerwone |
|---|---|---|
| KN-1 | ogon liczony z rozpiętości kabiny | 1/292 |
| KN-2 | `_cabView.Visible = true` | 1/292 |
| KN-3 | `PlaceWithRear` przekierowane na `Place` | 1/292 |
| KN-4 | wiersz `[KABINA]` usunięty z logu | 1/292 |

`md5sum -c: OK` po każdej z siedmiu.

### 7a. TA BRAMKA BYŁA TAUTOLOGICZNA I JEST PRZEPISANA, A NIE DOPISANA OBOK

Tabela wyżej zostaje w całości — cztery wymienione w niej mutacje naprawdę dawały
1/292. Nieprawdziwe było zdanie, które z niej wyprowadzałem: że bramka leksykalna
domyka to, czego testy arytmetyczne nie widzą. **Domykała cztery mutacje z listy,
którą sam napisałem, i przepuszczała cztery, których nie napisałem** — wszystkie
cztery dające tę samą usterkę 0,700 m, od której zaczęła się ta pozycja. Zmierzone
na kodzie sprzed audytu (`dotnet test tests/Game.Tests`):

| mutacja | stara bramka | nowa bramka |
|---|---|---|
| **W** `var trainLength = _train.LengthM` → `_cabView.LengthM` | `292/292` | **1 czerwony** |
| **X** `+ 0.7` w ciele `CabView.PlaceAt` | `292/292` | **1 czerwony** |
| **Y1** `+ 0.7` na wyniku wyrażenia w argumencie sceny | `292/292` | **1 czerwony** |
| **Z1** wywołanie owinięte w `if (…) { … }` | `292/292` | **1 czerwony** |
| **Z2** to samo `if` BEZ klamer (ta sama głębokość) | — | **1 czerwony** |
| **R** kontrola przyrządu: `+ 0.7` w samej `RearOfTrain` | — | **2 czerwone** |
| **T** tautologia: bryły kabiny na `(−999, −998)` | `1/1 przeszło` ✱ | **1 czerwony** ✱ |

✱ pod `--filter Ta_sama_wspolrzedna_X_daje_ten_sam_kilometraz_w_obu_zbiorach`. Bez
filtra ta sama podmiana dawała `290/292` — dwie inne metody ją łapały, więc
**tautologia siedziała w jednej metodzie, nie w całym pliku**, i to rozróżnienie jest
tu treścią: metoda liczyła OBIE strony równości tym samym wyrażeniem na tych samych
bryłach, więc porównywała liczbę ze sobą. `md5sum -c: OK` po każdej z siedmiu.

**Dlaczego stara bramka nie mogła tego złapać.** Pytała o PISOWNIĘ, a nie o treść:
`Assert.IsTrue(argumenty.Contains("trainLength"))` jest prawdą także dla
`chainage - trainLength + 0.7`, a `kod.Contains("TrainLayout.PlaceWithRear(")` jest
prawdą także dla `PlaceWithRear(axis, _bodies, rearChainageM + 0.7)`. Liczenie
WYSTĄPIEŃ tekstu daje przy tym jedynkę również wtedy, gdy całe wywołanie stoi
w martwym `if` — wywołanie, które nie wykona się nigdy, wygląda w wyszukiwaniu
tekstu dokładnie tak samo jak wykonywane co klatkę.

**Co weszło w zamian — poprawka jest w KODZIE, a nie w samej bramce.** Arytmetyka
ogona wyszła z wyrażenia wpisanego w argument wywołania do czystej funkcji
`TrainLayout.RearOfTrain(frontChainageM, trainLengthM)`, bo wyrażenia w argumencie
nie widzi żaden test. Bramka pyta odtąd o **rozbiór**, a nie o token: całą listę
argumentów znak w znak, głębokość klamer w miejscu wywołania i znak poprzedzający
(bo `if` bez klamer ma tę samą głębokość co poprawne wywołanie — stąd Z2 jako osobna
kontrola). Czytnik źródła maskuje komentarze i literały i **ma własną kontrolę
negatywną** na literale surowym `$$"""` z JSON-em pełnym klamer.

Metod testowych w pliku: **6 → 10**. Podniesione zapadki stoją odtąd na:
`ASERCJI_RAZEM` — 2924 (było 2902), `Z_KOMUNIKATEM_RAZEM` — 1475 (było 1453),
`PINY_GRY["CabPlacementTests.cs"]` — 6 (było 1), suma pinów gry — 58 (było 53),
`LICZBA_C` — 52 (było 47), rozkład liczbowych `tests/Game.Tests` — 229 (było 221),
postacie literału `zwykly` — 3996 (było 3912) i `werbatim (@)` — 55 (było 54).

**Dwie zapadki zeszły W DÓŁ i to jest poprawny kierunek, nie regresja:**
`MIN_GAME_NEEDLES` stoi na 87 (było 89), `MAX_GAME_UNMATCHED_NEEDLES` na 48
(było 50). Zniknęły dokładnie
te dwie igły, `trainLength` i `TrainLayout.PlaceWithRear(` — czyli **te dwie asercje,
które przepuszczały W, X i Y1**. Zastąpiły je porównania dokładne (`Assert.AreEqual`),
których `igly()` z definicji nie liczy, bo liczy wyłącznie `Contains`. Igieł jest
mniej, a bramka mocniejsza.

**Granica, która ZOSTAJE, i mówię to wprost.** Mutacja `LengthM = maxX - minX - 0.7`
w `TrainView.Load` daje tę samą szkodę 0,700 m i **przechodzi**: `Load` skanuje AABB
siatek Godota, więc `dotnet test` jej nie wykona, a żaden pin jej nie czyta. Nie
domykam tego w tym commicie, żeby liczby zapadek odpowiadały dokładnie kodowi, który
oddaję; pozycja dla pasma A.

## 8. CZEGO NIE ZROBIŁEM I PYTANIE DO WŁAŚCICIELA

**Kabina nie ma ścian — ani czołowej, ani bocznych. To jest zmierzone, nie wrażenie.**
Wypis szesnastu brył z `m7_cab_build.py` zawiera wyłącznie: podłogę, grodź tylną
(trzy części tworzące otwór drzwiowy), pudło pulpitu, blat, siedzisko i oparcie —
po osiem na każdy koniec.

**Zdanie o polu `openings` jest PRZEPISANE, a nie dopisane obok** (audyt 14.09.2026).
Poprzednia wersja mówiła, że pozycje `windscreen` i `cab_window` są „otworami
przeznaczonymi dla SKORUPY", i podawała to jako fakt zmierzony — a zmierzone nie było.
Sprawdzone: **skorupa ich NIE niesie**.

```
build/t400/M7_shell.json  openings=38
  opening_summary: double_total=36, double_per_side=18, cab_total=2
  kind `cab` = drzwi maszynisty w BOKU pudła, 0,80 x 1,87 m, center_x 2,9 i 91,1
  ani jednej pozycji kind `windscreen` ani `cab_window`
grep -c windscreen tools/blender/m7_shell.py   -> 0
grep -c cab_window tools/blender/m7_shell.py   -> 0
czoła skorupy w M7_shell.glb: po 4 trójkąty na x=0 i x=94, 6 wierzchołków,
  cały przekrój 0,95-3,30 m - ZASLEPIONE n-gonem, bez otworu czołowego
```

Sześć pozycji `windscreen`/`cab_window` z `M7_cab.json` jest więc na dziś **zdaniem
INTENCJI, a nie opisem czyjejkolwiek geometrii** — i mówi to wprost docstring
`m7_cab.py::openings`: „Wycięcie otworu w skorupie należy do generatora skorupy
(`m7_shell.py`), którego ta pozycja nie zmienia […] a nie żeby udawać, że kabina ma
szyby". Nie wycina ich ani kabina, ani skorupa. To zmienia drogę 1 z listy niżej
i jest w niej zapisane.

Skutek: `FirstRun.ApplyView` chowa skorupę w widoku kabinowym (bo z jej wnętrza
widać drugą stronę ścianek), więc razem ze skorupą znikają **ściany** — ramy szyby nie
ma zaś po żadnej ze stron i nigdy nie było. Maszynista ma podłogę, pulpit i fotel,
a tam, gdzie powinny być ściany, widzi tunel.

**Odległość do grodzi jest PRZEPISANA, a nie dopisana obok.** Poprzednia wersja mówiła
„grodź 3,5 m za plecami" i była to **długość kabiny podana jako odstęp**: kabina ma
3,600 m deklarowane w `cab_length_m` (3,250 m rozpiętości brył), a grodź stoi dwa razy
bliżej. Zmierzone na kabinie wiodącej, lokalne X: lico grodzi **90,48**, oko **92,20**,
tylna krawędź oparcia **92,00** — czyli **1,720 m od oka** i **1,520 m od pleców**.

**Nie rozstrzygam tego sam i nie „poprawiam przy okazji", bo to jest decyzja
projektowa, której nie ma w żadnym dokumencie** (`CLAUDE.md` §8). Widzę dwie drogi
i obie wychodzą poza pole „Wyjście" tej pozycji:

1. **Przestać chować skorupę w widoku kabinowym** — wtedy ściany i otwory szyby są
   skorupy, a kabina dokłada wnętrze. Wymaga sprawdzenia, czy skorupa naprawdę niesie
   otwory z listy `openings`, i zmiany zachowania, które stoi od T-400.
2. **Dołożyć kabinie ściany** — zmiana w `m7_cab.py`, czyli w generatorze, a nie
   w scenie.

Do czasu rozstrzygnięcia wnętrze **jest widoczne, podąża za składem i nie znika razem
ze skorupą** — czyli pole „Skończone, gdy" tej pozycji jest spełnione co do litery.

Poza tym nie zrobiłem: rekonstrukcji pulpitu M7, dekoracji, tekstur i logo (pole
„Poza zakresem").

## 8.1 `--cab` było NIEOSIĄGALNE i jest to moja własna usterka z tej pozycji

`FirstRun.BuildWorld` czyta `Argument("cab")`, ale `"cab"` nie weszło do
`RunPlan.KnownArguments` — a plan odrzuca argument spoza tej listy komunikatem
„nieznany argument". Nadpisanie ścieżki kabiny było więc **nieosiągalne**: jedyną drogą
do innej bryły było podmienienie pliku na dysku.

Żaden test tego nie widział i nie mógł: cała rodzina testów `RunPlan` chodzi w pętli
po `KnownArguments`, więc argument, którego tam nie ma, po prostu nie istnieje dla
bramki. Znalazłem to dopiero czytając tę listę przy MB-07, przy zupełnie innym pytaniu.

Poprawka stoi w TEJ pozycji, a nie w następnej, bo usterka jest jej — `"cab"` dopisane
przy `"shell"` i `"platforms"`, czyli przy dwóch argumentach tej samej rodziny
(ścieżka do bryły wczytywanej przez scenę, bez żadnego towarzysza).

**Że to naprawdę działa, jest zmierzone dwoma przebiegami tej samej sceny:**

```
--cab=…/M7_cab_end0.glb   [KABINA] brył=8  rozpiętość=3.250 m  …
bez --cab (domyślny plik)  [KABINA] brył=16 rozpiętość=93.300 m …
```

Osiem brył wobec szesnastu i 3,250 m wobec 93,300 m — argument wybiera plik, a nie jest
przyjmowany i ignorowany.

**Bramka to potwierdziła liczbą, a nie moim słowem:**
`EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds` liczy argumenty SAMOTNE
(przyjmowane bez towarzysza) i ruszyła **17 → 18**. Gdyby `--cab` wymagało czegokolwiek
innego, wpadłoby do drugiej rodziny i ta liczba by nie drgnęła.

## 9. Co zauważyłem po drodze, ale zostawiłem

- **Kotwice pinów w `test_csharp_pins.py` przesunęły się TRZECI RAZ Z RZĘDU o ten sam
  trzywierszowy komentarz** (MB-02, MB-04, MB-05). Kotwica po numerze wiersza płaci ten
  koszt przy każdej edycji powyżej siebie. Zamiana jej na kotwicę po TREŚCI jest pozycją
  do kolejki — przy aktywnym kamieniu milowym pobocznego znaleziska się nie bierze.
- **Komunikat bramki `test_kazdy_pin_ma_kategorie_i_suma_sie_zgadza` mówił liczbę
  o pięć mniejszą niż jego własna asercja** („nie sumują się do 47" przy warunku na 52).
  Poprawione w tym commicie, bo dotykałem tej samej linijki — kto by na ten komunikat
  trafił, szukałby rozbieżności, której nie ma.
- `render_check.py` dobiera kamerę `_inside` heurystyką osi tunelu i dla zasobu
  wnętrza daje klatkę o małej wartości. Pozycja dla pasma A.
- **Kotwice pinów przesunęły się w tym commicie DWA RAZY** — raz o trzy wiersze
  (komentarz z powodem), raz o JEDEN (jednowierszowy komentarz przy poprawce `--cab`).
  Czwarty ruch tej samej kotwicy w ciągu doby. Kotwica po numerze wiersza płaci ten
  koszt przy każdej edycji powyżej siebie, także jednolinijkowej.
- `RunPlan.PathArguments` **nie zawiera** `--shell` ani `--platforms`, choć obie są
  ścieżkami. Nie tknąłem: lista pilnuje, dla których argumentów pusta wartość jest
  błędem, i jej zakres jest osobnym pytaniem. Pozycja dla pasma A.
- **Droga 1 z §8 („przestać chować skorupę") stoi na przesłance, która padła przy
  audycie 14.09.2026, i jest przez to DROŻSZA, niż ją opisałem.** Zapisałem ją jako
  „wtedy ściany i otwory szyby są skorupy" z zastrzeżeniem „wymaga sprawdzenia, czy
  skorupa naprawdę niesie otwory z listy `openings`" — sprawdzenie zostało wykonane
  i wyszło NEGATYWNIE: `M7_shell.json` ma 38 otworów, wszystkie drzwiowe (36 `double`
  + 2 `cab`), `grep` na `windscreen` i `cab_window` w `m7_shell.py` daje zero, a czoła
  skorupy są zaślepione (po 4 trójkąty na x=0 i x=94). Samo odsłonięcie skorupy dałoby
  więc maszyniście widok w GŁUCHĄ ścianę czołową zamiast w tunel, czyli stan gorszy od
  dzisiejszego; droga 1 wymaga TAKŻE wycięcia otworów w `m7_shell.py`, a to jest zmiana
  generatora — dokładnie tak samo jak droga 2. Nie tknąłem: to nadal ta sama decyzja
  właściciela, tylko z poprawioną ceną.
