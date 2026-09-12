# 6.D152 — pięć pól wpisu `POMIARY` z pięciu wychodzi z logu; człowiek zostaje tam, gdzie logu nie ma

**12.09.2026**, na `7870610`. Wejście: `tools/ci/timing_record.py`,
`tools/tests/test_timing_record.py`, `tools/tests/test_suite_runtime_budget.py`
(`POMIARY`), sześć logów kroku „Run tool tests" z przebiegów PR #524 … #529.
Pozycja: przy 6.D135 dopisałem do listy **siedem** wpisów, każdy przepisany z logu
z ręki — ten sam kształt, który 6.D26 naprawiło dla JEDNEJ liczby, a nie dla listy.

## 1. Przesłanka pozycji jest nieprawdziwa i ten raport jest jej przepisaniem

Pozycja mówiła: *„wpis niesie jednak też maszynę i zdanie o warunkach, których log nie
podaje wprost, więc automat wypełniłby je zgadując. Pozycja ma zmierzyć, ile pól da się
wziąć z logu bez zgadywania, a ile zostaje człowiekowi"*.

**Zmierzone: z logu wychodzą wszystkie pięć.** Zgadywać nie trzeba niczego — ani maszyny,
ani zdania „na czym". Poniżej jest pomiar, a nie zapewnienie.

| pole wpisu | wiersz logu, z którego wychodzi |
|---|---|
| `data` | stempel czasu, którym runner poprzedza każdy wiersz: `2026-09-11T12:40:55.2867490Z` |
| `sekundy` | `czas sciany test_all.py: 89.518 s (prog 150.0 s)` |
| `modulow` | `  RAZEM 88.675 s, 2315 testów, 122 modułów` |
| `maszyna` | `Runner name: 'metro-wsl-DOM-NEW-01'` |
| `na_czym` → job | `Complete job name: tools` |
| `na_czym` → PR | `[command]/usr/bin/git checkout --progress --force refs/remotes/pull/524/merge` |
| `na_czym` → CPU/ściana | `czas sciany 89.518 s w progu 150.0 s, stosunek CPU/sciana 1.971 (podloga 0.75)` |
| `na_czym` → testów | ten sam wiersz `RAZEM` |

## 2. Sześć logów, sześć wpisów, zero rozbieżności

`timing_record.z_logu` puszczone na logach tych samych przebiegów, z których 6.D135
przepisało wpisy ręcznie. Kolumna „brak" to drugi element zwracanej krotki:

| PR | data | ściana | modułów | testów | CPU/ściana | brak |
|---|---|---:|---:|---:|---:|---|
| #524 | 2026-09-11 | 89.518 | 122 | 2315 | 1.971 | `()` |
| #525 | 2026-09-11 | 92.119 | 122 | 2320 | 1.857 | `()` |
| #526 | 2026-09-11 | 97.863 | 122 | 2326 | 1.801 | `()` |
| #527 | 2026-09-11 | 100.654 | 122 | 2330 | 1.810 | `()` |
| #528 | 2026-09-11 | 116.404 | 122 | 2335 | 1.599 | `()` |
| #529 | 2026-09-11 | 109.420 | 122 | 2335 | 1.610 | `()` |

