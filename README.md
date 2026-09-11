# Metro BXL

Symulator prowadzenia pociągu na rzeczywistej sieci metra STIB/MIVB w Brukseli.
Cztery linie, 59 stacji, 39,9 km, tabor M7, przejście z sygnalizacji klasycznej na CBTC.

Zasada architektoniczna, z której wynika cała reszta:

> **Linia jest symulacją, która działa bez gracza. Kabina jest jednym z jej widoków.**

Reguły pracy: `CLAUDE.md`. Architektura: `docs/01-architecture.md`. Kolejność zadań
i lista tego, co blokuje co: `docs/TASKS.md`.

## Start

```bash
bash doctor.sh                       # kontrola środowiska i testów
python3 tools/tests/test_all.py      # testy narzędzi, bez Blendera i bez sieci
dotnet test tests/Sim.Tests          # rdzeń symulacji, bez Godota
```

## Stan: co działa, a czego nie ma

**Rdzeń symulacji — `src/Sim/`, 53 plików `.cs`, kompiluje się i testuje bez silnika:**

- fizyka: model trakcji M7, opór Davisa, hamowanie służbowe i granica przyczepności,
  krok stały 1/120 s liczony **licznikiem kroków**, nigdy `t += dt`;
- sygnalizacja: bloki stałe, autoryzacja jazdy, ochrona pociągu, obszar testowy CBTC,
  nastawnia automatyczna ryglująca trasę na następny odcinek międzystacyjny;
- prowadzenie: scenariusz jazdy, przejazd linią, cykl drzwi, postój na stacji,
  obsługa stacji dla składu prowadzonego ręcznie (okno zatrzymania, blokada trakcji);
- każdy parametr niesie status (`spec`, `source_backed`, `design_assumption`, `unknown`) —
  wartość bez źródła nie da się podstawić po cichu.

**Warstwa silnika — `src/Game/`, projekt Godot 4.7 mono:**

- jeden skład M7 jedzie 6,56 km po pakiecie A, napędzany rdzeniem;
- **przejazd zatrzymuje się na stacjach**: dojazd w okno ±5 m otwiera cykl drzwi,
  trakcja jest zablokowana do potwierdzenia zamknięcia, przejechana stacja ląduje
  w liczniku miniętych; błąd zatrzymania jest mierzony i pokazywany;
- **tryb `--line`**: scena przejeżdża całą linię z 11 zatrzymaniami, prowadzona rdzeniem;
  zatrzymania sceny i rdzenia są identyczne co do wszystkich kolumn (próg **zerowy**);
- **sygnalizacja w kabinie** (`--signalling`, działa też BEZ `--line`): skład wchodzi
  na bloki, nastawnia rygluje mu trasy, a ATP **naprawdę hamuje za maszynistę** —
  ostrzeżenie, potem hamulec służbowy. HUD pokazuje prędkość dopuszczalną, autorytet
  jazdy z powodem jego końca, licznik zaryglowanych tras i rodzaj ingerencji. Pod
  limitem planu ochrona nie rusza ani jednego kroku i ślad jest identyczny co do bitu
  z przejazdem bez niej; wyłączyć jej z kabiny nie można;
- rozjazd Godot ↔ rdzeń **0,000 m**, ten sam odcisk telemetrii przy nierównym podziale
  klatek (`reports/T-400-first-run.md`);
- zrzuty z silnika idą przez tę samą kontrolę wizualną co geometria, odtwarzalne co do
  bajtu również między maszynami (`reports/T-012-godot-capture.md`).

**Geometria — zweryfikowana wizualnie:**

- pipeline Blendera — generacja, render kontrolny, wykrywanie regresji, odrzucanie
  pustej klatki;
- osie sześciu pakietów z oficjalnej geometrii STIB: `L1_A`, `L1_B`, `L2_E`, `L5_C`,
  `L5_D`, `L6_F`, każda z własnym plikiem provenance;
- proceduralne tunele pakietów: szczelina na szwie 0,000 mm, normalne do wnętrza,
  eksport per chunk plus manifest streamingowy dla Godota;
- proceduralna skorupa M7: 94,0 m, 6 członów, 18 drzwi podwójnych na stronę;
- skrajnia M7 w tunelu, mierzona **dwiema niezależnymi drogami** zgodnymi do 3,9 mm;
- rozkład jazdy odtworzony z GTFS: 49 z 49 odcinków sieci dopasowanych.

**Czego nie ma i dlaczego:**

- **profilu pionowego.** Brak publicznych rzędnych główki szyny, a dwa oficjalne źródła
  podają sprzeczne głębokości stacji. Wszystkie **sześć** osi w `data/track/` ma Z = 0
  i `vertical.status = not_modelled`, a generator **odrzuca** `--variant production`.
  Od 6.D120 odcinek Parc↔Arts-Loi wchodzi do geometrii jako wariant `partial-vertical`:
  rzędne z rejestru tam, gdzie są, i jawny, niewygładzony uskok na granicy wiedzy.
  Zablokowane: T-112, czeka na T-901.
  To samo blokuje scenę z **dwoma** pakietami — przy Z = 0 rury A i E przenikają się
  w rejonie Arts-Loi;
