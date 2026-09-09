# Osiem narzędzi wobec nieosiągalnego źródła: pięć kończy kodem 0 (6.D51)

**Zmierzone 09.09.2026 na:** `0513a22`, kontener tej sesji.
**Przyrząd:** przejście po `tools/track/` i `tools/data/` (AST, nie grep po nazwach),
`tools/data/provenance.py` (`fetch_url`), osiem narzędzi uruchomionych z `timeout`
przy dwóch rodzajach niedostępności, `python3 tools/tests/test_all.py`.

---

## 1. Inwentarz — i trzy twierdzenia wpisu, które pomiar obalił

Sieć wychodzi z tego repozytorium **jednymi drzwiami**: `provenance.fetch_url`
(`urllib.request.urlopen`). Kto przez nie woła, policzone z drzewa:

```
plików narzędzi w tools/track i tools/data:            22
wołających fetch_url (poza samym provenance.py):        8
   crosscheck_alignment.py, fetch_gtfs.py, fetch_osm_routes.py,
   fetch_stib_shapes.py, inspire_rail.py, surface_sections.py,
   tunnel_width.py, snapshot_source.py
z PRAWDZIWĄ opcją argparse --offline:                   3
   crosscheck_alignment.py, fetch_gtfs.py, fetch_stib_shapes.py
```

Wpis 6.D51 mówił co innego i **trzy jego twierdzenia są nieprawdziwe**:

| twierdzenie wpisu | pomiar |
|---|---|
| „do sieci sięga **siedem**", z `build_alignment.py` na liście | **osiem**, a `build_alignment.py` **nie sięga wcale** — jedyne `http` w tym pliku to przestrzeń nazw SVG w generatorze podglądu |
| „z tych siedmiu `--offline` ma **tylko `provenance.py`**" | `provenance.py` **nie ma** tej opcji i **nie jest programem** (brak `main`); jedyna wzmianka o `--offline` stoi w jego docstringu. Opcję argparse mają trzy inne narzędzia |
| lista pomija `fetch_gtfs`, `fetch_stib_shapes`, `snapshot_source` | wszystkie trzy wołają `fetch_url` |

Liczba 8 jest **pomiarem z drzewa**, jak żądało pole „Skończone, gdy": wyliczona
z wywołań `fetch_url`, a lista `--offline` z węzłów `add_argument` w drzewie składni,
nie z wystąpień napisu (napis łapie też komentarze — na tym poległ wpis).

## 2. Dwa rodzaje niedostępności, bo dają różne odpowiedzi

Pytanie wpisu brzmi „pada czy zawiesza się" i **zależy od tego, jak sieć nie działa**:

- **odmowa** — port zamknięty, `ECONNREFUSED` natychmiast. Symulowane proxy na
  `127.0.0.1:9`;
- **cisza** — pakiety znikają, odpowiedzi nie ma. Symulowane proxy na `203.0.113.1:9`
  (TEST-NET-3, adres z definicji nieroutowalny).

Zmienne proxy ustawiane **wyłącznie dla pojedynczego wywołania**; weryfikacji TLS nikt
nie tykał, `HTTPS_PROXY` sesji nie było zmieniane.

## 3. Wynik

| narzędzie | odmowa: kod / czas | cisza: kod / czas | własny `--timeout` | `--offline` |
|---|---|---|---|---|
| `fetch_gtfs` | **1** / 0,11 s | **1** / 60,22 s | 60 s | tak |
| `fetch_stib_shapes` | **1** / 0,15 s | **1** / 60,29 s | 60 s | tak |
| `snapshot_source` | — (patrz §5) | **1** / 30,13 s | 30 s | nie |
| `fetch_osm_routes` | **0** / 0,13 s | **0** / 90,22 s | 90 s | nie |
| `tunnel_width` | **0** / 0,13 s | **0** / 90,13 s | 90 s | nie |
| `inspire_rail` | **0** / 0,15 s | **0** / 90,20 s | 90 s | nie |
| `crosscheck_alignment` | **0** / 0,15 s | **0** / 180,26 s | 90 s × 2 wywołania | tak |
| `surface_sections` | **0** / 0,37 s | **124** / >320 s (zabite) | 120 s × **liczba próbek** | nie |

**Odpowiedź na pytanie wpisu ma dwie części, bo narzędzia dzielą się na dwie grupy.**

*Siedem z ośmiu dochodzi do własnego timeoutu i kończy.* Tam problemem nie jest
zawieszenie, tylko **kod wyjścia: pięć z tych siedmiu kończy zerem** przy nieosiągalnym
źródle, a `crosscheck_alignment` robi to po **trzech minutach** czekania.

*`surface_sections` nie ma ograniczenia na całość i to jest ósmy przypadek.* Timeout
120 s dotyczy **jednego żądania**, a narzędzie wysyła **po jednym na próbkę osi**:

```
DEFAULT_STEP_INSIDE_M: 300.0 m,  długość osi L1_A: 6686.35 m
-> ok. 23 próbki, czyli 23 wywołania fetch_url przy pustym cache
-> najgorszy przypadek: 23 × 120 s = ok. 46 MINUT na najkrótszej osi pakietu A
```

Zmierzone: przy granicy 320 s zostało **zabite** (kod 124), nie zapisawszy pliku
wyjściowego. Dla porównania — job `tools` w CI ma `timeout-minutes: 15`, więc przy
braku sieci to narzędzie wyczerpałoby limit joba, zanim dojdzie do połowy osi.
Cache (`--osm-dir`) tę liczbę obniża, ale pusty cache jest stanem świeżego runnera.

## 4. Niuans na korzyść tych pięciu, i on też jest zmierzony

Kod wyjścia kłamie, ale **plik wynikowy nie**. `crosscheck_alignment` bez sieci zapisuje
raport, w którym stoi wprost:

```json
"urbis": {"status": "niedostępne",
          "reason": "<urlopen error [Errno 111] Connection refused>",
          "url": "https://data.mobility.brussels/..."}
```

To jest degradacja **jawna w treści**: narzędzie nie udaje, że ma dane. Zawodzi
wyłącznie kanał, którym czyta je automat — kod wyjścia. Krok CI wołający to narzędzie
zobaczy sukces i pójdzie dalej, a człowiek czytający plik zobaczy prawdę.

## 5. Czego NIE zmierzyłem i dlaczego to tu stoi

**`snapshot_source` przy odmowie.** Pierwsze wywołanie odbiło się od jego własnej
walidacji argumentów (`error: the following arguments are required: --format`), więc
kod 2 z tamtego przebiegu mówi o moim wywołaniu, nie o sieci. W wariancie z ciszą
wywołanie było już poprawne i tam liczba jest prawdziwa.

**Kod 124 z dwóch pierwszych przebiegów był MOIM artefaktem** i zostaje tu zapisany,
bo prawie trafił do wniosków. `fetch_osm_routes` i `tunnel_width` dały „kod=124, czas
90,01 s" przy ograniczeniu zewnętrznym `timeout 90` — a ich własny domyślny timeout
wynosi **dokładnie 90 s**. Pomiar mówił więc o granicy, którą sam postawiłem, nie
o narzędziu. Po powtórzeniu z granicą 200 s oba kończą **kodem 0 po 90,2 s**. Ta sama
pomyłka powtórzyła się przy `surface_sections` (2 × 120 s wobec granicy 200 s)
i została poprawiona tym samym sposobem.

**Nie mierzyłem zachowania z `--offline`** tam, gdzie ta opcja istnieje — pozycja pyta
o zachowanie przy nieosiągalnym źródle, a nie o tryb odmowy, i dopisywanie `--offline`
jest w niej wprost poza zakresem.

**Nie tykałem `data/`** ani polityki sieci.

## 6. Rekomendacja, którą ten pomiar uzasadnia

Nie „dopisać `--offline` wszędzie", bo trzy narzędzia już go mają, a problem leży gdzie
indziej. Kolejność wynikająca z liczb:

1. **`surface_sections` przed wszystkim innym**: nie brak `--offline` jest tu problemem,
   tylko brak **ograniczenia na całość przebiegu**. Jedno żądanie ma timeout, cały
   przebieg nie ma żadnego, więc przy braku sieci narzędzie zjada limit joba CI.
2. **Kod wyjścia pięciu narzędzi** (`fetch_osm_routes`, `tunnel_width`, `inspire_rail`,
   `crosscheck_alignment`, `surface_sections`) nie odróżnia „zrobione" od „źródła nie
   było". To jest ta sama rodzina, co 6.D46 i 6.D65: przyrząd melduje sukces, którego
   nie osiągnął. Poprawka jest jednowierszowa na narzędzie, ale **zmienia kontrakt**
   (część z nich celowo degraduje się do wyniku częściowego), więc wymaga decyzji, czy
   w takim wypadku ma być kod niezerowy, czy nowy przełącznik `--require-source`.
3. **`crosscheck_alignment` czeka trzy minuty**, zanim powie, że nie ma sieci — dwa
   timeouty po 90 s pod rząd. Przy `--offline` nie czeka wcale, ale nikt tego nie woła
   z CI.
4. Dopiero potem `--offline` w pozostałych pięciu.

## 7. Weryfikacja

```
python3 tools/tests/test_all.py
  -> RAZEM 2087 testów, 111 modułów, kod 0
```

Zestaw nietknięty: ta pozycja niczego w drzewie nie zmienia poza dopisaniem tego
raportu i adnotacji w wierszu kolejki.
