# T-313 — klasyczna sygnalizacja 2026

Tryb historyczny na **31.08.2026**: bloki stałe, movement authority, minimalne ryglowanie
tras i ochrona pociągu. Ten dokument opisuje, **co jest faktem, co jest modelem i gdzie
przebiega granica** między jednym a drugim.

Ground truth: [`docs/10-signalling-ground-truth.md`](10-signalling-ground-truth.md),
maszynowo `data/signalling/ground-truth.json`.
Konfiguracja bloków: `data/design/signalling/classic-2026.json`.
Kod: `src/Sim/Signalling/`.

---

## 1. Jednym zdaniem

Model odwzorowuje **zasadę** bloków stałych, którą STIB opisuje publicznie, i **nie
odwzorowuje** ani jednego szczegółu, którego STIB nie opisuje — granice bloków, aspekty
sygnałów, logika nastawni, krzywe bezpieczeństwa i protokół KCV pozostają poza modelem
albo są jawnie oznaczone jako `design_model`.

## 2. Co jest source-backed

Z `data/signalling/ground-truth.json` do T-313 wchodzą cztery fakty i nic ponadto:

| fakt | id w ground truth | co z niego wynika w kodzie |
|---|---|---|
| system działa na blokach stałych, maks. jeden pociąg w strefie | `legacy_fixed_blocks` | `Block`, `FixedBlockSystem` — jeden `_occupant` na blok |
| strefy formują obwody torowe | `legacy_track_circuits` | zajętość jest własnością **odcinka**, nie punktu |
| system automatycznie spowalnia skład przy naruszeniu odstępu | `legacy_automatic_speed_protection` | `TrainProtection` ingeruje sam, bez maszynisty |
| KCV istnieje na liniach 2/6 i ma trzy wymienione funkcje | `kcv_lines_2_6`, `kcv_confirmed_functions_lines_2_6` | `ProtectionVariant.LegacyWithKcv`, `KcvFunction` |

Pakiet A to **linia 1**, więc plan `classic-2026.json` deklaruje
`protection_variant: legacy_fixed_block` i `TrainProtection.RequireKcv()` na nim rzuca
wyjątkiem. Przypisanie KCV linii 1 byłoby wymyśleniem faktu o sieci.

## 3. Co jest `design_model` — pełna lista z liczbami

Wszystko poniżej mieszka w `data/design/signalling/classic-2026.json`, w polach
z jawnym `status`, i jest wymienione w `SignallingPlan.Assumptions`.

| parametr | wartość dla pakietu A | dlaczego nie jest faktem |
|---|---|---|
| granice i długości bloków | **23 bloki** na 6734,0 m: 12 peronowych, 11 szlakowych | „exact fixed-block boundaries and lengths" jest w `unknown_parameters` |
| długość bloku peronowego | **94,0 m** | liczba ma źródło (`parameters.length_m`, `spec`), ale decyzja „blok peronowy = jeden skład" źródła nie ma |
| podział na szlaku | jeden blok na międzystacje: **220,93–1125,01 m**, mediana **497,47 m** | STIB nie publikuje żadnego planu podziału |
| prędkość dopuszczalna | **72 km/h** | `reports/R-006-line-speed.md`: żaden dokument STIB nie podaje prędkości na torze |
| zapas za końcem authority | **0,0 m** | overlapu nie ma w żadnym źródle; zero znaczy „model nie wymyśla zapasu" |
| konflikt tras | wspólny blok | „station-specific route-locking/interlocking logic" jest w `unknown_parameters` |
| czas reakcji urządzeń | **0 s** | „device reaction times" jest w `unknown_parameters`; zerowa zwłoka jest widoczna, zmyślone 0,4 s wyglądałoby jak zmierzone |

Czego w pliku **nie ma i nie będzie bez źródła**: aspektów sygnałów, ich rozmieszczenia,
telegramów, balis, częstotliwości, krzywych ATP producenta, procedur degraded mode.

## 4. Reguła podziału na bloki