- **stacji wynikających z danych.** Bryły stacji SĄ — T-212 jest scalone i daje na
  stacji Parc schody, windę, antresolę, korytarz i portal — ale układ jest **kanoniczny**:
  `tools/track/station_components.py` stawia **18** wymiarów jako `design_assumption`
  i ani jednego ze STIB. Rzut stacji, liczba i położenie wyjść zostają `unknown`;
- **wielu składów W SCENIE.** Rdzeń prowadzi ich **N** — `LineCore` krokuje wszystkie
  na jednym zegarze, jednej osi i jednym planie bloków, a testy przybijają, że skład
  nie wjeżdża w blok zajęty przez inny. Scena pokazuje **jeden**: `FirstRun` ma jeden
  węzeł `TrainView`. To jest ograniczenie WIDOKU, nie rdzenia — T-320 ma etap 2
  zrobiony, a otwarty zostaje takt i obiegi z T-113;
- **wnętrza kabiny w scenie.** Geometria kabiny jest od 6.D119 —
  `tools/blender/m7_cab.py` buduje ją ze skryptu — ale **24** jej wymiary to
  `design_assumption` i ani jeden nie pochodzi ze STIB, a scena nie ma węzła wnętrza;
- **ciągłego kilometrażu linii.** `data/track/` pokrywa pakiety, nie linie; między
  pakietami zostaje 4034 m bez geometrii — ta druga liczba jest z kształtów GTFS,
  których w repozytorium nie ma, więc **żadna bramka jej nie sprawdza** (6.D104 §5).
  Zakres pakietów to decyzja właściciela.

Pełny audyt tego, co jest faktem o brukselskim metrze, a co decyzją projektową:
**`docs/21-measured-vs-assumed.md`**.

## Weryfikacja

Bramki nie mają być zielone — mają **odrzucać**. Każda ma kontrolę negatywną wypisaną
w commicie, który ją wprowadził, a od audytu mutacyjnego z 02.09.2026 obowiązuje zasada
**dwóch niezależnych dróg do tej samej liczby**. Zielona bramka bez pokrycia jest gorsza
niż brak bramki, bo usypia.

```bash
python3 tools/tests/test_all.py             # testy narzędzi
dotnet test tests/Sim.Tests                 # rdzeń, bez Godota
dotnet test tests/Game.Tests/Game.Tests.csproj   # warstwa silnika (poza MetroBxl.sln)

bash tools/ci/blender_smoke.sh       # T-010: generacja + render + testy negatywne
bash tools/ci/visual_smoke.sh        # T-012: determinizm, regresja, pusta klatka
bash tools/ci/m7_shell_check.sh      # T-220: skorupa M7 i jej wymiary
bash tools/ci/tunnel_alignment.sh    # T-210: tunel pakietu A, chunki, manifest
bash tools/ci/vehicle_clearance.sh   # skrajnia M7 w tunelu, pomiar na siatce
```

`tests/Game.Tests` celowo **nie jest w `MetroBxl.sln`**: solucja pilnuje reguły 9
(nic w `src/Sim/` nie importuje Godota), a projekt testowy warstwy silnika by tę bramkę
rozmontował. Uruchamia się go po ścieżce i osobnym krokiem w `godot-first-run.yml`.

**Rendery trzeba obejrzeć.** Metryka automatyczna nie zastępuje oględzin — jednolita
szara klatka przechodzi kontrolę „nie jest pusta". Szczegóły: `docs/17-visual-regression.md`.

## CI

Dziesięć workflowów: `blender-smoke`, `visual-regression`, `tunnel-alignment`,
`m7-shell`, `material-style-smoke`, `station-details`, `python-tests`, `sim-tests`,
`godot-first-run`, `prune-merged-branches`.

Wszystkie oprócz ostatniego są bramkami, po jednej na zadanie weryfikacyjne;
`prune-merged-branches` jest utrzymaniowy i odpala się wyłącznie ręcznie
(`workflow_dispatch`).

**Wszystkie chodzą na self-hosted runnerze**, na gołej etykiecie — bez ani jednej
dodatkowej. Tego samego wymaga `tools/tests/test_ci_workflows.py`, gdzie komplet dwóch
etykiet jest już odrzucany. Nazw ani liczby maszyn README nie podaje: dobór idzie po
etykiecie, a liczebności puli nie da się sprawdzić z repozytorium. Runnera nie wybiera
się po nazwie — to zwężałoby pulę do jednej maszyny.

Ten akapit stoi osobno i bez ani jednego markera przeszłości, żeby `test_docs_ci_claims.py`
faktycznie go czytał; powód rozpisany w `CLAUDE.md` §9 i zmierzony
w `reports/9-goly-selektor.md`.

