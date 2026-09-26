#!/usr/bin/env bash
# MB-04 · Paczka dla gracza: binarka, zasoby i nic poza tym.
#
# **CZEGO TEN SKRYPT NIE ROBI I DLACZEGO TO JEST WAŻNIEJSZE OD TEGO, CO ROBI.**
# Nie kopiuje `build/t400` w całości. Odruchowe `cp -r` wsadziłoby do paczki
# **924 kiB martwego balastu** (zmierzone): `L1_A.glb` (887 952 B) — monolit, którego
# scena NIE CZYTA, bo jedzie chunkami — i `godot.csv` (32 757 B), czyli plik TELEMETRII
# wytworzony przez CI. Ten drugi jest gorszy od balastu: wygląda w paczce jak zasób,
# a jest zapisem cudzego przejazdu.
#
# **Lista zasobów jest WYPISANA, a nie wzięta wzorcem.** Wzorzec `*.glb` dawałby
# monolit i obwiednię M7 razem z chunkami, a `*.json` — metryki i raporty generatorów.
# Co scena naprawdę otwiera, widać w `FirstRun.BuildWorld` (manifest, skorupa, perony)
# i w `TunnelView` (pliki LOD z manifestu); wypisanie tego tutaj jest jedynym sposobem,
# żeby paczka rosła świadomie.
#
# **Struktura paczki jest treścią, nie porządkiem:**
#
#     MetroBXL/
#       MetroBXL.x86_64            <- binarka
#       MetroBXL.pck               <- kod i scena
#       data_MetroBxl.Game_*/      <- runtime .NET (self-contained)
#       zasoby/                    <- CZYTANE PRZEZ `FirstRun.RepoPath` w paczce
#         M7_shell.glb, M7_cab.glb    <- skorupa i kabina kanoniczna (MB-05)
#         chunks/…                    (nazwa katalogu: `FirstRun.PackageAssetsDirectory`)
#         data/track/L1_A.json
#         data/design/signalling/classic-2026.json
#       CZYTAJ-TO-NAJPIERW.txt
#
# `zasoby/` leży OBOK binarki, a nie pod `res://`, bo `.glb` jest w Godocie formatem
# IMPORTOWANYM: do `.pck` trafia zaimportowana scena i `.remap`, a surowego `.glb`
# tam nie ma wcale — `FileAccess.Open("res://….glb")` w paczce zawodzi. Zmiana tego
# wymagałaby przemianowania 38 plików na rozszerzenie, którego Godot nie importuje,
# i przepisania pola `file` w manifeście chunków.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT="${1:-build/paczka}"
ZASOBY_SRC="${2:-build/t400}"
NAZWA="MetroBXL"
case "${PACZKA_SYSTEM:-linux}" in
    linux)
        PRESET="Linux"
        BINARKA="$NAZWA.x86_64"
        URUCHOMIENIE="./$BINARKA"
        ;;
    windows)
        PRESET="Windows Desktop"
        BINARKA="$NAZWA.exe"
        URUCHOMIENIE="$BINARKA"
        ;;
    *)
        echo "[PACZKA] BŁĄD: PACZKA_SYSTEM musi mieć wartość linux albo windows." >&2
        exit 2
        ;;
esac
PACZKA_SYSTEM="${PACZKA_SYSTEM:-linux}"

GODOT_EXE="${GODOT_BIN:-godot}"
if ! command -v "$GODOT_EXE" >/dev/null 2>&1 && [ ! -x "$GODOT_EXE" ]; then
    echo "[PACZKA] nie ma Godota: '$GODOT_EXE'." >&2
    echo "[PACZKA] ustaw GODOT_BIN albo zainstaluj przypiętą wersję:" >&2
    echo "[PACZKA]   bash tools/ci/godot_install.sh" >&2
    exit 3
fi

# **`dotnet` MUSI BYĆ W `PATH`, a jego brak nie daje komunikatu — daje SIGSEGV.**
# Zmierzone 14.09.2026 na tej maszynie: `Godot_v4.7.2-stable_mono` bez `dotnet` w ścieżce
# wypisuje `sh: 1: dotnet: not found`, potem `Failed to load hostfxr`, a następnie
# `handle_crash: Program crashed with signal 11` i zrzut stosu z prośbą o zgłoszenie
# błędu do projektu Godot. Kod wyjścia (134, `Aborted`) jest nieodróżnialny od awarii
# eksportu, a jedyne zdanie mówiące, o co naprawdę chodzi, stoi w ŚRODKU zrzutu.
# Sonda jest tu po to, żeby brak narzędzia kończył się nazwanym błędem, a nie prośbą
# o zgłoszenie cudzego buga. Instalator SDK kładzie `dotnet` w `$HOME/.dotnet`, którego
# nie ma w domyślnym `PATH` — dlatego sonda sama tam zagląda, zamiast tylko odmówić.
if ! command -v dotnet >/dev/null 2>&1; then
    if [ -x "$HOME/.dotnet/dotnet" ]; then
        PATH="$HOME/.dotnet:$PATH"
        export PATH
        echo "[PACZKA] dotnet spoza PATH: $HOME/.dotnet/dotnet" >&2
    else
        echo "[PACZKA] BŁĄD: nie ma 'dotnet' w PATH." >&2
        echo "[PACZKA] Godot mono bez niego NIE wypisuje błędu — wywala się z sygnałem 11." >&2
        echo "[PACZKA] wersja SDK: global.json; instalacja: https://dot.net/v1/dotnet-install.sh" >&2
        exit 7
    fi
