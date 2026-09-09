# Wspólna grupa `concurrency` kasuje N−2 przebiegi z N (6.D52)

**Zmierzone 09.09.2026 na:** `d5b919b`, pull request #450 na puli właściciela.
**Przyrząd:** trzy fale commitów na jednej gałęzi, każda z inną liczbą plików
workflowu w różnicy pull requesta, czyli z inną liczbą przebiegów w jednej grupie;
stany przebiegów próbkowane co 15 s przez REST GitHuba; `python3 tools/tests/test_all.py`.

---

## 1. Odpowiedź na pytanie wpisu, w jednym zdaniu

Trzeci przebieg w grupie **nie opóźnia — anuluje oczekującego**, i nie jest to
regularność wyczytana z dokumentacji, tylko trzy pomiary na tym repozytorium:
z **N** przebiegów utworzonych w tej samej sekundzie i wpuszczonych do jednej grupy
przeżywa **dwa**, a **N−2** dostaje `cancelled` w ciągu dwóch sekund.

## 2. Trzy fale

Wszystkie na gałęzi tego pull requesta, ziarno grupy identyczne we wszystkich
plikach: `metro-ci-${{ github.ref }}`, `cancel-in-progress: false` wpisane **jawnie**,
bo wartość domyślna jest tym, o co pytamy, a nie tym, co wolno założyć.
Liczbę przebiegów w grupie ustawiała liczba plików workflowu w **różnicy całego
pull requesta** — filtry `paths` liczą ją od bazy do wierzchołka, nie z ostatniego
commita, i to samo w sobie jest pomiarem: fala 2 miała trzy commity, a puściła
dwa workflowy.

| fala | commit | przebiegów w grupie | ruszył | czekał | **anulowanych** |
|---|---|---|---|---|---|
| 1 | `b220769` | **8** | M7 shell | Python tool tests | **6** |
| 2 | `a611eff` | **2** | Sim core tests | Python tool tests | **0** |
| 3 | `d5b919b` | **3** | Neutral material style smoke | Sim core tests | **1** |

Fala 1, wszystkie osiem utworzone o **18:43:03Z**:

```
34390714173  296 Neutral material style smoke  akt=18:43:04  cancelled
34390714275  885 Sim core tests                akt=18:43:05  cancelled
34390714180  466 Blender smoke                 akt=18:43:05  cancelled
34390714258  309 Station platforms and wayside akt=18:43:05  cancelled
34390714164  433 Tunnel alignment              akt=18:43:05  cancelled
34390714270  439 Visual regression             akt=18:43:05  cancelled
34390714092  437 M7 shell                      akt=18:44:23  success
34390714280 1010 Python tool tests             akt=18:45:28  success
```

Fala 2, oba utworzone o **18:45:54Z** — i to jest przypadek „dwa przebiegi naraz":

```
34391009039  886 Sim core tests      akt=18:46:30  success
34391009118 1011 Python tool tests   akt=18:47:36  success   (czekał `pending`, potem ruszył)
```

Fala 3, wszystkie trzy utworzone o **18:48:45Z** — dosłowne pytanie wpisu:

```
34391294433 1012 Python tool tests             akt=18:48:46  cancelled
34391294417  297 Neutral material style smoke  akt=18:49:25  success
34391294430  887 Sim core tests                pending -> success
```

## 3. Co z tego wynika dla decyzji z 08.09.2026

Decyzja właściciela brzmiała „zserializować joby czasowe wobec renderów".
Jedynym mechanizmem był wspólny `concurrency`, bo dziesięć jobów stoi w dziesięciu
osobnych plikach, a `needs:` działa tylko wewnątrz jednego pliku. Pomiar mówi,
że **ten mechanizm nie serializuje ośmiu przebiegów — kasuje sześć z nich**:

- w fali 1 wśród anulowanych był **`Sim core tests`**, czyli dokładnie ten job,
  którego mierzalności serializacja miała bronić. Job anulowany nie jest
  „niemierzalny" — **jego nie ma**;
- w fali 3 anulowany został `Python tool tests`, drugi z dwóch jobów czasowych;
- pull request z taką grupą **nie może stać się zielony**, bo sześć wymaganych
  przebiegów kończy się stanem, którego nikt nie zamawiał.

„Skończone, gdy" wpisu 6.D52 żądało, żeby przy trzech przebiegach naraz **ani jeden**
job czasowy nie był `cancelled`. Pomiar pokazuje, że tego warunku **nie da się
spełnić wspólną grupą** przy N > 2, niezależnie od doboru ziarna: ziarno decyduje
wyłącznie o tym, KTÓRE przebiegi wpadają do jednej grupy, a nie o tym, co grupa
z nadmiarem robi.

## 4. Drugi pomiar: czy choroba, na którą to jest lekiem, dziś w ogóle występuje

Serializacja miała odebrać rozstęp powtórzeń jobowi `sim`, bo „pierwszy przebieg
każdego pull requesta jest niemierzalny z konstrukcji". Przeszedłem po **24 kolejnych
przebiegach `pull_request`** workflowu `Sim core tests` z 09.09.2026, wszystkie
**próba 1**, i wyciągnąłem z logów wiersz `[BUDZET-BRAMKA]`:

```
rozstęp:   min 1,7 %   mediana 7,8 %   max 17,0 %      (24 pomiary, 24 zielone)
powyżej spread_pct_max 100,0 %:  0 z 24
powyżej spread_pct_warn 22,5 %:  0 z 24
```

