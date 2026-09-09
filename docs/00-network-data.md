# Dane sieci — źródło prawdy

Bazowy snapshot danych ma stan 30.08.2026; research źródeł odświeżono 31.08.2026. Maszynowa wersja: `data/network/lines.json`, provenance: `data/network/sources.json`.

## Sieć
- 59 stacji metra · 69 łącznie z premetro
- 39,9 km metra · 52,0 km łącznie z tunelami tramwajowymi
- rozstaw 1435 mm
- metro: 900 V DC, trzecia szyna górna
- premetro: 600 V DC, sieć górna
- pierwsze premetro 17.12.1969 · pierwsze metro 20.09.1976 · obecny układ linii 04.04.2009

## Linie
| Linia | Relacja | Długość | Stacje |
|---|---|---:|---:|
| 1 | Gare de l'Ouest ↔ Stockel | 12,5 km | 21 |
| 2 | Elisabeth ↔ Simonis | 10,3 km | 19 |
| 5 | Erasme ↔ Herrmann-Debroux | 17,3 km | 28 |
| 6 | Roi Baudouin ↔ Elisabeth | 15,5 km | 26 |

Linie 1 i 5 dzielą 12-stacyjny pień Gare de l'Ouest – Merode.

## M7
CAF, umowa 2016 na maks. 43 składy, 36 dostarczonych do końca 2025. 6 członów, 94 m długości, 2700 mm szerokości, 742 pasażerów, prędkość maks. 80 km/h. 4 człony napędne. Linie 1 i 5.

## Sygnalizacja — stan 31.08.2026
Na liniach 1 i 5 trwa **wdrożenie i walidacja CBTC; pełny system nie jest jeszcze oddany do eksploatacji na całych liniach**. Instalacja jest zakończona na odgałęzieniach Erasme i Stockel i trwa ich testowanie. Do końca 2026 ma zostać wyposażony odcinek Jacques Brel–Merode, a na początku 2027 odgałęzienie Herrmann-Debroux. STIB zapowiada uruchomienie po zakończeniu instalacji i testów na całości linii 1 i 5.

20 z 21 składów M6 jest wyposażonych pokładowo pod CBTC według komunikatu STIB 02.07.2026. Dla linii 2 i 6 planowany jest mini-CBTC przy zachowaniu KCV.

## Zajezdnie
- **Delta** i **Jacques Brel** — MX i M6
- **Erasme** — otwarta 2021, podziemna, 900 m, 23 składy postoju, 7 stanowisk obsługi, myjnia, dwie suwnice 110 m, tor testowy ok. 1 km

## Provenance
Aktualne źródła pierwotne i ich role są w `data/network/sources.json`. Najważniejsze: STIB Shapefiles/GTFS, warstwa regionalna `bm_public_transport:Metro` (CC0), oficjalny komunikat STIB o CBTC z 02.07.2026 oraz raport działalności STIB 2025.
