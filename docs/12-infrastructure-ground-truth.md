# R-005 — ground truth infrastruktury torowej i zasilania

Stan odniesienia: **31.08.2026**. Maszynowy rejestr: `data/infrastructure/metro-system.json`.

## Najważniejszy wniosek

Publiczne źródła STIB pozwalają bezpiecznie zamrozić trzy podstawowe fakty: metro korzysta z **900 V**, jest zasilane przez **trzecią szynę**, a STIB publicznie opisuje jazdę do **72 km/h w tunelu** oraz **40 km/h przy wjeździe do stacji** w komunikacie bezpieczeństwa.

Nie pozwalają natomiast automatycznie uznać za `spec`:

- rozstawu 1435 mm;
- dokładnego profilu szyny;
- geometrii i położenia trzeciej szyny;
- polaryzacji i sekcjonowania zasilania;
- geometrii rozjazdów;
- konstrukcyjnego Vmax M7 = 80 km/h;
- jednej globalnej reguły 40 km/h dla wszystkich wjazdów do stacji.

Brak źródła pierwotnego pozostaje `unknown`, nawet jeśli wartość jest branżowo bardzo prawdopodobna.

## Fakty source-backed

| fakt | wartość | status | źródło | ograniczenie interpretacji |
|---|---:|---|---|---|
| napięcie systemu trakcyjnego metra | 900 V | observed | STIB 2025 + raport statystyczny 2024 + Metro 3 | nominalna wartość systemowa, bez modelu spadków napięcia |
| pobór energii | trzecia szyna | observed | STIB 2025 | brak publicznego potwierdzenia dokładnej geometrii styku/odsunięcia |
| kable BT Metro 900 V | 111,5 km w 2024 | observed | raport statystyczny STIB 2024 | to długość kabli, nie długość toru |
| rozjazdy z napędem elektrycznym | 121 w 2024 | observed | raport statystyczny STIB 2024 | Delta i Demets wyłączone; brak geometrii i logiki sterowania |
| posterunki sygnalizacyjne | 82 w 2024 | observed | raport statystyczny STIB 2024 | Delta i Demets wyłączone; brak granic bloków/aspektów |
| podstacje trakcyjne w tabeli elektrycznej STIB | 120 w 2024 | observed | raport statystyczny STIB 2024 | tabela nie rozbija tej liczby na metro i tram — **nie nazywać tego 120 podstacjami metra bez dodatkowego źródła** |
| prędkość w tunelu | do 72 km/h | observed | STIB komunikat bezpieczeństwa | kontekst operacyjny/safety, nie konstrukcyjny Vmax pojazdu |
| prędkość przy wjeździe do stacji | 40 km/h | observed | STIB komunikat bezpieczeństwa | nie jest dowodem uniwersalnego limitu każdego segmentu |
| wysokość krawędzi peronu względem szyn | ponad 1,10 m | observed | STIB komunikat bezpieczeństwa | wartość ogólna, nie wymiar każdej stacji |
| konwersja premetra do metra wymaga m.in. 900 V, właściwego gabaritu/peronów, sygnalizacji i rozjazdów | potwierdzone kategorie | observed | STIB raport roczny 2023 | nie daje wymiarów istniejących linii 1/5 |

## Ważna korekta: 120 podstacji

Raport statystyczny STIB 2024 pokazuje w sekcji `Électricité et signalisation`:

- 120 podstacji transformacyjnych;
- 120 podstacji trakcyjnych;
- 111,5 km kabli BT `Métro 900 V`;
- w osobnej podsekcji `Signalisation du métro`: 121 rozjazdów z napędem elektrycznym i 82 posterunki sygnalizacyjne.

W przeciwieństwie do pozycji `Métro 900 V` oraz nagłówka `Signalisation du métro`, wiersz z 120 podstacjami nie jest opisany jako `Métro`. Dlatego R-005 zachowuje tę liczbę jako **network total unsplit** i nie awansuje jej do „120 metro traction substations”. To koryguje zbyt mocne założenie z wcześniejszego researchu.

## 900 V i trzecia szyna

STIB w komunikacie o wtargnięciach na torowisko mówi wprost, że trzeci rail zasila metro energią elektryczną i że występuje na nim napięcie 900 V. To wystarcza do source-backed warstwy hazard/energy metadata.

Nie wystarcza do wygenerowania realistycznej geometrii przewodnika. Bez dalszego źródła następujące pola są `unknown` lub `design_model`:

