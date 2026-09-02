# Ground truth stacji — pakiet A

Stan audytu: **2026-09-02**. Stan modelowany: **2026-08-31**.
Canonical registry: `data/stations/package-a.json`. Schemat: `data/schema/station-registry.schema.json`.
Luki i to, czego nie dało się potwierdzić: `reports/package-a-station-source-gaps.md`.

Rejestr jest zbiorem **faktów**, nie modelem stacji. Nie zawiera ani jednej liczby,
która nie stoi w źródle. Tam, gdzie źródło milczy, stoi `unknown` z powodem, a nie
wartość domyślna.

## 1. Co jest w rejestrze

| | |
|---|---:|
| stacje | 12 / 12 |
| rekordy wyjść | 54 |
| kopert faktów | 696 |
| `source_backed` | 422 |
| `unknown` | 260 |
| `conflict` | 12 |
| `indicative` | 2 |
| zapisanych sprzeczności źródeł | 18 |

Rejestr **nie zawiera** grafik planów STIB, PDF-ów ani przepisanych opisów. Z opisów
tekstowych wyprowadzone są wyłącznie fakty: numer wyjścia, ulica, obecność schodów
stałych, schodów ruchomych i windy.

## 2. Źródła i ich role

| źródło | co z niego bierzemy | czego z niego NIE bierzemy |
|---|---|---|
| `stib_gtfs` (już w repo, `data/network/stops.json`) | współrzędne wejść i stacji, linie metra, liczba rekordów peronowych | liczby fizycznych peronów, układu peronów |
| `stib_district_plan_verbal` | wyposażenie pionowe wyjście po wyjściu, ulica wyjścia | pełnego pionu komunikacyjnego stacji |
| `stib_works_*`, `stib_traffic_*` | `works_state`, elementy tymczasowe, elementy przyszłe | stanu bieżącego z renderów docelowych |
| `stib_commercial_spaces` | istnienie poziomów funkcjonalnych (`-1`, `-2`) | wysokości w metrach, planu kondygnacji |
| `brussels_mobility_metro_access` | — (HTTP 401 bez bearer tokenu; raport luk §1.2) | — |
| `metro_bxl_issue_16_note` | tylko zapis roszczenia do weryfikacji | żadnych faktów |

Wszystkie nowe wpisy dopisane na końcu `data/network/sources.json`.

## 3. Koperta faktu

Każdy fakt jest słownikiem ze statusem i listą źródeł:

| status | znaczenie | wymagane pola |
|---|---|---|
| `source_backed` | wartość wprost potwierdzona przez wskazane źródło | `source_ids` ≥ 1 |
| `indicative` | źródło potwierdza istnienie cechy, ale nie jest planem ani pomiarem | `source_ids` ≥ 1, `note` |
| `conflict` | co najmniej dwa źródła podają różne wartości | `conflict_id`, `candidates` ≥ 2 |
| `unknown` | brak potwierdzenia | `value: null`, `reason`, pusta lista źródeł |

Fakt o **zmiennym stanie stacji** (wyposażenie wyjścia, `works_state`, dostępność)
niesie dodatkowo `as_of`. Pilnuje tego `test_facts_about_changing_state_carry_as_of`.

## 4. Stan czasowy — cztery stacje mają rozdzielone warianty

`works_state` ∈ `{stable, under_construction, planned_change, unknown}`.
**Brak znalezionego dossier robót nie jest dowodem `stable`** — osiem stacji ma
`works_state: unknown`, i tak zostaje do osobnego audytu.

| stacja | `works_state` 31.08.2026 | elementy tymczasowe | elementy przyszłe |
|---|---|---:|---:|
| Gare Centrale / Centraal Station | `under_construction` | 6 | 1 |
| Maelbeek / Maalbeek | `under_construction` | 5 | 2 |
| Beekkant | `under_construction` (otoczenie, nie wnętrze) | 2 | 2 |
| Parc / Park | `planned_change` | 0 | 2 |
| pozostałe 8 | `unknown` | 0 | 0 |

