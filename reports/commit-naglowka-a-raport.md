# 6.D10 · Czy commit z nagłówka raportu ma cokolwiek wspólnego z raportem

**Zmierzone 06.09.2026 na commicie:** `08d12b689b5a03b6f307ba46b4eb5134d89b882f`

## 0. Liczba z polecenia kontra liczba zmierzona

Zadanie przynosi liczbę z pomiaru sprzed kilku godzin (na `51d324a`, 06.09.2026
09:56): **48** raportów z SHA w nagłówku, **25** bez żadnej z dwóch relacji,
`51fd842` w **siedmiu**. Zmierzone teraz, na HEAD tej gałęzi:

| | z polecenia (`51d324a`) | zmierzone teraz (`08d12b6`) |
|---|---|---|
| raportów w `reports/` w ogóle | 63 | **71** |
| raportów z ≥1 SHA w nagłówku | 48 | **69** |
| raportów cytujących `51fd842` jako główny SHA nagłówka | 7 | **9** |

Różnica nie jest błędem pomiaru — to ta sama sesja, w której to zadanie powstało,
dopisała między `51d324a` a HEAD **8 nowych plików** w `reports/` (m.in.
`bpy-extraction-round-2.md`, `bpy-extraction-round-3.md`, `energy-balance.md`,
`mutation-triage-round-2-modules.md`, `L1_A-track-spacing.md`), z których większość
od razu niesie SHA w nagłówku. Liczby z prompta są więc już nieaktualne w chwili
pisania tego raportu, i to jest dokładnie zjawisko, przed którym ostrzega
`tools/tests/test_report_hygiene.py`: **datowanego pomiaru się nie przelicza**, ale
NOWY pomiar musi podać własne liczby, a nie cytować cudze jako aktualne. Reszta tego
raportu liczy na **69**, nie na 48.

## 1. Metoda pomiaru

Dla każdego raportu w `reports/` z co najmniej jednym tokenem `` `[0-9a-f]{7,40}` ``
w **nagłówku** (tekst przed pierwszym `## `, dokładnie ta sama definicja co
w `test_report_hygiene.py`) wzięty jest **pierwszy** taki token — to on stoi przy
polu „Zmierzone (…) na commicie" / „Snapshot na commicie" / „Scalone na" w każdym
sprawdzonym przypadku (patrz §4 o tokenach dodatkowych, gdy jest ich więcej niż
jeden). Dla tego SHA sprawdzane są po kolei:

1. **`git cat-file -e <SHA>^{commit}`** — jeśli zawodzi, werdykt to **NIEOSIĄGALNY**
   i dalej nic się nie sprawdza (obiektu nie ma czym sprawdzić).
2. **`git log --follow --format=%H -- reports/<plik>`** — jeśli pełny SHA jest na
   tej liście, werdykt to **DOTYKA** (ten commit rzeczywiście zmienił plik raportu).
3. W przeciwnym razie: **`git merge-base --is-ancestor <SHA> <W>`**, gdzie `<W>` to
   najstarszy commit, który wprowadził **dokładnie ten token** do pliku
   (`git log --follow -S<token> -- reports/<plik>`, pickaxe na sam ciąg znaków, nie
   na cały diff). Gdy prawda — werdykt to **PRZODEK_WPROWADZENIA** (SHA jest
   przodkiem commita, który zapisał to zdanie w raporcie). Gdy fałsz — **ŻADNA**.

Pickaxe na token, a nie „pierwszy commit, który w ogóle dodał plik" (co była pierwsza,
odrzucona wersja tego skryptu) jest tu istotny: nagłówki bywają **przepisywane**
(patrz `mutation-sweep.md` niżej), więc pytanie o relację musi dotyczyć commita,
który wpisał TEN KONKRETNY SHA, nie commita, który stworzył plik po raz pierwszy.
Z pierwszą, węższą wersją metody 6 raportów fałszywie wypadało jako ŻADNA, mimo że
SHA z ich nagłówka był przodkiem edycji, która ten SHA tam zapisała — poprawka opisana
niżej w §5 jest częścią tego pomiaru, nie tylko metodologiczną notatką.

