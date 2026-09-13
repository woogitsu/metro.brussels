# 6.D192 — ciszy nie ma, a rozdziela job, nie maszyna

**13.09.2026**, na `175a50b`. Wejście: `tools/ci/timing_record.py` (`z_logu`, `WZORY_LOGU`,
`MASZYNA_Z_LOGU`, `WYPROWADZANE`), `tools/tests/test_timing_record.py`,
`tests/data/ci-logs/`, `reports/6d162-dwie-maszyny-jedno-slowo.md`.

## 1. Czego pozycja żądała

Rozstrzygnięcia, czy w logach w drzewie stoi już inny, **treściowy** sygnał „to jest log
runnera" — policzony, nie wymyślony — i czy warunek ma się o niego oprzeć, czy zostać
tam, gdzie jest, z zapisanym powodem.

## 2. Pozycja stawiała dwa twierdzenia. Pierwsze jest prawdziwe, drugie NIE

| twierdzenie | wynik |
|---|---|
| `maszyna` ustawia się wtedy i tylko wtedy, gdy w logu stoi `Runner name:`, a treść nazwy nie wpływa na nic | **prawda** |
| log bez tego wiersza „zostanie cicho uznany za nie-runnera i jego pomiar wypadnie z listy **bez ani jednego komunikatu**" | **nieprawda** |

Zmierzone na prawdziwym logu ze zdjętym jednym wierszem:

```
wierszy przed: 3130 po: 3129
brakujace: ('runner', 'maszyna')

$ python3 tools/ci/timing_record.py --z-logu …/bez-runner-name.log
BRAK w …/bez-runner-name.log: runner, maszyna — to nie jest log kroku „Run tool tests”
albo krok zmienił wypisy
kod wyjscia: 1
```

**Ciszy nie ma.** `brakujace` zbudowano w 6.D152 dokładnie po to i ono działa; obawa
pozycji dotyczy mechanizmu, który już ma obronę. Jest to więc pozycja, której **połowa
odpowiedzi leżała w drzewie od dnia, w którym ją wpisano** — i to jest jej wynik, nie
porażka pomiaru.

## 3. Sygnał treściowy ISTNIEJE i jest zmierzony na dwunastu logach

Osiem logów self-hosted z drzewa i **cztery** logi GitHub-hosted sprzed przecięcia
(01.09.2026, `labels: ['ubuntu-latest']` potwierdzone z API, nie z nazwy) — ta druga
czwórka jest materiałem **historycznym**, sprzed przeniesienia CI na maszynę właściciela,
i nie mówi nic o dzisiejszym `runs-on`. Krytyczna kontrola confounda: **wersja runnera
po obu stronach jest ta sama, `2.337.0`**, więc różnica nagłówka nie jest artefaktem
wersji.

**Materiał GitHub-hosted jest HISTORYCZNY i to jest o nim cała prawda:** pochodzi sprzed
02.09.2026, czyli sprzed przeniesienia całego CI na maszynę właściciela, i **żaden
dzisiejszy job tego repozytorium na runnerze GitHuba nie chodzi**. Tabela niżej opisuje
zmierzoną RÓŻNICĘ MIĘDZY DWIEMA EPOKAMI, a nie dzisiejszy `runs-on` — warunków pomiaru
się nie przepisuje (6.D108), a nazwa `ubuntu-latest` stoi tu jako etykieta zmierzonej
próbki, nie jako propozycja.

| wzorzec | GitHub ×4 | self-hosted ×8 |
|---|---|---|
| `Runner name:` | **0/4** | **8/8** |
| `Runner group name:`, `Machine name:` | 0/4 | 8/8 |
| `Runner Image Provisioner`, `Hosted Compute Agent`, `Azure Region:` | **4/4** | **0/8** |
| `##[group]Operating System`, `Image:`, `Image Release:` | 4/4 | 0/8 |
| `Current runner version` | 4/4 | 8/8 |
| `self-hosted` (z dywizem) | 0/4 | **0/8** |

Nagłówki nie są tym samym blokiem z innymi wartościami — to **dwa rozłączne bloki**
wstawione w to samo miejsce, między `Current runner version` a
`##[group]GITHUB_TOKEN Permissions`.

**Pozytywnego wiersza „to jest self-hosted" nie ma w ogóle**: słowo `self-hosted` pada
0 razy w 8/8 logach. Jedyne trafienia na `self_hosted` to nazwy **testów tego
repozytorium** w wyjściu zestawu — treść z checkoutu, nie z infrastruktury.

## 4. Rozstrzygnięcie: warunek ZOSTAJE, a powód jest zapisany

