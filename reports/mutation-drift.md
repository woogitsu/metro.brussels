# Dryf pokrycia mutacyjnego po triażu

**Zmierzone na commicie:** `6c1048b` (`main`, 05.09.2026), 4 robotniki, 139 minut.
**Data pomiaru:** 2026-09-05.
**Narzędzie:** `tools/tests/mutation_sweep.py`, jeden przebieg na moduł
(`--only ŚCIEŻKA --workers 4`), osobny dziennik JSONL na moduł.
**Zestaw operatorów: STARY — `operator, prog`** (dziś `--operators operator,prog`,
czyli `LEGACY_KINDS`). To nie jest zaniedbanie, tylko warunek sensu tego audytu:
porównuje on dzisiejsze liczby z liczbami z raportów triażu, a te powstały **wszystkie**
przed 05.09.2026, kiedy narzędzie innego zestawu nie miało. Policzenie kolumny „dziś"
zestawem pełnym (`logika, argument, przypisanie` doszły w #258) dałoby pod jednym
nagłówkiem dwie różne rzeczy. Skala tej różnicy jest zmierzona, a nie oszacowana: przy
zestawie pełnym rozjeżdżają się **wszystkie 28** modułów tej tabeli, choć w drzewie nie
zmienił się ani jeden z nich — na przykład `crs.py` 14 wobec 29. **Przeliczenie audytu
zestawem pełnym jest osobnym zadaniem** (1940 mutacji osiągalnych wobec 985) i tego
raportu nie unieważnia: opisuje on dryf zmierzony tą samą miarą, co raporty, z którymi
porównuje.
**Wyrocznia:** `tools/tests/test_all.py` — ten sam zestaw, którym mierzyły raporty
triażu, tyle że urósł od tamtej pory z **692** pozycji (stan przed triażami) przez
**1333** (na `66b8301`) do **1553** na drzewie pomiaru. Wyrocznią samego przebiegu było
**1525** pozycji, bo narzędzie kasuje w drzewie roboczym własny plik testowy
`tools/tests/test_mutation_sweep.py` — mierzy bramki, nie siebie. Sprawdzone wprost:

```
$ git worktree add --detach /tmp/oracle 6c1048b && rm /tmp/oracle/tools/tests/test_mutation_sweep.py
$ cd /tmp/oracle && python3 tools/tests/test_all.py | tail -1
  1525/1525 przeszło
```

Pozycja 6.D5 z `docs/TASKS.md`. Pytanie: **które moduły odzyskały ocalałe mutacje od
czasu swojego raportu triażu** — i czy każdą różnicę da się przypisać commitowi,
zamiast opisać słowem „prawdopodobnie".


**Adnotacja 07.09.2026 (6.B42):** ten raport powstał, gdy nagłówek podawał **tylko
commit**, więc nie da się z niego odczytać, z jakiej TREŚCI mutowanych plików wyszły
poniższe liczby. Od 6.B42 nagłówek niesie odcisk treści przebiegu i tabelę
moduł → odcisk. Liczby zostają **nieprzeliczone** — są pomiarem z datą
(`docs/04-conventions.md`) — a ta adnotacja mówi tylko, czego w nich brakuje.

## Zakres: dwanaście raportów, dwadzieścia osiem modułów

6.D5 wymienia jako wejście „wszystkie dwanaście `reports/mutation-triage-*.md`".
Tyle ich jest i wszystkie dwanaście są tu policzone. **Modułów opisują dwadzieścia
osiem**, bo siedem raportów bierze po kilka plików naraz — i to moduł, nie raport, ma
własną liczbę ocalałych, więc tabelą główną jest tabela dwudziestu ośmiu modułów,
a tabela dwunastu raportów stoi nad nią jako podsumowanie.

Rozjazd w słowach, który przy okazji trzeba nazwać: `docs/TASKS.md` w jednym miejscu
mówi „wszystkie dwanaście modułów z raportem triażu", a w drugim — po scaleniu #247 —
„jedenaście modułów poza `clearance_profile.py`". Żadna z tych dwóch liczb nie zgadza
się z zawartością katalogu: raportów jest dwanaście, opisanych w nich modułów
dwadzieścia osiem, a `clearance_profile.py` **nie ma** własnego raportu triażu i nie
wchodzi do żadnej z tych liczb. Ten audyt liczy wszystkie dwadzieścia osiem, bo to
jedyny zakres, przy którym żaden moduł z raportem triażu nie zostaje bez liczby.

**Poza zakresem, świadomie:** `tools/blender/clearance_profile.py`. Jego wiersz domknęło
#247, które zmierzyło go ponownie (**16 / 77 na `9f4ae98`** zamiast 66 / 77 z `66b8301`)
i wpisało pomiar do `reports/mutation-sweep.md`. Powtarzanie tego tutaj nie dołożyłoby
ani jednej liczby.


## Wynik w jednym zdaniu

Z dwudziestu ośmiu modułów **dwadzieścia trzy mają dziś dokładnie tę liczbę ocalałych,
którą podał ich raport triażu**, jeden (`tools/blender/placement.py`) nie ma po drugiej
stronie żadnej liczby, a różnice są cztery. Z tych czterech **jedna jest regresem
pokrycia**: `tools/ci/assert_shot_metadata.py` poszło z 2 ocalałych na 32,
a 26 z nich pochodzi z jednego commita — `2c916de`.

Pozostałe trzy idą w drugą stronę: `pngio.py` 7 → 4, `lod.py` 38 → 37,
`crs.py` 6 → 4. Każda z czterech ma niżej commit, nie domysł.

## Metoda przypisania — czym jest „wyjaśnienie commitem"

Liczba różnicy nie jest wyjaśnieniem. Dla każdej ocalałej mutacji z dzisiejszego
przebiegu pytam **`git blame` o wiersz, w którym ona stoi**, i dostaję commit, który
ten wiersz napisał. To dzieli ocalałe na dwie rozłączne grupy:

* **wiersz starszy niż raport triażu** — mutacja jest tą samą, którą tamten raport już
  policzył i sklasyfikował;
* **wiersz młodszy niż raport triażu** — mutacja przyszła z konkretnym commitem,
  którego nazwa stoi w tabeli.

Dodatkowo dla każdego modułu, w którym zmieniła się **liczba mutacji**, liczę tę liczbę
z AST na kolejnych commitach (`git show COMMIT:ŚCIEŻKA` przepuszczone przez
`mutations_for`) i wskazuję ten, przy którym się zmieniła. Obie drogi są mechaniczne
i obie da się powtórzyć; żadna nie jest lekturą kodu „na oko".

Tam, gdzie tak przypisać się nie dało, stoi to wprost napisane — patrz §„Czego nie
udało się przypisać".


## Dwanaście raportów triażu — zbiorczo

| raport triażu | commit raportu | modułów | ocalałe po triażu | ocalałe dziś | Δ | mutacji wtedy → dziś |
|---|---|---:|---:|---:|---:|---:|
| `reports/mutation-triage-alignment.md` | `d6996bb` | 1 | 39 | 39 | 0 | 69 → 69 |
| `reports/mutation-triage-clearance.md` | `7545e45` | 1 | 6 | 6 | 0 | 11 → 11 |
| `reports/mutation-triage-fizyka.md` | `f1eb803` | 4 | 13 | 13 | 0 | 44 → 44 |
| `reports/mutation-triage-inspire-rail.md` | `7ade22c` | 1 | 2 | 2 | 0 | 41 → 41 |
| `reports/mutation-triage-lod.md` | `5697a09` | 1 | 38 | 37 | -1 | 105 → 104 |
| `reports/mutation-triage-parametry.md` | `fe92daa` | 7 | 4 | 4 | 0 | 64 → 66 |
| `reports/mutation-triage-placement.md` | `3262bb4` | 1 | — | 26 | — | 40 → 40 |
| `reports/mutation-triage-png-metadata.md` | `c1101aa` | 2 | 9 | 36 | +27 | 71 → 103 |
| `reports/mutation-triage-surface-width.md` | `b5bcf34` | 2 | 3 | 3 | 0 | 57 → 57 |
| `reports/mutation-triage-validate.md` | `cdf0591` | 2 | 4 | 4 | 0 | 55 → 56 |
| `reports/mutation-triage-wczytywanie.md` | `ff13aa6` | 4 | 7 | 5 | -2 | 43 → 49 |
| `reports/mutation-triage-wizualna.md` | `a9d6011` | 2 | 1 | 1 | 0 | 46 → 46 |


Kolumna „ocalałe po triażu" jest sumą liczb z §Wynik poszczególnych raportów, kolumna
„ocalałe dziś" — sumą dzisiejszych przebiegów. `reports/mutation-triage-placement.md`
nie podaje liczby po triażu, więc jego wiersz ma w tej kolumnie kreskę, a nie zero.

## Dwadzieścia osiem modułów — po jednym wierszu

| moduł | raport triażu | ocalałe po triażu | ocalałe dziś | Δ | mutacji wtedy | mutacji dziś | skąd różnica |
|---|---|---:|---:|---:|---:|---:|---|
| `tools/track/build_alignment.py` | alignment | 39 | 39 | 0 | 69 | 69 | `14ceed2` zmienił moduł, liczba mutacji bez zmian (69), ocalałe te same |
| `tools/blender/clearance.py` | clearance | 6 | 6 | 0 | 11 | **12** | 6.B5 dopisało `scan`, `margin_at` i `merge_spans` — jedna mutacja więcej (granica sklejania przedziałów kilometrażu), zabita przez `test_curve_radius_span_merge_joins_neighbours_and_splits_a_real_gap`; przeliczone 06.09.2026 tym samym poleceniem i zestawem `operator,prog`, wypis w `reports/promien-luku-szesc-osi.md` §7 |
| `tools/physics/braking.py` | fizyka | 5 | 5 | 0 | 11 | 11 | moduł bez zmian od `f1eb803` — `git diff` pusty |
| `tools/physics/reference.py` | fizyka | 3 | 3 | 0 | 8 | 8 | moduł bez zmian od `f1eb803` — `git diff` pusty |
| `tools/physics/schedule_envelope.py` | fizyka | 5 | 5 | 0 | 10 | 10 | moduł bez zmian od `f1eb803` — `git diff` pusty |
| `tools/track/timetable.py` | fizyka | 0 | 0 | 0 | 15 | 15 | moduł bez zmian od `f1eb803` — `git diff` pusty |
| `tools/track/inspire_rail.py` | inspire-rail | 2 | 2 | 0 | 41 | 41 | `deb3910` zmienił moduł, liczba mutacji bez zmian (41), ocalałe te same |
| `tools/blender/lod.py` | lod | 38 | 37 | -1 | 105 | 104 | `93687a8` — próg wyszedł do parametru, mutacja i ocalała znikły razem |
| `tools/blender/profiles.py` | parametry | 1 | 1 | 0 | 13 | 13 | moduł bez zmian od `fe92daa` — `git diff` pusty |
| `tools/track/detail_layout.py` | parametry | 1 | 1 | 0 | 8 | 9 | `74008bf` dołożył 1 mutację, zabitą |
| `tools/track/network_chainage.py` | parametry | 0 | 0 | 0 | 7 | 7 | moduł bez zmian od `fe92daa` — `git diff` pusty |
| `tools/blender/m7_layout.py` | parametry | 1 | 1 | 0 | 17 | 17 | moduł bez zmian od `fe92daa` — `git diff` pusty |
| `tools/track/station_layout.py` | parametry | 1 | 1 | 0 | 7 | 8 | `b7eef85` dołożył 1 mutację, zabitą |
| `tools/data/provenance.py` | parametry | 0 | 0 | 0 | 7 | 7 | moduł bez zmian od `fe92daa` — `git diff` pusty |
| `tools/track/data_freshness.py` | parametry | 0 | 0 | 0 | 5 | 5 | moduł bez zmian od `fe92daa` — `git diff` pusty |
| `tools/blender/placement.py` | placement | — | 26 | — | 40 | 40 | **nie przypisano**: raport triażu nie podaje liczby po; moduł bez zmian od `3262bb4` |
| `tools/visual/pngio.py` | png-metadata | 7 | 4 | -3 | 38 | 38 | `b16ae65` scalił dwie kopie przycinania w jedną (−3 ocalałe równoważne) |
| `tools/ci/assert_shot_metadata.py` | png-metadata | 2 | 32 | +30 | 33 | 73 | `a643f05` +4 ocalałe, `2c916de` +26 ocalałych (bramka peronu bez testów) |
| `tools/track/surface_sections.py` | surface-width | 1 | 1 | 0 | 29 | 29 | `1cbad40` zmienił moduł, liczba mutacji bez zmian (29), ocalała ta sama |
| `tools/track/tunnel_width.py` | surface-width | 2 | 2 | 0 | 28 | 28 | moduł bez zmian od `b5bcf34` — `git diff` pusty |
| `tools/track/validate.py` | validate | 2 | 2 | 0 | 36 | 37 | `b5c2eb9` dołożył 1 mutację, zabitą |
| `tools/track/crosscheck_alignment.py` | validate | 2 | 2 | 0 | 19 | 19 | moduł bez zmian od `cdf0591` — `git diff` pusty |
| `tools/track/crs.py` | wczytywanie | 6 | 4 | -2 | 8 | 14 | `d419437` −2/+3, `16726cd` +1, `f5126a3` (#250) −4 |
| `tools/track/fetch_osm_routes.py` | wczytywanie | 0 | 0 | 0 | 9 | 9 | moduł bez zmian od `ff13aa6` — `git diff` pusty |
| `tools/track/shapefile.py` | wczytywanie | 1 | 1 | 0 | 17 | 17 | moduł bez zmian od `ff13aa6` — `git diff` pusty |
| `tools/track/normalize_stops.py` | wczytywanie | 0 | 0 | 0 | 9 | 9 | moduł bez zmian od `ff13aa6` — `git diff` pusty |
| `tools/visual/compare.py` | wizualna | 0 | 0 | 0 | 24 | 25 | **6.D9 dołożył jedno porównanie** (zgodność sum `IDAT`), więc 24 → 25. Nowa mutacja jest **ZABITA** — pomiar celowany 06.09.2026: `==` → `!=` wywraca trzy testy (`test_te_same_piksele_z_innym_tEXt_sa_zgodne_co_do_bajtu`, `test_jeden_inny_piksel_zapala_bramke_mimo_ze_progi_go_przepuszczaja`, `test_json_wyniku_da_sie_zserializowac`), 1699/1703. Ocalałych nadal zero |
| `tools/visual/framing.py` | wizualna | 1 | 1 | 0 | 22 | 22 | moduł bez zmian od `a9d6011` — `git diff` pusty |

Kolumna „mutacji wtedy" jest liczbą z raportu triażu, „mutacji dziś" — policzoną z AST
przez to samo narzędzie na drzewie `6c1048b`. Kolumny `66b8301` tu nie ma, żeby wiersz
się mieścił; różnice wobec tamtego przebiegu są omówione niżej przy tych czterech
modułach, których dotyczą.

## Cztery różnice, każda z commitem

### `tools/ci/assert_shot_metadata.py`: 2 → 32, i to jest jedyny realny regres

Raport `reports/mutation-triage-png-metadata.md` §Wynik podaje po triażu **2 ocalałe
na 33 mutacje** (pokrycie 93,9 %), zmierzone na `737d592`, a wpisane commitem `c1101aa`.
Dziś jest ich 32 na **73**.

**Liczba mutacji przepisana 65 → 73 (08.09.2026, przy 6.C4), liczba ocalałych NIE
przeliczona — i to jest wybór, nie zaniedbanie.** 6.C4 dopisała do tego modułu
kotwicę geometrii na `subject_chainage_m` i dwa warunki dla widoku `inspect`, więc
mianownik urósł o osiem. Ocalałych nie przeliczam, bo ich pomiar to jeden pełny
przebieg zestawu na mutację — przy 73 mutacjach ponad godzina, a bramka
`test_drift_report_mutation_count_is_the_one_the_tool_gives_today` świadomie
sprawdza tylko mianownik, właśnie dlatego. Liczba **32 pochodzi więc z przebiegu
sprzed 6.C4** i tak ma być czytana; blok atrybucji niżej zostaje przy swoich 65,
bo jest zapisem tamtego pomiaru, a nie stanem bieżącym.

Przypisanie po `git blame`, wiersz po wierszu, wszystkie 65 mutacje:

```
tools/ci/assert_shot_metadata.py: mutacji 65, ocalałych 32
   2c916de  mutacji  26  ocalałych  26   Peron w scenie: kabina stojąca na stacji widzi peron
   79acb2e  mutacji  24  ocalałych   0   Scena Godota przestaje milczeć: metadane porównywane
   6991b8c  mutacji   8  ocalałych   2   Issue #107: scena bez składu nie jest przejazdem (#1
   a643f05  mutacji   7  ocalałych   4   Scena naprawdę streamuje: okno, LOD i bramka liczona
```

Czyta się to tak:

* `6991b8c` (02.09.2026, **przed** triażem) — 8 mutacji, 2 ocalałe. To **dokładnie te
  dwie**, które raport triażu zostawił świadomie: oba progi `0.0 -> 0.001` (dziś wiersze
  193 i 210), o których tamten raport pisze, że odróżnia je wyłącznie przedział
  `(0; 1 mm]`, a test zabijający musiałby twierdzić, że długość składu 0,5 mm ma
  przechodzić bramkę. Nic z nimi nie zrobiono i nic nie miało być zrobione;
* `79acb2e` — 24 mutacje, **0 ocalałych**. Bramka z czasów, gdy powstawała;
* `a643f05` (03.09.2026, `+108` wierszy modułu i `+163` wiersze testów) — 7 mutacji,
  **4 ocalałe**. Ten commit dopisał do bramki okno streamowania i predykat LOD **razem**
  z testami do własnego pliku testowego; mimo to cztery z siedmiu jego porównań nie
  dostały testu na granicy. To jest ta część dryfu, którą widać już w
  `reports/mutation-sweep.md` na `66b8301`: **6 ocalałych na 39**, czyli 2 + 4;
* `2c916de` (04.09.2026, `+201` wierszy modułu) — **26 mutacji i 26 ocalałych**.
  Ani jedna nie jest zabijana przez cokolwiek w zestawie.

Czwarty wiersz jest całym znaleziskiem tego audytu i ma jednozdaniowe wytłumaczenie,
które nie jest domysłem, tylko zawartością commita: `2c916de` dołożył kontrolę peronu
w scenie (`platform_problems`, `platform_radius_bounds`, kontrola obwiedni i wysokości
peronu) i **nie tknął `tools/tests/test_shot_metadata_gate.py`**. Sprawdzone wprost:

```
$ git show 2c916de --numstat --format= -- tools/ci/assert_shot_metadata.py \
      tools/tests/test_shot_metadata_gate.py
201	1	tools/ci/assert_shot_metadata.py
```

— druga ścieżka nie ma w tym commicie ani jednego wiersza. Testy tego commita poszły
do `tests/Game.Tests/PlatformFitTests.cs`, czyli po stronie C#, gdzie mierzą
`PlatformFit`, a nie bramkę pythonową, która ogląda metadane zrzutu.

Od `c1101aa` do dziś do `tools/tests/test_shot_metadata_gate.py` wszedł **dokładnie
jeden** commit, `a643f05`:

```
$ git log --oneline --no-merges c1101aa..HEAD -- tools/tests/test_shot_metadata_gate.py
a643f05 Scena naprawdę streamuje: okno, LOD i bramka liczona z predykatu
```

**Czego ten wpis NIE przesądza.** Nie każda z 26 ocalałych jest dziurą — część to
z pewnością mutanty równoważne, jak `!=` na porównaniu list długości albo próg `0.0`
przy obwiedni zwiniętej do punktu. Rozstrzygnięcie wymaga triażu, czyli tego, co
6.D5 ma **poza zakresem**. Zmierzone jest tu jedno: liczba i jej pochodzenie.


### `tools/track/crs.py`: 6 → 8 → 4, i wszystkie trzy liczby są zmierzone

To jest drugi przypadek, który 6.D5 nazywa wprost, i w trakcie tego audytu **zmienił się
pod ręką** — dlatego stoją tu dwa moje przebiegi, a nie jeden.

| stan | ocalałe / mutacje | skąd liczba |
|---|---:|---|
| po triażu, `ff13aa6` | 6 / 8 | `reports/mutation-triage-wczytywanie.md` §Wynik |
| `66b8301` | 8 / 14 | `reports/mutation-sweep.md` §„Kolejność triażu" |
| `e709f49`, mój przebieg z 05.09.2026 09:50 | **8 / 14** | wyjście niżej |
| `6c1048b`, mój przebieg z 05.09.2026 12:23 | **4 / 14** | wyjście niżej |

**Skąd 8 zamiast 6.** Sześć mutacji doszło dwoma commitami; liczone z AST na kolejnych
drzewach:

```
tools/track/crs.py: ff13aa6 -> 8, dfa8897 -> 8, d419437 -> 13, 16726cd -> 14, 66b8301 -> 14, 6c1048b -> 14
```

`d419437` („warunek zbieżności zamiast stałych 12 obrotów") dołożył pięć mutacji,
`16726cd` („residuum ponad dokładność datum") jedną. Przy okazji `d419437` **zabrał
dwie z sześciu ocalałych z triażu**, i to też jest sprawdzalne w źródle: strażnik
`if abs(step) < 1e-14: break` (wiersz 234 na `ff13aa6`) miał dwie mutacje, obie ocalałe
— operator uznany za równoważny i próg `1e-14`, opisany w tamtym raporcie jako
„obserwowalny, poniżej progu znaczenia" (33 nanometry). Dziś w tym miejscu stoi
`if abs(step) < tolerance_rad: return phi` (wiersz 406): **próg wyszedł do parametru,
więc mutacja progu nie ma już gdzie powstać**, a mutacja operatora jest zabijana przez
`test_crs_convergence_authalic_step_exactly_at_tolerance_fails` — test dopisany w tym
samym commicie.

Rachunek zamyka się co do jedności: 6 − 2 (wiersz 234) + 4 nowe ocalałe = 8.

**Skąd 4 zamiast 8.** Między moimi dwoma przebiegami wszedł `f5126a3` (#250,
„Testy jednostkowe dla dwóch modułów `tools/` pokrytych dotąd tylko integracyjnie"),
który dołożył `tools/tests/test_crs.py`. Przypisanie ocalałych po `git blame`, oba
przebiegi obok siebie:

```
e709f49                                        6c1048b
d419437  mutacji 5  ocalałych 3                d419437  mutacji 5  ocalałych 0
d47ae47  mutacji 4  ocalałych 2                d47ae47  mutacji 4  ocalałych 2
dfa8897  mutacji 2  ocalałych 0                dfa8897  mutacji 2  ocalałych 0
51fd842  mutacji 2  ocalałych 2                51fd842  mutacji 2  ocalałych 2
16726cd  mutacji 1  ocalałych 1                16726cd  mutacji 1  ocalałych 0
```

Zniknęły dokładnie te cztery, które przyszły po triażu (`d419437` i `16726cd`).
Zostały dwie z `d47ae47` i dwie z `51fd842` — czyli **te same cztery, które raport
triażu opisał jako mutanty równoważne** (strażnik wyznacznika i strażnik `rho`, oba
z progiem `1e-12`, oba z zerem jako jedyną osiągalną wartością po tej stronie progu).

Różnica wobec raportu triażu wynosi więc dziś **−2**, a nie **+2**, i obie połowy tej
drogi mają commit: `d419437` zabrał dwie ocalałe i dołożył cztery, `f5126a3` zabrał
te cztery.


### `tools/visual/pngio.py`: 7 → 4, i to nie jest poprawa pokrycia

Raport `reports/mutation-triage-png-metadata.md` §„Ocalałe po zmianie — 7, wszystkie
równoważne" wylicza je z wierszy: `42` (`pa <= pb`), `148` × 3 i `165` × 3. Wiersze 148
i 165 to **dwie kopie tego samego przycinania** — jedna w `write_gray`, druga
w `write_rgb`:

```
$ git show c1101aa:tools/visual/pngio.py | sed -n '148p;165p'
            value = 0.0 if value < 0.0 else (1.0 if value > 1.0 else value)
                channel = 0.0 if channel < 0.0 else (1.0 if channel > 1.0 else channel)
```

`b16ae65` („odrzuć strumień IDAT krótszy, niż deklaruje IHDR; **scal ścieżkę zapisu**")
zostawił z tych dwóch kopii jedną, dziś w wierszu 240 wspólnego `_write_8bit`. Trzy
ocalałe zniknęły więc razem z duplikatem kodu, a nie dlatego, że ktoś je zabił testem.
Cztery dzisiejsze ocalałe to wiersz 42 i trzy z wiersza 240 — czyli **ten sam zestaw
klas równoważności co po triażu, policzony raz zamiast dwa razy**.

Liczba mutacji nie drgnęła (38 → 38) i to też jest zmierzone, nie założone:

```
tools/visual/pngio.py: mutacji 38, ocalałych 4
   51fd842  mutacji  34  ocalałych   4
   63e0a6e  mutacji   2  ocalałych   0
   37dff99  mutacji   1  ocalałych   0
   b16ae65  mutacji   1  ocalałych   0
```

Cztery mutacje ubyły ze scaleniem ścieżki zapisu i cztery doszły z kontrolą CRC
i długości strumienia (`37dff99`, `b16ae65`, `63e0a6e`) — te nowe są zabite co do jednej.

### `tools/blender/lod.py`: 38 → 37

`reports/mutation-triage-lod.md` §Wynik podaje **38 ocalałych na 105**. Nazajutrz
`93687a8` („Zapas skrajni M7 poniżej milimetra jest stykiem, nie zapasem") wykonał na
tym module decyzję właściciela: próg `gauge_margin_m <= 0.0` zamienił na parametr
`COLLISION_GAUGE_MARGIN_MIN_M` i dopisał do `tools/tests/test_lod.py` cztery kontrole
negatywne. Ta jedna ocalała była wprost powodem tamtego commita — jego komunikat
cytuje `reports/mutation-triage-lod.md` i mutację `0.0 -> 0.001`.

Liczba mutacji zeszła przy tym ze 105 na 104 (literał `0.0` w warunku przestał istnieć
jako miejsce mutacji, bo stoi dziś jako wartość domyślna parametru, a nie w porównaniu),
a przypisanie ocalałych mówi, że po tamtym commicie nie została w nim ani jedna:

```
tools/blender/lod.py: mutacji 104, ocalałych 37
   51fd842  mutacji 102  ocalałych  37
   5697a09  mutacji   1  ocalałych   0
   93687a8  mutacji   1  ocalałych   0
```


## Dwadzieścia trzy moduły, w których liczba się nie zmieniła

To też jest wynik i też wymaga dowodu, bo „nie zmieniło się" da się napisać bez patrzenia.
Dowody są dwa i oba mechaniczne.

**Siedemnaście modułów nie zmieniło się o ani jeden bajt** od commita, który wpisał ich
raport triażu. Sprawdzone `git diff --numstat BAZA HEAD -- ŚCIEŻKA` — pusto dla:
`tools/blender/clearance.py`, `tools/blender/m7_layout.py`, `tools/blender/placement.py`,
`tools/blender/profiles.py`, `tools/data/provenance.py`, `tools/physics/braking.py`,
`tools/physics/reference.py`, `tools/physics/schedule_envelope.py`,
`tools/track/crosscheck_alignment.py`, `tools/track/data_freshness.py`,
`tools/track/fetch_osm_routes.py`, `tools/track/network_chainage.py`,
`tools/track/normalize_stops.py`, `tools/track/shapefile.py`, `tools/track/timetable.py`,
`tools/track/tunnel_width.py`, `tools/visual/framing.py`.

Szesnaście z nich ma dziś dokładnie liczbę ze swojego raportu triażu, a siedemnastym
jest `tools/blender/placement.py`, który liczby po triażu nie dostał (§„Czego nie udało
się przypisać"). Dla tych szesnastu zgodność dzisiejszego pomiaru z raportem triażu jest
zarazem **kontrolą narzędzia**: ten sam plik, ta sama liczba, mierzone przez dwie różne
sesje w odstępie dwóch dni. Gdyby któraś się rozjechała, rozjazd byłby w mierniku albo
w wyroczni, a nie w kodzie.

**Siedem modułów zmieniło się, a liczba ocalałych została.** W każdym z nich commit,
który dołożył porównanie, dołożył też test, który je zabija — i to widać w przypisaniu
mutacji po `git blame`:

| moduł | commit po triażu | mutacji na jego wierszach | z tego ocalałych |
|---|---|---:|---:|
| `tools/track/build_alignment.py` | `14ceed2` | 4 | 2 |
| `tools/track/inspire_rail.py` | `deb3910` | 0 | 0 |
| `tools/track/surface_sections.py` | `1cbad40` | 2 | 0 |
| `tools/visual/compare.py` | `ac7d0d0` | 0 | 0 |
| `tools/track/validate.py` | `b5c2eb9` | 1 | 0 |
| `tools/track/detail_layout.py` | `74008bf` | 1 | 0 |
| `tools/track/station_layout.py` | `b7eef85` | 1 | 0 |

Dwa zera w kolumnie „mutacji" nie są błędem odczytu: `deb3910` i `ac7d0d0` zmieniły
te moduły, ale nie dotknęły ani jednego wiersza z porównaniem albo progiem, więc
narzędzie nie ma tam czego mutować.

Dwie ocalałe przy `14ceed2` też nie są dryfem, i to trzeba powiedzieć wprost, bo tabela
sama tego nie mówi: nagłówek `reports/mutation-triage-alignment.md` podaje jako commit
pomiaru **`14ceed2`**, czyli ten sam, a nie `d6996bb`, którym raport wszedł do `main`.
Te dwie ocalałe są więc **w środku** liczby 39 z tamtego raportu, a nie ponad nią —
i dlatego dzisiejsze 39 zgadza się z tamtym 39 co do jedności.


Wiersz `station_layout.py` jest tu wart osobnego zdania, bo jego liczba **mutacji**
urosła już po `66b8301`: `b7eef85` („Decyzja o długości peronu dociera do pipeline'u:
95,0 m zamiast 94,0 m") dołożył jedno porównanie, siódme na 7 → 8. `reports/mutation-sweep.md`
wypisuje dla tego pliku `1 / 7`; dziś jest `1 / 8` i jedynka jest ta sama.


## Czego nie udało się przypisać

**`tools/blender/placement.py` — brak liczby po drugiej stronie.**
`reports/mutation-triage-placement.md` jest jedynym z dwunastu raportów, który
**nie podaje liczby ocalałych po triażu**. Ma sekcję „Pięć realnych dziur" z pięcioma
zabiciami sprawdzonymi wykonaniem i sekcję „Czego NIE uznałem za równoważne", ale
tabeli „przed / po" nie ma; sam raport pisze przy tym, że liczba 20 z pozycji 5.1 jest
sprzed naprawy narzędzia i traktuje ją „jako wskazówkę, nie pomiar". Dzisiejsza liczba
jest zmierzona (26 / 40) i zgadza się co do jedności z `reports/mutation-sweep.md`
na `66b8301`, ale **różnicy wobec triażu nie da się policzyć, bo nie ma od czego
odejmować**. Nie zgaduję jej: moduł od `3262bb4` nie zmienił się o bajt, więc dzisiejsze
26 jest zarazem stanem z dnia tamtego raportu — i to jest wszystko, co można tu
powiedzieć bez wymyślania.

**Nic poza tym.** Pozostałe dwadzieścia siedem modułów ma obie liczby i przypisaną
różnicę — zero albo commit.

## Czego ten raport NIE mówi

* **Nie klasyfikuje ocalałych.** Ocalała mutacja to albo dziura w pokryciu, albo mutant
  równoważny, i narzędzie tego nie rozstrzyga. 26 nowych ocalałych w
  `assert_shot_metadata.py` to liczba, nie werdykt — triaż jest osobną robotą i 6.D5
  ma go poza zakresem.
* **Nie naprawia niczego.** Ani jednego testu nie dopisano do modułów pod pomiarem;
  jedyna zmiana w kodzie idzie do `tools/tests/test_mutation_sweep.py` i pilnuje
  tego raportu, nie modułów (niżej).
* **Nie przelicza `reports/mutation-sweep.md`.** Tamten raport jest zdjęciem drzewa
  `66b8301` i tak ma zostać; ten stoi obok niego jako zdjęcie `6c1048b`. Liczby z
  `66b8301`, które pojawiają się wyżej w prozie, są **przepisane** z tamtego raportu,
  a nie zmierzone ponownie — i są jedynymi liczbami w tym raporcie, które nie pochodzą
  z przebiegu wykonanego na potrzeby tego audytu ani z `git show`.

## Bramka: co pilnuje, żeby ta tabela nie zestarzała się po cichu

Do `tools/tests/test_mutation_sweep.py` doszło sześć testów. Pilnują **liczby mutacji**,
nie liczby ocalałych: liczbę mutacji liczy się z AST w ułamku sekundy, więc da się ją
sprawdzać przy każdym przebiegu zestawu, a liczba ocalałych kosztuje pełny przebieg
testów na mutację — 686 mutacji, 139 minut przy czterech robotnikach.

To wystarcza, bo **w obu udokumentowanych przypadkach dryfu ocalałe przyszły razem
z mutacjami**: `assert_shot_metadata.py` 33 → 39 → 65 i `crs.py` 8 → 13 → 14. Bramka
mówi więc: „moduł, dla którego ten audyt podał liczby, urósł o porównanie — przelicz
audyt", i nie udaje, że pilnuje pokrycia.

Kontrole negatywne — wykonane, nie zadeklarowane: sześć, po jednej na test,
każda wykonana na kopii raportu i każda **musi** paść:

```
1. skasowany jeden wiersz tabeli modułów
   -> AssertionError: wierszy modułów: 27, oczekiwano 28
2. „mutacji dziś" dla crs.py podniesione o jeden (14 -> 15)
   -> AssertionError: reports/mutation-drift.md rozjechał się z drzewem — przelicz
      audyt dla tych modułów: ['tools/track/crs.py: raport mówi 15, narzędzie liczy 14']
3. powód różnicy zamieniony na „prawdopodobnie przez zmiany w zapisie PNG"
   -> AssertionError: różnice bez commita i bez przyznania się:
      ["tools/visual/pngio.py: 'prawdopodobnie przez zmiany w zapisie PNG'"]
4. liczba z raportu triażu przepisana na dzisiejszą (6 -> 4)
   -> AssertionError: tools/track/crs.py: liczba z raportu triażu to 4
5. jeden z dwunastu raportów przestaje być w audycie wymieniony
   -> AssertionError: mutation-triage-wczytywanie.md
6. DRIFT_COLUMNS przestawione z 8 na 4, czyli detektor łapie obie tabele
   -> IndexError w test_the_drift_table_detector_is_not_matching_prose
```

Kontrola nr 6 nie jest ozdobnikiem — **to jest usterka, którą ta para testów naprawdę
złapała w trakcie pisania**. Pierwsza wersja detektora brała każdy wiersz zaczynający
się od ścieżki w grawisach, więc łapała też czterokolumnową tabelę z §„Dwadzieścia trzy
moduły…", nadpisywała nią siedem wierszy tabeli głównej i test liczby mutacji padał
`IndexError`, zamiast cokolwiek sprawdzić. Warunek na liczbę kolumn wszedł z tego
pomiaru, nie z ostrożności.

## Jak to powtórzyć

```bash
git checkout 6c1048b
for m in $(sed -n 's/^| `\(tools[^`]*\)`.*/\1/p' reports/mutation-drift.md | sort -u); do
    python3 tools/tests/mutation_sweep.py --only "$m" --workers 4 \
        --journal "build/drift-6c1048b/$(basename $m .py).jsonl" \
        --json    "build/drift-6c1048b/$(basename $m .py).json"
done
```

Zmierzone na tej maszynie: 686 mutacji w 28 modułach, 4 robotniki, 139 minut
(zestaw testów sam w sobie chodzi 45 s, więc jedna mutacja to ok. 12 s przy
czterech drzewach roboczych naraz). Dziennik JSONL jest dopisywany po każdej mutacji,
więc przerwany przebieg wznawia się tym samym poleceniem — ta własność uratowała ten
pomiar, gdy sesja padła w połowie.

Mutacje powstają z AST w ustalonej kolejności, więc dwa przebiegi na tym samym drzewie
dają tę samą listę i te same identyfikatory `plik:wiersz:przesunięcie`.


## Wyjścia przebiegów — wszystkie dwadzieścia osiem

```
$ python3 tools/tests/mutation_sweep.py --only tools/track/build_alignment.py --workers 4 \
      --journal build/drift-6c1048b/build_alignment.jsonl --json build/drift-6c1048b/build_alignment.json
[MUTACJE] 69 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/build_alignment.jsonl
[MUTACJE] rozstrzygniętych 69/69, zabitych 30, ocalałych 39, nierozstrzygniętych 0
rc=0  czas=628s

$ python3 tools/tests/mutation_sweep.py --only tools/blender/clearance.py --workers 4 \
      --journal build/drift-6c1048b/clearance.jsonl --json build/drift-6c1048b/clearance.json
[MUTACJE] 11 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/clearance.jsonl
[MUTACJE] rozstrzygniętych 11/11, zabitych 5, ocalałych 6, nierozstrzygniętych 0
rc=0  czas=121s

$ python3 tools/tests/mutation_sweep.py --only tools/physics/braking.py --workers 4 \
      --journal build/drift-6c1048b/braking.jsonl --json build/drift-6c1048b/braking.json
[MUTACJE] 11 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/braking.jsonl
[MUTACJE] rozstrzygniętych 11/11, zabitych 6, ocalałych 5, nierozstrzygniętych 0
rc=0  czas=119s

$ python3 tools/tests/mutation_sweep.py --only tools/physics/reference.py --workers 4 \
      --journal build/drift-6c1048b/reference.jsonl --json build/drift-6c1048b/reference.json
[MUTACJE] 8 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/reference.jsonl
[MUTACJE] rozstrzygniętych 8/8, zabitych 5, ocalałych 3, nierozstrzygniętych 0
rc=0  czas=160s

$ python3 tools/tests/mutation_sweep.py --only tools/physics/schedule_envelope.py --workers 4 \
      --journal build/drift-6c1048b/schedule_envelope.jsonl --json build/drift-6c1048b/schedule_envelope.json
[MUTACJE] 10 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/schedule_envelope.jsonl
[MUTACJE] rozstrzygniętych 10/10, zabitych 5, ocalałych 5, nierozstrzygniętych 0
rc=0  czas=112s

$ python3 tools/tests/mutation_sweep.py --only tools/track/timetable.py --workers 4 \
      --journal build/drift-6c1048b/timetable.jsonl --json build/drift-6c1048b/timetable.json
[MUTACJE] 15 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/timetable.jsonl
[MUTACJE] rozstrzygniętych 15/15, zabitych 15, ocalałych 0, nierozstrzygniętych 0
rc=0  czas=151s

$ python3 tools/tests/mutation_sweep.py --only tools/track/inspire_rail.py --workers 4 \
      --journal build/drift-6c1048b/inspire_rail.jsonl --json build/drift-6c1048b/inspire_rail.json
[MUTACJE] 41 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/inspire_rail.jsonl
[MUTACJE] rozstrzygniętych 41/41, zabitych 39, ocalałych 2, nierozstrzygniętych 0
rc=0  czas=453s

$ python3 tools/tests/mutation_sweep.py --only tools/blender/lod.py --workers 4 \
      --journal build/drift-6c1048b/lod.jsonl --json build/drift-6c1048b/lod.json
[MUTACJE] 104 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/lod.jsonl
[MUTACJE] rozstrzygniętych 104/104, zabitych 67, ocalałych 37, nierozstrzygniętych 0
rc=0  czas=960s

$ python3 tools/tests/mutation_sweep.py --only tools/blender/profiles.py --workers 4 \
      --journal build/drift-6c1048b/profiles.jsonl --json build/drift-6c1048b/profiles.json
[MUTACJE] 13 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/profiles.jsonl
[MUTACJE] rozstrzygniętych 13/13, zabitych 12, ocalałych 1, nierozstrzygniętych 0
rc=0  czas=110s

$ python3 tools/tests/mutation_sweep.py --only tools/track/detail_layout.py --workers 4 \
      --journal build/drift-6c1048b/detail_layout.jsonl --json build/drift-6c1048b/detail_layout.json
[MUTACJE] 9 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/detail_layout.jsonl
[MUTACJE] rozstrzygniętych 9/9, zabitych 8, ocalałych 1, nierozstrzygniętych 0
rc=0  czas=124s

$ python3 tools/tests/mutation_sweep.py --only tools/track/network_chainage.py --workers 4 \
      --journal build/drift-6c1048b/network_chainage.jsonl --json build/drift-6c1048b/network_chainage.json
[MUTACJE] 7 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/network_chainage.jsonl
[MUTACJE] rozstrzygniętych 7/7, zabitych 7, ocalałych 0, nierozstrzygniętych 0
rc=0  czas=72s

$ python3 tools/tests/mutation_sweep.py --only tools/blender/m7_layout.py --workers 4 \
      --journal build/drift-6c1048b/m7_layout.jsonl --json build/drift-6c1048b/m7_layout.json
[MUTACJE] 17 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/m7_layout.jsonl
[MUTACJE] rozstrzygniętych 17/17, zabitych 16, ocalałych 1, nierozstrzygniętych 0
rc=0  czas=175s

$ python3 tools/tests/mutation_sweep.py --only tools/track/station_layout.py --workers 4 \
      --journal build/drift-6c1048b/station_layout.jsonl --json build/drift-6c1048b/station_layout.json
[MUTACJE] 8 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/station_layout.jsonl
[MUTACJE] rozstrzygniętych 8/8, zabitych 7, ocalałych 1, nierozstrzygniętych 0
rc=0  czas=83s

$ python3 tools/tests/mutation_sweep.py --only tools/data/provenance.py --workers 4 \
      --journal build/drift-6c1048b/provenance.jsonl --json build/drift-6c1048b/provenance.json
[MUTACJE] 7 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/provenance.jsonl
[MUTACJE] rozstrzygniętych 7/7, zabitych 7, ocalałych 0, nierozstrzygniętych 0
rc=0  czas=78s

$ python3 tools/tests/mutation_sweep.py --only tools/track/data_freshness.py --workers 4 \
      --journal build/drift-6c1048b/data_freshness.jsonl --json build/drift-6c1048b/data_freshness.json
[MUTACJE] 5 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/data_freshness.jsonl
[MUTACJE] rozstrzygniętych 5/5, zabitych 5, ocalałych 0, nierozstrzygniętych 0
rc=0  czas=72s

$ python3 tools/tests/mutation_sweep.py --only tools/blender/placement.py --workers 4 \
      --journal build/drift-6c1048b/placement.jsonl --json build/drift-6c1048b/placement.json
[MUTACJE] 40 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/placement.jsonl
[MUTACJE] rozstrzygniętych 40/40, zabitych 14, ocalałych 26, nierozstrzygniętych 0
rc=0  czas=685s

$ python3 tools/tests/mutation_sweep.py --only tools/visual/pngio.py --workers 4 \
      --journal build/drift-6c1048b/pngio.jsonl --json build/drift-6c1048b/pngio.json
[MUTACJE] 38 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/pngio.jsonl
[MUTACJE] rozstrzygniętych 38/38, zabitych 34, ocalałych 4, nierozstrzygniętych 0
rc=0  czas=396s

$ python3 tools/tests/mutation_sweep.py --only tools/ci/assert_shot_metadata.py --workers 4 \
      --journal build/drift-6c1048b/assert_shot_metadata.jsonl --json build/drift-6c1048b/assert_shot_metadata.json
[MUTACJE] 65 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/assert_shot_metadata.jsonl
[MUTACJE] rozstrzygniętych 65/65, zabitych 33, ocalałych 32, nierozstrzygniętych 0
rc=0  czas=769s

$ python3 tools/tests/mutation_sweep.py --only tools/track/surface_sections.py --workers 4 \
      --journal build/drift-6c1048b/surface_sections.jsonl --json build/drift-6c1048b/surface_sections.json
[MUTACJE] 29 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/surface_sections.jsonl
[MUTACJE] rozstrzygniętych 29/29, zabitych 28, ocalałych 1, nierozstrzygniętych 0
rc=0  czas=559s

$ python3 tools/tests/mutation_sweep.py --only tools/track/tunnel_width.py --workers 4 \
      --journal build/drift-6c1048b/tunnel_width.jsonl --json build/drift-6c1048b/tunnel_width.json
[MUTACJE] 28 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/tunnel_width.jsonl
[MUTACJE] rozstrzygniętych 28/28, zabitych 26, ocalałych 2, nierozstrzygniętych 0
rc=0  czas=387s

$ python3 tools/tests/mutation_sweep.py --only tools/track/validate.py --workers 4 \
      --journal build/drift-6c1048b/validate.jsonl --json build/drift-6c1048b/validate.json
[MUTACJE] 37 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/validate.jsonl
[MUTACJE] rozstrzygniętych 37/37, zabitych 35, ocalałych 2, nierozstrzygniętych 0
rc=0  czas=505s

$ python3 tools/tests/mutation_sweep.py --only tools/track/crosscheck_alignment.py --workers 4 \
      --journal build/drift-6c1048b/crosscheck_alignment.jsonl --json build/drift-6c1048b/crosscheck_alignment.json
[MUTACJE] 19 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/crosscheck_alignment.jsonl
[MUTACJE] rozstrzygniętych 19/19, zabitych 17, ocalałych 2, nierozstrzygniętych 0
rc=0  czas=220s

$ python3 tools/tests/mutation_sweep.py --only tools/track/crs.py --workers 4 \
      --journal build/drift-6c1048b/crs.jsonl --json build/drift-6c1048b/crs.json
[MUTACJE] 14 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/crs.jsonl
[MUTACJE] rozstrzygniętych 14/14, zabitych 10, ocalałych 4, nierozstrzygniętych 0
rc=0  czas=217s

$ python3 tools/tests/mutation_sweep.py --only tools/track/fetch_osm_routes.py --workers 4 \
      --journal build/drift-6c1048b/fetch_osm_routes.jsonl --json build/drift-6c1048b/fetch_osm_routes.json
[MUTACJE] 9 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/fetch_osm_routes.jsonl
[MUTACJE] rozstrzygniętych 9/9, zabitych 9, ocalałych 0, nierozstrzygniętych 0
rc=0  czas=123s

$ python3 tools/tests/mutation_sweep.py --only tools/track/shapefile.py --workers 4 \
      --journal build/drift-6c1048b/shapefile.jsonl --json build/drift-6c1048b/shapefile.json
[MUTACJE] 17 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/shapefile.jsonl
[MUTACJE] rozstrzygniętych 17/17, zabitych 16, ocalałych 1, nierozstrzygniętych 0
rc=0  czas=197s

$ python3 tools/tests/mutation_sweep.py --only tools/track/normalize_stops.py --workers 4 \
      --journal build/drift-6c1048b/normalize_stops.jsonl --json build/drift-6c1048b/normalize_stops.json
[MUTACJE] 9 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/normalize_stops.jsonl
[MUTACJE] rozstrzygniętych 9/9, zabitych 9, ocalałych 0, nierozstrzygniętych 0
rc=0  czas=167s

$ python3 tools/tests/mutation_sweep.py --only tools/visual/compare.py --workers 4 \
      --journal build/drift-6c1048b/compare.jsonl --json build/drift-6c1048b/compare.json
[MUTACJE] 24 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/compare.jsonl
[MUTACJE] rozstrzygniętych 24/24, zabitych 24, ocalałych 0, nierozstrzygniętych 0
rc=0  czas=317s

$ python3 tools/tests/mutation_sweep.py --only tools/visual/framing.py --workers 4 \
      --journal build/drift-6c1048b/framing.jsonl --json build/drift-6c1048b/framing.json
[MUTACJE] 22 mutacji do policzenia, 4 robotników, commit 6c1048b, dziennik build/drift-6c1048b/framing.jsonl
[MUTACJE] rozstrzygniętych 22/22, zabitych 21, ocalałych 1, nierozstrzygniętych 0
rc=0  czas=366s
```