Każda stacja ma `variants.historical_2026_08_31` i `variants.future_completed`.
Wariant przyszły ma `active_at_2026_08_31: false`, a każdy element w `future_changes`
ma `exists_at_2026_08_31: false`. To jest twarda blokada: element przyszły nie może
wejść do scenariusza o wcześniejszym `as_of`.

Konkretnie:

- **Gare Centrale** — 31.08.2026 windy na perony są wyłączone, dostępność PMR nie
  jest gwarantowana do września 2026, jedne schody na peron w kierunku Parc/Park są
  zamknięte na stałe od 13 lutego, jedne w kierunku De Brouckère czasowo, posadzka
  peronów jest zdjęta. Stan docelowy („bigger, more modern, brighter, more accessible”)
  siedzi wyłącznie w `future_completed`. **Renderów projektu nie wolno użyć do
  historycznego vertical slice.**
- **Maelbeek** — roboty od października 2025 trwają; metro kursuje. Nowe windy i
  „100 % accessible” to stan docelowy, nie stan 31.08.2026.
- **Beekkant** — zakres robót to **otoczenie i terminus autobusu 87**, nie wnętrze.
  Objazd 87 trwa 11.05.2026 – IV.2027, więc nowy terminus nie istnieje 31.08.2026.
  Nie przenosić robót powierzchniowych na geometrię peronów.
- **Parc** — faza 2 zakończona; STIB podaje **4 windy i 7 schodów ruchomych** oraz
  pełną dostępność bez stopni. Faza 3 (nowe wejście od parku) to 2027–2030 i **nie
  może być aktywna** w 2026. Toalety publiczne: STIB pisze „opening soon” bez daty,
  więc ich stan 31.08.2026 jest nieustalony i element nie jest aktywny.

Dzieło „Mers et Océans” i pozostałe prace artystyczne pozostają poza assetami
produkcyjnymi — `docs/03-legal.md`, T-903.

## 5. Czego rejestr celowo nie zawiera

Każda stacja ma blok `geometry_not_in_this_registry`, w którym pięć pozycji jest
zawsze `unknown`:

`depth_below_street`, `platform_height_above_rail`, `platform_length`,
`mezzanine_clear_height`, `room_dimensions`.

Punkt wejścia z GTFS jest kotwicą na powierzchni. Nie mówi nic o głębokości, przebiegu
korytarza ani poziomie peronu. Poziomy w metrach to #29 T-901 / #10 T-112.

`platform_configuration` (`island` / `side` / `interchange`) jest `unknown` we
**wszystkich dwunastu** stacjach: ani GTFS, ani opisy tekstowe o tym nie orzekają.
Liczba rekordów peronowych GTFS jest zapisana osobno i **nie jest** liczbą fizycznych
peronów — jeden peron bywa kilkoma rekordami dla różnych linii.

## 6. Graf dostępu jest jawnie niepełny

Dla każdej stacji `access_graph` ma `completeness: "partial"`:

```
street_<exit>  --[schody / escalator / winda, source_backed]-->  intermediate_unknown
intermediate_unknown  --[unknown]-->  platform_level
```

Źródło potwierdza, jakie urządzenia stoją przy wyjściu. **Nie potwierdza, dokąd
dochodzą** ani ile poziomów pośrednich jest po drodze. Krawędź na peron jest zawsze
`unknown` i taka zostaje, dopóki nie ma przekroju albo planu kondygnacji.

Poziomy funkcjonalne są znane tylko dla dwóch stacji, ze statusem `indicative`:

- **De Brouckère** — poziom `-1` w strefie kontrolowanej (dwie oferty lokali STIB);
- **Schuman** — `-1` przy Rond-Point poza strefą kontrolowaną i `-2` przy peronie
  w strefie kontrolowanej.

