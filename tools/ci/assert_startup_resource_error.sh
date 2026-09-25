#!/usr/bin/env bash
# Run the same missing-assets startup in a console and on an invisible Xvfb screen.
# A GUI build launched by double-click has no console: it must wait for the player
# to acknowledge the error. Headless automation must still exit with code 4.
set -euo pipefail

GODOT="${GODOT_BIN:?set GODOT_BIN to the pinned Godot mono binary}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

set +e
"$GODOT" --headless --path src/Game -- --assets="$TMP/empty" \
    >"$TMP/headless.log" 2>&1
headless_status=$?
set -e
if [ "$headless_status" -ne 4 ] || ! grep -Fq '[ASSETS] brak manifestu' "$TMP/headless.log"; then
    cat "$TMP/headless.log" >&2
    echo "[STARTUP] headless musi zgłosić brak manifestu i zakończyć się kodem 4 (otrzymano $headless_status)" >&2
    exit 1
fi

set +e
timeout 20s xvfb-run -a "$GODOT" --path src/Game -- --assets="$TMP/empty" \
    >"$TMP/gui.log" 2>&1
gui_status=$?
set -e
if [ "$gui_status" -ne 124 ] || ! grep -Fq '[ASSETS] brak manifestu' "$TMP/gui.log"; then
    cat "$TMP/gui.log" >&2
    echo "[STARTUP] okno błędu nie zatrzymało zamykania gry (status $gui_status)" >&2
    exit 1
fi

echo '[STARTUP] headless: kod 4 i nazwany zasób; ukryty ekran Xvfb: okno błędu czeka na potwierdzenie'
