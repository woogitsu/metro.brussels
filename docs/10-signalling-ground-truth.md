# R-003 — ground truth sygnalizacji metra

Stan odniesienia: **31.08.2026**.

Celem tego dokumentu jest odseparowanie publicznie potwierdzonych faktów o sygnalizacji STIB/MIVB od szczegółów technicznych, których nie wolno odtwarzać przez zgadywanie. Maszynowym odpowiednikiem jest `data/signalling/ground-truth.json`.

## Wniosek dla scenariusza historycznego

Domyślny tryb dla 31.08.2026 to **`classic_2026`**. Pełny CBTC na liniach 1 i 5 nie jest jeszcze uruchomionym trybem produkcyjnym: STIB 02.07.2026 podaje, że instalacja jest zakończona na odgałęzieniach do Erasme/Erasmus i Stockel/Stokkel, gdzie trwają testy; Jacques Brel–Merode ma zostać wyposażone do końca 2026, a Herrmann-Debroux na początku 2027. Uruchomienie CBTC ma nastąpić dopiero po zakończeniu instalacji i testów na całych liniach 1/5.

W praktyce silnik musi mieć osobne scenariusze:

| tryb | status 31.08.2026 | zastosowanie |
|---|---|---|
| `classic_2026` | historyczny baseline produkcyjny | domyślny dla vertical slice 2026 |
| `cbtc_test` | instalacja/testy, nie pełna eksploatacja | scenariusze laboratoryjne i odcinkowe |
| `cbtc_future` | przyszłość | moving/variable block + ATS jako model po wdrożeniu |
| `cbtc_mini_future` | przyszłość linii 2/6 | lokalizacja torowa + zachowany KCV |

## Fakty source-backed

| fakt | status | źródło | abstrakcja symulacji |
|---|---|---|---|
| istniejący system działa na blokach stałych | observed | STIB 21.08.2025; STIB Stories | fixed-block baseline |
| stałe strefy są formowane przez track circuits | observed | STIB Stories | occupancy zone; dokładne granice pozostają `design_model` |
| obecny system automatycznie spowalnia skład przy naruszeniu chronionego odstępu | observed | STIB Stories | vendor-neutral train-protection interface |
| nowy ATS jest wdrażany stopniowo w dispatchingu | observed | STIB 21.08.2025 i 02.07.2026 | osobna warstwa nadzoru, nigdy obejście ATP |
| pełny CBTC 1/5 nie jest jeszcze uruchomiony | observed | STIB 02.07.2026 | `classic_2026` pozostaje default |
| Erasme i Stockel: instalacja zakończona, testy trwają | observed | STIB 02.07.2026 | dozwolony `cbtc_test`, nie historyczny full-service |
| Jacques Brel–Merode: wyposażenie planowane do końca 2026 | observed plan | STIB 02.07.2026 | metadata future rollout |
| Herrmann-Debroux: finalizacja planowana na początek 2027 | observed plan | STIB 02.07.2026 | metadata future rollout |
| na liniach 2/6 pozostaje KCV; CBTC-mini ma dodać lokalizację torową | observed | STIB 02.07.2026 | osobny przyszły tryb `cbtc_mini_future` |
| STIB wymienia funkcje KCV na 2/6: zabezpieczenie automatycznego otwierania drzwi, zapowiedzi M7, smarowanie kół na części łuków | observed | STIB 02.07.2026 | tylko interfejsy funkcjonalne, bez emulacji protokołu |
| Ansaldo STS France SA wybrano jako wykonawcę nowej sygnalizacji | observed | raport działalności STIB 2016 | provenance vendor; runtime pozostaje vendor-neutral |
| kontrakt 1/5: około 88 mln EUR, 35,5 km, 37 stacji, 60 pociągów w zakresie referencyjnym, Driverless CBTC | observed | Ansaldo STS/Hitachi 07.10.2016 | zakres programu, nie dowód UTO w 2026 |
| framework obejmował CBTC, ATS oraz integrację z passenger information i passenger announcement | observed | Ansaldo STS/Hitachi 03.08.2016 | przyszłe interfejsy domenowe, bez vendor protocol |
| pełniejsza automatyzacja wymaga także drzwi/fasad peronowych | observed | STIB 21.08.2025 | UTO pozostaje gated future scenario |
| cel programu na wspólnym odcinku 1/5: około 2:00 wobec około 2:30 w systemie legacy | observed target | STIB Stories | cross-check capacity/headway, nie safety constant |

## Czego nie wolno oznaczać jako `spec`

Bez nowego źródła pierwotnego nie wprowadzamy jako danych STIB/Ansaldo:

- długości i granic poszczególnych bloków;
- kompletnego rozmieszczenia oraz tabel aspektów sygnałów;
- częstotliwości radiowych, protokołów, ramek i telegramów CBTC/KCV;
- parametrów balis/lokalizatorów i dokładnego sposobu pozycjonowania;
- rzeczywistych krzywych ATP/ATO i safe-braking margins;
- czasów reakcji urządzeń;
- szczegółowej logiki route locking/interlockingu dla konkretnych stacji i rozjazdów;
- rzeczywistych procedur failover/degraded mode;
- operacyjnego poziomu GoA niewskazanego jawnie przez źródło;
- magic numbers przejętych z innych wdrożeń Ansaldo/Hitachi.

Jeżeli funkcja gry wymaga któregoś z tych elementów, parametr ma status **`design_model`**, jest konfigurowalny i odseparowany od rejestru historycznego.

## Fixed block — bez reverse engineeringu

STIB wprost opisuje obecny system jako podział na duże stałe strefy, maksymalnie z jednym pociągiem w strefie, utworzone przez track circuits. To wystarcza T-313 do implementacji bezpiecznej abstrakcji:

1. jawna lista bloków w konfiguracji;
2. occupancy/reservation;
3. movement authority kończące się przed konfliktem;
4. jedna wspólna krzywa hamowania z T-311;
5. boundaries i route conflicts oznaczone `design_model`, dopóki nie ma planów źródłowych.

Nie ma podstawy do nazywania naszej tabeli bloków „rzeczywistym planem STIB”.

## KCV i CBTC-mini

STIB 02.07.2026 potwierdza, że planowany CBTC-mini dla linii 2/6 zachowuje istniejący KCV i dodaje wyposażenie lokalizacyjne w torze. Publicznie wskazane funkcje KCV można modelować jako interfejsy domenowe. Nie znamy natomiast telegramów, częstotliwości, dokładnej topologii lokalizatorów ani sprzętowej logiki safety.

W efekcie `cbtc_mini_future` nie jest „odchudzonym kopią prawdziwego CBTC”, tylko vendor-neutral future scenario ograniczonym do publicznie opisanych funkcji.

## CBTC i ATS

Źródła STIB opisują przejście od dużych fixed zones do dokładniejszej lokalizacji/komunikacji pozwalającej zmniejszać separację. Materiały wykonawcy potwierdzają Driverless CBTC i ATS w zakresie kontraktu oraz integrację z informacją pasażerską i zapowiedziami.

Dla T-314 oznacza to:

- CBTC i ATS są dwoma odrębnymi komponentami domenowymi;
- ATS może regulować/monitorować ruch, ale nie omija train protection;
- dynamiczny movement authority i protective buffer są naszym `design_model`, dopóki nie znajdziemy publicznych parametrów wdrożenia;
- `cbtc_future` nie może być historycznym defaultem dla daty 31.08.2026.

## Headway i capacity

STIB Stories podaje programowy cel około 2 minut na wspólnym odcinku 1/5 wobec około 2 min 30 s w systemie legacy. To jest użyteczne jako późniejsza kontrola wyniku T-320/T-314, ale nie jako stała bezpieczeństwa ani gwarantowany timetable. Symulator powinien najpierw wyprowadzać headway z fizyki, dwell, authority i timetable, a następnie porównywać wynik z komunikowanym celem.

## Źródła zweryfikowane 31.08.2026

1. STIB, 21.08.2025 — `https://stib.prezly.com/metro--coup-daccelerateur-pour-la-nouvelle-signalisation-cbtc-sur-les-lignes-1-et-5`
2. STIB, 02.07.2026 — `https://stib.prezly.com/nouvelle-signalisation-metro-on-en-est-ou`
3. STIB Stories — `https://en.stibstories.be/shorter-waiting-times-on-the-metro-thanks-to-new-signalling-cbtc/`
4. STIB Activity Report 2016 — `https://2016.stib-activityreports.brussels/en/a-high-performing-company`
5. Ansaldo STS / Hitachi Rail, 03.08.2016 — `https://www.mynewsdesk.com/uk/hitachi-rail-global/pressreleases/ansaldo-sts-has-been-appointed-for-brussels-metro-signalling-system-renewal-3014905`
6. Ansaldo STS / Hitachi, 07.10.2016 — `https://www.hitachi.com/en-eu/press/ansaldo-sts-brussels-metro-lines-15-signalling-system-renewal/`

## Reguła dla kolejnych zadań

T-313/T-314 powinny importować/odczytywać granicę wiedzy z `data/signalling/ground-truth.json`. Każdy nowy parametr oznaczony jako realny STIB/Ansaldo musi wskazać nowe źródło. Brak danych nie jest powodem do awansu `design_model` → `spec`.