Plik `classic-2026.json` nie jest napisany ręcznie — jest **wynikiem reguły**, którą
wykonuje `SignallingPlan.FromAxis`:

1. każda stacja osi dostaje blok peronowy długości jednego składu M7, wyśrodkowany na
   jej kilometrażu (przycięty od dołu do początku osi);
2. między dwoma kolejnymi peronami leży dokładnie jeden blok szlakowy;
3. plan sięga od 0 do dalszego z dwóch końców: długości osi albo końca ostatniego bloku
   peronowego;
4. trasa prowadzi peron → szlak → następny peron, więc dwie kolejne trasy dzielą blok
   peronowy i przez to są w konflikcie.

Dzięki temu jedyną liczbą spoza danych jest **sama reguła**: kilometraże stacji pochodzą
z `data/track/L1_A.json`, a długość składu z rejestru M7. Test
`Plik_planu_jest_dokladnie_tym_co_daje_regula_generowania` przypina plik do reguły —
i jest **jedynym** miejscem, które trzeba usunąć, gdy pojawi się plan z prawdziwym
źródłem. Kod nie zna ani jednej granicy bloku.

### Kontrola sensowności, którą plan przechodzi

Droga hamowania służbowego z 72 km/h wynosi przy krzywej z T-311 **196,39 m**.
Najkrótszy blok szlakowy pakietu A ma **220,93 m** (S10, Maelbeek–Schuman), czyli
o 24,54 m więcej. Skład, który wjechał do bloku poprzedzającego zajęty, ma się więc gdzie
zatrzymać. Pilnuje tego test
`Najkrotszy_blok_szlakowy_miesci_droge_hamowania_z_predkosci_planu`; zmiana prędkości
planu albo podziału na bloki bez sprawdzenia tego warunku go wywróci.

Bloki peronowe (94 m) tego warunku **nie spełniają i nie mają spełniać** — prędkość
dopuszczalna przy authority równym blokowi peronowemu wychodzi z krzywej i wynosi
33,86 km/h, a nie 72.

## 5. Movement authority

`MovementAuthority` odpowiada na pytanie „dokąd wolno jechać i dlaczego nie dalej".
Wyznaczenie jest jednym przebiegiem po blokach w przód od bloku, **który skład zajmuje**:

| przerwanie | `AuthorityLimit` |
|---|---|
| blok zajęty przez inny skład | `OccupiedBlock` |
| blok zarezerwowany pod cudzą trasę | `ReservedByOtherRoute` |
| plan wymaga trasy, a blok do trasy tego składu nie należy | `BlockNotReserved` |
| skończyły się bloki | `EndOfLine` |

Koniec authority leży na **granicy ostatniego bloku, który przeszedł kontrolę**,
pomniejszonej o `authority_margin_m` (dla pakietu A: zero).

Blok czoła liczy się po zajętości, nie po samym punkcie. Przy półotwartej konwencji
`[Start, End)` chainage dokładnie na granicy należy już do bloku następnego — którego
skład jeszcze nie zajmuje. Bez tej poprawki skład stojący czołem na granicy bloku zajętego
dostawałby authority **przez** ten blok.

### Prędkość dopuszczalna: jedna krzywa, nie dwie

Zasada 4 z zadania: ATP nie ma własnej fizyki. `TrainProtection.PermittedSpeedMps`
odwraca `BrakingPointSolver` z T-311 — ten sam obiekt, którym prowadzi się skład
w `LineRun`. Odwrócenie idzie bisekcją o **stałej** liczbie 64 kroków, z tego samego
powodu, dla którego solver ma stałe 200: pętla „aż się zbiegnie" nie jest deterministyczna.

| authority | prędkość dopuszczalna |
|---:|---:|
| 47,00 m (blok peronowy) | 33,86 km/h |
| 100,00 m | 50,60 km/h |
| 250,00 m | 72,00 km/h (limit planu) |

### Progi ingerencji są policzone, nie przyjęte

