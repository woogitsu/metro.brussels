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
Ta różnica jest widoczna, a nie zamieciona.

## 6. Ryglowanie tras — minimalny model

Trasa to uporządkowany zbiór bloków. Cały interlocking sprowadza się do czterech reguł:

- żądanie odrzucone, gdy trasa jest już zaryglowana, gdy skład ma inną trasę, gdy skład
  nie stoi w bloku początkowym trasy, gdy któryś blok jest zajęty przez inny skład albo
  zarezerwowany pod inną trasę;
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

## 12. Znaleziona rozbieżność w danych osi

Kilometraż ostatniej stacji pakietu A (Merode, **6686,99 m**) leży **0,25 m za** końcem
osi zagęszczonej (**6686,739 m**). Blok peronowy przycięty do końca osi nie zawierałby
punktu zatrzymania własnej stacji, a od tego zależy zwolnienie drzwi — dlatego plan sięga
do dalszego z dwóch końców i kończy się na 6733,99 m.

To jest **usterka danych osi, nie modelu**, i T-313 jej nie naprawia: `data/` jest tylko
do odczytu (reguła 6), a przesunięcie kilometrażu stacji byłoby zmianą faktu o sieci.