fi

# SZABLONY EKSPORTU są potrzebne WYŁĄCZNIE tutaj — `--export-pack` obywa się bez nich,
# `--export-release` nie. Brak kończy się nazwanym błędem, a nie listą ścieżek Godota.
SZABLONY="${GODOT_TEMPLATES_DIR:-}"
if [ -z "$SZABLONY" ]; then
    SZABLONY="$(bash tools/ci/godot_templates_install.sh)" || {
        echo "[PACZKA] nie ma szablonów eksportu i nie dało się ich pobrać." >&2
        echo "[PACZKA] wersja i suma: tools/ci/godot-version.txt" >&2
        exit 5
    }
fi

if [ ! -d "$ZASOBY_SRC/chunks" ]; then
    echo "[PACZKA] brak wygenerowanych zasobów w '$ZASOBY_SRC'." >&2
    echo "[PACZKA] uruchom najpierw: bash tools/dev/prepare-playable.sh $ZASOBY_SRC" >&2
    exit 4
fi

rm -rf "$OUT"
mkdir -p "$OUT/$NAZWA/zasoby/chunks"
DOCELOWY="$OUT/$NAZWA"
ZASOBY="$DOCELOWY/zasoby"

echo "[PACZKA] eksport binarki -> $DOCELOWY/$BINARKA"
"$GODOT_EXE" --headless --path src/Game \
    --export-release "$PRESET" "$ROOT/$DOCELOWY/$BINARKA" 2>&1 | tee "$OUT/eksport.log"

# **KOD WYJŚCIA ZERA TU NIE WYSTARCZA i to jest zmierzone.** Bez `MetroBxl.Game.sln`
# eksport kończy się ZEREM, wypisując przy tym ostrzeżenie — i pakuje PEŁNE ŹRÓDŁA C#
# zamiast zaślepek: `res://FirstRun.cs` ważyło wtedy 105 023 B, a cała paczka 314 536 B
# wobec 11 608 B. Skrypt patrzący tylko na kod wyjścia oddałby graczowi cały kod
# z komentarzami i nie powiedziałby ani słowa.
if grep -q "no solution file was found" "$OUT/eksport.log"; then
    echo "[PACZKA] BŁĄD: eksport nie znalazł pliku rozwiązania i spakował ŹRÓDŁA C#." >&2
    echo "[PACZKA] ma istnieć src/Game/MetroBxl.Game.sln (MB-04)." >&2
    exit 6
fi

test -f "$DOCELOWY/$BINARKA" || {
    echo "[PACZKA] BŁĄD: eksport nie zostawił binarki." >&2; exit 6; }

echo "[PACZKA] zasoby runtime -> $ZASOBY"
cp "$ZASOBY_SRC/M7_shell.glb"        "$ZASOBY/"
cp "$ZASOBY_SRC/M7_cab.glb"          "$ZASOBY/"
cp "$ZASOBY_SRC/L1_A-platforms.glb"  "$ZASOBY/"
cp "$ZASOBY_SRC/L1_A-station-board.glb" "$ZASOBY/"
cp "$ZASOBY_SRC/L1_A-visual-tail.glb" "$ZASOBY/"
cp "$ZASOBY_SRC/L1_A-visual-tail-detail.glb" "$ZASOBY/"
cp "$ZASOBY_SRC/L1_A-visual-tail-axis.json" "$ZASOBY/"
cp "$ZASOBY_SRC/chunks/L1_A-chunks.json" "$ZASOBY/chunks/"
# Chunki i ich LOD-y — po nazwie, bo manifest wymienia je po nazwie.
cp "$ZASOBY_SRC"/chunks/L1_A_*.glb "$ZASOBY/chunks/"

python3 - "$ZASOBY_SRC/chunks/L1_A-chunks.json" "$ZASOBY_SRC/chunks" <<'PY'
import json
import os
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    chunks = json.load(handle)["chunks"]
missing = [entry["id"] + "_detail.glb" for entry in chunks
           if not os.path.isfile(os.path.join(sys.argv[2], entry["id"] + "_detail.glb"))]
