# METRO BXL — konstytucja projektu

Czytasz ten plik **przed każdym zadaniem**. Jeśli polecenie z czatu stoi w sprzeczności
z czymkolwiek poniżej — powiedz o tym, zanim zaczniesz.

---

## 1. Czym jest ten projekt

Symulator prowadzenia pociągu na rzeczywistej sieci metra STIB/MIVB w Brukseli.
Cztery linie, 59 stacji, 39,9 km, tabor M7, przejście z sygnalizacji klasycznej na CBTC.

Zasada architektoniczna, z której wynika cała reszta:

> **Linia jest symulacją, która działa bez gracza. Kabina jest jednym z jej widoków.**

Szczegóły: `docs/01-architecture.md`.

## 2. Zanim cokolwiek zrobisz

```bash
bash doctor.sh                       # kontrola środowiska i testów
python3 tools/tests/test_all.py      # testy narzędzi, wszystkie muszą przechodzić
```

Jeśli `doctor.sh` zgłasza brak Blendera, a zadanie dotyczy geometrii — **przerwij**
i powiedz o tym. Nie próbuj obejść.

## 3. Mapa dokumentów

| plik | do czego |
|---|---|
| `docs/00-network-data.md` | fakty o sieci — **źródło prawdy**, nie zmieniasz |
| `docs/01-architecture.md` | podział na moduły, krok czasowy, determinizm |
| `docs/02-simulation.md` | równania i **tablica referencyjna** dla testów fizyki |
| `docs/03-legal.md` | twarde blokady prawne |
| `docs/04-conventions.md` | jednostki, osie, nazewnictwo, git |
| `docs/05-glossary.md` | słownik FR/NL/PL — do czytania źródeł STIB |
| `docs/06-worked-example.md` | **wzorcowo wykonane zadanie** — przeczytaj przed pierwszym |
| `docs/07-open-data-research.md` | hierarchia źródeł, publiczne dane i repozytoria referencyjne |
| `docs/22-heartbeat.md` | puls sesji — kiedy zakładać i dlaczego ma milczeć |
| `docs/23-environment.md` | **skąd wziąć** Blender, .NET i Godota — wersje, adresy, sumy |
| `docs/24-clearance-profile-decisions.md` | trzynaście progów luzu — **rozstrzygnięte 04.09.2026**, zero otwartych |
| `docs/TASKS.md` | lista zadań |
| `docs/TASK-TEMPLATE.md` | format nowego zadania |
| `data/network/lines.json` | dane sieci maszynowo |
| `data/network/sources.json` | maszynowy rejestr źródeł i licencji danych |

Skille w `.claude/skills/` wchodzą automatycznie: `blender-asset`, `track-data`,
`sim-physics`, `heartbeat`.

## 4. Twarde reguły

1. **Nie zgaduj danych o sieci.** Najpierw `docs/00-network-data.md`, `data/network/`
   i hierarchia z `docs/07-open-data-research.md`. Dla nowych danych: oficjalne STIB →
   oficjalne dane Regionu/Paradigm → OSM → źródła wtórne. Repo GitHub bez jawnej,
   kompatybilnej licencji jest tylko referencją. Czego nie da się potwierdzić — pytasz.
   Zmyślona głębokość stacji wygląda dokładnie tak samo jak prawdziwa, dopóki ktoś
   z Brukseli w to nie zagra.
2. **Nie modeluj ręcznie tego, co da się wygenerować.** Tunele, tory, koryta, słupki,
   oświetlenie — proceduralnie ze skryptu, z danych.
3. **Każdy zasób 3D powstaje przez skrypt w `tools/blender/`.** Żadnego „otworzyłem
   Blendera i pociągnąłem myszą". Czego nie da się zeskryptować — oznacz i przerwij.
4. **Każde zadanie kończy się weryfikacją, którą sam wykonujesz.** Sekcja 5.
5. **1 jednostka = 1 metr.** Wszędzie. Reszta jednostek: `docs/04-conventions.md`.
6. **`data/` jest tylko do odczytu**, chyba że zadanie mówi inaczej wprost.
7. **Blokady prawne z `docs/03-legal.md` są twarde.** Nie proponujesz obejścia,
   nie robisz „podobnego, ale innego" wariantu cudzego dzieła.