## 2. Wynik zbiorczy

| kategoria | liczba (na 69 raportów, główny token nagłówka) |
|---|---|
| **DOTYKA** — SHA sam zmienił plik raportu | 23 |
| **PRZODEK_WPROWADZENIA** — SHA jest przodkiem commita, który wpisał to zdanie | 41 |
| **ŻADNA** — ani jedno, ani drugie | 4 |
| **NIEOSIĄGALNY** — obiekt nie istnieje w drzewie | 1 |

23 + 41 + 4 + 1 = 69. Innymi słowy: **65 z 69** (94 %) niesie SHA, który albo
bezpośrednio dotknął pliku, albo jest jego przodkiem — dokładnie ten rozkład, który
`docs/TASKS.md` nazywa „naturalną kolejnością pracy": zmierz, scal, dopisz raport
commitem następnym. **Cztery** przypadki nie mieszczą się w żadnej z tych dwóch
relacji i są wymienione z nazwy w §5 — żaden z nich nie jest literówką ani
przypadkiem: wszystkie cztery to jeden i ten sam, powtarzalny wzorzec.

## 3. Pełna tabela — 69 raportów, jeden werdykt na raport

| raport | SHA w nagłówku | werdykt |
|---|---|---|
| `L1_A-chunks.md` | `51fd842` | przodek |
| `L1_A-crosscheck.md` | `51fd842` | przodek |
| `L1_A-geometry.md` | `51fd842` | przodek |
| `L1_A-lod.md` | `51fd842` | przodek |
| `L1_A-track-spacing.md` | `51fd842` | przodek |
| `M7-clearance-profile.md` | `51fd842` | dotyka |
| `M7-curve-clearance.md` | `51fd842` | przodek |
| `M7-in-tunnel.md` | `d4a9c54` | dotyka |
| `M7-shell-liczba-testow.md` | `77c72da` | przodek |
| `M7-shell.md` | `51fd842` | przodek |
| `R-007-platform-dimensions.md` | `68e1c81` | dotyka |
| `T-011-detail-markers.md` | `c6eb1ca` | dotyka |
| `T-011-details-BF.md` | `154ad30` | przodek |
| `T-012-godot-capture.md` | `4575195` | dotyka |
| `T-113-timetable.md` | `e2c32e9` | dotyka |
| `T-211-station-layout.md` | `1426940` | dotyka |
| `T-211-stations-BF.md` | `527f509` | przodek |
| `T-212-station.md` | `a5356f0` | przodek |
| `T-310-physics.md` | `614bfeb` | dotyka |
| `T-311-braking.md` | `9c94c1a` | dotyka |
| `T-312-doors.md` | `ed0f5e2` | dotyka |
| `T-400-first-run.md` | `39123b9` | dotyka |
| `T-400-stage-3b.md` | `619b179` | przodek |
| `axis-station-chainage.md` | `4a03982` | dotyka |
| `bpy-extraction-round-2.md` | `3c01fbb` | **ŻADNA** |
| `bpy-extraction-round-3.md` | `fc5db5ff09eb3257e18ac6d8aaa7c5811f32fa18` | **ŻADNA** |
| `branch-audit.md` | `737d592` | przodek |
| `clearance-BE.md` | `1b7c2bb` | dotyka |
| `droga-do-grywalnosci.md` | `3c242f7` | przodek |
| `dziennik-mutacyjny.md` | `05c0f59` | przodek |
| `energy-balance.md` | `d48f5a1d79396208b2459c3f9090db11833097fa` | **ŻADNA** |
| `golden-trace-gate.md` | `51d324a` | przodek |
| `kolejka-audyt-aktualnosci.md` | `9b4d26d` | przodek |
| `kolejka-uzupelnienie.md` | `51d324a` | przodek |
| `linecore-budget.md` | `6c1048b` | przodek |
| `m7-glb-nondeterminism.md` | `2fa30c1` | dotyka |
| `m7-ground-truth-verification.md` | `51fd842` | przodek |
| `mutacje-rdzen-sygnalizacji.md` | `3c242f7` | przodek |
| `mutation-drift.md` | `6c1048b` | przodek |
| `mutation-sweep.md` | `66b8301` | przodek |
| `mutation-triage-alignment.md` | `14ceed2` | dotyka |
| `mutation-triage-clearance.md` | `5f6b68e` | przodek |
| `mutation-triage-fizyka.md` | `737d592` | przodek |
| `mutation-triage-inspire-rail.md` | `737d592` | przodek |
| `mutation-triage-lod.md` | `c572eb3` | **NIEOSIĄGALNY** |
| `mutation-triage-m7-report.md` | `8c3f752` | przodek |
| `mutation-triage-make-test-track.md` | `ec926a2` | przodek |
| `mutation-triage-parametry.md` | `737d592` | przodek |
| `mutation-triage-placement.md` | `3262bb4` | dotyka |
| `mutation-triage-png-metadata.md` | `737d592` | przodek |
| `mutation-triage-round-2-modules.md` | `9a57130a10699d4a1362fc1cac08ed05b0ba3aa9` | **ŻADNA** |
| `mutation-triage-surface-width.md` | `b5bcf34` | dotyka |
| `mutation-triage-sweep.md` | `7a817df` | przodek |
| `mutation-triage-validate.md` | `cdf0591` | dotyka |
| `mutation-triage-wczytywanie.md` | `737d592` | przodek |
| `mutation-triage-wizualna.md` | `737d592` | przodek |
| `network-chainage.md` | `580882c` | dotyka |
| `package-a-station-source-gaps.md` | `8e2faea` | dotyka |
| `packages-BE-tunnels.md` | `aeaa322` | dotyka |
| `packages-BF-alignment.md` | `d47ae47` | dotyka |
| `pixel-hash-oracle.md` | `4516a13` | przodek |
| `report-claims-audit.md` | `e2382f7` | przodek |
| `service-day.md` | `0aec7ae` | przodek |
| `snapshot-drift.md` | `377b59e` | przodek |
| `surface-vs-tunnel.md` | `01c457d` | dotyka |
| `typy-sim-bez-testu.md` | `4e56958` | przodek |
| `wyrocznia-mutacyjna-falszywe-zabicia.md` | `8c3f752` | przodek |
| `zapadka-dwie-role.md` | `154ad30` | przodek |
| `zapadka-liczy-prace.md` | `8edb1d8` | przodek |

