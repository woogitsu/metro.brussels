# Pakiet A — czego nie dało się potwierdzić (R-004)

**Zmierzone na commicie:** `8e2faea`

Audyt: **2026-09-02**. Stan modelowany: **2026-08-31**.
Rejestr: `data/stations/package-a.json`. Opis: `docs/11-station-ground-truth.md`.

Ten raport jest listą dziur, nie listą osiągnięć. 260 z 696 kopert faktów w rejestrze
ma status `unknown`. Poniżej: skąd się biorą i co trzeba zrobić, żeby je zamknąć.

## 1. Dwie blokady, które dotyczą całego pakietu

### 1.1 Cztery stacje nie mają dziś tekstowego opisu planu dzielnicowego

Na stronie STIB `plans-de-reseau-et-plans-de-quartier` linki „version verbale” dla
**De Brouckère, Étangs Noirs, Sainte-Catherine i Schuman** mają `href="#"`. Pliki pod
adresami, które strona podaje w atrybucie `title`, zwracają **HTTP 404**:

```
FR/DeBrouckere.pdf                     404
FR/EtangsNoirs(ZwarteVijvers).pdf      404
FR/Sainte-Catherine(Sint-Katelijne).pdf 404
FR/Schuman.pdf                          404
```

Sprawdzone też warianty `NL/`, nazwy z akcentem i nazwy bez nawiasu — wszystkie 404.
Dla porównania pozostałe osiem stacji pakietu A pobrało się poprawnie (HTTP 200,
1,4–3,0 kB, PDF 1–3 strony). Katalog opisów tekstowych obejmuje 44 z 59 stacji metra
i urywa się alfabetycznie po „Parc”.

**Skutek:** dla tych czterech stacji wyposażenie pionowe każdego wyjścia
(`fixed_stairs`, `escalator`, `lift`) jest `unknown`, a jedynym źródłem wyjść jest GTFS.
To 118 z 260 wszystkich `unknown` w rejestrze.

**Sprzeczność, którą trzeba nazwać wprost.** Notatka badawcza w Issue #16 (komentarz
z 31.08.2026) podaje dla tych czterech stacji konkretne listy wyjść — De Brouckère
1–5, dwa razy 6 i 9; Étangs Noirs 0–2; Sainte-Catherine 0–6; Schuman 1–9 z windami
przy 2, 3, 4, 5, 6 i 8. **Nie udało się dziś potwierdzić żadnej z tych liczb u STIB.**
Rejestr ich nie przejmuje: siedzą w `conflicts` jako `C-VERBAL-MISSING-4` o rodzaju
`unverified_claim`, a test `test_unverified_claim_about_missing_descriptions_is_not_promoted_to_fact`
pilnuje, żeby notatka nigdy nie awansowała do faktu. Albo pliki zniknęły ze strony
STIB między 31.08 a 02.09.2026, albo notatka opisuje inne źródło. Jedno i drugie
wymaga rozstrzygnięcia przez człowieka.

### 1.2 `bm_public_transport:metro_access` jest zamknięty bez bearer tokenu

Metadane Paradigm potwierdzają licencję **CC0** i źródło STIB, ale strona datasetu
mówi wprost: *„Ce jeux de données est (partiellement) limité. Si vous souhaitez
utiliser ces données en tant que service, vous devez ajouter un bearer token comme
authentification dans vos requêtes.”*

Sprawdzone punkty wejścia, wszystkie **HTTP 401**:

```
geoserver/bm_public_transport/wfs?...typeName=bm_public_transport:metro_access&outputFormat=json   401
geoserver/ogc/features/v1/collections/bm_public_transport%3Ametro_access/items                     401
```

Tokenu nie zdobywam i nie zapisuję — `data/network/sources.json`, `policy.secrets`.

**Skutek:** wejść nie da się dziś kotwiczyć niezależnym źródłem regionalnym. Rejestr
używa zamiast tego rekordów wejść z **STIB GTFS** (`data/network/stops.json`,
`location_type=2`), które są w hierarchii źródeł **wyżej** niż Paradigm, więc nie jest
to obejście. Cena jest inna: tracimy niezależną kontrolę krzyżową współrzędnych, a
7 wyjść znanych wyłącznie z opisu tekstowego zostaje bez współrzędnych.

## 2. Luki wspólne dla wszystkich dwunastu stacji

| pole | stan | dlaczego |
|---|---|---|
| `platform_configuration` | 12 × `unknown` | ani GTFS, ani opisy tekstowe nie orzekają o `island`/`side`/`interchange` |
| `geometry_not_in_this_registry.*` | 12 × 5 × `unknown` | brak publicznych rzędnych, kot peronu i wymiarów pomieszczeń — #29 T-901 / #10 T-112 |
| `operator_scope.non_stib_elements` | 12 × `unknown` | żadne źródło nie opisuje granicy STIB / SNCB-NMBS |
| `access_graph` krawędź na peron | 12 × `unknown` | źródło potwierdza urządzenia przy wyjściu, nie ich zakończenie |

## 3. Per stacja

