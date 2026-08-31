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
python3 tools/tests/test_all.py      # 25 testów narzędzi, muszą przechodzić
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
| `docs/TASKS.md` | lista zadań |
| `docs/TASK-TEMPLATE.md` | format nowego zadania |
| `data/network/lines.json` | dane sieci maszynowo |
| `data/network/sources.json` | maszynowy rejestr źródeł i licencji danych |

Skille w `.claude/skills/` wchodzą automatycznie: `blender-asset`, `track-data`, `sim-physics`.

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
# 3 OBEJRZYJ: renders/L1_A_iso.png, _side.png, _inside.png
# 4 OPISZ słowami, co widzisz na każdym z trzech
```

Czego szukasz:

| render | wykrywa |
|---|---|
| `_iso` | pustą scenę, geometrię zwiniętą w punkt, zły przebieg |
| `_side` | pomylone jednostki, zły profil pionowy |
| `_inside` | wywrócone normalne — widać „przez" ścianę |

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

## 9. CI / GitHub Actions

- Wszystkie workflow muszą używać **self-hosted runnera WSL2**.
- Domyślne etykiety: `[self-hosted, linux, x64]`.
- **Nie używaj** GitHub-hosted runnerów: `ubuntu-latest`, `windows-latest`, `macos-latest`.
- Projekt nie zakłada dostępnych GitHub Actions minutes.
- Preferuj narzędzia już zainstalowane na runnerze (`python3`, `dotnet`, `blender`, `godot`) zamiast `actions/setup-*`, jeśli nie jest to konieczne.