(69 wierszy — dwa raporty, `R-006-line-speed.md` i `T-401-line-run.md`, nie mają
żadnego SHA w nagłówku wcale; to zamierzony wyjątek `COMMIT_EXCEPTIONS`
w `tools/tests/test_report_hygiene.py`, więc nie są w tej tabeli w ogóle — nie jest
to przeoczenie tego pomiaru.)

## 4. Sześć raportów z więcej niż jednym SHA w nagłówku

Sześć raportów niesie w nagłówku **więcej niż jeden** token wyglądający jak SHA.
Tabela w §3 liczy tylko **pierwszy** (ten przy polu „Zmierzone / Snapshot / Scalone
na commicie" — sprawdzone ręcznie w każdym z sześciu przypadków, że to faktycznie
ten opisany jako „commit pomiaru", nie przypadkowy sąsiad). Pozostałe tokeny są
odsyłaczami do INNYCH commitów/raportów/gałęzi, wymienionych w tym samym akapicie
z osobnym podpisem — mierzone tu osobno, żeby żaden SHA w nagłówku nie został pominięty:

| raport | token dodatkowy | werdykt | co to jest naprawdę |
|---|---|---|---|
| `T-400-stage-3b.md` | `cb7321e` | przodek | commit PR-a #210 (`stacje-w-scenie`), scalonego wcześniej tego samego etapu |
| `T-400-stage-3b.md` | `32588a8` | przodek | commit PR-a #212 (`scena-przejazd-linii`) |
| `T-400-stage-3b.md` | `9e2066aef7ef` | NIEOSIĄGALNY | **to w ogóle nie jest commit** — to hash builda Blendera 5.2.1 LTS, zacytowany w opisie środowiska pomiaru. Wygląda jak SHA (sam hex), test `test_report_hygiene.py` łapie go tym samym wzorcem `COMMIT`, i tak samo łapie go ten pomiar — ale `git cat-file -e` słusznie się na nim wywraca, bo obiektu o takiej treści nikt nigdy nie stworzył. Fałszywe trafienie wzorca, nie błąd repozytorium. |
| `linecore-budget.md` | `dfbde8f` | przodek | ten sam zestaw pomiarów wykonany 90 min wcześniej, cytowany jako kontrola powtarzalności w §8.4 tego raportu |
| `mutacje-rdzen-sygnalizacji.md` | `a3d8c57` | **ŻADNA** | „commit raportu" przeglądu **A** na gałęzi PR #229 — ta gałąź nigdy nie wylądowała na `main` jako taka, bo dwa równoległe przeglądy zostały ręcznie scalone w jeden plik przez commit `3c242f7` (główny token, patrz §3) |
| `mutacje-rdzen-sygnalizacji.md` | `cbd1192` | **ŻADNA** | to samo, „commit raportu" przeglądu **B**, gałąź PR #230 |
| `mutacje-rdzen-sygnalizacji.md` | `d495051` | przodek | commit `main`, na którym mierzył przegląd A (`mierzony commit main` w tabeli raportu) |
| `mutacje-rdzen-sygnalizacji.md` | `b41c158` | przodek | to samo dla przeglądu B |
| `mutation-drift.md` | `66b8301` | przodek | snapshot poprzedniego audytu (`mutation-sweep.md`), z którym ten raport się porównuje |
| `mutation-sweep.md` | `737d592` | przodek | snapshot JESZCZE wcześniejszego audytu (03.09.2026), z którym ten raport się porównuje |
| `mutation-triage-sweep.md` | `66b8301` | przodek | snapshot `reports/mutation-sweep.md`, z którego ten raport bierze punkt odniesienia „37/79" |

Te dziesięć dodatkowych tokenów **nie są błędami** — to raporty odsyłające do
commitów INNYCH raportów albo INNYCH gałęzi, cytowane jawnie jako punkt odniesienia,
z podpisem obok w tym samym akapicie. Jedyny naprawdę osobny przypadek to
`9e2066aef7ef`: nie jest to w ogóle commit, tylko hash builda Blendera, i trafia
w ten sam wzorzec regex z zupełnie innego powodu niż squash-merge (patrz §6).

Dwa z tych dziesięciu (`a3d8c57`, `cbd1192`) to jednak prawdziwe „ŻADNA" —
z tego samego, dobrze rozumianego powodu co całe §5: commit na gałęzi, która
nigdy nie stała się częścią `main` w tej postaci.

## 5. Cztery przypadki „ŻADNA" — z nazwy, jak wymaga zadanie

Wszystkie cztery są dziś (06.09.2026) i wszystkie mają **ten sam mechanizm**:
raport zapisał w nagłówku SHA z **gałęzi funkcyjnej tej samej sesji**, a ta gałąź
wylądowała na `main` przez commit, którego treść jest identyczna, ale którego SHA
jest **inny obiekt** — bo commit na `main` nie jest tym samym commitem co na
gałęzi (squash / przepisanie historii przy scaleniu), tylko nowym obiektem
o tej samej treści i innym rodzicu. Stąd żadna z dwóch relacji nie zachodzi: SHA
z nagłówka nie dotyka pliku (bo plik wylądował na `main` przez INNY commit) i nie
jest jego przodkiem (bo graf commitów `main` go w ogóle nie zawiera — to gałąź
równoległa, nie przodek).

1. **`bpy-extraction-round-2.md`** — SHA `3c01fbb` istnieje jako obiekt
   (`git cat-file -e` przechodzi), ale nie jest osiągalny z **żadnej** gałęzi ani
   tagu w tym repozytorium (`git branch/tag --contains` i przegląd wszystkich refów
   dają pustą listę — sprawdzone wprost, nie założone). Plik wprowadził commit
   `97c20c1` na `main`, o identycznym komunikacie („6.B9: logika spod bpy
   wyciągnięta…"), ale innym SHA.
2. **`bpy-extraction-round-3.md`** — SHA `fc5db5ff09eb3257e18ac6d8aaa7c5811f32fa18`,
   ten sam wzorzec: plik wprowadził `10e7828` na `main`, SHA z nagłówka jest
   nieosiągalny z żadnego refa.
3. **`energy-balance.md`** — SHA `d48f5a1d79396208b2459c3f9090db11833097fa`. Ten
   raport **sam to mówi w treści**, zdaniem w nawiasie zaraz po nagłówku: „(Ten SHA
   jest commitem tej sesji na `claude/6a5-bilans-energii`, który już niósł kod…)" —
   czyli autor raportu wiedział, że cytuje commit gałęzi, nie `main`, i zapisał to
   wprost. Plik wprowadził na `main` commit `88bd4b3`, innym SHA, ten sam komunikat.
4. **`mutation-triage-round-2-modules.md`** — SHA
   `9a57130a10699d4a1362fc1cac08ed05b0ba3aa9`, ten sam wzorzec: plik wprowadził
   `6267a2c` na `main`.

**Uwaga o trwałości tego stanu.** Wszystkie cztery obiekty dziś **istnieją**
(`cat-file -e` przechodzi), ale żaden nie jest osiągalny z żadnej gałęzi ani tagu —
to dokładnie stan „dangling", opisany w docstringu `test_report_hygiene.py` jako
powód, dla którego bramka **nie** sprawdza osiągalności: te cztery obiekty przeżyły
tylko dlatego, że lokalne repozytorium jeszcze ich nie wygarbage-collectowało (albo
zostały pobrane razem z gałęzią przed jej squash-mergem). Zwykłe `git gc --prune=now`
albo świeży płytki klon (patrz §7) sprawiłyby, że wszystkie cztery przeszłyby z
„ŻADNA" do **NIEOSIĄGALNY** — to nie są dwie różne usterki, to jeden i ten sam
przypadek w dwóch fazach swojego życia.

## 6. Jeden przypadek NIEOSIĄGALNY (główny token nagłówka)

**`mutation-triage-lod.md`** → `c572eb3`. `git cat-file -e c572eb3^{commit}` zawodzi
— obiektu nie ma w drzewie w ogóle, nawet jako dangling. To dokładnie ten przypadek,
który `test_report_hygiene.py` cytuje wprost w swoim docstringu jako powód, dla
którego świadomie nie sprawdza osiągalności SHA („`reports/mutation-triage-lod.md`
podaje `c572eb3` i ten SHA nie rozwiązuje się w `main`"). Ten pomiar go potwierdza,
nie odkrywa na nowo.

```
$ git cat-file -e c572eb3^{commit} ; echo $?
1
```

## 7. Dlaczego bramka oparta na `git log` / `merge-base` nie przetrwałaby CI

Sprawdzone wprost, zgodnie z instrukcją zadania — świeży płytki klon zamiast pełnego
worktree:

```
$ rm -rf /tmp/plytki-klon-d10
$ git clone -q --depth 1 file:///…/wt-d10 /tmp/plytki-klon-d10
$ cd /tmp/plytki-klon-d10 && git log --oneline | wc -l
1
$ git rev-parse --is-shallow-repository
true
```

Płytki klon ma **jeden** commit w historii. `git log --follow -- reports/…` i
`git merge-base --is-ancestor` na czymkolwiek poza tym jednym commitem albo zwracają
pustą historię, albo kończą się błędem „no merge base" — i to jest dokładnie to samo
ograniczenie, na które `.github/workflows/*.yml` w tym repozytorium już natrafia
z `actions/checkout` na domyślnym `fetch-depth: 1` (`CLAUDE.md` §9, akapit o
`prune-merged-branches.yml` jako jedynym wyjątku). **Bramka oparta na tej relacji
działałaby na tej maszynie, w tym worktree z pełną historią — i nigdzie indziej.**
Na `ubuntu`/self-hosted runnerze z płytkim checkoutem każdy test wykonujący
`git merge-base --is-ancestor` na commicie starszym niż płytki punkt odcięcia
kończyłby się fałszywym negatywem (`fatal: … does not exist` albo `NO` z powodu
braku historii, nie z powodu braku relacji) — czyli bramka kłamałaby w jedną stronę
akurat na tej samej maszynie, na której ma stać.

## 8. Dlaczego ta pozycja **nie** dostaje bramki

Warunek z `docs/TASKS.md` na dopisanie bramki: „relacja prawdziwa dla wszystkich
poza wymienionymi wyjątkami". Nie jest tu spełniony z **dwóch niezależnych** powodów,
każdy sam w sobie wystarczający:

1. **Cztery przypadki z §5 nie są wyjątkami do wypisania na stałą listę — są
   powtarzalnym trybem pracy tej sesji** (squash-merge gałęzi zadaniowej tego samego
   dnia). Kolejne zadania tej sesji będą produkować kolejne takie przypadki
   (widać to już w dynamice §0: 8 nowych raportów między dwoma pomiarami tego samego
   dnia) — a `MAX_COMMIT_EXCEPTIONS` w `test_report_hygiene.py` jest **zapadką
   w dół**, zamkniętą świadomie na 2, właśnie po to, żeby wyjątków nie dopisywać
   „na zapas". Bramka na tę relację odziedziczyłaby ten sam problem, tylko bez
   zapadki, która go dziś powstrzymuje w tamtym module.
2. **Sama relacja nie przetrwałaby CI** — §7 pokazuje to wykonaną kontrolą, nie
   przewidywaniem: płytki klon z domyślnym `fetch-depth: 1` nie ma historii, na
   której `git merge-base --is-ancestor` mógłby cokolwiek rozstrzygnąć. Bramka
   zbudowana na tej relacji byłaby czerwona (albo fałszywie zielona przez brak
   historii, co jest gorsze) na dokładnie tym self-hosted runnerze, na którym CI
   tego projektu faktycznie chodzi.

Wynik „żadnej relacji nie wolno przybić bramką, bo historia jest przepisywana" jest
tu **dosłownie prawdziwy w obu znaczeniach tego zdania**: historia jest przepisywana
w sensie squash-merge (§5) i w sensie płytkiego checkoutu (§7). `docs/TASKS.md`
nazywa to poprawnym zakończeniem pozycji i to jest jej zakończenie.

## 9. Weryfikacja

```
$ python3 tools/tests/test_all.py 2>&1 | tail -3
```
— wynik wklejony w raporcie do właściciela zadania (ta pozycja nie zmienia żadnego
pliku produkcyjnego ani żadnej bramki, więc liczba testów nie rusza się względem
stanu przed tym zadaniem).

## 10. Poza zakresem tej pozycji

Nagłówki `bpy-extraction-round-2.md`, `bpy-extraction-round-3.md`,
`energy-balance.md`, `mutation-triage-round-2-modules.md` i `mutation-triage-lod.md`
**nie zostały poprawione** — `docs/TASKS.md` wprost zabrania dopisywania ani
podmieniania SHA w nagłówkach raportów w tej pozycji: „pozycja mierzy zapis, nie
poprawia go; poprawka bez pomiaru zamazałaby dowód". Podmiana SHA `d48f5a1d…` na
`88bd4b3` w `energy-balance.md` byłaby dokładnie taką poprawką — i jest osobnym
zadaniem, nie tym.