Dzisiejsze zgadywanie po obecności `Runner name:` jest w tym materiale poprawne
**12/12**. Zostaje, i oto powód, razem z jego granicą:

- poprawność stoi na **nieobecności** wiersza po stronie GitHuba, a nieobecność jest
  słabszą podstawą niż obecność;
- sygnał przeciwny (`Runner Image Provisioner` / `Hosted Compute Agent` / `Azure Region:`)
  opiera się na obecności i jest logicznie mocniejszy, ale stoi na materiale
  **z jednego dnia** — repozytorium nie ma świeższego logu GitHub-hosted i mieć nie
  będzie, bo od 02.09.2026 wszystko chodzi na self-hosted;
- **przepisanie warunku na sygnał GitHuba byłoby zamianą jednej jednodniowej podstawy
  na drugą**, przy zerowym zysku dla usterki, której pozycja się bała — bo tej usterki
  (cichego wypadnięcia) nie ma.

## 5. Co jest PRAWDZIWĄ luką — i leży gdzie indziej, niż pozycja patrzyła

`Runner name:` nie odróżnia joba `tools` od **żadnego innego joba tego repozytorium**.
Zmierzone czytnikiem z repozytorium na trzech cudzych logach:

```
sim.log            pola: {'data': …, 'job': 'sim',            'maszyna': 'runner', 'modulow': 1,   'pr': 584, 'testow': 5}
                   brakujace: ('sekundy', 'cpu_na_sciane', 'na_czym')
m7-shell.log       pola: {'data': …, 'job': 'm7-shell',       'maszyna': 'runner', 'modulow': 124, 'pr': 584, 'testow': 2434}
                   brakujace: ('sekundy', 'cpu_na_sciane', 'na_czym')
material-style.log pola: {'data': …, 'job': 'material-style', 'maszyna': 'runner', 'pr': 584}
                   brakujace: ('sekundy', 'modulow', 'testow', 'cpu_na_sciane', 'na_czym')
```

**Trzy z pięciu pól wpisu powstają z cudzego logu**, a z `m7-shell` wychodzą
`modulow=124` i `testow=2434` — **co do jednego tyle samo**, co z prawdziwego logu
`tools` z tego samego przebiegu. Nie rzuca się to w oczy niczym, bo **sześć skryptów
w `tools/ci/` woła goły `python3 tools/tests/test_all.py`**: `blender_smoke`,
`m7_shell_check`, `station_details`, `tunnel_alignment`, `vehicle_clearance`,
`visual_smoke`.

Barierą, która cudzy log FAKTYCZNIE zatrzymuje, są dwa wiersze wypisywane wyłącznie
przez krok `Run tool tests`:

| pole | wypis | gdzie w drzewie |
|---|---|---|
| `sekundy` | `czas sciany test_all.py: … s (prog … s)` | `.github/workflows/python-tests.yml`, raz |
| `cpu_na_sciane` | `stosunek CPU/sciana … (podloga …)` | `tools/tests/test_suite_runtime_budget.py` (`werdykt`), raz |

Sygnał treściowy więc **istnieje i `z_logu` już się na nim opiera** — tylko że rozdziela
**JOB**, a nie **MASZYNĘ**. Pozycja pytała o maszynę i dlatego go nie zobaczyła.

## 6. Co z tego weszło do drzewa jako bramka

Nie opis, tylko **wczesne ostrzeżenie**, i to czytane z DRZEWA, nie z logów — logi
opisują przeszłość, a bramka ma zapalić się, zanim ktoś pobierze zły log:

- `test_obecnosc_nazwy_runnera_NIE_rozdziela_joba_tools_od_zadnego_innego` — wejście
  syntetyczne z prawdziwego materiału: log ze zdjętymi dwoma wypisami kroku **nadal
  dostaje `maszyna`**, a wpisu z niego złożyć się nie da. Dopisywać cudzych logów do
  drzewa nie wolno (pole „Poza zakresem"), więc cudzy log jest tu **zbudowany
  z prawdziwego**.
- `test_bariera_stoi_w_DOKLADNIE_JEDNYM_miejscu_drzewa` — każdy z dwóch wypisów bariery
  ma stać w drzewie raz. Druga kopia znaczy drugi job, z którego logu da się złożyć
  komplet, a wtedy odpowiedź tej pozycji przestaje być prawdziwa.
- `test_ile_cudzych_jobow_wypisuje_RAZEM_nieodroznialne_od_tools` — zapadka równościowa
  na **sześć**. Siódmy skrypt sam z siebie nic nie psuje, ale powiększa zbiór logów
  przechodzących przez `WZORY_LOGU` w trzech polach na pięć.

**Własny plik jest ze skanu wycięty i to nie jest wyjątek dla wygody** — `WYPISY_BARIERY`
CYTUJE te wiersze, więc bramka skanująca samą siebie zapalałaby się na własnej deklaracji
i zostałaby wyłączona, nie poprawiona (ta sama konstrukcja co `ZNACZNIK_WLASNEJ_SEKCJI`
w `test_assertion_gate.py`). Żeby wycięcie nie było dziurą, obok stoi warunek: w tym
module wypis ma paść **dokładnie raz**. Mierzy to KN-6.

## 7. Sześć kontroli negatywnych, baza 40/40, ani jedna zielona

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | drugi skrypt CI wypisuje wiersz bariery | 39/40 |
| KN-2 | siódmy skrypt woła goły zestaw | 39/40 |
| KN-3 | wejście syntetyczne przestaje cokolwiek obcinać | 39/40 |
| KN-4 | `maszyna` wiązana z krokiem zamiast z `Runner name:` | **38/40** |
| KN-5 | `sekundy` czytane z wiersza `RAZEM`, który wypisuje KAŻDY job | **37/40** |
| KN-6 | druga kopia wypisu bariery we własnym module | 39/40 |

**KN-5 jest tu najważniejsza**, bo wykonuje dokładnie ten ruch, przed którym ta pozycja
ma bronić — przesuwa barierę z wiersza własnego kroku na wiersz wspólny wszystkim jobom:

```
FAIL test_obecnosc_nazwy_runnera_NIE_rozdziela_joba_tools_od_zadnego_innego:
     z logu bez wypisów kroku zabrakło ['cpu_na_sciane', 'modulow', 'na_czym',
     'sekundy', 'testow'], a spodziewane było ['cpu_na_sciane', 'na_czym', 'sekundy']
     — bariera przesunęła się na inne pola, więc odpowiedź 6.D192 trzeba przeliczyć
```

Zapala trzy bramki naraz, w tym dwie cudze. **KN-4 pokazuje drugą stronę:** związanie
`maszyna` z krokiem zamiast z nazwą runnera czerwieni i nową bramkę, i kontrolę przyrządu
z 6.D152 — czyli zmiana odpowiedzi tej pozycji nie przechodzi po cichu.

## 8. Czego świadomie nie zrobiłem

- **Pola `maszyna` nie zmieniłem na nazwę** — rozstrzygnięte przez 6.D162 na „nie",
  pole „Poza zakresem".
- **`runs-on` nie tknąłem** — to samo pole.
- **Logów do drzewa nie dopisywałem** — to samo pole. Trzy logi cudzych jobów i cztery
  logi GitHub-hosted, na których stoi §3 i §5, leżą poza repozytorium; do drzewa weszło
  wyłącznie wejście **zbudowane z logu, który już tam jest**. Te cztery są materiałem
  **historycznym**, sprzed 02.09.2026, i nie mówią nic o dzisiejszym `runs-on`.
- **Warunku nie przepisałem na sygnał GitHuba**, choć jest logicznie mocniejszy — powód
  i jego granica w §4.

## 9. Zauważone po drodze, nie tknięte

- **`Job is about to start running on the runner` nie występuje w żadnym z dwunastu
  logów** — ani self-hosted, ani GitHub. Ten wiersz stoi w logu **przebiegu**
  (`runs/<id>/logs`), nie joba (`jobs/<id>/logs`), więc przy dzisiejszym sposobie
  pobierania jest niedostępny. Jedyny wzorzec z listy, którego nieobecność może być
  artefaktem punktu pobrania, a nie różnicy runnerów — i dlatego nie oparłem o niego
  niczego.
- **`Cache mode: write`** ma rozkład 8/8 self-hosted wobec 0/4 GitHub, ale materiał
  GitHuba jest **historyczny** i o dwanaście dni starszy, więc równie dobrze może to być
  funkcja usługi wdrożona w międzyczasie. Bez świeższej próbki — której to repozytorium
  nie ma i mieć nie będzie, bo od 02.09.2026 nie chodzi na maszynie GitHuba ani jeden
  job — nie nadaje się na sygnał.
- **Katalog roboczy rozdziela 4/4 wobec 8/8** (`/home/runner/work/…` wobec
  `/home/<użytkownik>/actions-runner-…/_work/…`), ale zależy od nazwy konta i miejsca
  instalacji runnera, więc jako bramka byłby kruchszy od nagłówka.