Nie ma marginesu ostrzegania, bo nie ma dla niego źródła. Zamiast tego dwa progi
wynikające z krzywej:

1. **prędkość ponad dopuszczalną** → `OverspeedWarning` + `ServiceIntervention`; ATP żąda
   dokładnie tego opóźnienia, którego wymaga pozostała droga;
2. **hamulec służbowy już nie wystarcza** (albo authority jest wyczerpane, a skład jedzie)
   → `EmergencyIntervention`.

Hamowanie awaryjne jako *polecenie maszynisty* w tym repo nie istnieje —
`DriverCommand.Brake = 1` to pełny hamulec **służbowy**. `ProtectionDecision` niesie
żądane opóźnienie liczbą, a `BrakeCommandFraction` obcina je do możliwości polecenia.
Obcięcie jest poprawne, ale samo w sobie zamiatałoby przekroczenie: żądanie 2,00 m/s²
i żądanie 1,10 m/s² dają ten sam nastawnik. Dlatego różnicę pokazuje osobno
`DemandExceedsServiceBrake` — jest widoczna, a nie zamieciona.

### ATP naprawdę hamuje — decyzja właściciela z 04.09.2026

Do tego dnia progi powyżej były **liczone i nie stosowane**. `TrainProtection.Supervise`
zwracało decyzję, a jedyne jego wołanie stało w HUD-zie sceny i było tam wprost opisane
jako „odczyt, nie ingerencja": czy ATP ma hamować za maszynistę, było decyzją o rozgrywce,
a nie usterką. Decyzja zapadła — **„ostrzeżenie, potem hamulec służbowy"** — i ochrona
jest teraz w rdzeniu.

Trzy poziomy, dokładnie te z `ProtectionAction`:

| reakcja | co dostaje pojazd |
|---|---|
| `None` | polecenie maszynisty **bez zmiany**; samo przekroczenie jest ostrzeżeniem |
| `ServiceIntervention` | trakcja zerowana, hamulec = **większy** z dwóch: maszynisty i ochrony |
| `EmergencyIntervention` | pełny hamulec |

„Większy z dwóch" jest tu treścią: ochrona idzie **tylko** w stronę mocniejszego
hamowania. Gdyby wstawiała swój ułamek zamiast brać maksimum, maszynista hamujący pełnym
hamulcem dostałby przy ostrzeżeniu hamulec **słabszy**.

Nadzór wchodzi w **fazie 2** kroku `LineCore`, razem z odczytem autorytetów: liczy się ze
stanu **sprzed** kroku. Zastosowanie decyzji jest w fazie 3, przez `LineDrive.Supervisor`,
**za** zatrzaskiem hamowania — więc hamulec podany przez ATP nie zatrzaskuje jazdy na cel
i ingerencja puszcza, gdy prędkość wróci pod krzywą.

Jedna z tych dwóch rzeczy jest zmierzona, a druga nie — i trzeba je rozdzielić.

**Miejsce zastosowania jest mierzalne.** Filtr przed zatrzaskiem zamiast za nim zmienia
przejazd radykalnie: ingerencji jest **6 zamiast 4576**, bo zatrzask przejmuje prowadzenie
i skład nigdy nie wraca nad limit. Kontrola negatywna to łapie.

**Miejsce nadzoru nie jest.** Przeniesienie nadzoru z fazy 2 do fazy 3 **nie zmienia ani
jednej liczby**: dwa składy na pakiecie A przy 76 km/h, osiem odstępów od 5 s do 150 s
(przy 5 s nastawnia odmawia 603 razy, czyli składy są tak blisko, jak ryglowanie pozwala)
— sumy kilometraży, liczba ingerencji i liczba odmów wychodzą identyczne, cały zestaw 376
testów przechodzi po mutacji. Powód jest strukturalny: ruch innego składu może autorytet
tylko **wydłużyć** (zwolniony blok), nigdy skrócić, a żeby wydłużenie zmieniło decyzję,
skład musiałby być nad prędkością dopuszczalną dokładnie w tym kroku, w którym
poprzedzający zwalnia blok — a skład stojący za sygnałem jest wtedy zatrzymany.

