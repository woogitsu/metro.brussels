# 6.D190 — szóstka opisuje jeden dzień, a nie stan listy; siódmy i ósmy wpis runnera dopisane

**13.09.2026**, na `6d0152a`. Wejście: `tools/tests/test_suite_runtime_budget.py`
(`POMIARY_RUNNERA`, `test_runner_liczy_rownolegle_a_kontener_szeregowo`),
`reports/6d149-prog-a-maszyna.md`, `reports/6d160-rozrzut-kontenera.md`.

## 1. Czego pozycja żądała

Rozstrzygnięcia, czy pomiary runnera nadal się zapisuje — a jeśli tak, **co asercja
przypina zamiast gołej szóstki**, tak żeby siódmy wpis nie czynił żadnego raportu
nieprawdziwym.

## 2. Jedna asercja robiła DWIE rzeczy

```python
assert len(stosunki) == 6, "wpisow runnera jest %d, a pomiar z 11.09.2026 dal szesc"
```

| co robiła | rodzaj |
|---|---|
| pilnowała, że **każdy** wpis runnera niesie stosunek CPU/ściana | kontrola **żywa** |
| zapisywała, ile przebiegów dał **11.09.2026** | fakt **historyczny** |

Dopóki były jednym zdaniem, **każdy nowy pomiar runnera kosztował edycję twierdzenia
o przeszłości**. Ta sama rodzina, którą 6.D108 rozstrzygnęło dla raportów: zdanie
o wartości bieżącej to nie zdanie o wartości z dnia pomiaru.

## 3. ROZSTRZYGNIĘCIE: zapisujemy dalej, a szóstka zostaje przy swoim dniu

- **Fakt historyczny** stoi osobno: `POMIARY_RUNNERA_11_09` i równość na sześciu,
  w `test_liczba_przebiegow_runnera_z_11_09_jest_FAKTEM_HISTORYCZNYM`. Dzień się
  skończył, więc ta liczba zmienić się nie może — i równość jest tu właściwa.
- **Kontrola żywa** zostaje w starym teście, a liczba wpisów jest tam przypięta
  **podłogą** (`MIN_WPISOW_RUNNERA = 6`), nie równością. Podłoga broni przed jedyną
  rzeczą, przed którą ma bronić: zepsutym czytnikiem listy, który daje zero i cicho
  przechodzi każde `min()` niżej (6.D27).
- Sprawdzenie stosunku (`assert trafienie`) działa na **wszystkich** wpisach, także
  na dopisanych po tej pozycji — KN-1 to potwierdza.

## 4. Siódmy wpis nie kosztuje jednej linii — kosztuje LOG