To potwierdza istnienie poziomów, nie ich wysokość ani rzut.

## 7. STIB kontra SNCB/NMBS

Jedyna stacja, dla której źródło STIB wprost odróżnia infrastrukturę kolejową, to
**Gare Centrale** — strona robót pisze o „the SNCB/NMBS station” osobno. Dla Schuman
i Gare de l'Ouest **żadne użyte źródło nie przypisuje im wprost kompleksu kolejowego**,
więc `railway_interchange` jest tam `unknown`. To nie znaczy, że kolei tam nie ma —
znaczy, że nie mam na to źródła i nie zgaduję.

`operator_scope.non_stib_elements` jest `unknown` we wszystkich dwunastu stacjach:
granica fizyczna STIB / SNCB nie jest opisana w żadnym dostępnym źródle.

## 8. Sprzeczne źródła są zapisywane, nie nadpisywane

Rejestr trzyma 18 sprzeczności w tablicy `conflicts`. Fakt sprzeczny ma
`status: "conflict"`, `value: null` i obu kandydatów z ich `source_id`.
**Rejestr nie wybiera zwycięzcy.**

Trzy rodziny sprzeczności:

1. **Przypisanie ulicy do numeru wyjścia** (12 wyjść: Arts-Loi 1, 2, 5, 6;
   Gare de l'Ouest 1; Gare Centrale 2; Merode 1, 3, 4, 7, 8; Parc 1). Dwa oficjalne
   źródła STIB dają temu samemu numerowi różne adresy. Przy Arts-Loi numeracja jest
   przesunięta jako całość, więc nie jest to literówka w jednym rekordzie.
2. **Numeracja wyjść.** Opis tekstowy Gare Centrale używa etykiety „Sortie 0”
   cztery razy; GTFS ma dwa różne rekordy „3 – Rue des Colonies”; Sainte-Catherine
   ma **pięć** rekordów z etykietą „1” pod trzema różnymi adresami; w De Brouckère
   numer w `stop_id` nie odpowiada etykiecie (`0010106` to wyjście „4”).
   Rekordy o tej samej etykiecie **nie są scalane** — scalenie skasowałoby realne
   wyjścia. Każde wyjście ma własne, stabilne `exit_id`.
3. **Pokrycie.** Opis wyjść Parc zna jedno wyjście z jednymi schodami ruchomymi,
   a projekt STIB dla tej samej stacji podaje 4 windy i 7 schodów ruchomych.
   Wniosek jest ogólny i dotyczy wszystkich stacji: **lista wyjść nie jest grafem
   komunikacji pionowej wnętrza** i nie wolno z niej liczyć wind ani escalatorów.

## 9. Jak tego używać w T-211 / T-212

- Bierz `variants.historical_2026_08_31`. Nigdy `future_completed`.
- Fakt ze statusem `unknown` jest sygnałem „zapytaj albo zostaw dziurę”, nie
  zaproszeniem do przyjęcia wartości typowej.
- Fakt ze statusem `conflict` wymaga decyzji człowieka. Nie uśredniaj współrzędnych
  ani nie wybieraj „ładniejszej” ulicy.
- Liczby stacyjne (windy, escalatory) bierz z pól `accessibility`, nigdy z sumowania
  listy wyjść.
- Głębokości, wysokości i wymiary pomieszczeń nie istnieją w tym rejestrze i mają
  tak zostać do T-901.

## 10. Weryfikacja

```bash
python3 tools/tests/test_all.py
```

Testy proweniencji rejestru: `tools/tests/test_stations.py` (22 testy). Sprawdzają
kompletność 12 stacji, poprawność każdej koperty faktu, rozwiązywalność wszystkich
`source_id` w `data/network/sources.json`, brak zgadywanej geometrii, zachowanie
zduplikowanych etykiet wyjść, rozdzielenie stanów czasowych i to, że element przyszły
nie jest aktywny 31.08.2026.