Faza 2 zostaje mimo to, bo niezmiennik „odczyt przed ruchem" ma trzymać z zasady. Ale nie
wolno pisać, że to **ona** broni niezależności od kolejności zgłoszenia składów: broni jej
to, że składy respektują autorytet.

#### Co z tego wychodzi na pakiecie A

Przejazd samotnego składu, plan `classic-2026` (limit **72,00 km/h**), hamulec służbowy
1,100 m/s², awaryjny 1,300 m/s²:

| limit scenariusza | bez ATP | z ATP | ostrzeżenia / ingerencje |
|---|---|---|---|
| 70,0 km/h | 89 958 kroków, 733,14 s | 89 958 kroków, 733,14 s | 0 / 0 |
| 72,0 km/h | 89 667 | 89 667 | 0 / 0 |
| 74,0 km/h | 89 431 | 94 060 | 4576 / 4576 |
| 76,0 km/h | 89 244, 727,19 s | 94 060, 767,33 s | 4576 / 4576 |
| 80,0 km/h | 88 974 | 94 060 | 4576 / 4576 |

Dwie rzeczy z tej tabeli są treścią modelu:

- **pod limitem planu ochrona nie rusza ani jednego kroku** — ślad jest identyczny co do
  bitu, nie tylko „tyle samo sekund". Zweryfikowane 733,14 s zostaje zweryfikowanym
  733,14 s;
- **nad limitem planu limit planu staje się faktycznym pułapem** — 74, 76 i 80 km/h dają
  dokładnie ten sam przejazd, bo ogranicza go krzywa ochrony, a nie nastawa scenariusza.

Ochrona przy tym **spowalnia** przejazd (767,33 s wobec 727,19 s przy 76 km/h) i tak ma
być: to nadzór, a nie regulator prędkości. Ingeruje **po** przekroczeniu i puszcza, gdy
prędkość wróci pod krzywą, więc jazda nad limitem planu jest piłą, a nie płaskim
ograniczeniem. Kto chce jechać szybko, ma nie przekraczać.

#### Granica: prędkość dokładnie równa dopuszczalnej NIE jest przekroczeniem

Wiersz `72,0 km/h` z tabeli wyżej jest **granicą**, a nie kolejnym pomiarem: limit
scenariusza jest tam dokładnie limitem planu. Warunek w `Supervise` brzmi
`speedMps > permitted`, i to `>`, a nie `>=`, jest treścią — jazda po limicie limit
respektuje. Uzasadnienie jest ze źródeł, nie z tego, że taki operator akurat stoi w kodzie:

- ten sam dokument mówi, że ochrona ingeruje **po** przekroczeniu, a tabela pokazuje przy
  72,0 km/h ślad identyczny co do bitu i `0 / 0`;
- `data/signalling/ground-truth.json`, `legacy_automatic_speed_protection`: ochrona
  reaguje, „when the protected separation is **not respected**";
- ta sama konwencja równości stoi już w `DemandExceedsServiceBrake` (żądanie równe
  pełnemu hamulcowi jeszcze go nie przekracza) — dwie różne konwencje w jednym pliku
  byłyby usterką;
- przy `>=` limit planu przestałby być **osiągalny**: sterownik dociąga prędkość dokładnie
  do limitu, więc ochrona hamowałaby każdy skład, który dojechał do własnego pułapu.

**Zmierzone 05.09.2026**, przejazd samotnego składu po pakiecie A przy limicie scenariusza
72,00 km/h, czysty kod wobec mutacji `>` → `>=`:

| | czysty kod | z mutacją |
|---|---:|---:|
| kroki przejazdu | 89 667 | 89 672 |
| kroki z prędkością **dokładnie** równą dopuszczalnej | 4492 | 4492 |
| ostrzeżenia | 0 | 0 |
| ingerencje służbowe | 0 | **4492** |

