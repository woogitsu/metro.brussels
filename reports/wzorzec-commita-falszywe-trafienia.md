# 6.D13 · Wzorzec SHA w bramce higieny raportów łapie też to, co SHA nie jest

**Zmierzone 06.09.2026 na commicie:** `936c4ad`

## 0. Pytanie i metoda

Zadanie: znaleźć **wszystkie** tokeny łapane przez wzorzec `COMMIT` z
`tools/tests/test_report_hygiene.py` w nagłówkach `reports/*.md` (dokładnie ta sama
definicja nagłówka co w bramce: tekst przed pierwszym `## `) i wydać werdykt dla
**każdego z osobna** — czy jest commitem, czy nie. To pytanie inne niż w 6.D10
(`reports/commit-naglowka-a-raport.md`): tamten pomiar sprawdzał, czy SHA z
nagłówka jest w jakiejś relacji z historią pliku (dotyka / przodek / brak relacji /
nieosiągalny). Ten pomiar pyta prościej i wcześniej: **czy token w ogóle jest
commitem**, niezależnie od tego, do czego się odnosi.

Metoda: wzorzec `` `([0-9a-f]{7,40})` `` (wzorzec SPRZED tej poprawki, żeby zmierzyć
problem, a nie już poprawiony stan) uruchomiony na nagłówkach wszystkich plików
`reports/*.md`, z wypisaniem każdego trafienia osobno (ten sam plik może dać więcej
niż jeden token — patrz `T-400-stage-3b.md` niżej, cztery tokeny w jednym nagłówku).

## 1. Wynik zbiorczy

| | |
|---|---|
| raportów w `reports/` | **80** |
| tokenów złapanych w nagłówkach | **90** |
| długość 7 znaków (skrócony SHA) | **78** |
| długość 40 znaków (pełny SHA) | **11** |
| długość **inna** niż 7 albo 40 | **1** |
| tokenów, które **nie są** commitem | **1** |

78 + 11 + 1 = 90. Jeden jedyny token o długości innej niż 7 albo 40 to jednocześnie
jedyny token, który werdykt „nie jest commitem" dostaje — **to nie jest zbieg
okoliczności, tylko podstawa zawężenia wzorca** opisana w §3.

## 2. Werdykt dla każdego z 90 tokenów

