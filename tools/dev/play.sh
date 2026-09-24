#!/usr/bin/env bash
# MB-01 · Jedna komenda, która otwiera grywalny trening.
#
# **PO CO.** Punkt 1 odbioru M1 (`docs/PLAYABILITY.md` §3) brzmi: „gracz uruchamia
# właściwy tryb BEZ WPISYWANIA ARGUMENTÓW". Do 13.09.2026 trening uruchamiało się
# poleceniem z trzema ścieżkami bezwzględnymi, z których jedna (`--signalling`)
# decydowała o tym, czy ATP w ogóle działa — a jej pominięcie dawało scenę, która
# wygląda tak samo i nie chroni.
#
# **Tryb ręczny jest trybem DOMYŚLNYM** (`src/Game/RunPlan.cs`), więc ten skrypt nie
# dokłada żadnej flagi trybu. Dokłada dwie rzeczy, których brak jest niewidoczny:
# plan sygnalizacji (ATP) i zapis wejść (bez niego przejazdu nie da się odtworzyć,
# a punkt 6 odbioru M1 tego żąda).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Godot jest przypięty po wersji i leży POZA workspace, tak samo jak Blender.
GODOT_EXE="${GODOT_BIN:-godot}"
ASSETS="${ASSETS_DIR:-$ROOT/build/t400}"
PLAN="$ROOT/data/design/signalling/classic-2026.json"
# ZAPIS WEJŚĆ IDZIE DO KATALOGU UŻYTKOWNIKA, nie obok zasobów (MB-04, 14.09.2026).
# Ten wiersz jest przepisany, a nie dopisany obok: do 14.09.2026 log lądował
# w `$ASSETS`, czyli w paczce dla gracza — w katalogu binarki. Na Windowsie w
# `Program Files` zapis by po prostu padł, a `FirstRun.WriteInputLog` nie ma dokąd
# się cofnąć. `user://` jest jedyną ścieżką, która w paczce ZAWSZE jest zapisywalna
# i została zmierzona jako poprawna także z `.pck`
# (`/root/.local/share/godot/app_userdata/<nazwa>/`).
#
# W checkoucie ta zmienna nadal wskazuje `build/`, bo tu nikt nie szuka logów
# w katalogu użytkownika, a `build/` i tak nie idzie do gita (reguła 8).
INPUT_LOG="${INPUT_LOG:-$ROOT/build/t400/playtest-input.log}"

if ! command -v "$GODOT_EXE" >/dev/null 2>&1 && [ ! -x "$GODOT_EXE" ]; then
    echo "[TRENING] nie ma Godota: '$GODOT_EXE'." >&2
    echo "[TRENING] ustaw GODOT_BIN albo zainstaluj przypiętą wersję:" >&2
    echo "[TRENING]   bash tools/ci/godot_install.sh" >&2
    echo "[TRENING] wersja: docs/23-environment.md" >&2
    exit 3
fi

# **Nazwany błąd zamiast pustej sceny** — punkt 7 odbioru M1. Bez tej kontroli brak
# zasobów kończył się sceną, w której nie ma tunelu, i wyglądało to jak usterka
# renderera, a nie jak nieuruchomione przygotowanie.
BRAKI=()
for plik in \
    "$ASSETS/chunks/L1_A-chunks.json" \
    "$ASSETS/M7_shell.glb" \
    "$ASSETS/L1_A-platforms.glb"
    "$ASSETS/L1_A-station-board.glb"
do
    [ -f "$plik" ] || BRAKI+=("$plik")
done
[ -f "$PLAN" ] || BRAKI+=("$PLAN")

if [ "${#BRAKI[@]}" -gt 0 ]; then
    echo "[TRENING] brakuje zasobów, których scena nie zbuduje sama:" >&2
    for plik in "${BRAKI[@]}"; do echo "[TRENING]   $plik" >&2; done
    echo "[TRENING] uruchom najpierw: bash tools/dev/prepare-playable.sh" >&2
    exit 4
fi

echo "[TRENING] zasoby: $ASSETS"
echo "[TRENING] ATP: $(basename "$PLAN")"
echo "[TRENING] zapis wejść: $INPUT_LOG"

# **WIERSZA ZE STEROWANIEM TU NIE MA I TO JEST WYBÓR** (poprawione 13.09.2026, jeszcze
# w MB-01, po przeglądzie własnej zmiany). Pierwsza wersja tego skryptu wypisywała
# „Spacja hamulec · R reset" — i była już rozjechana z grą w chwili, w której powstała:
# `src/Game/UI/UiText.cs:114` nazywa spację „hamulec awaryjny (= pełny służbowy)",
# a `R` — „od nowa", nie „reset". Katalog `UiText` istnieje dokładnie po to, żeby napisy
# interfejsu miały JEDNO miejsce (6.D83), a HUD pokazuje z niego wiersz sterowania, gdy
# przy sterowaniu siedzi człowiek (`src/Game/UI/Hud.cs`). Druga kopia w powłoce nie ma
# ani jednej bramki nad sobą i rozjeżdżałaby się dalej, po cichu.

exec "$GODOT_EXE" --path src/Game -- \
    --assets="$ASSETS" \
    --signalling="$PLAN" \
    --input-log="$INPUT_LOG"