Kolumna „wyjścia” to `rekordy w rejestrze (z GTFS / z opisu tekstowego)`.

### Gare de l'Ouest / Weststation — 3 wyjścia (3 / 3), 15 `unknown`, 1 sprzeczny fakt
- `works_state: unknown`. Nie znalazłem dossier robót wnętrza; to **nie** jest dowód `stable`.
- Konflikt `C-GARE_DE_L_OUEST-STREET-1`: GTFS daje wyjściu 1 avenue Joseph Baeck,
  opis tekstowy chaussée de Ninove.
- Opis tekstowy podaje dla wyjścia 1 brak schodów stałych, brak escalatora i brak
  windy jednocześnie. Nie wiem, czym się w takim razie wchodzi — źródło tego nie mówi.
- `railway_interchange: unknown` — stacja kolejowa SNCB/NMBS nie jest potwierdzona
  żadnym użytym źródłem STIB.

### Beekkant — 2 wyjścia (2 / 2), 14 `unknown`
- `works_state: under_construction`, ale zakres to **otoczenie i terminus 87**.
  Brak jakiegokolwiek źródła o robotach we wnętrzu stacji.
- Węzeł rozjazdowy Beekkant (linie 1, 2, 5, 6) nie jest w rejestrze w żadnej formie —
  rejestr jest o dostępie pasażerskim, nie o torach.
- Nie wiadomo, ile wind ma stacja; opis tekstowy nie wymienia żadnej przy dwóch wyjściach.

### Étangs Noirs / Zwarte Vijvers — 2 wyjścia (2 / 0), 24 `unknown`
- Brak opisu tekstowego (§1.1): schody, escalatory i windy przy obu wyjściach `unknown`.
- `works_state: unknown`.

### Comte de Flandre / Graaf van Vlaanderen — 3 wyjścia (2 / 3), 16 `unknown`
- Wyjście „3” (winda na ulicę, rue Sainte-Marie) **nie ma rekordu w GTFS**, więc nie
  ma współrzędnych. Do zamknięcia dopiero po `metro_access` albo po pomiarze.
- `works_state: unknown`.

### Sainte-Catherine / Sint-Katelijne — 5 wyjść (5 / 0), 36 `unknown`
- Brak opisu tekstowego (§1.1).
- **Numeracja jest nieużywalna:** wszystkie pięć rekordów GTFS nosi etykietę „1”, pod
  trzema różnymi adresami (Quai au Bois à Brûler ×2, Quai aux Briques ×3). Rejestr
  zachowuje pięć osobnych `exit_id` i zapisuje `C-SAINTE_CATHERINE-DUP-1`.
- Nie wiadomo, ile wyjść stacja ma naprawdę ani jak są ponumerowane w terenie.

### De Brouckère — 4 wyjścia (4 / 0), 31 `unknown`
- Brak opisu tekstowego (§1.1).
- `C-DE_BROUCKERE-ID-LABEL`: numer w `stop_id` nie odpowiada etykiecie wyjścia
  (`0010106` → „4 – Boulevard Anspach”, `0010406` → „1 – Place De Brouckère”).
  Nie wolno wyprowadzać numeru wyjścia z identyfikatora.
- Poziom `-1` w strefie kontrolowanej jest `indicative` z ofert lokali STIB. Ile
  poziomów ma stacja naprawdę — nieustalone.
- Issue #16 wymienia dwa różne rekordy „Exit 6” i wyjście „9”. Nie potwierdzone.

### Gare Centrale / Centraal Station — 12 wyjść (8 / 7), 36 `unknown`, 1 sprzeczny fakt i 3 wpisy w `conflicts`
- **Najgorzej udokumentowana stacja pakietu.** Opis tekstowy i GTFS opisują dwa różne
  światy: opis używa „Sortie 0” cztery razy i nie zna wyjść 1, 3, 5, 6; GTFS nie zna
  Marché au Bois ani carrefour de l'Europe. Dla etykiety „2” podają różne ulice.
  Zapisane jako `C-GARE_CENTRALE-NUMBERING` i `C-GARE_CENTRALE-STREET-2`.
- Dwa różne rekordy GTFS mają tę samą etykietę „3 – Rue des Colonies”
  (`C-GARE_CENTRALE-DUP-3`).
- 12 rekordów wyjść w rejestrze to **unia dwóch niespójnych źródeł**, a nie
  potwierdzona liczba wyjść stacji. Rzeczywista liczba jest nieustalona.
- Stacja jest w trakcie kompleksowej przebudowy, więc część rekordów może opisywać
  stan sprzed robót. STIB nie datuje opisów tekstowych.
- Liczba wind i escalatorów: `unknown`. Wiadomo tylko, że windy na perony są 31.08.2026
  wyłączone.

### Parc / Park — 1 wyjście (1 / 1), 11 `unknown`, 1 sprzeczny fakt i 2 wpisy w `conflicts`
- `C-PARC-EXITS-VS-EQUIPMENT`: opis wyjść zna jedno wyjście z jednymi schodami
  ruchomymi tylko na wyjście; projekt STIB podaje 4 windy i 7 escalatorów oraz pełną
  dostępność bez stopni. **Gdzie fizycznie są te 4 windy i 7 escalatorów — nieustalone.**
  To jest najostrzejszy dowód, że lista wyjść nie jest grafem pionu.