Kolumna „TAK/NIE" odpowiada na pytanie zadania: czy token jest commitem. Dla 89
tokenów odpowiedź wynika z tego, że każdy stoi w zdaniu, które go tak właśnie
nazywa („Zmierzone … na commicie", „scalenie #NNN", „commit PR-a", „snapshot
poprzedniego audytu, z którym ten raport się porównuje" itd.) — sprawdzone ręcznie
w nagłówku każdego raportu, nie założone z kształtu tokenu. Sześć z tych 89
(`a3d8c57`, `cbd1192` w `mutacje-rdzen-sygnalizacji.md` i cztery z §5 poniżej) to
commity, które dziś nie są osiągalne z `main` (gałąź scalona przez squash) — ale to
pytanie z 6.D10, nie z tej pozycji: **commitem były w chwili powstania**, bo ktoś
faktycznie wykonał `git commit` i to jest treść tego werdyktu.

| raport | token | długość | commit? |
|---|---|---|---|
| `L1_A-chunks.md` | `51fd842` | 7 | TAK |
| `L1_A-crosscheck.md` | `51fd842` | 7 | TAK |
| `L1_A-geometry.md` | `51fd842` | 7 | TAK |
| `L1_A-lod.md` | `51fd842` | 7 | TAK |
| `L1_A-track-spacing.md` | `51fd842` | 7 | TAK |
| `M7-clearance-profile.md` | `51fd842` | 7 | TAK |
| `M7-curve-clearance.md` | `51fd842` | 7 | TAK |
| `M7-in-tunnel.md` | `d4a9c54` | 7 | TAK |
| `M7-shell-liczba-testow.md` | `77c72da` | 7 | TAK |
| `M7-shell.md` | `51fd842` | 7 | TAK |
| `R-007-platform-dimensions.md` | `68e1c81` | 7 | TAK |
| `T-011-detail-markers.md` | `c6eb1ca` | 7 | TAK |
| `T-011-details-BF.md` | `154ad30` | 7 | TAK |
| `T-012-godot-capture.md` | `4575195` | 7 | TAK |
| `T-113-timetable.md` | `e2c32e9` | 7 | TAK |
| `T-211-station-layout.md` | `1426940` | 7 | TAK |
| `T-211-stations-BF.md` | `527f509` | 7 | TAK |
| `T-212-station.md` | `a5356f0` | 7 | TAK |
| `T-310-physics.md` | `614bfeb` | 7 | TAK |
| `T-311-braking.md` | `9c94c1a` | 7 | TAK |
| `T-312-doors.md` | `ed0f5e2` | 7 | TAK |
| `T-400-first-run.md` | `39123b9` | 7 | TAK |
| `T-400-stage-3b.md` | `619b179` | 7 | TAK |
| `T-400-stage-3b.md` | `cb7321e` | 7 | TAK |
| `T-400-stage-3b.md` | `32588a8` | 7 | TAK |
| `T-400-stage-3b.md` | **`9e2066aef7ef`** | **12** | **NIE** |
| `axis-station-chainage.md` | `4a03982` | 7 | TAK |
| `bpy-extraction-round-2.md` | `3c01fbb` | 7 | TAK |
| `bpy-extraction-round-3.md` | `fc5db5ff09eb3257e18ac6d8aaa7c5811f32fa18` | 40 | TAK |
| `branch-audit.md` | `737d592` | 7 | TAK |
| `clearance-BE.md` | `1b7c2bb` | 7 | TAK |
| `commit-naglowka-a-raport.md` | `08d12b689b5a03b6f307ba46b4eb5134d89b882f` | 40 | TAK |
| `czas-przegladu-mutacyjnego.md` | `08d12b689b5a03b6f307ba46b4eb5134d89b882f` | 40 | TAK |
| `droga-do-grywalnosci.md` | `3c242f7` | 7 | TAK |
| `dziennik-mutacyjny.md` | `05c0f59` | 7 | TAK |
| `energy-balance.md` | `d48f5a1d79396208b2459c3f9090db11833097fa` | 40 | TAK |
| `golden-trace-gate.md` | `51d324a` | 7 | TAK |
| `kolejka-audyt-aktualnosci.md` | `9b4d26d` | 7 | TAK |
| `kolejka-uzupelnienie.md` | `51d324a` | 7 | TAK |
| `komendy-weryfikacji.md` | `74f5b4a6a0a8060ab807fc92fa79dab230d76d04` | 40 | TAK |
| `liczba-trybow-run-plan.md` | `74f5b4a` | 7 | TAK |
| `linecore-budget.md` | `6c1048b` | 7 | TAK |
| `linecore-budget.md` | `dfbde8f` | 7 | TAK |
| `m7-glb-nondeterminism.md` | `2fa30c1` | 7 | TAK |
| `m7-ground-truth-verification.md` | `51fd842` | 7 | TAK |
| `mutacje-rdzen-sygnalizacji.md` | `3c242f7` | 7 | TAK |
| `mutacje-rdzen-sygnalizacji.md` | `a3d8c57` | 7 | TAK |
| `mutacje-rdzen-sygnalizacji.md` | `cbd1192` | 7 | TAK |
| `mutacje-rdzen-sygnalizacji.md` | `d495051` | 7 | TAK |
| `mutacje-rdzen-sygnalizacji.md` | `b41c158` | 7 | TAK |
| `mutation-drift.md` | `6c1048b` | 7 | TAK |
| `mutation-drift.md` | `66b8301` | 7 | TAK |
| `mutation-sweep.md` | `66b8301` | 7 | TAK |
| `mutation-sweep.md` | `737d592` | 7 | TAK |
| `mutation-triage-alignment.md` | `14ceed2` | 7 | TAK |
| `mutation-triage-clearance.md` | `5f6b68e` | 7 | TAK |
| `mutation-triage-fizyka.md` | `737d592` | 7 | TAK |
| `mutation-triage-inspire-rail.md` | `737d592` | 7 | TAK |
| `mutation-triage-lod.md` | `c572eb3` | 7 | TAK |
| `mutation-triage-m7-report.md` | `8c3f752` | 7 | TAK |
| `mutation-triage-make-test-track.md` | `ec926a2` | 7 | TAK |
| `mutation-triage-parametry.md` | `737d592` | 7 | TAK |
| `mutation-triage-placement.md` | `3262bb4` | 7 | TAK |
| `mutation-triage-png-metadata.md` | `737d592` | 7 | TAK |
| `mutation-triage-round-2-modules.md` | `9a57130a10699d4a1362fc1cac08ed05b0ba3aa9` | 40 | TAK |
| `mutation-triage-surface-width.md` | `b5bcf34` | 7 | TAK |
| `mutation-triage-sweep.md` | `7a817df` | 7 | TAK |
| `mutation-triage-sweep.md` | `66b8301` | 7 | TAK |
| `mutation-triage-sweep.md` | `66b8301` | 7 | TAK |
| `mutation-triage-validate.md` | `cdf0591` | 7 | TAK |
| `mutation-triage-wczytywanie.md` | `737d592` | 7 | TAK |
| `mutation-triage-wizualna.md` | `737d592` | 7 | TAK |
| `negative-control-audit.md` | `045730bd639c771d59b6d3b876c4d390d85f16ad` | 40 | TAK |
| `network-chainage.md` | `580882c` | 7 | TAK |
| `nieznana-opcja-runnera.md` | `417d3dc484c017a42b4b5bd32b1a5634d1840146` | 40 | TAK |
| `package-a-station-source-gaps.md` | `8e2faea` | 7 | TAK |
| `packages-BE-tunnels.md` | `aeaa322` | 7 | TAK |
| `packages-BF-alignment.md` | `d47ae47` | 7 | TAK |
| `pixel-hash-oracle.md` | `4516a13` | 7 | TAK |
| `polecenia-runnera-bez-testu.md` | `08d12b689b5a03b6f307ba46b4eb5134d89b882f` | 40 | TAK |
| `report-claims-audit.md` | `e2382f7` | 7 | TAK |
| `service-day.md` | `0aec7ae` | 7 | TAK |
| `snapshot-drift.md` | `377b59e` | 7 | TAK |
| `surface-vs-tunnel.md` | `01c457d` | 7 | TAK |
| `test-all-runtime-gate.md` | `045730bd639c771d59b6d3b876c4d390d85f16ad` | 40 | TAK |
| `typy-sim-bez-testu.md` | `4e56958` | 7 | TAK |
| `wyrocznia-mutacyjna-falszywe-zabicia.md` | `8c3f752` | 7 | TAK |
| `zapadka-dwie-role.md` | `154ad30` | 7 | TAK |
| `zapadka-liczy-prace.md` | `8edb1d8` | 7 | TAK |
| `zapisy-do-data.md` | `045730bd639c771d59b6d3b876c4d390d85f16ad` | 40 | TAK |

**Jeden fałszywy token na 90** — `9e2066aef7ef` w `T-400-stage-3b.md`, zdanie:
„Blender **5.2.1 LTS** (hash `9e2066aef7ef`)". To hash builda Blendera, zacytowany
w opisie środowiska pomiaru — poprawna i pożyteczna informacja, nie commit. Sam hex,
w grawisach, 12 znaków: format nierozróżnialny od skróconego SHA żadną regułą
składniową prostszą niż długość (patrz §3). Pierwszy raz nazwany w
`reports/commit-naglowka-a-raport.md` §4, jako produkt uboczny zupełnie innego
pomiaru (6.D10); ten raport go **potwierdza jako jedyny** na całym `reports/`, nie
tylko wśród 69 nagłówków, które badał tamten pomiar.

## 3. Zawężenie wzorca — dlaczego {7, 40}, a nie inny zakres

Kolumna „długość" w tabeli wyżej pokazuje coś więcej niż ciekawostkę: **wśród 90
tokenów nie ma ani jednego o długości 8..11 albo 13..39.** Tylko trzy długości
w ogóle występują: 7 (78 razy), 40 (11 razy) i 12 (dokładnie raz — i to ten
fałszywy). To nie jest przypadek zakresu, tylko konwencja: 7 i 40 to dwie jedyne
formy, jakie faktycznie produkuje `git` — `git rev-parse --short` (domyślny skrót,
7 znaków) i `git rev-parse` (pełny SHA-1, 40 znaków). Ten projekt nigdy nie cytuje
commita w żadnej **innej** długości.

Stąd poprawka w `tools/tests/test_report_hygiene.py`: wzorzec `COMMIT` zmieniony
z `` `([0-9a-f]{7,40})` `` (zakres — łapie KAŻDĄ długość od 7 do 40) na
`` `([0-9a-f]{40}|[0-9a-f]{7})` `` (dokładnie dwie długości — te, których projekt
naprawdę używa). Bramka **przestała łapać** ten jeden fałszywy token, bo żaden
prawdziwy SHA w tym repozytorium nigdy nie miał 12 znaków — a nie dlatego, że
`9e2066aef7ef` dostał specjalne traktowanie z nazwy. Nowy token o długości 12,
gdyby się pojawił, zostałby złapany tak samo jak dziś — to jest różnica między
zawężeniem opartym na zmierzonej konwencji a wyjątkiem opartym na treści jednego
znalezionego przypadku.

**Kontrola negatywna wykonana** (opisana w §4): zawężony wzorzec nadal łapie
prawdziwe SHA obu długości — dowód, że zawężenie nie zabiło detekcji, tylko zdjęło
jeden fałszywy przypadek.

## 4. Kontrola negatywna — wykonana, nie opisana

Nowy test `test_wzorzec_commita_lapie_realne_dlugosci_i_nie_lapie_hasza_narzedzia`
w `tools/tests/test_report_hygiene.py` sprawdza cztery przypadki na raz: skrócony
SHA (7) wchodzi, pełny SHA (40) wchodzi, hash Blendera (12) **nie** wchodzi, losowy
hex o długości 20 też nie wchodzi (żeby zawężenie nie okazało się wyjątkiem „na
jeden token"). Piąty punkt w tym samym teście odtwarza STARY wzorzec `{7,40}`
lokalnie i pokazuje, że on ten sam token łapie — dowód, że problem istniał, nie
tylko twierdzenie o nim.

Wykonane wprost, poza zestawem, przez podmianę `COMMIT` z powrotem na
`` `([0-9a-f]{7,40})` `` w pliku i uruchomienie modułu:

```
$ python3 -c "..."   # test_report_hygiene.py, wszystkie funkcje test_*
PASS test_data_i_commit_stoja_w_naglowku_a_nie_gdziekolwiek_w_raporcie
PASS test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie
PASS test_kazdy_raport_podaje_commit_na_ktorym_mierzono
PASS test_kazdy_raport_podaje_date_pomiaru
PASS test_konwencja_naglowka_jest_wyczytana_z_raportow_ktore_ja_juz_maja
PASS test_lista_wyjatkow_jest_zamknieta
PASS test_lista_wyjatkow_nie_gnije
PASS test_lista_wyjatkow_od_sciezek_nie_gnije
FAIL test_wzorzec_commita_lapie_realne_dlugosci_i_nie_lapie_hasza_narzedzia -> (AssertionError)
PASS test_wzorzec_sciezki_lapie_to_co_ma_i_nie_lapie_prozy
liczba FAIL/ERROR: 1
```

Ze starym, szerokim wzorcem pada **dokładnie ten jeden, nowy test** — żaden
z dziewięciu istniejących nie widzi tej zmiany, co jest oczekiwane: `T-400-stage-3b.md`
ma w nagłówku TAKŻE prawdziwy skrócony SHA (`619b179`), więc
`test_kazdy_raport_podaje_commit_na_ktorym_mierzono` był zielony niezależnie od
tego, czy Blender-hash liczył się jako commit. To jest właśnie ryzyko opisane
w zadaniu: fałszywy token nie psuje NIC dzisiaj, dopóki stoi obok prawdziwego —
psułby dopiero raport, który zacytowałby taki hash **bez** żadnego prawdziwego SHA
obok. Po przywróceniu zawężonego wzorca (`git diff` poniżej pokazuje tylko
zamierzoną zmianę) wszystkie 10 testów przechodzi.

## 5. Weryfikacja

```
$ python3 tools/tests/test_all.py
...
  RAZEM 64.281 s, 1735 testów, 84 modułów
$ echo $?
0
```

`test_report_hygiene.py` ma teraz **10** testów (było 9), zestaw ogólny **1735**
(było 1734 przed dopisaniem tej pozycji). Zero linii `FAIL`.

## 6. Skończone, gdy — odhaczenie kryterium z `docs/TASKS.md`

„Raport podaje dla każdego tokenu łapanego przez wzorzec, czy jest commitem, czy
nie" — §2, wszystkie 90. „Bramka przestaje łapać te, które nie są" — §3, zawężenie
`{7,40}` → dokładne `{7}`/`{40}`, zero wyjątków na liście (rozwiązanie wybrane:
zawężenie wzorca, nie lista wyjątków — bo jest dokładnie jeden przypadek i jest on
wynikiem zmierzonej konwencji długości, nie osobliwości wymagającej nazwanego
wyjątku). „Kontrola negatywna wykonana: zawężony wzorzec nadal łapie prawdziwe
SHA" — §4, oba przypadki (7 i 40) w tym samym teście, który też dowodzi problemu
na starym wzorcu.

## 7. Poza zakresem

Żaden nagłówek raportu nie został zmieniony. `9e2066aef7ef` w `T-400-stage-3b.md`
stoi tam, gdzie stał — to poprawna i pożyteczna informacja o środowisku pomiaru,
zgodnie z zastrzeżeniem zadania. Zmieniony jest wyłącznie wzorzec w
`tools/tests/test_report_hygiene.py`.