Każda z tych liczb zgadza się z wpisem w `POMIARY`. Zdanie „na czym" złożone z czterech
ostatnich kolumn zgadza się **znak w znak w pięciu wpisach na sześć**. Szósty (#528) ma
doklejone `, NAJWYŻSZY na runnerze` — i to jest jedyny ślad człowieka w całej szóstce.

**Ten dopisek nie jest zdaniem o przebiegu, tylko o LIŚCIE**, a przy tym powtarza to, co
`MEASURED_MAX_WALL_S` już z listy liczy. Zestarzeje się przy pierwszym wolniejszym
przebiegu i nikt tego nie zauważy — dokładnie tak, jak zestarzały się dwie poprzednie
wartości opisane w `reports/zapis-czasu-zestawu.md`. Liczy go dziś stała
`WPISOW_Z_DOPISKIEM` w bramce; jej zejście do zera jest poprawką, a nie regresem.

## 3. Rozstrzygnięcie: co uzasadnia utrzymywanie listy ręcznie

**Wpisy z CI — nic.** Pięć pól z pięciu wychodzi z logu, a od tej pozycji wypisuje je
gotowe do wklejenia `python3 tools/ci/timing_record.py --z-logu <log>`:

```
    ("2026-09-11", 109.420, 122, MASZYNA_RUNNER,
     "job `tools`, PR #529, CPU/ściana 1,610 — 2335 testów"),
# runner: metro-wsl-DOM-NEW-03
```

**Wpisy kontenerowe — wszystko**, bo **nie mają logu**. Kontener sesji nie jest runnerem,
nikt nie zapisuje z niego niczego maszynowo, a zdania „host pod obciążeniem", „`ps aux`
pokazywał równoległy `dotnet build`" są obserwacją człowieka zrobioną w trakcie i
nieodtwarzalną potem. Pięć wpisów na dwanaście jest właśnie takich — i to one, a nie
jakiekolwiek pole wpisu z CI, są powodem, dla którego lista ma człowieka.

Dopisywania wpisów automatem **nie zrobiłem**: stoi w polu „Poza zakresem" pozycji.
Tryb `--z-logu` wypisuje na standardowe wyjście i niczego nie dotyka — o tym, czy pomiar
wchodzi do listy, nadal decyduje człowiek. Zdjęte z niego zostało wyłącznie przepisywanie
liczb, czyli ta część, którą przy 6.D135 wykonał siedem razy.

## 4. Bramka, żeby to nie było zdaniem w raporcie

Samo zmierzenie niczego nie pilnuje: następny wpis też można przepisać z pamięci.
Dlatego sześć logów leży w drzewie (`tests/data/ci-logs/`, **dosłowne i niespakowane**),
a `test_timing_record.py` porównuje **każdy wpis runnera z jego logiem** i wymaga, żeby
każdy taki wpis log w drzewie MIAŁ.

Dosłowne, a nie przycięte do „wierszy, które są potrzebne": przycięcie znaczyłoby, że
bramka sprawdza wybór człowieka, a nie log.

### Niespakowane — bo pierwsza wersja była spakowana i CI ją odrzuciło

**Ta sekcja jest przepisana, a nie dopisana obok.** Pierwsza wersja tej pozycji wstawiła
sześć plików `.gz` z uzasadnieniem „ok. 70 KB na przebieg wobec ok. 292 KB surowo".
Zdanie było prawdziwe i **nie o tym, co trzeba**. Obaliły je dwa pomiary:

**1. Siedem jobów CI naraz.** `test_conflict_markers.test_skan_czyta_CALE_drzewo_a_nie_pusty_zbior`
wymienia pliki nieczytelne jako UTF-8 i **odmawia ich przemilczenia**: plik binarny
zmniejsza skan znaczników konfliktu bez ani jednego słowa, więc ma być decyzją, a nie
cichym pominięciem. Komunikat z przebiegu PR #548:

```
FAIL test_skan_czyta_CALE_drzewo_a_nie_pusty_zbior: pliki nieczytelne jako UTF-8,
więc niepilnowane: ['tests/data/ci-logs/tools-pr524.log.gz', … ] — jeżeli mają
w drzewie zostać, wzorzec pilnowanych plików wymaga decyzji, a nie cichego pominięcia
```

Czerwone poszły `tools`, `blender-smoke`, `m7-shell`, `station-details`,
`tunnel-alignment` ×3 i `visual-regression` — **siedem jobów, jedna przyczyna**: pozostałe
sześć woła `doctor.sh`, a ten woła cały zestaw.

**2. `.gz` w repozytorium jest DROŻSZY, i to jest zmierzone.** Dwa puste repozytoria, te
same sześć logów, `git gc`, rozmiar `.git/objects`:

| postać | bajtów w repozytorium |
|---|---:|
| tekst | **234 858** |
| `gzip -9` | **428 699** |

Tekst jest **1,83x tańszy**. Git i tak pakuje zlibem, a przy tym **deltuje pliki podobne
do siebie** — sześć logów tego samego joba to materiał dla delty niemal idealny. Blobu już
spakowanego nie skompresuje ani nie zdeltuje. Oszczędność z `gzip -9` istnieje wyłącznie
w katalogu roboczym; płaci się ją w historii, czyli tam, gdzie zostaje na zawsze.

Odpowiedzią **nie jest wyjątek na liście pilnowanych plików**: taki wyjątek zdejmuje plik
spod bramki na zawsze, co sam `test_conflict_markers.py` nazywa gorszym od kotwiczenia
wzorca („plik, który raz na niej stanie, przestaje być pilnowany na zawsze"). Odpowiedzią
jest plik, który bramka **umie przeczytać**. Wzorców konfliktu w tych logach jest **zero**:
każdy wiersz zaczyna się od stempla czasu, a wzorce są zakotwiczone na początku wiersza.

### Dlaczego zestaw był u mnie zielony, a na CI czerwony

**Bo `git ls-files` nie widzi plików nieśledzonych.** Zestaw puszczałem, zanim zrobiłem
`git add`, więc skan `test_conflict_markers.py` po prostu tych sześciu plików nie znał
i wychodziło **2387/2387, kod 0**. Po `git add` ta sama komenda daje FAIL. To jest
rodzina 6.D27 w wersji na własnej głowie: przyrząd meldował sprawdzenie drzewa, którego
w tym kształcie jeszcze nie było.

Wniosek do stosowania, nie do zapisania: **zestaw ma sens po `git add`, nie przed** —
przy każdej zmianie, która dokłada do drzewa PLIKI, a nie tylko wiersze.

## 5. Kontrole negatywne

Baza `test_timing_record.py` + `test_suite_runtime_budget.py`: **30/30** (KN-8 ma własną
bazę, `test_conflict_markers.py` + `test_timing_record.py`: **16/16**). Przed każdym
przebiegiem czyszczony `__pycache__`, po każdym przywrócenie przez `cp` i `md5sum -c: OK`.
**Ani jedna nie wyszła zielona.**

| | co psuje | wynik | co zapaliło |
|---|---|---|---|
| KN-1 | `89.518` → `89.519` w jednym wpisie `POMIARY` | 29/30 | porównanie pola `sekundy` z logiem |
| KN-2 | `tools-pr526.log.gz` znika z drzewa | **28/30** | oba: brak materiału i brak wiązania wpisu z logiem |
| KN-3 | `z_logu` wstawia `runner = "nieznany"`, gdy wiersza nie ma | 29/30 | kontrola przyrządu — `zgłoszone braki to [], a spodziewane ['maszyna', 'runner']` |
| KN-4 | `MASZYNA_Z_LOGU` → `"runnner"` | 28/30 | rozjazd dwóch napisów o tej samej maszynie |
| KN-5 | `1,801` → `1,081` w prozie wpisu #526 | 28/30 | moje porównanie **i** cudza bramka „runner liczy równolegle" |
| KN-6 | z wpisu #528 znika `, NAJWYŻSZY na runnerze` | 29/30 | `WPISOW_Z_DOPISKIEM` |
| KN-7 | logi #524 i #525 zamienione miejscami | 29/30 | wiązanie plik↔wpis jest sprawdzane, nie zakładane |
| KN-8 | jeden `.gz` wraca do drzewa **i do indeksu** | 15/16 | `test_skan_czyta_CALE_drzewo_…` — i **tylko on**, więc decyzja z §4 ma jedną przyczynę, nie domysł |

### KN-3 jest tu najważniejsza

Prawdziwy log ma wszystko, więc na nim samym „pola są" nie odróżnia czytelnika rzetelnego
od takiego, który wstawia wartości domyślne — a to jest rodzina 6.D27, tropiona w tym
projekcie od tamtej pozycji. Wejście do tej kontroli jest **syntetyczne z prawdziwego
materiału**: z logu znika po jednym wierszu naraz, a bramka żąda, żeby zapaliło się
dokładnie tyle pól, ile od tego wiersza zależy. Zależności są wypisane, nie policzone,
bo to one są twierdzeniem: `modulow` i `testow` stoją w JEDNYM wierszu `RAZEM` i nie da
się zgubić jednego bez drugiego.

Trzy poprzednie pozycje kończyły się kontrolą zieloną, bo drzewo nie miało wejścia
oddzielającego mechanizm od jego braku (6.D147 KN-6, 6.D148 KN-4, 6.D149 KN-2 — powtarzalność
tego jest pozycją 6.D161). Tutaj wejście syntetyczne było wbudowane w kontrolę **od
początku**, a nie dokładane po tym, jak wyszła zielona.

## 6. Znalezione po drodze, nie tknięte

Sześć wpisów oznaczonych jednym słowem `runner` pochodzi z **więcej niż jednej maszyny
puli**: logi nazywają `metro-wsl-DOM-NEW-01` przy #524/#526/#527 i `…-03` przy
#525/#528/#529 (przebieg #546 chodził jeszcze na `…-02`). Pole `maszyna` zlewa je w jedno,
`MEASURED_MAX_WALL_S` bierze maksimum przez wszystkie, a log nazwę **ma**. To ta sama
rodzina, co 6.D135 — „jedna lista na dwie maszyny daje margines nieprawdziwy dla obu" —
tylko o poziom niżej.

**Wniosku z tego NIE wyciągam i dlatego jest to pozycja, a nie akapit.** Materiał jest
zmieszany ze wzrostem zestawu: w tym samym oknie liczba testów szła 2315 → 2335, więc
różnicy między maszynami nie da się odjąć od różnicy między przebiegami bez nowego pomiaru.
`CLAUDE.md` §9 zakazuje **wybierania** runnera po nazwie i podawania liczebności puli;
zapisanie nazwy w pomiarze nie jest ani jednym, ani drugim, ale pozycja ma to nazwać wprost.

## 7. Czego nie zrobiono

- **Nie dopisałem wpisów automatem** ani nie ruszyłem progu — oba stoją w „Poza zakresem".
- **Nie zmieniłem kształtu wpisu `POMIARY`** o pole z nazwą maszyny, choć log ją niesie:
  to jest treść pozycji z sekcji 6, a nie skutek uboczny tej.
- **Nie usunąłem dopisku `, NAJWYŻSZY na runnerze`**, mimo że sekcja 2 mówi, czemu się
  zestarzeje: usunięcie zdania z listy pomiarów jest zmianą tamtej listy, a ta pozycja
  miała ją zmierzyć, nie redagować. Stała `WPISOW_Z_DOPISKIEM` trzyma to na widoku.
- **Nie wstawiłem logu przebiegu kontenerowego**, bo takiego logu nie ma — to jest
  rozstrzygnięcie, nie brak.