if missing:
    raise SystemExit("[PACZKA] BŁĄD: brak detali dla chunków: " + ", ".join(missing))
PY
mkdir -p "$ZASOBY/data/track" "$ZASOBY/data/design/signalling"
cp data/track/L1_A.json "$ZASOBY/data/track/"
cp data/design/signalling/classic-2026.json "$ZASOBY/data/design/signalling/"

cat <<'CZYTAJ' | sed "s|@URUCHOMIENIE@|$URUCHOMIENIE|" > "$DOCELOWY/CZYTAJ-TO-NAJPIERW.txt"
METRO BXL — trening: pierwsze dwa postoje
=========================================

URUCHOMIENIE
    @URUCHOMIENIE@

    Nie trzeba podawać żadnych argumentów. Nie trzeba mieć Godota ani Blendera.
    Katalog `zasoby/` musi zostać obok binarki — gra czyta go po ścieżce liczonej
    OD SIEBIE, więc paczkę można rozpakować gdziekolwiek, także w katalogu ze
    spacjami w nazwie.

STEROWANIE
    Opisy w tej tabeli są przepisane CO DO ZNAKU z katalogu tekstów gry; pilnuje
    tego `tools/tests/test_player_package.py`, bo rozjechana tabela sterowania
    już raz w tym projekcie powstała.

    W / Z / strzałka w górę   ciąg
    S / strzałka w dół    hamulec
    X                     wybieg
    Spacja                hamulec awaryjny (= pełny służbowy)
    C                     widok — kabina albo za składem
    R                     od nowa
    Esc                   wyjście

ZADANIE
    Ruszyć z Gare de l'Ouest i zatrzymać się na DWÓCH kolejnych stacjach:
    Beekkant, potem Étangs Noirs / Zwarte Vijvers.

    Zatrzymanie liczy się, gdy czoło składu stanie w oknie ±5,0 m od punktu
    zatrzymania. Drzwi otworzą się same; do ich zamknięcia nastawnik jazdy jest
    zablokowany i HUD mówi, dlaczego pociąg nie rusza.

    Minięcie celu kończy sesję niezaliczeniem — skład nie ma biegu wstecznego.

    Po zakończeniu na ekranie staje panel wyniku: obsłużone cele, błąd zatrzymania
    na każdym, czas, droga i liczniki ochrony. `R` zaczyna od nowa.

CZEGO W TEJ PACZCE NIE MA
    Dźwięku, wiernego modelu kabiny M7, innych linii niż pakiet A, rozkładu jazdy
    i punktacji. Widoczna kabina i wystrój tunelu są projektową wizualizacją;
    wynik to fakty, nie punkty.

ZAPIS WEJŚĆ
    Każdy przejazd prowadzony z klawiatury zapisuje naciśnięcia klawiszy do pliku
    `zapisy/ostatni-przejazd.log` w katalogu użytkownika. Gra WYPISUJE tę ścieżkę
    na starcie wierszem `[ZAPISY] wejścia maszynisty -> …`, więc nie trzeba jej
    zgadywać; na Linuksie wychodzi z tego
    `~/.local/share/godot/app_userdata/METRO BXL — pierwszy przejazd/zapisy/`.
    Zapis zawiera WYŁĄCZNIE nazwy klawiszy prowadzenia i numery kroków; nie ma
    w nim ani jednej danej o Tobie.

    NAZWA JEST JEDNA I PLIK JEST NADPISYWANY przy każdym uruchomieniu. Jeśli chcesz
    zachować konkretny przejazd, skopiuj go stamtąd przed następnym startem albo
    uruchom grę z `--input-log=ŚCIEŻKA` i podaj własną nazwę.
CZYTAJ

echo "[PACZKA] rozmiar:"
du -sh "$DOCELOWY" | sed 's/^/[PACZKA]   /'
find "$ZASOBY" -type f | wc -l | sed 's/^/[PACZKA]   plików w zasobach: /'
RELEASE_COMMIT="$(git rev-parse HEAD 2>/dev/null || printf '%s' unknown)"
export RELEASE_COMMIT PACZKA_SYSTEM PRESET BINARKA DOCELOWY
python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path

root = Path(os.environ["DOCELOWY"])
files = []
for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "release-manifest.json"):
    rel = path.relative_to(root).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    files.append({"path": rel, "bytes": path.stat().st_size, "sha256": digest})
manifest = {
    "schema_version": 1,
    "git_commit": os.environ["RELEASE_COMMIT"],
    "package_system": os.environ["PACZKA_SYSTEM"],
    "godot_preset": os.environ["PRESET"],
    "executable": os.environ["BINARKA"],
    "files": files,
}
(root / "release-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
echo "[PACZKA] gotowe: $DOCELOWY/$BINARKA"