8. **Nie commituj `build/`, `renders/`, plików > 10 MB.**
9. **Nic w `src/Sim/` nie importuje Godota.** Rdzeń ma się kompilować i testować
   bez silnika.
10. **Jedno zadanie = jedna gałąź = jeden commit.** Nie poprawiasz przy okazji
    plików spoza zadania.

## 5. Pętla weryfikacji — obowiązkowa

Nie masz oczu, dopóki sam sobie ich nie zrobisz.

### Geometria

```bash
# 1 generuj
blender --background --python tools/blender/tunnel_sweep.py -- \
    --centerline data/track/L1_A.json --profile box_double --out build/L1_A.glb
# 2 renderuj
blender --background --python tools/blender/render_check.py -- \
    --in build/L1_A.glb --out renders/L1_A
# 3 OBEJRZYJ: renders/L1_A_iso.png, _side.png, _normals.png, _inside.png
# 4 OPISZ słowami, co widzisz na każdej z czterech
```

Czego szukasz:

| render | wykrywa |
|---|---|
| `_iso` | pustą scenę, geometrię zwiniętą w punkt, zły przebieg |
| `_side` | pomylone jednostki, zły profil pionowy |
| `_normals` | wywrócone normalne — przód ściany ciemny, tył jasny |
| `_inside` | kadr z osi: brak geometrii wokół kabiny, przekrój, nakładka siatki |

