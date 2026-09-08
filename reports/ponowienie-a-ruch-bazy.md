# Ponowienie joba a ruch bazy — co zmierzone, a czego zmierzyć się NIE DAŁO (6.D47)

**Zmierzone 08.09.2026 na commicie:** `a214ab9356dbdf1f29434a48c90d32b1fc95afbb`
(`main` po scaleniu #407). Pomiar czyta **wyłącznie metadane i logi zakończonych
przebiegów**; ani jeden przebieg nie został na potrzeby tego raportu utworzony
ani ponowiony.

Pozycja 6.D47 pyta: przebieg `pull_request` sprawdza scalankę bazy z gałęzią,
a baza w międzyczasie ruszyła — czy **ponowienie** joba liczy na scalance
zapisanej przy tworzeniu przebiegu (STAREJ), czy przelicza ją na dzisiejszej
bazie (NOWEJ)? Od odpowiedzi zależy, czy wolno scalać na podstawie ponowionego
joba, bo sesja z 08.09.2026 robiła to kilkanaście razy i nazywała to weryfikacją.

**Wynik w jednym zdaniu:** w KAŻDYM ponowieniu, jakie to repozytorium ma
w logach, job liczył na scalance **zapisanej przy tworzeniu przebiegu** —
pobieranej po SHA, nie po nazwie refa, i starszej od samego przebiegu — ale
w całym dostępnym materiale **nie ma ani jednego ponowienia, między którego
próbami `main` naprawdę ruszył**, więc pytanie o zachowanie po ruchu bazy
zostaje **nierozstrzygnięte** i tego raport nie zamazuje.

## 1. Przesłanka pozycji jest nieprawdziwa: `main` nie ruszał między próbami

Pozycja (i polecenie, z którym siadałem do pomiaru) wskazuje przebieg
`34194126232` — job `sim`, gałąź `claude/uzupelnienie-kolejki-6d48`, pull
request #406, **trzy próby** — i mówi, że `main` przesuwał się w tym czasie
o scalenia #403, #404 i #405.

To jest sprawdzalne z `git log` i **nie zgadza się**. Wierzchołki `main`
z tego dnia, czasy w UTC (`%cI` przeliczone z `+02:00`):

```
2026-09-08T04:36:21Z c92b8ff4036e7fee448d519a989a0f988180702b Scalenie #395
2026-09-08T04:53:59Z b2df576fd6539d9dba478b221231342a778b9508 Scalenie #403
2026-09-08T05:18:28Z d201b16c8f507eac9a01a16955a011a887e5d109 Scalenie #404
2026-09-08T06:10:46Z 5b1405de60785b11cb246c98f019e44b64212d25 Scalenie #405
2026-09-08T07:30:28Z 8b4cf7cf20811e9d86ca976b035b07a4b453f844 Scalenie #406
2026-09-08T08:12:35Z a214ab9356dbdf1f29434a48c90d32b1fc95afbb Scalenie #407
```

A oto okno przebiegu `34194126232` (z metadanych GitHuba):

| co | kiedy (UTC) |
|---|---|
| przebieg utworzony (`created_at`) | 2026-09-08T06:18:55Z |
| próba 1, `Checkout` | 2026-09-08T06:23:36Z |
| próba 2, `Checkout` | 2026-09-08T07:16:22Z |
| próba 3, `Checkout` | 2026-09-08T07:23:38Z |
| próba 3 zakończona | 2026-09-08T07:24:48Z |

Wszystkie trzy scalenia z przesłanki (#403 o 04:53:59Z, #404 o 05:18:28Z,
#405 o 06:10:46Z) weszły **PRZED** utworzeniem przebiegu o 06:18:55Z, a następny
ruch `main` — #406 o 07:30:28Z — nastąpił **PO** zakończeniu trzeciej próby
o 07:24:48Z. Wierzchołkiem `main` przez cały czas trwania trzech prób był
`5b1405de60785b11cb246c98f019e44b64212d25`.

Wskazany przebieg **nie mógł więc rozstrzygnąć pytania** i to jest pierwszy
wynik tego pomiaru: przesłanka „a `main` w tym czasie się przesuwał" była
zapisem z pamięci, nie z logu.

## 2. Co jednak jest z tych prób mierzalne: job stoi na JEDNYM commicie, pobieranym po SHA

`actions/checkout` w `.github/workflows/sim-tests.yml` i w
`.github/workflows/python-tests.yml` nie dostaje wejścia `ref` — sprawdzone
na wszystkich dziesięciu workflowach naraz, zero wystąpień:

```
$ grep -rn -A3 "uses: actions/checkout" .github/workflows/*.yml | grep -c "ref:"
0
```

Bez `ref` akcja bierze `github.sha` przebiegu. W logu widać, **jak** go bierze,
i to jest sedno: refspec ma po lewej stronie **literalny SHA**, a nie nazwę
refa `refs/pull/406/merge`. Trzy próby, trzy joby, trzy wklejone wiersze:

```
próba 1, job 101958058524, runner woogitsu-linux-04
2026-09-08T06:23:35.0834352Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +d7360be1b4857a34c56aacf974155b790c1abdfa:refs/remotes/pull/406/merge
2026-09-08T06:23:36.0037890Z HEAD is now at d7360be Merge 006bb7fe5bc10b9dca03924bea6de7406d9644cd into 5b1405de60785b11cb246c98f019e44b64212d25
2026-09-08T06:23:36.0221918Z [command]/usr/bin/git log -1 --format=%H
2026-09-08T06:23:36.0229350Z d7360be1b4857a34c56aacf974155b790c1abdfa

próba 2, job 101968069832, runner woogitsu-linux-02
2026-09-08T07:16:21.8748536Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +d7360be1b4857a34c56aacf974155b790c1abdfa:refs/remotes/pull/406/merge
2026-09-08T07:16:22.6204658Z [command]/usr/bin/git log -1 --format=%H
2026-09-08T07:16:22.6206382Z d7360be1b4857a34c56aacf974155b790c1abdfa

próba 3, job 101972409030, runner woogitsu-linux-03
2026-09-08T07:23:37.7739898Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +d7360be1b4857a34c56aacf974155b790c1abdfa:refs/remotes/pull/406/merge
2026-09-08T07:23:38.4166135Z HEAD is now at d7360be Merge 006bb7fe5bc10b9dca03924bea6de7406d9644cd into 5b1405de60785b11cb246c98f019e44b64212d25
2026-09-08T07:23:38.4346759Z d7360be1b4857a34c56aacf974155b790c1abdfa
```

Trzy pary `GITHUB_SHA` (bo `git log -1` wypisuje dokładnie to, co `GITHUB_SHA`
wskazuje po checkoucie) i **jedna liczba w każdej**:
`d7360be1b4857a34c56aacf974155b790c1abdfa`, przez 60 minut i trzy różne maszyny.
Wiersz `HEAD is now at` podaje przy tym oba rodzicielstwa scalanki wprost:
gałąź `006bb7fe5bc10b9dca03924bea6de7406d9644cd`, baza
`5b1405de60785b11cb246c98f019e44b64212d25` — czyli `main` po scaleniu #405.

## 3. Drugi przebieg, inna gałąź, ten sam kształt

Żeby to nie stało na jednym przebiegu: `34182392141` (job `tools`, gałąź
`claude/6d34-audyt-game-tests`, pull request #398), utworzony 03:06:59Z, dwie
próby.

| próba | job | `Checkout` (UTC) | `git log -1 --format=%H` |
|---|---|---|---|
| 1 | 101923920955 | 2026-09-08T03:07:07Z | `e7f36bc95be2db6da5437714460e8954024f15dd` |
| 2 | 101933517009 | 2026-09-08T04:05:02Z | `e7f36bc95be2db6da5437714460e8954024f15dd` |

```
2026-09-08T04:05:01.9154014Z [command]/usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +e7f36bc95be2db6da5437714460e8954024f15dd:refs/remotes/pull/398/merge
2026-09-08T04:05:02.5135241Z HEAD is now at e7f36bc Merge 62dea90cdacbf1aea30b00d16f0704b602f2724b into 4fe2050de6287e7fe94811490cce99ab3db464e6
2026-09-08T04:05:02.5212758Z e7f36bc95be2db6da5437714460e8954024f15dd
```

Baza `4fe2050de6287e7fe94811490cce99ab3db464e6` to `main` po scaleniu #397
(03:04:48Z), czyli wierzchołek `main` w obu próbach — następne scalenie, #398,
weszło o 04:09:49Z, cztery minuty **po** zakończeniu drugiej próby. Znowu okno
bez ruchu bazy.

## 4. Scalanka jest STARSZA od przebiegu — o trzy i o dwie sekundy

To najmocniejsza rzecz, jaką dało się zmierzyć bez nowego przebiegu. Commit
scalanki nie jest tworzony na potrzeby próby: obiekt istniał, zanim przebieg
powstał. Daty commitera obu scalanek, wzięte z API:

| scalanka | commiter | przebieg utworzony | ostatnia próba czytała ją |
|---|---|---|---|
| `d7360be1b4857a34c56aacf974155b790c1abdfa` | 2026-09-08T06:18:52Z | 06:18:55Z | 07:23:38Z |
| `e7f36bc95be2db6da5437714460e8954024f15dd` | 2026-09-08T03:06:57Z | 03:06:59Z | 04:05:02Z |

Trzecia próba przebiegu `34194126232` pracowała więc na obiekcie commita
**starszym od siebie o 64 minuty i 46 sekund**, a druga próba przebiegu
`34182392141` — o 58 minut i 5 sekund. Ponowienie nie zbudowało nowej scalanki;
odtworzyło tę, która powstała przy zdarzeniu pull requesta.

Dlaczego to nie wystarcza do odpowiedzi na pytanie 6.D47: SHA commita w gicie
obejmuje datę commitera, więc scalanka przeliczona na nowej bazie **musiałaby**
mieć inny SHA — ale przy bazie NIERUCHOMEJ hipoteza „ponowienie pobiera zapisane
`GITHUB_SHA`" i hipoteza „ponowienie odczytuje ref `refs/pull/N/merge` jeszcze
raz" dają identyczne liczby, bo ref w tym czasie na nic innego nie wskazywał.
Rozróżnia je wyłącznie przebieg z ruchem bazy między próbami — a takiego nie ma.

## 5. Przeszukanie: 45 ponowień, ZERO z ruchem bazy między próbami

Nie zostało to przyjęte z jednego przebiegu. Przez `list_workflow_runs` zebrane
zostały **1919** unikatowych przebiegów zdarzenia `pull_request` z okna
2026-09-01T15:51:34Z … 2026-09-08T08:26:57Z (wszystkie workflowy dla ostatnich
dwóch dni plus pełna dostępna historia workflowów `sim-tests`, `python-tests`,
`visual-regression`, `blender-smoke`, `godot-first-run` i `tunnel-alignment`;
listowanie GitHuba kończy się na tysiącu pozycji na zapytanie, i to jest granica
tego skanu). Dla każdego przebiegu z więcej niż jedną próbą porównany został
wierzchołek `main` z chwili `created_at` z wierzchołkiem z chwili
`run_started_at` (a to pole GitHub **przestawia** przy ponowieniu, więc obejmuje
całe okno prób; `main` rośnie monotonicznie, więc równość na końcach przedziału
znaczy brak ruchu w środku):

```
runs: 1919 window: 2026-09-01T15:51:34Z .. 2026-09-08T08:26:57Z
runs with >1 attempt: 45
straddling (main moved between run creation and last attempt): 0
stale-head reruns (branch got a newer push before the last attempt): 0
```

Powód jest w zwyczaju pracy, nie w przypadku: właściciel scala **po** zieleni,
a sesja przy każdej kolizji wciągała `main` do gałęzi i pchała — co daje nowy
commit i **nowy przebieg**, nie ponowienie. Pozycja 6.D47 mówi to o sobie sama:
tak zrobiono „z ostrożności, nie z pomiaru". Materiał historyczny jest więc
zgodny z regułą, którą sesja stosowała — i dlatego nie zawiera ani jednego
przypadku, na którym dałoby się tę regułę sprawdzić.

## 6. Czego brakuje do rozstrzygnięcia — dokładny opis brakującego przebiegu

Do zamknięcia 6.D47 trzeba **jednego** przebiegu o takim kształcie:

1. otwarty pull request na `main`, przebieg `pull_request` utworzony w chwili T,
   z logiem `Checkout` podającym `Merge <gałąź> into <baza A>`;
2. scalenie czegokolwiek innego do `main` w chwili T+x, czyli `main` = `baza B`,
   `B` różne od `A`;
3. `re-run failed jobs` na TYM przebiegu w chwili T+y, y > x;
4. odczyt z logu próby drugiej: `HEAD is now at … Merge … into <baza ?>`.

Jeśli w punkcie 4 stoi `A` — ponowienie sprawdza starą scalankę i zielony
job nie mówi nic o dzisiejszym `main`. Jeśli `B` — sprawdza nową.

Tego przebiegu **nie utworzyłem świadomie**: polecenie tej pozycji zabrania
uruchamiania jobów na cudzych gałęziach i tworzenia nowych przebiegów, a pula
runnerów jest wąska. Warunek 2 wymaga do tego cudzego scalenia, czyli decyzji
właściciela — a pomiar, który wymaga cudzej decyzji, jest dokładnie tym
miejscem, w którym `CLAUDE.md` §8 każe się zatrzymać.

## 7. Co z tego weszło do `CLAUDE.md` §9

Punkt o `queued` jest **przepisany, nie dopisany obok**, i nie niesie zdania,
którego pomiar nie potwierdził. Nie stoi tam więc „ponowienie sprawdza starą
scalankę" — bo tego nie zmierzono. Stoi to, co zmierzone i co wystarcza
czytającemu do decyzji o scaleniu: zielony job mówi o **scalance nazwanej we
własnym logu**, tę scalankę podaje wiersz `HEAD is now at … Merge <gałąź> into
<baza>` kroku `Checkout`, a weryfikacją wobec dzisiejszego `main` jest tylko
taki przebieg, w którym `<baza>` równa się dzisiejszemu wierzchołkowi `main`.
Ta reguła jest odporna na nierozstrzygnięte pytanie: obowiązuje niezależnie od
tego, co ponowienie robi, bo każe **przeczytać bazę z logu**, a nie zgadywać ją
z historii przebiegu. Obok stoi jednozdaniowy zapis granicy pomiaru,
z odsyłaczem do tego raportu — żeby następna sesja nie zaczynała od zera i żeby
brak pomiaru nie wyglądał na jego wynik.

Bramka `tools/tests/test_docs_ci_claims.py` porównuje prozę §9 z treścią
workflowów **tylko co do runnerów**: nazwy o kształcie maszyny jednorazowej,
napis o klasie takiej maszyny i etykiety dopisane po kotwicy listy etykiet.
Zapisu o scalance nie widzi i widzieć nie może — nie ma go w żadnym YAML-u. Nie
została z tego powodu poluzowana ani o jotę.

**Została natomiast PRZEKIEROWANA tak, żeby sprawdzała więcej — bo pomiar
pokazał, że nie sprawdzała tego, o czym meldowała.** Jej zbiór dokumentów
liczył `docs/*.md`, `reports/*.md` i `README.md`, a **`CLAUDE.md` w nim nie
było**: docstring modułu otwiera się zdaniem „`CLAUDE.md` §9 mówi…" i to samo §9
było powodem, dla którego do bramki weszło `reports/` — sam plik reguły stał
poza skanem. Dziś jest w nim, a asercja w głównym teście pilnuje, żeby z niego
nie wypadł. Włączenie było darmowe, i to jest zmierzone: na `a214ab9` dryf
w `CLAUDE.md` wynosi zero, bo wszystkie nieaktualne nazwy maszyn stoją tam
w akapitach z markerem historii.

Trzy kontrole, wszystkie **wykonane**, wszystkie pliki po nich przywrócone
z równością sum MD5. Ta sama mutacja dokumentu przed zmianą i po niej — bo
kontrola tylko na jednej stronie nie pokazywałaby dziury, a jedynie bramkę:

```
Zmierzone 08.09.2026. Mutacja we wszystkich trzech ta sama: do CLAUDE.md dopisane
zdanie „Joby chodzą na ubuntu-latest, artefakty także przy fail." — bez markera
historii, czyli twierdzenie o stanie bieżącym.
.
KN-1  bramka SPRZED zmiany (CLAUDE.md poza zbiorem dokumentów), zdanie dopisane:
      5/5 przeszło
      Zero trafień na CLAUDE.md. Dziura zmierzona, nie założona.
.
KN-2  bramka PO zmianie, to samo zdanie dopisane:
      FAIL test_no_document_states_a_runner_that_no_workflow_uses: dokumenty opisują
      runnera, którego nie ma w CI: CLAUDE.md:273: runner `ubuntu-latest`, a workflowy
      używają ['i5-10400f', 'linux', 'nvidia-gtx1070', 'self-hosted', 'woogitsu', 'x64']
      4/5 przeszło
.
KN-3  bramka PO zmianie, dokument NIETKNIĘTY, ale CLAUDE.md zdjęte z documents():
      FAIL test_no_document_states_a_runner_that_no_workflow_uses: `CLAUDE.md`
      wypadło z pętli — bramka wróciła do pilnowania samych odsyłaczy
      4/5 przeszło
```
(Kropka w osobnym wierszu rozdziela wpisy zamiast pustego wiersza: pomijanie
w tej bramce idzie z granulacją AKAPITU, a puste wiersze rozcięłyby cytat na
akapity, z których tylko pierwszy nosiłby marker pomiaru.)

Bez KN-3 samo włączenie pliku mogłoby z bramki wypaść tak samo cicho, jak przez
trzy dni w niej nie było.

## 8. Jak to powtórzyć

Bez `gh` i bez bezpośredniego API — narzędziami MCP:

- `actions_list` / `list_workflow_runs` z filtrem `{"event": "pull_request"}`,
  po stronie, żeby zebrać przebiegi i ich `run_attempt`;
- `actions_list` / `list_workflow_jobs` z filtrem `{"filter": "all"}` — bez
  tego filtru widać wyłącznie próbę ostatnią, a pomiar jest o różnicy między
  próbami;
- `get_job_logs` **bez** `return_content` — zwraca podpisany adres, który da
  się pobrać `curl`-em i przeszukać lokalnie; `tail_lines` nie sięga początku
  loga, a `Checkout` stoi na jego początku;
- `get_commit` z `detail: "none"` — po datę commitera scalanki;
- `git log origin/main --first-parent --pretty=format:'%H %cI %s'` — po
  wierzchołki `main` i ich czasy.

Weryfikacja zestawu po zmianie dokumentu:

```
$ python3 tools/tests/test_all.py
  1996/1996 przeszło
  RAZEM 93.011 s, 1996 testów, 105 modułów
$ python3 tools/tests/test_all.py >/dev/null 2>&1; echo "kod: $?"
kod: 0
```

## 9. Czego nie tknąłem

- **Nie utworzyłem żadnego przebiegu ani nie ponowiłem żadnego joba** — punkt 6
  mówi, jakiego przebiegu brakuje.
- **Nie oznaczyłem 6.D47 jako ZROBIONE.** Jej pole Wyjście żąda pomiaru na żywym
  pull requeście z ruchem bazy między próbami; tego pomiaru nie ma, więc pozycja
  zostaje otwarta, a jej pole Skąd dostało odsyłacz do tego raportu. Raport
  nazywa się inaczej niż plik obiecany w polu Wyjście tej pozycji, i to jest
  wybór, nie przeoczenie: bramka
  `test_a_documented_item_whose_reports_all_exist_says_so_in_its_row` czyta
  istnienie zadeklarowanego pliku jako sygnał „praca weszła", a tu weszła praca
  o innym zakresie.
- **Nie zmieniłem strategii checkoutu ani reguł repozytorium** (pole „Poza
  zakresem" 6.D47): żadnego `ref:`, żadnego wymogu aktualnej gałęzi, żadnego
  automatycznego scalania bazy.
- **Nie tknąłem `docs/04-conventions.md`.** Pole Wyjście 6.D47 każe dopisać tam
  zapis „ponowienie nie jest weryfikacją wobec dzisiejszej bazy" **pod
  warunkiem**, że pomiar pokaże starą scalankę. Pomiar tego nie pokazał, więc
  zapisu nie ma — wpisanie go byłoby dorobieniem wniosku do formularza.

## 10. Zauważone obok, nietknięte

- `run_started_at` przebiegu jest **przestawiane** przy ponowieniu, a
  `created_at` nie. Para tych pól jest jedynym tanim sposobem, żeby z listy
  przebiegów wyczytać, że ponowienie w ogóle było i kiedy — i to na niej stoi
  skan z punktu 5.
- Krok „Workspace jest czysty po checkoucie" (`.github/actions/check-workspace`)
  **nie wypisuje rewizji**. Gdyby wypisywał `git log -1 --format=%H` razem
  z bazą scalanki, każdy job niósłby odpowiedź na pytanie 6.D47 we własnym logu,
  bez czytania wyjścia `actions/checkout`. Nie dopisałem tego: to zmiana
  w workflowach, a nie pomiar, i wchodzi na osobnej pozycji.
- Listowanie przebiegów przez GitHuba kończy się na tysiącu pozycji na
  zapytanie, a filtra po dacie to narzędzie nie ma. Historię starszą niż
  01.09.2026 da się dziś oglądać tylko workflow po workflowie i to jest granica
  skanu z punktu 5, nie jego wynik.
