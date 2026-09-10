# Zmiana akcji lokalnej nie odpalała ani jednego joba, który jej używa (6.D78)

**Zmierzone 10.09.2026 na:** `150e746`, kontener tej sesji.
**Przyrząd:** przejście po dziesięciu workflowach z `yaml.safe_load`,
`python3 tools/tests/test_all.py`, cztery kontrole negatywne z `md5sum -c`
po każdym powrocie.

---

## 1. Macierz, od której zaczyna się ta pozycja

Dziesięć workflowów, każdy użyty raz. Kolumna „filtr obejmuje akcje" jest tą, o którą
chodzi:

| workflow | używa akcji | ma `paths:` | filtr obejmuje `.github/actions/` |
|---|---|---|---|
| blender-smoke.yml | check-workspace, probe-tools | 6 wzorców | **NIE** |
| godot-first-run.yml | check-workspace, probe-tools | 11 wzorców | **NIE** |
| m7-shell.yml | check-workspace, probe-tools | 9 wzorców | **NIE** |
| material-style-smoke.yml | check-workspace, probe-tools | 6 wzorców | **NIE** |
| station-details.yml | check-workspace, probe-tools | 13 wzorców | **NIE** |
| tunnel-alignment.yml | check-workspace, probe-tools | 15 wzorców | **NIE** |
| visual-regression.yml | check-workspace, probe-tools | 7 wzorców | **NIE** |
| python-tests.yml | check-workspace | brak filtra | — |
| sim-tests.yml | check-workspace | brak filtra | — |
| prune-merged-branches.yml | check-workspace | brak `pull_request` | — |

**Siedem luk.** Dwa doprecyzowania, oba istotne i oba potwierdzone przeliczeniem:

- **`check-workspace` ma dwóch konsumentów bez filtra** — `python-tests.yml`
  i `sim-tests.yml` odpalają się na każdym pull requeście, więc zmiana tej akcji
  była przed scaleniem **de facto wykonywana**;
- **`probe-tools` nie ma takiego konsumenta ani jednego.** Wszystkie siedem
  workflowów, które jej używają, mają filtr, a filtr jej katalogu nie obejmował.
  Jej zmiana nie była przed scaleniem wykonywana **wcale**.

`prune-merged-branches.yml` ma wyłącznie `workflow_dispatch`, więc stoi poza regułą —
tego wprost żąda pole „Skończone, gdy" („workflowy bez filtra i bez wyzwalacza
`pull_request` zostają poza listą, żeby bramka nie wymuszała martwych wpisów").

## 2. Dlaczego to nie jest nowy pomysł, tylko brakujące rodzeństwo

`test_ci_workflows_running_tools_ci_are_triggered_by_tools_ci` stoi w tym samym pliku
od 02.09.2026 i wyrósł z pomiaru: `tools/ci/vehicle_clearance.sh` (495 linii) był
wołany w `tunnel-alignment.yml`, ale w `paths:` siedział wyłącznie
`tools/ci/tunnel_alignment.sh` — **wstrzyknięty `exit 3` przeszedł**, bo job w ogóle
się nie uruchomił.

Akcja lokalna jest dokładnie tym samym rodzajem kodu: mieszka w repozytorium, zmienia
się razem z gałęzią i jej treść wykonuje ten sam runner właściciela. Brakowało jej
rodzeństwa tamtej bramki, i to jest cała treść tej pozycji.

## 3. Akcja z Marketplace do tej reguły NIE należy

`actions/checkout@d23441a4…` jest przypięta po SHA commita (`CLAUDE.md` §9) i nie
zmienia się razem z gałęzią, więc jej zmiana nie może wejść przez pull request do tego
repozytorium. Wzorzec `AKCJA_LOKALNA` żąda przedrostka `./`, a kontrola negatywna
sprawdza obie strony tego rozróżnienia.

## 4. Poprawka

`- '.github/actions/**'` dopisane do `paths:` siedmiu workflowów, z komentarzem
odsyłającym do tego samego powodu, co przy `tools/ci/**` wyżej w tej samej liście.

## 5. Cztery kontrole negatywne, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK` (jedenaście plików).

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | wzorzec znika z JEDNEGO workflowa | **czerwona** 74/75, nazywa `tunnel-alignment.yml`, obie akcje i dzisiejsze wzorce |
| KN-2 | bramka liczy też akcje z Marketplace | **czerwona** 74/75, zgłasza `actions/checkout` |
| KN-3 | bramka przestaje pomijać workflowy bez filtra | **czerwona** 74/75, wymusza martwy wpis w `prune-merged-branches.yml` |
| KN-4 | skan akcji przestaje cokolwiek widzieć | **czerwona** 73/75, obie kontrole przyrządu |

KN-3 jest tu najważniejsza i nie jest kontrolą dla samej symetrii: pokazuje, że
pominięcie workflowów bez filtra to **warunek pola „Skończone, gdy"**, a nie
złagodzenie bramki — bez niego reguła żądałaby wpisu w pliku, który nie ma
`pull_request` wcale.

## 6. Kontrola przyrządu z liczbami zmierzonymi, nie okrągłymi

`test_the_local_action_gate_is_looking_at_workflows_that_use_local_actions` przybija
rozkład: **10** workflowów z akcją lokalną, **7** z akcją i filtrem, **3** z akcją
bez filtra — z nazwami — i osobno, że `prune-merged-branches.yml` nie ma
`pull_request`, a dwa pozostałe mają. Bez tego wiersza pusta lista zgłoszeń byłaby
zielona także po literówce we wzorcu (KN-4).

## 7. Czego NIE zrobiłem

**Nie tknąłem zawartości samych akcji** ani **nie dodałem żadnego wyzwalacza** — oba
stoją w polu „Poza zakresem". `prune-merged-branches.yml` nadal chodzi wyłącznie
z `workflow_dispatch` i tak ma zostać.
**Nie sprawdziłem tego przebiegiem**: ta zmiana dotyczy warunku URUCHOMIENIA joba,
więc jej skutek widać dopiero w pull requeście, który rusza **wyłącznie** plik pod
`.github/actions/` — a ten commit rusza też `tools/tests/`, czyli odpaliłby te joby
i bez niej. Dowodem jest tu treść filtra i bramka.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py test_ci_workflows.py
  -> 75/75 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 94,198 s, 2136 testów, 113 modułów, kod 0

yaml.safe_load po dziesięciu workflowach: wszystkie parsują się
```

Zestaw urósł z **2133** do **2136** testów; modułów bez zmiany.