Czyli mutacja hamuje przez 37,43 s skład, który niczego nie łamie, i **nie zapisuje przy
tym ani jednego ostrzeżenia** — bo flaga `Overspeed` zostaje przy `>`, a rozjazd dwóch
porównań tej samej pary liczb jest właśnie tym, co czyni ingerencję niewidoczną. Do
05.09.2026 cały zestaw 376 testów tego nie widział, bo żaden nie jechał po granicy
(były 70 oraz 74/76/80). Przybija to `TrainProtectionTests`.

**Ingerencji awaryjnych jest zero i to trzeba powiedzieć, a nie przemilczeć.** Największe
żądanie ochrony w tym przejeździe to 0,863 m/s², czyli 78 % hamulca służbowego — żeby
ochrona sięgnęła po hamowanie awaryjne, hamulec służbowy musiałby **nie wystarczyć** do
zatrzymania przed końcem authority, a na tym planie authority kończy się dalej, niż sięga
droga hamowania z 80 km/h. Ścieżka awaryjna zostaje więc na pakiecie A
**nieprzećwiczona**; sprawdzają ją testy jednostkowe `ProtectionDecision.Apply`, a to, że
przejazd jej nie wywołuje, jest osobno przybite testem.

## 6. Ryglowanie tras — minimalny model

Trasa to uporządkowany zbiór bloków. Cały interlocking sprowadza się do czterech reguł:

- żądanie odrzucone, gdy trasa jest już zaryglowana, gdy skład ma inną trasę, gdy skład
  **nie zajmuje** bloku początkowego trasy, gdy któryś blok jest zajęty przez inny skład
  albo zarezerwowany pod inną trasę;
- zaryglowanie rezerwuje **wszystkie** bloki trasy;
- authority przechodzi tylko przez bloki zarezerwowane pod trasę tego składu
  (gdy `require_route`);
- trasa zwalnia się, gdy **czoło** składu wjedzie do jej bloku docelowego.

Ostatnia reguła wymaga uzasadnienia. Rezerwacja i zajętość chronią co innego: ogon składu
wciąż stoi w blokach poprzedzających i wciąż je **zajmuje**, a sama zajętość skraca cudze
authority i odrzuca cudze żądanie trasy. Trzymanie rezerwacji do wyjazdu ogona nic by nie
dodało do bezpieczeństwa. Czekanie na cały skład byłoby zresztą nieosiągalne: blok peronowy
ma długość dokładnie jednego składu, więc skład zatrzymany na środku peronu ma ogon
w bloku poprzednim.

Odmowa trasy **nie jest wyjątkiem** — jest zdarzeniem `RouteRejected` z powodem. Wyjątkiem
jest tylko postawienie składu na zajętym bloku, bo to błąd scenariusza, a nie sytuacja
ruchowa.

### „Stoi w bloku" znaczy „zajmuje blok", a nie „ma w nim czoło"

**Przepisane 05.09.2026, a nie dopisane obok.** Do tego dnia kod pytał wyłącznie o blok,
w którym stoi **czoło** (`FixedBlockSystem.RejectionReason`), i to wystarczało, bo jedyny
wołający — `LineCore` — wstawia skład na plan z czołem dokładnie na kilometrażu pierwszej
stacji, czyli w bloku peronowym.

Powód zmiany jest wymiarowy, nie estetyczny: **skład M7 ma 94 m i blok peronowy ma
dokładnie tyle samo**, więc skład przy peronie nigdy nie mieści się w jednym bloku.
Kabina prowadzona ręcznie (G-5) zaczyna przejazd z czołem na **94,000 m** — bo cały skład
ma stać na osi — a to na pakiecie A jest już blok szlakowy `S01`; w peronowym `P01` stoi
wtedy **ogon**. [ZMIERZONE] Dopóki warunek patrzył na samo czoło, nastawnia nie zamawiała
dla takiego składu **ani jednej trasy**: autorytet kończył się na **462,730 m** z powodem
`BlockNotReserved`, a ochrona hamowała skład **awaryjnie przez 1998 kroków**, zanim ten
dojechał do pierwszej stacji.