- kontakt górny/dolny/boczny;
- odległość od osi toru;
- wysokość względem główki szyny;
- przekrój przewodnika;
- izolatory i podpory;
- polaryzacja;
- sekcje zasilania, przerwy i przełączanie;
- zachowanie napięcia pod obciążeniem.

T-210/T-211 mogą pozostawić bezpieczny envelope pod trzecią szynę, ale nie mogą przedstawiać projektowego offsetu jako pomiaru STIB.

## Prędkości: operacyjne ≠ konstrukcyjne

STIB podaje `jusqu’à 72 km/h en tunnel` oraz `40 km/h en entrée de station` w kontekście ostrzeżenia o wejściu na torowisko.

W projekcie oznacza to:

- `72 km/h` jest source-backed cross-checkiem dla ruchu w tunelu;
- `40 km/h` jest source-backed obserwacją/kontekstem wjazdu do stacji;
- żadna z tych wartości nie jest automatycznie globalnym speed profile;
- `80 km/h` nie zostaje uznane za konstrukcyjny Vmax M7 bez źródła pierwotnego CAF/STIB;
- T-111/T-313/T-320 powinny później budować ograniczenia prędkości z realnych danych/konfiguracji, a nie z jednego komunikatu prasowego.

## Rozstaw toru

`1435 mm` występuje w źródłach wtórnych i jest wartością bardzo prawdopodobną, lecz w R-005 nie znaleziono bezpośredniego źródła STIB, Regionu Brukselskiego ani CAF, które można uczciwie przypiąć do rekordu `spec`.

Dlatego `data/infrastructure/metro-system.json` przechowuje 1435 wyłącznie jako `secondary_reference_only`, a właściwy status `track_gauge_mm` pozostaje `unknown_primary_source_not_confirmed`.

Nie oznacza to twierdzenia, że rozstaw jest inny. Oznacza tylko, że projekt nie miesza wiedzy branżowej z audytowalnym ground truth.

## Rozjazdy i sygnalizacja

Liczby 121 elektrycznie sterowanych rozjazdów i 82 posterunków sygnalizacyjnych są źródłowym dowodem, że te klasy infrastruktury istnieją na realnej sieci. Nie wynikają z nich:

- konkretne lokalizacje wszystkich rozjazdów;
- promienie/skosy;
- napędy i czasy przestawiania;
- route locking;
- granice bloków;
- aspekty sygnałów.

R-003 określa granicę wiedzy o signalling; R-005 nie próbuje jej obchodzić.

## Metro 3 jako kontrola kategorii infrastruktury

STIB opisując konwersję osi premetra do Metro 3 wymienia konieczność dostosowania gabaritu, wysokości peronów, zasilania 900 V, sygnalizacji, rozjazdów i innego wyposażenia technicznego.

To jest dobre potwierdzenie, że 900 V i te klasy systemów są charakterystycznymi wymaganiami metra STIB. Nie wolno jednak kopiować wymiarów ani rozwiązań Metro 3 na istniejące linie 1/5 bez osobnego źródła.

## Źródła zweryfikowane 31.08.2026

1. STIB, raport statystyczny 2024 — `https://www.stib-mivb.be/files/live/sites/STIBMIVB/files/Corporate/STIB_statisticreport2024_FR.pdf`
2. STIB, komunikat o wtargnięciach na tory — `https://stib.prezly.com/le-metro-interrompu-95-heures-a-cause-dintrusions-sur-les-voies`
3. STIB, raport roczny 2023 / modernizacja Metro 3 — `https://stib.prezly.com/rapport-annuel-stib-2023--frequentation-offre-et-kilometres-parcourus-en-hausse`

Raport statystyczny został sprawdzony także wizualnie na stronie infrastruktury: tabela potwierdza 111,5 km `Métro 900 V`, 121 `Aiguillages à commande électrique`, 82 `Postes de signalisation` oraz ogólne 120 `Sous-stations de traction`.

## Reguła dla kolejnych zadań

- **T-210:** trzeci rail ma mieć miejsce w envelope, ale geometria pozostaje design, dopóki nie ma źródła.
- **T-211/T-212:** `>1,10 m` służy tylko sanity-checkowi, nie jest wysokością konkretnego peronu.
- **T-310:** 900 V może wejść jako metadana systemu energii; prąd/sekcjonowanie/spadki napięcia pozostają modelem projektowym.
- **T-313:** istnienie rozjazdów/posterunków jest faktem; dokładna logika i lokalizacja muszą pochodzić z R-003/T-111 lub pozostać design/unknown.
- **speed profiles:** 72/40 km/h nie są magic numbers do globalnego hard-code.