**Wiersz `_inside` jest przepisany, a nie dopisany obok** (09.09.2026). Poprzednia
wersja przypisywała mu wykrywanie wywróconych normalnych („widać »przez« ścianę"),
a to zostało **zmierzone jako nieprawda**: para fixture różniąca się wyłącznie windingiem
dała klatki `_inside` różne o **cztery bajty na 737 tysięcy**, czyli o szum kompresji,
a obejrzane nie różniły się niczym — wersja z odwróconymi ścianami wyglądała jak zdrowy
tunel (6.D75, `reports/6d75-klatka-orientacji.md`). Zdolność istnieje od 09.09.2026,
tylko w **osobnej klatce `_normals`**: kulling na materiale kontrolnym byłby dosłowniej
zgodny z dawnym brzmieniem tego wiersza, ale ten sam skrypt renderuje też pudło pojazdu
i przekroje stacji, oglądane **legalnie od tyłu**, więc zapalałby się na poprawnej
geometrii. Klatek jest więc **cztery, nie trzy**, a wypis `[NORMALNE] tylna_strona=`
jest **podłogą, nie oceną** — obejrzenie `_normals` jest obowiązkowe tak samo jak
trzech pozostałych.

### Kod

```bash
python3 tools/tests/test_all.py
dotnet test tests/Sim.Tests
```

### Zakazane formy weryfikacji

- „skrypt wykonał się bez błędu"
- „wygląda dobrze"
- „powinno działać"
- „zaimplementowałem zgodnie ze specyfikacją"

Skrypt bez błędu potrafi wyprodukować pustą scenę. **Zadanie nie jest skończone,
dopóki nie pokażesz rzeczywistego wyjścia weryfikacji.**

## 6. Format zadania

Sześć pól. Brakuje któregoś — dopytaj, nie zaczynaj.
Szablon i przykłady dobrych kryteriów: `docs/TASK-TEMPLATE.md`.

| pole | |
|---|---|
| Wejście | konkretne ścieżki |
| Wyjście | konkretne ścieżki |
| Weryfikacja | polecenie i oczekiwany wynik |
| Skończone, gdy | zdanie z liczbami |
| Poza zakresem | czego NIE robisz |
| Zależy od | numery zadań |

## 7. Jak raportujesz

Na koniec zadania piszesz, w tej kolejności:

1. co zrobiłeś, w jednym zdaniu
2. **rzeczywiste wyjście weryfikacji** — wklejone, nie opisane
3. co widzisz na renderach, jeśli zadanie ich dotyczyło
4. czego świadomie nie zrobiłeś i dlaczego
5. co zauważyłeś przy okazji, ale nie tknąłeś

Wzór: `docs/06-worked-example.md`.

## 8. Kiedy przerwać i zapytać

- zadanie wymaga oceny estetycznej
- brakuje danych, których nie ma w `data/` ani `docs/`
- trzeba podjąć decyzję projektową, której nie ma w dokumentach
- render pokazuje coś, czego nie umiesz jednoznacznie ocenić
- zadanie dotyka `docs/03-legal.md`
- zadanie wymagałoby zmiany silnika, dodania zależności albo złamania reguły z sekcji 4

**Zatrzymanie się w tych miejscach jest poprawnym wynikiem pracy, nie porażką.**
Zgadywanie w tym projekcie jest kosztowniejsze niż czekanie na odpowiedź.

**Ale zatrzymanie się z powodu pustej kolejki nią nie jest.** Powyższa lista mówi, kiedy
przerwać **konkretne zadanie** — nie kiedy przestać pracować. Gdy zadanie utknie na cudzej
decyzji albo na cudzym przebiegu CI, agent bierze następną pozycję z fazy 5 lub 6
w `docs/TASKS.md`; są tam wyłącznie zadania, które nie wymagają ani jednej decyzji
właściciela. Gdy kolejka zejdzie poniżej dwunastu pozycji, **pierwszym zadaniem jest jej
uzupełnienie**, nie zatrzymanie się. Pilnuje tego `tools/tests/test_backlog.py`, żeby
reguła nie była życzeniem zapisanym w dokumencie.

Zadania wymyślonego na miejscu, bo akurat skończyła się kolejka, nie bierze się nigdy:
omija format z sekcji 6 i zwykle ląduje w kodzie, którego nikt nie prosił o zmianę.

## 9. CI / GitHub Actions

**Od 02.09.2026 całe CI chodzi na self-hosted runnerze**, po wyczerpaniu minut
GitHub Actions. Poprzednia wersja tego punktu mówiła, że standardem jest
`ubuntu-latest`; to już nieprawda i dlatego jest tu przepisana, a nie dopisana obok.

- **`runs-on: self-hosted`** — gołą etykietą, bez ani jednej dodatkowej. Tak stoi
  w każdym z dziesięciu workflowów i tego samego wymaga `REQUIRED_RUNNER_LABELS`
  w `tools/tests/test_ci_workflows.py`, gdzie komplet dwóch etykiet jest już
  odrzucany. **Runnera nie wybiera się po nazwie**: nazwa zwęża pulę do jednej
  maszyny, a to jest awaria opisana w literze pierwszej niżej — tym razem z własnej
  ręki. Liczby maszyn ten punkt nie podaje i nigdy nie będzie: dobór idzie wyłącznie
  po etykiecie, więc liczebność puli jest dla selektora nieistotna, a wpisana tu
  zestarzałaby się po cichu — dwa razy już to zrobiła.

  **Warunek zmiany.** Wraca komplet etykiet wtedy i tylko wtedy, gdy do puli
  dołączy maszyna, która etykietę `self-hosted` nosi, a zadań tego projektu wykonać
  nie może — bo wtedy odsianie znów jest do czegoś potrzebne. Sam wzrost albo spadek
  liczebności puli nie jest takim powodem.

  **Ten akapit stoi osobno i to jest wybór, nie formatowanie.** `test_docs_ci_claims.py`
  pomija akapity z markerem przeszłości, a marker działa na cały akapit — deklaracja
  wtopiona w wywód o dawnych literach reguły była więc **poza bramką**, która istnieje
  dokładnie po to, żeby jej pilnować. Rozbieżność z 09.09.2026 (§9 opisywało komplet
  sześciu etykiet, gdy wszystkie joby chodziły już na gołej) znalazło z tego powodu
  czyjeś oko, a nie test. Deklaracja ma stać w akapicie bez markera, żeby następną
  taką rozbieżność zapaliła bramka.

- **Cztery litery tej reguły, i wszystkie zostają wymienione**, bo bez nich nie widać,
  czemu dzisiejsza jest taka, jaka jest. Ten punkt jest przepisany, a nie dopisany
  obok — po raz **trzeci**.
  Litera pierwsza (do 05.09.2026): gołe `self-hosted`, bez dodatkowych etykiet.
  Powód był **jeden**: w `matmaxalez/osadale` zdjęto etykietę `wsl2` 02.08.2026, bo
  maszyna, która ją nosiła, była JEDNA i została wyłączona, a joby zawisły w `queued`.
  Ochroną była wtedy szerokość selektora.
  Litera druga (05.09–07.09.2026): komplet pięciu etykiet z `wsl2`. Ochroną przestała
  być szerokość, a stała się **liczebność puli**: cztery maszyny
  `woogitsu-wsl-DOM-NEW-01` … `-04` z tym samym kompletem, więc wyłączenie jednej nie
  zawieszało niczego.
  Litera trzecia (07.09–09.09.2026): komplet sześciu etykiet, z dwiema sprzętowymi.
  Pula została wtedy wymieniona, a stare maszyny **nadal były zarejestrowane**;
  cztery etykiety starego kompletu nosiły oba zbiory, więc samo zdjęcie `wsl2` dałoby
  selektor łapiący stare razem z nowymi. Odsiać stare dało się **tylko dodaniem**
  etykiety, której nie miały — i to, a nie opis sprzętu, było powodem, dla którego
  w selektorze stały nazwy modelu procesora i karty.
  Litera czwarta, dzisiejsza (09.09.2026, decyzja właściciela): stara pula przestała
  być zarejestrowana, a maszyny są dedykowane temu repozytorium i niewspółdzielone.
  Odsiewać nie ma czego, więc odsiewanie znika razem z powodem, dla którego istniało.
  Kolejność jest tu treścią: etykiety sprzętowe **nie były** ozdobą i nie zostały
  usunięte jako ozdoba — zniknęły, bo zniknął zbiór, który miały odciąć.

- **Każdy job odrzuca pull requesty z forków.** To warunek bezpieczeństwa, nie higiena:
  joby wykonują kod ze sprawdzonego refa na maszynie właściciela. `metro.brussels` jest
  prywatne, ale ma włączone forkowanie, więc „forka nie da się zrobić" tu nie działa.
  Warunek nosi **każdy job osobno** — `needs:` nie jest zamiennikiem.

- **Workspace jest współdzielony między przebiegami.** Sprząta `actions/checkout`
  (`clean` domyślnie `true`, czyli `git clean -ffdx`, a `-x` obejmuje pliki ignorowane).
  Każdy workflow ma krok, który to **sprawdza**, bo bramki tego projektu oglądają pliki
  wyjściowe i stary plik przeszedłby je tak samo dobrze jak świeży.

- **Narzędzia instalują się warunkowo.** Krok sondujący sprawdza, czego brakuje;
  instalacja i cache odpalają się tylko przy braku. Świeży runner nadal działa bez
  ręcznego przygotowania, a trwały nie wywołuje `sudo apt-get` przy każdym przebiegu.

- **Godot i Blender leżą POZA workspace** (`runner.tool_cache`), bo w workspace kasował
  je `git clean -ffdx` z checkoutu przy każdym przebiegu.

- **Blender jest przypięty po wersji, nie brany z apt.** Od 03.09.2026, i ten punkt jest
  przepisany, a nie dopisany obok: poprzednia wersja mówiła, że sonda sprawdza
  `command -v blender`, i to już nieprawda. `apt` na Ubuntu 24.04 daje 4.0.2 do końca
  życia wydania, a 4.0.2 renderuje **legacy EEVEE**, podczas gdy baseline projektu jest
  z EEVEE Next — `enum_items` dla `engine` zwraca `['BLENDER_EEVEE']` na obu, więc nazwa
  silnika ich nie odróżnia. Sonda na obecność byłaby tu wręcz szkodliwa: na maszynie,
  która kiedykolwiek dostała Blendera z apt, uznałaby środowisko za gotowe.
  Wersja i suma SHA-256 są w `tools/ci/blender-version.txt`, instaluje
  `tools/ci/blender_install.sh`, a skrypty wołają `${BLENDER_BIN:-blender}` — tak samo
  jak `GODOT_BIN`. Z apt zostały wyłącznie biblioteki systemowe.

- **Narzędzia instalują się do `RUNNER_TOOL_CACHE`, nie do `/usr`.** Runner właściciela
  nie jest rootem, więc `actions/setup-dotnet` z domyślnym katalogiem `/usr/share/dotnet`
  pada serią `mkdir: Permission denied` — na jednorazowej maszynie GitHuba nie padał, bo
  tam runner jest rootem. `DOTNET_INSTALL_DIR` ustawiany **przed** krokiem `setup-dotnet`
  załatwia to razem z trwałością: `_tool` jest rodzeństwem workspace'u, więc `git clean`
  go nie dotyka. Ta sama zasada co dla Godota, z tego samego powodu i o jeden powód więcej.

- **Nie uznawaj `queued` za weryfikację — a zielony job mówi o SCALANCE NAZWANEJ
  W JEGO WŁASNYM LOGU, nie o dzisiejszym `main`.** Od 08.09.2026 ten punkt jest
  przepisany, a nie dopisany obok: poprzednia wersja kończyła się na „zakończony,
  zielony job i sprawdzenie wymaganych artefaktów" i nie mówiła, **co** ten job
  sprawdził — a to jest ta sama różnica, którą projekt tropi od 6.D27.
  Pierwsza połowa zostaje bez zmian: zadanie jest zweryfikowane dopiero po
  zakończonym, zielonym jobie i sprawdzeniu wymaganych artefaktów. Na jednym runnerze
  `queued` znaczy też „kolejka", nie tylko „zepsute" — ale nadal nie znaczy
  „zweryfikowane".
  Druga połowa jest nowa i wyszła z pomiaru (6.D47, `reports/ponowienie-a-ruch-bazy.md`).
  Przebieg `pull_request` liczy na **scalance** gałęzi z bazą, a `actions/checkout`
  nie dostaje w tych workflowach wejścia `ref`, więc bierze scalankę zapisaną
  w przebiegu i pobiera ją **po SHA**, nie po nazwie refa. Którą scalankę job
  naprawdę sprawdził, podaje jego log kroku `Checkout`, wierszem
  `HEAD is now at <sha> Merge <gałąź> into <baza>`. **Weryfikacją wobec dzisiejszego
  `main` jest tylko taki zielony job, w którym `<baza>` równa się dzisiejszemu
  wierzchołkowi `main`** — nie jest nią job, którego baza została w tyle, bez względu
  na to, ile ma prób i jak jest zielony. Gdy baza ruszyła: **wciągnij `main` do gałęzi
  i pchnij**. To daje nowy commit i NOWY przebieg, czyli scalankę na dzisiejszej
  bazie. Ponowienie (`re-run failed jobs`) tego nie daje: w każdym ponowieniu, jakie
  to repozytorium ma w logach, wszystkie próby pobrały **ten sam jeden SHA** scalanki,
  starszy od samego przebiegu (zmierzone na trzech próbach przebiegu 34194126232
  i dwóch przebiegu 34182392141).
  **Granica tego pomiaru stoi tu razem z nim, bo brak pomiaru nie jest jego wynikiem:**
  czy ponowienie po ruchu bazy przeliczyłoby scalankę na nowej bazie, **nie zostało
  zmierzone** — w 1919 przebiegach `pull_request` z 01–08.09.2026 (45 z więcej niż
  jedną próbą) nie ma ani jednego ponowienia, między którego próbami `main` ruszył.
  Reguła zdania wyżej tego rozstrzygnięcia nie potrzebuje: każe **przeczytać bazę
  z logu**, a nie wnioskować ją z historii przebiegu.
  **Tej połowy nie pilnuje żadna bramka i pilnować nie może** — inaczej niż reguł
  wyżej, wymienionych w ostatnim punkcie tej sekcji: `<baza>` stoi w logu przebiegu,
  a nie w repozytorium, więc nie ma czego sparsować. Jest to więc procedura czytania
  dla agenta i dla właściciela, a nie zdanie o treści workflowa.

- **Akcje są przypięte po SHA commita, nie po tagu.** `actions/checkout@v6` wskazuje na
  to, co właściciel akcji ostatnio tam przesunął; te joby chodzą na maszynie właściciela
  tego repozytorium, z dostępem do workspace'u, `runner.tool_cache` i `GITHUB_TOKEN`.
  Przy każdym SHA stoi komentarz z wersją — bez niego przypięcie jest nieczytelne i przez
  to nieaktualizowalne. Ta sama akcja ma wszędzie ten sam SHA.
- Reguły powyżej są pilnowane testami w `tools/tests/test_ci_workflows.py`; każda ma
  kontrolę negatywną wypisaną w commicie, który ją wprowadził.