To jest ta sama konwencja, którą `ComputeAuthority` stosuje kilkadziesiąt linii wyżej
w tym samym pliku („blok czoła liczony po **zajętości**, nie po samym punkcie"). Warunek
niczego nie rozluźnia — skład dalej musi być fizycznie w bloku początkowym trasy —
i został wprowadzony jako **suma** dwóch członów, a nie zamiana jednego na drugi:
stary człon (blok czoła) został nietknięty, więc każde żądanie, które przechodziło
przedtem, przechodzi tak samo teraz, a nowy może wyłącznie zamienić odmowę na zgodę.
[ZMIERZONE] Przejazd `--line` po pakiecie A przy 70 i przy 76 km/h, z ATP i bez,
daje po tej zmianie plik zatrzymań **identyczny co do bajtu** z plikiem sprzed niej.

### Kabina pod sygnalizacją: człowiek prowadzi, ATP pilnuje

`CabProtection` stawia pod planem **jeden skład prowadzony przez człowieka**: bloki,
nastawnia, autorytet jazdy i ochrona, która ingeruje w polecenie. Kolejność w kroku jest
ta sama, co w `LineCore.Step` — nastawnia, odczyt autorytetu i nadzór ze stanu sprzed
kroku, filtr polecenia, meldunek ruchu po kroku.

Dwie rzeczy odróżniają ją od linii i obie są treścią:

- **Regułę stacji ma `StationService`, nie `LineDrive`.** Autopilot uznaje zatrzymanie za
  wywołanie stacji przy `chainage >= cel − okno`, bez ograniczenia z góry; dla człowieka
  znaczyłoby to drzwi otwarte 200 m za peronem. `CabProtection` nie wie o stacjach nic
  i nie ma jak się z tamtą regułą rozjechać.
- **Ochrona jest OSTATNIM filtrem polecenia**, za nastawnikiem i za blokadą drzwi:
  `DriverNotch → StationService.Filter → CabProtection.Apply → TrainController`. Issue #26
  wymaga wprost, żeby „nie można było ominąć ATP przez input gracza", a filtr postawiony
  wcześniej dałby się nadpisać — przez człowieka albo przez cykl drzwi.

Sufit maszynisty (`--limit-kmh`) i prędkość dopuszczalna (limit planu) to **dwie różne
liczby**. Sufit ogranicza to, o co człowiek może poprosić; prędkości dopuszczalnej pilnuje
ochrona. Przy suficie równym limitowi planu sterownik i tak nie przekroczy 72,00 km/h,
więc ochrona nie ma czego łapać — dlatego sufit bez ochrony jest odmową argumentu, a nie
opcją.

[ZMIERZONE] Wzorzec `tests/data/manual-overspeed.log` (24 000 kroków, pełny ciąg,
zatrzymanie na Beekkancie, potem pełny ciąg przez trzy perony), pakiet A, plan
`classic-2026`:

| sufit maszynisty | ATP | czoło na końcu | szczyt | ostrzeżeń | służbowe | awaryjne |
|---|---|---:|---:|---:|---:|---:|
| 76,00 km/h | nie | 3203,714 m | 76,000 km/h | — | — | — |
| 76,00 km/h | tak | 2896,475 m | 72,012 km/h | 5406 | 3253 | 2153 |
| 72,00 km/h (= plan) | tak | 2913,007 m | 72,000 km/h | 2118 | 0 | 2118 |

Wzorzec `tests/data/manual-keys.log` — przejazd prowadzony poprawnie, ze szczytem
65,39 km/h — daje pod ochroną **0 ostrzeżeń, 0 ingerencji i ślad identyczny co do bitu**
z tym samym przejazdem bez ochrony. To jest ta sama własność, co wiersz „72,0 km/h"
w tabeli §5: pod limitem planu ochrona nie rusza ani jednego kroku.

**Ingerencje awaryjne w przejeździe przez peron są własnością modelu, nie usterką.**
Trasa `R0n` sięga do końca bloku peronowego stacji docelowej i nie da się jej zwolnić,
zanim czoło do tego peronu wjedzie. Skład, który przez peron **przejeżdża** z prędkością
liniową, dobija więc do końca autorytetu za każdym razem, a prędkość dopuszczalna liczona
z krzywej hamowania spada wtedy poniżej bieżącej — przy czym samo jej przekroczenie
wymaga już opóźnienia większego niż służbowe, bo to hamulec służbowy tę krzywą wyznacza.
Autopilot `LineDrive` tego nie widzi, bo staje na każdej stacji.

## 7. Duże `dt` nie przepuszcza składu przez blok

`FixedBlockSystem.MoveTrain` dostaje **nowe położenie czoła**, nie `dt`, i uzgadnia
zajętość na całym odcinku zamiecionym od dawnego tyłu do nowego czoła. Skok o 1560 m
w jednym wywołaniu zajmuje i zwalnia po drodze każdy blok; skok przez blok zajęty przez
inny skład daje `AuthorityViolation` z detalem `occupied-by=…`, **nawet jeżeli na końcu
skoku składy są już w różnych blokach**. Model, który patrzyłby tylko na punkt końcowy,
zameldowałby jeden blok i zgubił cztery.

Zajętości intruz nie przejmuje: blok zostaje przy składzie, który w nim jest.

## 8. Zdarzenia, odcisk stanu i odtworzenie

Sygnalizacja niczym nie steruje (zasada 6) — emituje `SignallingEvent`. Strumień jest
jednocześnie zapisem: `FixedBlockSystem.Replay` odtwarza z niego **stan ryglowania**
i `StateDigest()` wychodzi identyczny.

Odcisk stanu obejmuje: stan każdego bloku, jego zajmującego, jego rezerwację, listę
zaryglowanych tras i przypisanie tras do składów. **Nie obejmuje położenia ani prędkości
składów** — to nie jest stan sygnalizacji, tylko stan rdzenia fizyki, który ma własny test
determinizmu (`DeterminismTests`). Zdarzenia nadzoru prędkości i drzwi są **wynikami**,
nie stanem, więc odtworzenie je pomija; wchodzą do strumienia przez
`FixedBlockSystem.Report`, który odmawia przyjęcia zdarzenia zmieniającego stan ryglowania.

Determinizm stoi na trzech rzeczach: przeglądanie po indeksie tablicy zamiast iteracji
słownika, porównania łańcuchów `Ordinal`, numer porządkowy zdarzenia jako liczba całkowita.

## 9. KCV jako interfejs

Modelowana jest **jedna** funkcja z trzech potwierdzonych: zabezpieczenie automatycznego
otwierania drzwi. Pozostałe dwie — zapowiedzi M7 i smarowanie obrzeży na części łuków —
są wymienione w `KcvFunction`, żeby wiadomo było, co jest funkcją potwierdzoną, ale nic
w symulacji jeszcze na nich nie wisi.

`TrainProtection.DoorRelease` zwalnia drzwi, gdy skład stoi i czoło jest w bloku
peronowym; w wariancie linii 2/6 dochodzi potwierdzenie z KCV. Warunek zatrzymania jest
ten sam, co w T-312: liczy się **prędkość zero**, a nie dojechanie do kilometrażu peronu.

Telegramów, balis, częstotliwości i topologii lokalizatorów tu nie ma i mieć nie będzie.

## 10. Dwa składy na pakiecie A

Scenariusz z kryterium „skończone, gdy": skład **M1** stoi na Beekkant i jedzie do Étangs
Noirs, skład **M2** stoi na Gare de l'Ouest i chce jechać do Beekkant. Żaden nie wie
o drugim — cała regulacja odstępu wychodzi z ryglowania.

```
pakiet A / classic_2026: 14204 kroków = 118.37 s, 149 zdarzeń,
56 odrzuconych żądań trasy, 0 naruszeń authority;
M1 stanął na 1451.701 m, M2 na 509.435 m
```

M2 dostaje odmowę `block-occupied`, dopóki M1 nie zwolni bloków; trasę rygluje dopiero po
zdarzeniu `BlockReleased P02` składu M1. Test sprawdza tę kolejność po numerach
porządkowych zdarzeń, a nie po czasie. Błąd zatrzymania obu składów to −0,30 m — tyle samo,
ile daje sama pętla prowadzenia z T-401, więc sygnalizacja nic do niego nie dokłada.

## 11. Czego ten model świadomie nie ma

- **Aspektów sygnałów.** Authority jest ciągłe, bo tabel aspektów nie znamy. Praktycznie
  wychodzi na to samo, dopóki bloki szlakowe są dłuższe niż droga hamowania — a to jest
  sprawdzane (§4).
- **Rozjazdów i przebiegów przez rozjazdy.** Osie pakietów są jednotorowe, a planów
  rozjazdów nie ma. R-006 znalazł jedyne publiczne liczby o skali sygnalizacji STIB —
  **121 rozjazdów o napędzie elektrycznym i 82 nastawnie** (raport STIB 2025) — i one
  **nie** posłużyły do zbudowania niczego w tym modelu. Są punktem odniesienia na
  przyszłość, nie danymi wejściowymi.
- **Warstwy ATS.** Ground truth mówi wprost, że ATS jest osobną warstwą i nie omija
  ochrony pociągu. Dyspozytora tu nie ma; T-313 kończy się na ochronie.
- **CBTC.** To T-314. `classic_2026` jest domyślnym trybem historycznym dla 31.08.2026
  i tylko on jest tu zaimplementowany.
- **Symulatora ruchu.** Prowadzenie dwóch składów w scenariuszu jest kodem testu, a nie
  klasą w `src/Sim/` — wielopociągowy runtime to T-320.

## 12. Dlaczego plan sięga dalej niż oś

Ostatnia stacja pakietu leży **dokładnie na końcu osi**, a blok peronowy jest
wyśrodkowany na kilometrażu stacji — więc jego dalsza połowa z konieczności wystaje
za oś. Zmierzone na pakiecie A: `length_m` **6686,35 m**, kilometraż Merode
**6686,35 m**, koniec ostatniego bloku **6733,35 m**, czyli **47,00 m** za osią —
połowa 94-metrowego składu M7. Blok przycięty do końca osi nie zawierałby punktu
zatrzymania po całej długości peronu, a od tego zależy zwolnienie drzwi; plan idzie
zatem do dalszego z dwóch końców.

Do #86 (`4a03982`, 02.09.2026) ta sekcja nosiła tytuł „Znaleziona rozbieżność
w danych osi" i mówiła co innego: że kilometraż Merode (**6686,99 m**) leży 0,25 m
**za** końcem osi zagęszczonej (6686,739 m) i że jest to **usterka danych osi**.
#86 przeliczyło kilometraże na osi, która trafia do pliku, i ta rozbieżność
zniknęła — na wszystkich sześciu pakietach ostatnia stacja ma dziś kilometraż równy
`length_m` co do setnej metra, a stacji za końcem osi nie ma ani jednej. Wniosek
o zasięgu planu się nie zmienił, zmieniła się jego przesłanka.

Do #86 stało tu, że jest to **usterka danych osi, nie modelu**, i że T-313 jej nie
naprawia, bo `data/` jest tylko do odczytu (reguła 6). Naprawiło ją #86, po stronie
generatora osi — nie przez przesunięcie kilometrażu w pliku, a przez liczenie go na
tej samej łamanej, która do pliku trafia. Zasięg planu za koniec osi **nie był
skutkiem tej usterki** i dlatego został: wynika z wyśrodkowania bloku peronowego
na stacji, która leży na krańcu osi. Pilnuje tego `tools/tests/test_axis_claims.py`.