Progi z `tools/ci/linecore-step-budget.json`. Innymi słowy: **warunek „rozstęp
poniżej `spread_pct_max`", który wpis stawia jako cel serializacji, jest dziś
spełniony na 24 przebiegach z 24 — bez żadnej zmiany topologii.**

Dlaczego było inaczej 08.09.2026. Rozstępy **84,0 %** i **102,6 %**, które
uzasadniały decyzję (`reports/pojemnosc-puli-ci.md`), zmierzono na jobach
`101890547517` i `101900177486`, a te chodziły na **`woogitsu-linux-12`**
i **`woogitsu-linux-09`** — maszynach puli, która od 09.09.2026 **nie jest już
zarejestrowana** (`CLAUDE.md` §9, litera czwarta). Wszystkie 24 dzisiejsze pomiary
padły na `metro-wsl-DOM-NEW-01` (7), `-02` (10) i `-03` (7). To nie jest ten sam
przyrząd, więc i nie ta sama liczba.

## 5. Koszt serializacji — i granica tego, co tu jest zmierzone

Zestaw bramek na dzisiejszej topologii, **pięć kolejnych zdarzeń `pull_request`**,
osiem przebiegów i dziesięć jobów każde:

```
okno od zgłoszenia do ostatniego końca:  406 / 436 / 491 / 494 / 515 s  = 6,8-8,6 min
szczyt równoległości chwilowej:          3, 3, 3, 3, 3
suma czasu pracy wszystkich jobów:       1172 / 1195 / 1273 / 1283 / 1215 s
```

**Czasu „po" NIE MA i to nie jest przeoczenie**: pełnej serializacji nie da się
uzyskać mechanizmem, który przy ośmiu przebiegach kasuje sześć, więc nie ma czego
zmierzyć. Jedyne, co da się z tych liczb **wyliczyć** — i jest to wyliczenie,
nie pomiar — to że zestaw wykonywany po jednym jobie trwałby tyle, co suma pracy,
czyli **19,5–21,4 min wobec 6,8–8,6 min dzisiaj**, około **2,5×** dłużej.

## 6. Wybrane ziarno grupy

**Żadne — grupy nie ma i nie wchodzi.** Uzasadnienie jest w §3 i §4: mechanizm
kasuje job, którego miał bronić, a stan, do którego miał doprowadzić, jest już
osiągnięty. Wariant, który pomiar **dopuszcza**, to ziarno rozdzielające workflowy
(`${{ github.workflow }}-…`): tam przebieg anulowany jest przebiegiem **wypartym
przez nowszy commit tej samej gałęzi**, a nie przebiegiem sąsiada. Nie wprowadzam
go, bo z serializacją jobów czasowych wobec renderów nie ma nic wspólnego —
wymieniam, żeby bramka z §7 nie została odczytana jako zakaz `concurrency` w ogóle.

## 7. Bramka, bo zestaw tej zmiany nie zauważył

Commit `b220769` wkładał osiem workflowów do jednej grupy i kasował sześć
przebiegów pull requesta. **`python3 tools/tests/test_all.py` przeszedł na nim
2087 testami, 111 modułami, kodem 0** — zielono, bez jednego wiersza ostrzeżenia.
Zielony zestaw mówił wtedy o pliku, którego skutku nikt nie oglądał, i jest to ta
sama rodzina co 6.D46 i 6.D51: przyrząd melduje sprawdzenie, którego nie zrobił.

`test_no_concurrency_group_collects_runs_of_different_workflows`
w `tools/tests/test_ci_workflows.py` żąda, żeby ziarno każdej zadeklarowanej grupy
niosło `github.workflow`. Kontrola negatywna nie jest wymyślona: pierwsze dwie
asercje niosą **dosłownie** ziarno, które w fali 1 skasowało sześć przebiegów.

## 8. Czego NIE zmierzyłem

**Trzech pull requestów naraz**, jak dosłownie żądało pole „Weryfikacja". Sesja ma
regułę „wszystko na jednej wyznaczonej gałęzi", a trzy równoczesne pull requesty
wymagają trzech gałęzi. Zamiast tego zmierzyłem **osiem, trzy i dwa przebiegi
w jednej grupie**, co rozstrzyga to samo pytanie od strony mechanizmu: reguła
kolejkowania działa na **grupie**, a nie na tym, z ilu pull requestów przebiegi
do niej przyszły. Czego ten zamiennik nie pokrywa: przy ziarnie **globalnym**
(bez `github.ref`) grupę dzieliłyby przebiegi RÓŻNYCH pull requestów, więc jeden
pull request kasowałby przebiegi drugiego — tego **nie zmierzyłem** i piszę to
jako lukę, nie jako wniosek.

**Nie zmierzyłem `concurrency` na poziomie joba** — bramka z §7 czyta oba poziomy,
ale pomiar dotyczy wyłącznie deklaracji na poziomie pliku.

**Nie tykałem** progu kosztu kroku, `spread_pct_max`, liczby maszyn w puli ani
selektora `runs-on`; wszystkie cztery stoją w polu „Poza zakresem" wpisu.

## 9. Sprawa dla właściciela

Decyzja z 08.09.2026 zapadła na przesłance, której **dzisiejszy pomiar nie
potwierdza** (§4), a jedyny mechanizm jej wykonania **kasuje** job, którego miała
bronić (§3). Nie jest to uchylenie decyzji — jest to liczba, której przy jej
podejmowaniu nie było. Wpis 6.D52 zamykam pomiarem, a nie zmianą topologii.

## 10. Weryfikacja

```
python3 tools/tests/test_all.py
  -> RAZEM 2089 testów, 111 modułów, kod 0

grep -c "concurrency" .github/workflows/*.yml
  -> wszystkie zera
```
