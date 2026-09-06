# Cztery miejsca piszą do `data/`, dwa z nich nawet w trybie `--offline`

**Zmierzone 06.09.2026 na commicie:** `045730bd639c771d59b6d3b876c4d390d85f16ad`

Pozycja 6.D12. Zadanie **mierzy** rozjazd między `CLAUDE.md` §4.6 („`data/` jest
tylko do odczytu, chyba że zadanie mówi inaczej wprost") i realnym zachowaniem
narzędzi w `tools/`. Nie rozstrzyga go — wybór między zmianą reguły a zmianą
narzędzia zostaje właścicielowi (`CLAUDE.md` §8). Ten raport nie zmienia niczego
w `data/`; tam, gdzie pomiar wymagał realnego przebiegu narzędzia, zapis został
przywrócony `git checkout -- data/` zaraz po zmierzeniu różnicy — opisane w §4.

## 1. Metoda

Skan `tools/` po realnych zapisach, nie po nazwach:

```bash
grep -rlE "open\([^)]*['\"]w|write_text|shutil\.copy|shutil\.move|\.write\(|json\.dump\(|with open" tools/*.py tools/*/*.py
grep -rnE "default=.*(os\.path\.join\(.*[\"']data[\"']|[\"']data/)" tools/ --include=*.py
```

Dla każdego trafienia: co jest domyślnym lub udokumentowanym celem `--out`/`--manifest`/
`--report`, czy katalog docelowy jest w `.gitignore`, i czy `docs/`/istniejące wywołania
w repo faktycznie kierują go do `data/`. Dodatkowo sprawdzone wprost pod kątem ścieżki
składanej ze zmiennej środowiskowej (`grep -rn "os.environ\|getenv" tools/`) — jedno
trafienie, `tools/visual/capture_blender.py --commit`, dotyczy napisu w nazwie commita,
nie ścieżki pliku.

## 2. Wynik — cztery miejsca, w dwóch klasach

| # | narzędzie | co pisze do `data/` | zmienia plik przy niezmienionej treści źródła? |
|---|---|---|---|
| 1 | `tools/track/fetch_gtfs.py` | `data/network/gtfs-manifest.json` (śledzony), `data/gtfs/*.zip` (gitignored) | **TAK, zawsze** — także w `--offline`, zmierzone dziś dwoma realnymi przebiegami (§4.1) |
| 2 | `tools/track/fetch_stib_shapes.py` | `data/network/shapes-manifest.json` (śledzony), `data/raw/*.zip` (gitignored) | **TAK, zawsze** — identyczny kod co #1, zweryfikowane czytaniem źródła, nie ponownym pobraniem (§4.2, powód niżej) |
| 3 | `tools/track/build_alignment.py` | 6 par `data/track/<pakiet>.json` + `.provenance.json` (śledzone) | **POŚREDNIO TAK** — plik sam jest deterministyczny, ale osadza `retrieved_at` z manifestu #2, który zmienia się przy każdym uruchomieniu #2 (§4.3) |
| 4 | `tools/track/normalize_stops.py` | `data/network/stops.json` (śledzony) | **POŚREDNIO TAK** — ta sama konstrukcja, osadza `retrieved_at` z manifestu #1 (§4.4) |

Sprawdzone i **odrzucone** jako miejsca zapisu do `data/` (§5): `tools/data/snapshot_source.py`,
`tools/track/data_freshness.py`, oraz dziewięć narzędzi `tools/track/*.py` i wszystkie
skrypty `tools/blender/*.py` z wymaganym lub domyślnym `--out` poza `data/`.

## 3. Warianty — obok siebie, z kosztem każdego

Dwie klasy zapisu wymagają osobnych wariantów, bo #3 i #4 dziedziczą problem
po #1/#2, zamiast wytwarzać go same.

### Dla #1 i #2 (bezpośredni zapis manifestu proweniencji)

| wariant | na czym polega | koszt |
|---|---|---|
| **A. Zmienić regułę** | `CLAUDE.md` §4.6 dostaje jawny wyjątek: manifesty proweniencji (T-114) wolno aktualizować, bo niosą wyłącznie metadane obserwacji, nie treść | Osłabia globalny niezmiennik „`data/` = tylko do odczytu" jednym zdaniem, które trzeba będzie pilnować, żeby nie stało się furtką dla innych narzędzi uzasadniających zapis frazą „to tylko metadane" |
| **B. Zamknięta lista wyjątków w regule** | zamiast reguły ogólnej — nazwane po nazwie narzędzia dwa wyjątki w §4.6, tak jak `COMMIT_EXCEPTIONS` w `test_report_hygiene.py` | Węższe niż A, ale ten sam wzorzec utrzymania: każdy nowy fetcher z tym samym zapisem wymaga dopisania się do listy, inaczej wygląda jak złamanie reguły zamiast udokumentowany wyjątek |
| **C. Zmienić narzędzie — pisz manifest tylko przy zmianie treści** | `provenance.diff_manifests()` już istnieje i porównuje `content_sha256`; #1/#2 go nie wywołują. Można wczytać stary manifest przed zapisem i nadpisać plik tylko wtedy, gdy `content_sha256` się różni | Manifest przestaje być dowodem „że w ogóle uruchomiono pobranie" — trzeba dodać osobny komunikat konsolowy („sprawdzono, bez zmian") w miejsce dzisiejszego sygnału z `git diff`; wymaga decyzji, czy zmiana *innych* pól manifestu bez zmiany treści (np. `dataset_validity`) też ma nadpisywać plik |
| **D. Zmienić narzędzie — przenieść `retrieved_at` poza plik śledzony** | Manifest śledzony trzyma tylko to, co opisuje TREŚĆ (`content_sha256`, `source_id`, `dataset_validity`); znacznik czasu pobrania trafia do osobnego, gitignorowanego pliku obok surowego archiwum (`data/gtfs/`, `data/raw/` — już poza repo) | Manifest śledzony traci pole, które dziś każdy może odczytać bez kopania w historii git; trzeba zaktualizować `data/schema/source-manifest.schema.json` i sprawdzić, czy coś czyta `retrieved_at` z tego konkretnego, śledzonego pliku (patrz #3/#4 — czyta, patrz niżej) |

### Dla #3 i #4 (kaskada z #1/#2, dodatkowo do wariantów wyżej)

| wariant | na czym polega | koszt |
|---|---|---|
| **E. Nic — problem #3/#4 znika sam, jeśli rozwiązane #1/#2** | Jeśli właściciel wybierze C lub D dla #1/#2, `retrieved_at` w manifeście przestaje zmieniać się bez zmiany treści, a #3/#4 dziedziczą tę stabilność bez własnej zmiany kodu | Zero kosztu własnego, ale całkowita zależność: jeśli właściciel wybierze A/B dla #1/#2 (zaakceptować zapis jako jest), #3/#4 zostają tak samo niestabilne jak dziś — te dwie decyzje nie da się podjąć niezależnie, mimo że wyglądają jak osobne miejsca zapisu |
| **F. Nie osadzać `retrieved_at` w dokumencie wynikowym** | `document["source"]`/`document["feed"]` w #3/#4 trzyma tylko `content_sha256` i `source_id`; `retrieved_at` zostaje w logu konsoli uruchomienia, nie w bajtach commitowanego pliku | Commitowany `data/track/*.json`/`data/network/stops.json` traci pole, które dziś mówi wprost, kiedy dane wejściowe pobrano — trzeba sprawdzić `tools/tests/test_alignment.py` i `tools/tests/test_gtfs_stops.py`, które czytają skomitowane pliki, pod kątem założeń o obecności tego pola |

Żaden z wariantów nie jest tu wybrany. A/B i C/D się wykluczają nawzajem (nie da
się jednocześnie "zaakceptować zapisu jako jest" i "przestać pisać przy
niezmienionej treści"); E i F dla #3/#4 zależą od tego, co zostanie wybrane dla
#1/#2, więc kolejność decyzji ma znaczenie, nawet jeśli sama decyzja nie zapada tu.

## 4. Dowody — po jednym na miejsce zapisu

### 4.1 `fetch_gtfs.py` — zmierzone dwoma realnymi przebiegami dziś

```
$ cp data/network/gtfs-manifest.json /tmp/gtfs-manifest.before.json
$ python3 tools/track/fetch_gtfs.py
[POBRANO] https://api-management-discovery-production.azure-api.net/api/gtfs/feed/stibmivb/static -> .../data/gtfs/stib_gtfs.zip (14543732 B)
[RAPORT] sha256=28c2fba48783e278d20f8f703759e3f729b72608d015e00d0f8215fa3b278bb6
[RAPORT] rozmiar=14543732 B, pobrano=2026-09-06T12:32:36Z
...
$ git status --short data/
 M data/network/gtfs-manifest.json
$ diff /tmp/gtfs-manifest.before.json data/network/gtfs-manifest.json
<  ...,"retrieved_at":"2026-09-01T10:35:09Z",...
---
>  ...,"retrieved_at":"2026-09-06T12:32:36Z",...
```

`content_sha256` identyczny z manifestem sprzed pobrania (feed nie zmienił się od
6.A3, zmierzone tamtego samego dnia w `reports/service-day.md` §8) — jedyna zmiana
to `retrieved_at`. Następnie, drugi przebieg, w trybie który deklaruje, że **nie
pobiera** z sieci:

```
$ cp data/network/gtfs-manifest.json /tmp/gtfs-manifest.after-online.json
$ python3 tools/track/fetch_gtfs.py --offline
[RAPORT] sha256=28c2fba48783e278d20f8f703759e3f729b72608d015e00d0f8215fa3b278bb6
[RAPORT] rozmiar=14543732 B, pobrano=2026-09-06T12:32:50Z
$ diff /tmp/gtfs-manifest.after-online.json data/network/gtfs-manifest.json
<  ...,"retrieved_at":"2026-09-06T12:32:36Z",...
---
>  ...,"retrieved_at":"2026-09-06T12:32:50Z",...
$ git status --short data/
 M data/network/gtfs-manifest.json
```

`--offline` czyta plik już leżący na dysku (żadnego żądania sieciowego), a
`retrieved_at` mimo to skacze o 14 sekund — bo `main()` woła `P.utc_now_iso()`
bezwarunkowo w obu gałęziach (`if args.offline: ... retrieved_at = P.utc_now_iso()`),
a zapis manifestu na końcu `main()` nie jest osłonięty żadnym porównaniem ze
starą treścią. Po pomiarze przywrócone: `git checkout -- data/` i skasowany
gitignorowany `data/gtfs/stib_gtfs.zip`; `git status --short data/` czyste.

### 4.2 `fetch_stib_shapes.py` — zweryfikowane czytaniem kodu, nie ponownym pobraniem

Ten sam plik `tools/data/provenance.py` dostarcza obu narzędziom `fetch_url`,
`build_manifest` i `utc_now_iso`; `fetch_stib_shapes.py` ma identyczną strukturę
`main()`: gałąź `--offline` ustawia `retrieved_at = P.utc_now_iso()` z zegara, nie
z pliku, a zapis manifestu na końcu funkcji wykonuje się bezwarunkowo w obu
gałęziach, bez porównania ze starym plikiem. Nie odtworzyłem tego pomiaru realnym
pobraniem: archiwum shapefile'ów STIB jest większe niż jedyny transfer, na który
zadanie wskazuje wprost (GTFS, ~15 s / 14,5 MB), a kod obu narzędzi jest w tym
miejscu na tyle blisko identyczny (ta sama funkcja `provenance.utc_now_iso()`
wołana w tym samym miejscu, ten sam brak `diff_manifests()` przed zapisem), że
druga realna próba potwierdziłaby dokładnie to, co już widać w źródle.

### 4.3 `build_alignment.py` — kaskada zmierzona na aktualnym, skomitowanym drzewie

```
$ python3 -c "
import json
m = json.load(open('data/network/shapes-manifest.json'))
print(m['retrieved_at'])
d = json.load(open('data/track/L1_A.json'))
print(d['source']['retrieved_at'])
"
2026-09-01T10:48:05Z
2026-09-01T10:48:05Z
```

`build_alignment.py` czyta `data/network/shapes-manifest.json` i kopiuje
`retrieved_at` wprost do `document["source"]` (i do `.provenance.json`) — bez
zmiany geometrii, bez zmiany `content_sha256`. Skoro §4.2 pokazuje, że manifest
zmienia `retrieved_at` przy każdym uruchomieniu `fetch_stib_shapes.py`, każdy
przebieg `fetch_stib_shapes.py` → `build_alignment.py` (choćby dla nowego pakietu,
z tym samym archiwum) dotknie wszystkich sześciu par plików w `data/track/`,
nie tylko tej, którą się akurat buduje — bo manifest jest jeden, wspólny.

### 4.4 `normalize_stops.py` — ta sama kaskada, z `fetch_gtfs.py`

```
$ python3 -c "
import json
m = json.load(open('data/network/gtfs-manifest.json'))
print(m['retrieved_at'])
d = json.load(open('data/network/stops.json'))
print(d['feed']['retrieved_at'])
"
2026-09-01T10:35:09Z
2026-09-01T10:35:09Z
```

Identyczny mechanizm: `document["feed"]["retrieved_at"]` w `data/network/stops.json`
jest kopią pola z `data/network/gtfs-manifest.json`, więc §4.1 (manifest zmienia się
przy każdym uruchomieniu, także `--offline`) przenosi się wprost na ten plik, mimo
że sama normalizacja stacji jest funkcją wyłącznie treści feedu i nie ma w
`normalize_stops.py` żadnego własnego wywołania zegara.

## 5. Sprawdzone i odrzucone — nie piszą do `data/`

- `tools/data/snapshot_source.py` — CLI generyczne, `--output` jest **wymagane**
  bez domyślnej wartości; `docs/09-data-provenance.md` dokumentuje jego użycie
  z celem poza `data/`. Gdyby ktoś podał `--output` wskazujący w `data/`, zachowanie
  byłoby identyczne jak #1/#2 (ten sam `build_manifest`/`utc_now_iso`, bez trybu
  offline w ogóle) — ale żadne udokumentowane ani obecne w repo wywołanie tego nie
  robi, więc dziś to narzędzie tam nie pisze.
- `tools/track/data_freshness.py` — czyta cały `data/` rekurencyjnie, ale zapisuje
  tylko przy podanym `--out` (bez wartości domyślnej); żadne wywołanie w repo nie
  wskazuje go na `data/`.
- Dziewięć pozostałych narzędzi `tools/track/*.py` z zapisem (`crosscheck_alignment.py`,
  `surface_sections.py`, `inspire_rail.py`, `tunnel_width.py`, `station_layout.py`,
  `network_chainage.py`, `timetable.py`, `detail_layout.py`, `make_test_track.py`) —
  `--out` jest wymagane lub domyślnie wskazuje `build/`; sprawdzone przez
  `grep -rn "\-\-out[= ]*data/"` na `.github/`, `tools/`, `docs/` — jedyne cztery
  trafienia to #1–#4 wyżej.
- Wszystkie skrypty `tools/blender/*.py` — domyślne cele zapisu to `build/`;
  jedyny domyślny parametr wskazujący `data/` (`clearance.py --alignment`) jest
  **odczytem**, nie zapisem.
- Zmienne środowiskowe: jedyne użycie `os.environ`/`getenv` w `tools/` poza
  `tools/tests/` (`capture_blender.py --commit`) trafia do napisu w nazwie
  commita, nie do żadnej ścieżki pliku — brak pośredniego zapisu do `data/`
  składanego ze zmiennej.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py 2>&1 | tail -3
$ git status --short data/
```

Wynik wklejony w opisie commita tej pozycji (uruchomiony na świeżym klonie przed
push, zgodnie z poleceniem). `git status --short data/` puste na koniec pomiaru —
jedyny stan, w którym plik ten pozostawia repozytorium: dwa realne przebiegi
`fetch_gtfs.py` z §4.1 zmieniły `data/network/gtfs-manifest.json`, plik
przywrócony `git checkout -- data/` zaraz po zapisaniu diffu do tego raportu,
a gitignorowany `data/gtfs/stib_gtfs.zip` skasowany ręcznie.

## 7. Czego świadomie nie zrobiłem

- Nie odtworzyłem pobrania `fetch_stib_shapes.py` — powód w §4.2: transfer większy
  niż jedyny, na który zadanie wskazuje wprost, przy kodzie na tyle identycznym
  z #1, że druga próba potwierdziłaby to samo.
- Nie zbudowałem syntetycznego archiwum shapefile/GTFS, żeby uruchomić
  `build_alignment.py`/`normalize_stops.py` od zera w izolacji — kaskada w §4.3/§4.4
  jest już zmierzona bezpośrednio na aktualnym, skomitowanym drzewie (dwie
  wartości `retrieved_at` identyczne, źródło i pochodna), co jest silniejszym
  dowodem niż uruchomienie na sztucznych danych.
- Nie rozstrzygnąłem, który wariant z §3 wybrać — to jest poza zakresem pozycji
  wprost (`CLAUDE.md` §8, pole „Poza zakresem" pozycji 6.D12).
- Nie zmieniłem niczego w `data/`; jedyny zapis, do którego doszło (§4.1),
  przywrócony przed końcem zadania.

## 8. Zauważone obok, nietknięte

`docs/09-data-provenance.md` stwierdza wprost: „`retrieved_at`, ETag i
Last-Modified są metadanymi obserwacji. Nie są częścią hasha treści i **nie mogą
zmieniać byte-deterministycznego canonical outputu**." §4.3 i §4.4 pokazują, że to
zdanie jest dziś nieprawdziwe dla dwóch z czterech miejsc zapisu: `retrieved_at`
NIE jest częścią `content_sha256` (zgoda), ale JEST częścią canonical outputu
`data/track/*.json` i `data/network/stops.json` — trafia tam wprost, skopiowane
z manifestu. Ta pozycja tego zdania nie poprawia (nie ma go w `data/` ani w
`tools/`, którymi zajmuje się 6.D12 wprost) — zostawiam jako rozbieżność między
dokumentacją a kodem, osobną od pytania zadanego w tej pozycji.