Poprzednie litery tej reguły, przepisane a nie dopisane obok: do 05.09.2026 goła
etykieta (od wyczerpania minut GitHub Actions 02.09.2026); od 05.09.2026 do 07.09.2026
komplet pięciu etykiet z `wsl2` na czterech maszynach `woogitsu-wsl-DOM-NEW-*`;
od 07.09.2026 do 09.09.2026 komplet sześciu, z dwiema sprzętowymi, bo stara pula była
wtedy **nadal zarejestrowana** i odsiać ją dało się tylko etykietą, której nie miała.
Od 09.09.2026 stara pula jest odpięta, więc odsiewanie znika razem z powodem, dla
którego istniało — a nie jako uproszczenie zapisu.

Każdy job osobno odrzuca pull requesty
z forków, każdy sprawdza, że workspace jest czysty, i każdy instaluje narzędzia
warunkowo. Powody i pułapki: `CLAUDE.md` §9, testy: `tools/tests/test_ci_workflows.py`.

`queued` **nie jest weryfikacją**. Zadanie jest zweryfikowane po zakończonym, zielonym
jobie i sprawdzeniu wymaganych artefaktów.

## Struktura

| ścieżka | co tam jest |
|---|---|
| `CLAUDE.md` | konstytucja pracy agentów |
| `docs/` | architektura, symulacja, konwencje, legal, research, audyt wymiarów |
| `docs/TASKS.md` | rozpiska zadań, plan faz i tabela „co blokuje co" |
| `reports/` | raporty z wykonanych zadań, z rzeczywistymi wynikami weryfikacji |
| `data/network/` | snapshot sieci, rejestr źródeł i licencji, głębokości do T-901 |
| `data/track/` | osie sześciu pakietów i ich provenance |
| `data/vehicle/` | specyfikacja M7 |
| `src/Sim/` | rdzeń symulacji — fizyka, sygnalizacja, prowadzenie. **Bez Godota** |
| `src/Sim.Runner/` | uruchamianie scenariuszy rdzenia z linii poleceń |
| `src/Game/` | projekt Godot 4.7 mono — scena, widok składu, tunel, HUD, wejście |
| `tests/Sim.Tests/` | testy rdzenia |
| `tests/Game.Tests/` | testy warstwy silnika, poza `MetroBxl.sln` |
| `tools/track/` | pobieranie i budowa danych trasy, transformacje CRS, kontrole krzyżowe |
| `tools/blender/` | profile, generator tunelu, skorupa M7, osadzenie pojazdu, skrajnia |
| `tools/visual/` | canonical manifest kamer, kadrowanie, porównanie renderów |
| `tools/ci/` | pipeline'y weryfikacyjne, jeden na zadanie |
| `tools/tests/` | testy bez Blendera i bez sieci |

Skille w `.claude/skills/`: `blender-asset`, `track-data`, `sim-physics`, `heartbeat`.

## Zasady, które łatwo złamać przez przypadek

1. **Nie zgaduj danych o sieci.** Hierarchia źródeł: oficjalne STIB → oficjalne dane
   Regionu/Paradigm → OSM → źródła wtórne. Czego nie da się potwierdzić — pytasz.
2. **Nie modeluj ręcznie tego, co da się wygenerować.** Każdy zasób 3D powstaje przez
   skrypt w `tools/blender/`.
3. **1 jednostka = 1 metr.** Wszędzie.
4. **`src/Sim/` nie importuje Godota.** Rdzeń ma się kompilować i testować bez silnika.
5. **Nie commituj** `build/`, `renders/`, plików > 10 MB.
6. **`queued` nie jest weryfikacją.** Zadanie jest zweryfikowane po zielonym jobie
   i sprawdzeniu artefaktów.

## Źródła danych

Rejestr maszynowy: `data/network/sources.json` — URL, licencja, atrybucja, ograniczenia
i data sprawdzenia dla każdego źródła. Hierarchia i uzasadnienia:
`docs/07-open-data-research.md`. Provenance pobranych danych: `docs/09-data-provenance.md`.

Bazowa geometria trasy pochodzi z oficjalnych danych STIB, regionalne dane Brussels
Mobility/Paradigm służą jako niezależna kontrola, OSM jako źródło szczegółów torowych
i kolejna kontrola. **Rozbieżności między źródłami są liczone i zapisywane, nigdy
uśredniane.**

Snapshoty niosą własne okna ważności i część z nich jest **wygaśnięta** — INSPIRE Rails
w snapshocie z 01.09.2026 ma `tn:validFrom/validTo` 02.03.2026–28.06.2026. Rejestr to
odnotowuje zamiast ukrywać; odświeżenie snapshotów jest zadaniem utrzymaniowym.

## Zastrzeżenie

CBTC w scenariuszu historycznym 31.08.2026 jest traktowany jako system w trakcie
wdrożenia i testów, nie jako pełna eksploatacja na całych liniach 1 i 5.

Projekt nie używa brandingu, logotypów, map, piktogramów ani dzieł sztuki STIB/MIVB.
Zasady: `docs/03-legal.md`.
