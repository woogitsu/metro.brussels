#!/usr/bin/env bash
# MB-04 · Szablony eksportu Godota, przypięte po wersji i sumie wydawcy.
#
# **PO CO OSOBNY SKRYPT, SKORO `godot_install.sh` JUŻ POBIERA GODOTA.** Bo to są dwie
# różne rzeczy o dwóch różnych kosztach. Silnik jest potrzebny KAŻDEMU jobowi CI i waży
# kilkadziesiąt megabajtów; szablony są potrzebne WYŁĄCZNIE do zbudowania samodzielnej
# binarki dla gracza i ważą blisko gigabajt. Wciągnięcie ich do `godot_install.sh`
# dołożyłoby ten pobór do każdego przebiegu, który ich nie używa.
#
# **Czego szablony NIE są potrzebne — zmierzone, nie przyjęte.** `--export-pack` (sam
# `.pck`, bez binarki) działa BEZ nich: kod wyjścia 0, plik powstaje. Sprawdzone
# 14.09.2026 na projekcie sondującym. Dopiero `--export-release` odmawia i wymienia
# ścieżki, w których szablonów szukał.
#
# Wersja i suma: `tools/ci/godot-version.txt` — jedno źródło prawdy dla silnika
# i dla szablonów, bo to archiwa tego samego wydania.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLIK="$ROOT/tools/ci/godot-version.txt"

VERSION="$(sed -n 's/^version=//p' "$PLIK")"
SHA512="$(sed -n 's/^templates_sha512=//p' "$PLIK")"

if [ -z "$VERSION" ] || [ -z "$SHA512" ]; then
    echo "[SZABLONY] BŁĄD: $PLIK nie podaje 'version' albo 'templates_sha512'." >&2
    exit 1
fi

# Godot szuka szablonów pod `<katalog danych>/export_templates/<wersja>.mono`, a nie
# tam, gdzie leży binarka. Nazwa katalogu jest WERSJĄ ZGŁASZANĄ przez silnik
# (`4.7.2.stable.mono`), a nie tą z nazwy archiwum (`4.7.2-stable`) — te dwa zapisy
# różnią się i pomylenie ich daje katalog, którego eksport nie znajdzie.
KATALOG_WERSJI="$(echo "$VERSION" | tr '-' '.').mono"
DANE="${GODOT_DATA_DIR:-$HOME/.local/share/godot}"
DIR="$DANE/export_templates/$KATALOG_WERSJI"

if [ -f "$DIR/linux_release.x86_64" ]; then
    echo "[SZABLONY] już są: $DIR" >&2
    echo "$DIR"
    exit 0
fi

TPZ="${RUNNER_TEMP:-$(mktemp -d)}/Godot_v${VERSION}_mono_export_templates.tpz"
URL="https://github.com/godotengine/godot/releases/download/${VERSION}/Godot_v${VERSION}_mono_export_templates.tpz"

echo "[SZABLONY] pobieram $URL" >&2
curl -fL --retry 4 --retry-delay 3 --max-time 1800 -o "$TPZ" "$URL"

echo "[SZABLONY] sprawdzam sumę SHA-512" >&2
echo "$SHA512  $TPZ" | sha512sum -c - >&2

# `.tpz` jest zwykłym zipem z jednym katalogiem `templates/` w środku.
ROZPAK="${RUNNER_TEMP:-$(dirname "$TPZ")}/godot-templates-${VERSION}"
rm -rf "$DIR" "$ROZPAK"
mkdir -p "$DIR" "$ROZPAK"
unzip -q "$TPZ" -d "$ROZPAK"
mv "$ROZPAK/templates"/* "$DIR/"
rm -rf "$TPZ" "$ROZPAK"

if [ ! -f "$DIR/linux_release.x86_64" ]; then
    echo "[SZABLONY] BŁĄD: po rozpakowaniu brak $DIR/linux_release.x86_64" >&2
    ls -la "$DIR" >&2 || true
    exit 1
fi

echo "[SZABLONY] gotowe: $DIR" >&2
echo "$DIR"