To jest znalezione po drodze i **ważniejsze od samego rozdzielenia**, bo unieważnia
sposób, w jaki pozycja opisywała swój koszt („dopisanie jednej liczby").

Od 6.D152 wpis runnera ma w drzewie materiał, z którego wyszedł, i **dwie** bramki
tego pilnują:

| bramka | czego żąda |
|---|---|
| `test_kazdy_wpis_runnera_ma_log_w_drzewie` | **równości zbiorów**: log ↔ wpis, w obie strony |
| `test_kazde_pole_wpisu_runnera_wychodzi_z_logu_i_zgadza_sie_z_lista` | wszystkie **pięć** pól wyprowadzone z logu i zgodne **znak w znak** |

Napisałem oba wpisy z ręki i wywróciłem **obie** te bramki. Kiedy log wszedł do drzewa,
druga z nich pokazała, że ręczna wersja miała **trzy usterki naraz** — i żadnej z nich
nie dałoby się zauważyć czytaniem:

| co stało z ręki | co mówi log | dlaczego to usterka |
|---|---|---|
| `"2026-09-12"` (PR #571) | `2026-09-13` | przebieg poszedł na runnera **po północy**; datę wziąłem z dnia, w którym PR powstał |
| ogon `— pierwszy przebieg runnera, który NIE ustanowił nowego maksimum` | `— 2414 testów` | zdanie o **LIŚCIE**, nie o przebiegu. Dokładnie to, co 6.D163 zdjęło z wpisu #528, sprowadzając `WPISOW_Z_DOPISKIEM` do zera; moja wersja podniosłaby je z powrotem do dwóch |
| `2433 testy` | `2433 testów` | odmiana. `proza.startswith(pola["na_czym"])` łapie to na jednym znaku |

Wpisy są więc **wypisane, a nie przepisane**:

```
$ python3 tools/ci/timing_record.py --z-logu tests/data/ci-logs/tools-pr571.log
    ("2026-09-13", 104.530, 124, MASZYNA_RUNNER,
     "job `tools`, PR #571, CPU/ściana 1,819 — 2414 testów"),
# runner: metro-wsl-DOM-NEW-03
$ python3 tools/ci/timing_record.py --z-logu tests/data/ci-logs/tools-pr583.log
    ("2026-09-13", 113.982, 124, MASZYNA_RUNNER,
     "job `tools`, PR #583, CPU/ściana 1,781 — 2433 testów"),
# runner: metro-wsl-DOM-NEW-01
```

Do drzewa weszły dwa logi — **285 957 B** i **289 016 B**, dosłowne i niespakowane
(powody, oba zmierzone, stoją w `tests/data/ci-logs/README.md`). Sprawdzone przed
wstawieniem: czytelne jako UTF-8, **zero** wzorców konfliktu na początku wiersza,
sekrety zamaskowane przez GitHuba.

**Odpowiedź pozycji to nie zmienia, ale zmienia jej cenę i ta cena jest tu zapisana:**
zapisujemy dalej, a każdy zapisany przebieg to ok. 290 KB materiału w historii. Czterech
przebiegów tej sesji (#579–#582) nie dopisałem właśnie dlatego (§8).

### Co z tego weszło do listy

| dzień | ściana | moduły | CPU/ściana | testów | skąd |
|---|---:|---:|---:|---:|---|
| 2026-09-13 | 104,530 s | 124 | 1,819 | 2414 | job `tools`, PR #571 |
| 2026-09-13 | 113,982 s | 124 | 1,781 | 2433 | job `tools`, PR #583 |

Wpisów runnera jest odtąd **osiem**, z 11.09 nadal **sześć**. Żaden nowy nie rusza
maksimum — `MEASURED_MAX_WALL_S` zostaje **116,404 s**, a `MARGIN` **1,2886×**.
Zmiana progu jest poza zakresem pozycji i nie była potrzebna.

## 5. Znalezione po drodze: zdanie raportu 6.D149 NIE NIESIE DATY

Pozycja zakładała, że zdanie „w sześciu przebiegach" z `reports/6d149-prog-a-maszyna.md`
odnosi się do 11.09.2026. **Odnosi się, ale nie mówi tego.** W raporcie nie ma tam
żadnej daty; kotwicą jest **liczba modułów (122)** stojąca w sąsiednim zdaniu — a wpisów
runnera o 122 modułach jest dokładnie tych sześć z 11.09, żadnego innego dnia.

Bramka pilnuje więc **kotwicy, która istnieje**, a nie daty, której nie ma: sprawdza,
że raport nadal podaje 122 i że zbiór wpisów o 122 modułach pokrywa się co do jednego
z przebiegami z 11.09. Raportu nie przepisywałem — pole „Poza zakresem" mówi to wprost.

**Jest to materiał dla 6.D196** („liczba w polu «Skąd» opisuje dzień pomiaru, a czyta
się jak bieżącą") w drugim miejscu niż tamta pozycja patrzy: nie w `docs/TASKS.md`,
tylko w prozie raportu.

## 6. Sześć kontroli negatywnych, baza 25/25

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | nowy wpis runnera **bez** stosunku CPU/ściana | 24/25 |
| KN-2 | siódmy wpis wpisany z datą 11.09 | 24/25 |
| KN-3 | liczba modułów zdjęta z raportu 6.D149 | 24/25 |
| KN-4 | podłoga z powrotem równością (stan sprzed tej pozycji) | 24/25 |
| KN-5 | jeden przebieg z 11.09 zdjęty z listy | 24/25 |
| KN-6 | skan stosunków oślepiony (pętla bez obrotów) | 24/25 |

**KN-1 jest tu najważniejsza i to ona była żądaniem pola „Weryfikacja":** rozdzielenie
nie zgasiło tej połowy, która działała. Wpis dopisany bez stosunku — **dziewiąty**,
syntetyczny, dopisany na koniec listy — nadal zapala bramkę:

```
FAIL test_runner_liczy_rownolegle_a_kontener_szeregowo: wpis runnera nie podaje
     stosunku CPU/ściana: job `tools`, PR #999, 2400 testów
```

Zapala się więc na wpisie **dopisanym po tej pozycji**, a nie tylko na sześciu starych.

**KN-4 pokazuje drugą stronę:** przywrócenie równości natychmiast czerwieni listę
ośmiu wpisów. Dokładnie to, co kosztowało edycję twierdzenia o przeszłości przy każdym
nowym pomiarze.

```
FAIL … wpisow runnera jest 8 przy podlodze 6 …
     [1.971, 1.857, 1.801, 1.81, 1.61, 1.599, 1.819, 1.781]
```

**KN-6 mówi, po co ta podłoga w ogóle stoi**, bo sama podłoga wygląda na ustępstwo:

```
FAIL … wpisow runnera jest 0 przy podlodze 6 … []
```

Bez niej pusta lista przeszłaby każde `min()` niżej bez jednego sprawdzenia — i to
jest jedyna rzecz, przed którą ta liczba ma bronić (6.D27).

**Pierwsza próba KN-6 wyszła 25/25 i to NIE była kontrola zielona** — podstawienie
nie weszło, bo szukałem pętli po `POMIARY_RUNNERA`, a stoi tam pętla po `POMIARY`
z warunkiem na maszynę w środku. Wynik „baza, nie kontrola" ma w tym projekcie własną
nazwę od 6.D27 i wygląda dokładnie tak samo jak mechanizm bezczynny. Rozstrzyga
`grep` na podstawionym pliku, wykonany **przed** przebiegiem, a nie po.

## 7. Czego świadomie nie zrobiłem

- **Progu runnera, zapasu i podłogi mierzalności nie tknąłem** — pole „Poza zakresem".
  Nie było zresztą po co: żaden nowy wpis nie rusza maksimum.
- **`reports/6d149-prog-a-maszyna.md` nie przepisany** — to samo pole. Zamiast tego
  bramka pilnuje kotwicy, która w nim stoi.
- **Pomiarów kontenera nie dopisywałem** — to samo pole.
- **Raportów 6.D149, 6.D152, 6.D162 i 6.D164 nie przepisywałem**, choć każdy mówi
  „sześć logów". Każdy mówi to o **swoim dniu pomiaru** i dalej jest prawdziwy —
  to rozstrzygnięcie 6.D108, a nie wygoda. Przepisana została natomiast proza **żywa**,
  która prawdziwa być przestała: nagłówek i tabela `tests/data/ci-logs/README.md`
  oraz dwa komentarze w `tools/tests/test_timing_record.py`, gdzie liczba logów
  stała jako opis stanu katalogu. W obu miejscach liczby już nie ma: katalog rośnie
  z każdym wpisem, a druga kopia tej liczby rozjechałaby się przy pierwszym z nich
  (6.B28).

## 8. Zauważone po drodze, nie tknięte

- **Runner ma dziś w logach jeszcze cztery przebiegi z tej sesji** (PR-y #579–#582),
  każdy z własnym wierszem `[CZAS]`. Nie dopisałem ich, bo każdy kosztuje pobranie
  **i zacommitowanie** pełnego logu joba (§4), a pozycja pytała o siódmy wpis
  i o mechanizm, nie o komplet. Materiał leży w logach GitHuba i **ucieka**: artefakt
  czasu żyje trzydzieści dni (6.D164), log joba tyle, ile retencja logów Actions.
  Kto chce te cztery, ma czas — ale nie w nieskończoność.
- Stosunek CPU/ściana runnera zsuwa się z czasem: **1,971** przy 122 modułach
  (11.09) wobec **1,781** przy 124 (13.09). Osiem punktów to za mało, żeby nazwać to
  trendem, i tak to tu zostawiam — bez dorabianej reguły.