- `C-PARC-STREET-1`: GTFS podaje rue Royale, opis tekstowy parc de Bruxelles.
- Toalety publiczne: STIB pisze „opening soon” w publikacji z 25.11.2025 bez daty.
  Stan na 31.08.2026 nieustalony, element nieaktywny w wariancie historycznym.
- Wyjście ewakuacyjne do Parc de Bruxelles/Warandepark jest potwierdzone jako fakt,
  ale bez lokalizacji.

### Arts-Loi / Kunst-Wet — 7 wyjść (6 / 7), 16 `unknown`, 4 sprzeczne fakty
- Cztery konflikty ulic (wyjścia 1, 2, 5, 6). **Numeracja obu źródeł jest przesunięta
  jako całość**, więc żadnego z nich nie da się poprawić lokalnie.
- „Sortie 0 (plusieurs endroits)” z windą nie ma rekordu GTFS ani współrzędnych —
  z definicji jest w kilku miejscach naraz. Do rozbicia dopiero po `metro_access`.
- Stacja obsługuje cztery linie i jest węzłem przesiadkowym 1/2/5/6, ale układ peronów
  jest `unknown`.

### Maelbeek / Maalbeek — 5 wyjść (5 / 4), 18 `unknown`
- `works_state: under_construction` od października 2025.
- GTFS zna wyjście „3 – Rue de la Loi”, którego opis tekstowy nie wymienia. Nie wiadomo,
  czy jest zamknięte robotami, czy pominięte w opisie.
- Opis podaje dla wyjścia „4” brak schodów, escalatora i windy jednocześnie.
- Reorganizacja bramek przy chaussée d'Etterbeek jest w toku, więc topologia wejścia
  31.08.2026 może odbiegać od opisu tekstowego. STIB nie podaje daty opisu.
- Liczba i lokalizacja nowych wind: `unknown` — STIB pisze „new lifts” bez liczby.
- Przestrzeń pamięci ofiar 22.03.2016 jest poza zakresem modelowania (`docs/03-legal.md`).

### Schuman — 3 wyjścia (3 / 0), 27 `unknown`
- Brak opisu tekstowego (§1.1), mimo że STIB publikuje dla tej stacji także wariant 3D
  planu — czyli plan istnieje, a jego wersja tekstowa nie jest podana.
- `stop_id` wejść mają luki (`0060211`, `0060311` nie występują), co sugeruje wejścia
  usunięte z feedu. Ile wyjść ma stacja — nieustalone. Issue #16 mówi o 1–9;
  niepotwierdzone.
- Poziomy `-1` (Rond-Point, strefa niekontrolowana) i `-2` (peron, strefa kontrolowana)
  są `indicative` z ofert lokali.
- **`railway_interchange: unknown`.** Nie mam źródła STIB, które wprost przypisuje tej
  stacji metra kompleks kolejowy SNCB/NMBS. Rozdzielenie warstw STIB i SNCB, którego
  wymaga Issue #16, jest w rejestrze zrobione przez zapisanie `unknown`, a nie przez
  przypisanie czegokolwiek.

### Merode — 7 wyjść (6 / 7), 16 `unknown`, 5 sprzecznych faktów
- Pięć konfliktów ulic (wyjścia 1, 3, 4, 7, 8); zgadza się tylko wyjście 2. Przy
  wyjściu 7 różnica jest subtelna — „square” wobec „place” tego samego placu — i jest
  zapisana zamiast po cichu scalona. Nie jest to systematyczne przesunięcie jak
  w Arts-Loi, tylko rozjazd rekord po rekordzie.
- „Sortie 0” z windą nie ma rekordu GTFS ani współrzędnych.
- Dane z OpenPermits o modernizacji PMR nie zostały w tym audycie użyte: opis windy
  nie zamienia się w metry bez przekroju albo cot. To zostaje dla T-901.

## 4. Co trzeba zrobić, żeby te dziury zamknąć

1. **Rozstrzygnąć §1.1** — czy opisy tekstowe czterech stacji istnieją. Bez tego
   118 pól zostaje `unknown`, a Sainte-Catherine i Schuman nie mają w ogóle
   użytecznej numeracji wyjść.
2. **Zdobyć dostęp do `metro_access`** albo świadomie zrezygnować z niezależnej
   kontroli krzyżowej. Token nie wchodzi do repo.
3. **Rozstrzygnąć 12 konfliktów ulic.** To wymaga człowieka albo trzeciego źródła;
   uśrednianie nie jest opcją.
4. **Nie zamawiać u T-211/T-212 układu peronów ani głębokości.** Rejestr ich nie ma
   i nie będzie miał przed T-901.
5. **Powtórzyć audyt `works_state` dla ośmiu stacji z `unknown`.** Brak znalezionego
   dossier to brak wiedzy, nie brak robót.
