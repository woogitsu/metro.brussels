# 6.D170 — kryterium wejścia do Mapy: pomiar go NIE ZNALAZŁ, i to jest odpowiedź

**Data:** 18.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `94953f3`

Pozycja pytała, co wpuszcza dokument do Mapy dokumentów w `CLAUDE.md` §3, i żądała
kryterium zapisanego nad tabelą oraz bramki, która z tego kryterium liczy zbiór
wymagany. Pole „Wyjście" dopuszczało wprost wynik przeczący: „gdy pomiar pokaże, że
kryterium odróżniającego dzisiejsze czternaście od dwunastu pozostałych **nie ma**,
wyjściem jest raport w `reports/` mówiący to wprost". **Wyszedł wynik przeczący** —
i dlatego zapisana jest reguła o **kompletności przypisania**, a nie zmyślone
kryterium o treści dokumentów.

## 1. Liczby wejściowe odtworzone co do cyfry

Polecenie z pola „Weryfikacja", bez zmian:

```
$ python3 -c 'import re,glob,io; s=io.open("CLAUDE.md",encoding="utf-8").read(); \
    s=s.split("## 3. Mapa dokumentów")[1].split("\n## 4.")[0]; \
    w=set(re.findall(r"\|\s*`([^`]+)`\s*\|",s)); d=set(glob.glob("docs/*.md")); \
    print(len(w), len(d), len(d-w))'
16 26 12
```

Szesnaście wierszy tabeli (czternaście z `docs/`, dwa z `data/`), dwadzieścia sześć
plików `.md` w `docs/`, dwanaście poza tabelą — dokładnie ta dwunastka, którą wymienia
wiersz `| 6.D170 |`. Liczby z samego wiersza (24 pliki, 13 wymienionych) są starsze
o sześć dni i pole „Skończone, gdy" już to prostuje; ten raport ich nie przepisuje.

## 2. Czego pomiar szukał i czego nie znalazł

Cztery kandydatury na kryterium mechaniczne, każda policzona na całym `docs/`:

| kandydat | w tabeli z trafieniem | poza tabelą z trafieniem | rozdziela? |
|---|---|---|---|
| cytowany w `CLAUDE.md` POZA §3 | 9/14 | **0/12** | wystarczający, nie konieczny |
| cytowany w `.claude/skills/` | 4/14 | 0/12 | jak wyżej, słabszy |
| cytowany w `tools/tests/*.py` | 12/14 | 6/12 | nie |
| cytowany w innym `docs/*.md` | 14/14 | 10/12 | nie |

**Ani jedna nie dzieli czternastu od dwunastu.** Pierwsza jest warunkiem
**wystarczającym bez ani jednego kontrprzykładu** — i to jest jedyny wynik dodatni
tego pomiaru. Nie jest konieczna: pięć dokumentów w tabeli (`02-simulation`,
`05-glossary`, `22-heartbeat`, `23-environment`, `24-clearance-profile-decisions`)
nie jest cytowanych w `CLAUDE.md` nigdzie poza §3.

## 3. Jedyna własność, która rozdziela — i dlaczego NIE jest kryterium

Podział pokrywa się dokładnie z **przedziałem numerów w nazwie pliku**: w tabeli stoi
wszystko o numerze najwyżej siódmym, wszystko o numerze co najmniej dwudziestym drugim
i wszystko bez numeru; poza nią cały przedział od ósmego do dwudziestego pierwszego.
**Zero niezgodności na dwadzieścia sześć plików.** To jednak opis numeracji, a nie
reguła wejścia, i pomiar pokazuje trzy powody:

**Nie jest chronologiczny.** Daty powstania z `git log --diff-filter=A`:

```
2026-09-01  docs/08-m7-ground-truth.md          (POZA)
2026-09-01  docs/09-data-provenance.md          (POZA)
2026-09-01  docs/17-visual-regression.md        (POZA)
2026-09-01  docs/21-measured-vs-assumed.md      (POZA)
2026-09-01  docs/22-heartbeat.md                (W TABELI)
2026-09-02  docs/10,11,12,15,16                 (POZA)
2026-09-03  docs/23-environment.md              (W TABELI)
2026-09-03  docs/24-clearance-profile-decisions.md (W TABELI)
2026-09-04  docs/18,19,20                       (POZA)
```

`22-heartbeat` powstał tego samego dnia co `08`, `09`, `17` i `21`, a `18`, `19` i `20`
powstały **po** `23` i `24`. Numer nie idzie za datą, więc przedział numerów nie jest
przedziałem czasu.

**Nie jest tematyczny — po dwa kontrprzykłady w każdą stronę.**
`24-clearance-profile-decisions.md` to dokument rozstrzygniętych faktów o dziedzinie
i stoi **w** tabeli; `08-m7-ground-truth.md` jest tym samym gatunkiem i stoi **poza**.
Odwrotnie: `22-heartbeat.md` to dokument procesu i stoi **w** tabeli, a
`17-visual-regression.md` oraz `21-measured-vs-assumed.md` też są o procesie i stoją
**poza**.

**Numeracja ma dziurę, której nikt nie zapełnił.** `docs/13-*` i `docs/14-*` nie
istniały **nigdy** (`git log --all --diff-filter=A` po obu wzorcach: zero trafień),
a żaden plik `docs/*.md` nie został **nigdy** usunięty (`--diff-filter=D`: zero).
Reguła „przedział ósmy–dwudziesty pierwszy stoi poza Mapą" przypisałaby więc przyszły
`docs/13-…` do strony, której nikt nie wybrał — czyli robiłaby dokładnie to, przed czym
ostrzega wiersz `| 6.D170 |`: „żeby nie zależało od pamięci piszącego".

## 4. Co zostało zapisane zamiast kryterium

W `CLAUDE.md` §3, nad tabelą, stoi odtąd akapit mówiący **to, co pomiar pokazał**:
skład Mapy jest decyzją właściciela, bo własności mierzalnej z drzewa nie ma — twarde
są natomiast dwie rzeczy:

1. **Dokument, na który powołuje się którykolwiek inny punkt `CLAUDE.md`, musi stać
   w tabeli.** To jedyny wynik dodatni z §2, zapisany jako reguła: dwanaście z dwunastu,
   zero kontrprzykładów.
2. **Każdy plik `docs/*.md` musi stać albo w tabeli, albo w przypiętym zbiorze
   `POZA_MAPA`** w nowej bramce `tools/tests/test_docs_map.py`.

Bramki „na kształcie" (rozpoznającej gatunek dokumentu z jego treści) **nie ma i nie
powstaje**: zapalałaby się dziś na dokumentach poprawnych, czyli byłaby bramką z 6.D27,
wyłączaną zamiast naprawianą. Skład Mapy nie został zmieniony ani o jeden wiersz.

## 5. Pytanie do właściciela, postawione a nie rozstrzygnięte

Wiersz `| 6.D170 |` zauważa, że **pięć z dwunastu** dokumentów spoza Mapy
(`08-m7-ground-truth`, `09-data-provenance`, `10-signalling-ground-truth`,
`11-station-ground-truth`, `12-infrastructure-ground-truth`) to gatunek „ground truth",
czyli ten sam co `docs/00-network-data.md`, który §3 nazywa źródłem prawdy. Pomiar
tego nie rozstrzyga i nie może: przeniesienie ich do Mapy jest **decyzją o treści
konstytucji**, a §8 mówi wprost, że decyzji projektowej, której nie ma w dokumentach,
nie podejmuje się samemu. Pozycja zostawia je tam, gdzie były, i zapisuje pytanie tutaj.

## 6. Kontrole, przewidywania spisane PRZED przebiegami

Wszystkie na **pełnej** kopii drzewa z `.git`, `__pycache__` czyszczony przed każdym
przebiegiem, kopia przywracana z drzewa roboczego między kontrolami.

| kontrola | zmiana na kopii | przewidziane | zmierzone | zgodne |
|---|---|---|---|---|
| KN-3 | nic | zielone, wszystko przypisane | **7/7** | tak |
| KN-1 | nowy plik w `docs/`, o nazwie, której w drzewie nie ma | czerwień, nazywa plik | **6/7**, nazwał | tak |
| KN-2 | `18-rights-matrix` zdjęty z `POZA_MAPA` | czerwień | **6/7**, nazwał | tak |
| KN-4 | wiersz `22-heartbeat` usunięty z §3 | czerwień | **5/7**, DWA testy | tak |
| KN-5 | §9 cytuje `docs/18-rights-matrix.md` | czerwień reguły cytowania | **6/7** | tak |
| KN-6 | kotwica kryterium usunięta z §3 | czerwień | **6/7** | tak |
| KN-7 | ścieżka-widmo w `POZA_MAPA` | czerwień | **6/7** | tak |

Wyjście KN-1 i KN-5, dosłownie:

```
FAIL test_kazdy_dokument_docs_stoi_po_jednej_ze_stron: te pliki docs/ nie stoją ani w tabeli CLAUDE.md §3, ani w POZA_MAPA: ['docs/25-zmyslony.md'] — dopisz je do jednej ze stron w tym samym commicie, w którym powstały
FAIL test_cytowanie_w_konstytucji_pociaga_za_soba_wpis_do_mapy: CLAUDE.md powołuje się poza §3 na dokumenty, których w Mapie NIE MA: ['docs/18-rights-matrix.md'] — albo wpisz je do tabeli §3, albo nie odsyłaj do nich z konstytucji
```

**KN-4 dał więcej niż przewidywanie:** przewidziany był jeden czerwony test, padły
dwa — obok przypisania zapaliła się równość na liczbie wierszy tabeli. Przewidywanie
mówiło „czerwień", więc kierunek się zgadza, ale liczba testów nie; zapisane tak, jak
wyszło.

### Przewidywanie W2 — CZĘŚCIOWO OBALONE

Przed pomiarem przewidziałem, że w tabeli **nie** będą cytowane poza §3:
`PLAYABILITY.md`, `22-heartbeat.md`, `24-clearance-profile-decisions.md`,
`TASK-TEMPLATE.md` i jeden z `05-glossary.md` / `07-open-data-research.md`.
Zmierzone: `02-simulation.md`, `05-glossary.md`, `22-heartbeat.md`,
`23-environment.md`, `24-clearance-profile-decisions.md`. **Trafione trzy z pięciu**;
`PLAYABILITY.md` i `TASK-TEMPLATE.md` są cytowane (myliłem się), a `02` i `23` nie są
(nie przewidziałem ich). Lista w raporcie i w bramce jest **zmierzona**, nie ta
przewidziana.

## 7. Weryfikacja

```
$ python3 tools/tests/test_all.py
  2636/2636 przeszło
  RAZEM 317.852 s, 2636 testów, 137 modułów
  KOD=0
```

Zapadki podniesione w tym samym commicie, każda w zapisie „stoi dziś (stała wczoraj)":
`MODULOW_W_CALYM_DRZEWIE` = 217 (było 216), `BAJTKOD_PO_COMPILEALL_PLIKI` = 217
(było 216), `ROZKLAD_MODULOW` dla `tools/tests` = 145 (było 144),
`ASERCJI_NAPISOWYCH_RAZEM` = 932 (było 930), `ZAPADEK_RAZEM` = 86 (było 85),
rozkład klas zapadek 18/3/63/2 (było 18/3/62/2), para wolnych (63, 62) (było
(62, 61)), zdanie o modułach zestawu 137 (było 136) oraz `MIN_REPORTS` o jeden.

## 8. Czego świadomie nie zrobiono

* **Nie przeniesiono żadnego dokumentu do Mapy ani z niej** — §5.
* **Nie wpisano do `CLAUDE.md` reguły o przedziale numerów** — §3 mówi, dlaczego
  byłaby fałszywa jako kryterium i szkodliwa dla `docs/13-…`.
* **Nie napisano bramki rozpoznającej gatunek dokumentu z treści** — 6.D27.
* **Nie ruszono `.claude/skills/`**, choć kandydat „cytowany w skillu" był mierzony:
  liczba 4/14 opisuje skille, nie Mapę.

## 9. Zauważone przy okazji, nietknięte

* Tabela §3 wymienia dwa pliki z `data/`, więc „szesnaście wierszy" i „czternaście
  dokumentów" to dwie różne liczby o tej samej tabeli. Bramka trzyma obie osobno,
  bo pomylenie ich jest tu naturalnym błędem czytającego.
* `docs/13-*` i `docs/14-*` nie istniały nigdy, a numeracja biegnie dalej bez przerwy —
  nikt tego nigdzie nie odnotował. To nie usterka, ale zdanie, którego brak kosztował
  w tym pomiarze osobne sprawdzenie w historii.
