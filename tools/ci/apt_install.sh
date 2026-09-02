#!/usr/bin/env bash
# Instalacja pakietów systemowych na runnerze GitHuba.
#
# Co tu naprawdę boli, zmierzone 02.09.2026 w logu `first-run`:
#
#   Fetched 11.7 MB in 2s (4732 kB/s)   <- apt-get update: lustro odpowiada świetnie
#   Need to get 190 MB of archives.
#   Get:4 .../blender-data all 4.0.2 [35.9 MB]   <- 36 MB nie zeszło w 4 minuty
#
# `blender` ciągnie 162 pakiety i 190 MB. Przy ~150 kB/s, jakie lustro Azure potrafi
# dać, samo pobranie zajmuje ponad 20 minut. Trzy „zawieszenia" tego dnia (L2_E,
# blender-smoke, L1_B) wyglądały jak zerwane połączenie, ale każde robiło postęp —
# ucinał je 30-minutowy timeout joba, a nie martwe gniazdo.
#
# Wniosek: to nie jest awaria do powtórzenia, tylko budżet, który musi się zgadzać.
# Ten skrypt:
#   * daje aptowi jego własne limity na gniazdo (Acquire::*::Timeout) i powtórki
#     per plik (Acquire::Retries) — to załatwia PRAWDZIWE zerwanie połączenia;
#   * powtarza `update`, bo jest tani i bywa ubity przez blokadę dpkg;
#   * NIE powtarza `install` — 190 MB pobrane w połowie nie ma być wyrzucone przez
#     zewnętrzny limit; od pilnowania sufitu jest `timeout-minutes` na kroku.
#
# To nie jest obejście czerwonego testu: zmienia wyłącznie sposób pobrania
# zależności, nie pomija i nie wycisza żadnej kontroli.
set -euo pipefail

APT_OPTS=(-o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30)
UPDATE_ATTEMPTS=${APT_UPDATE_ATTEMPTS:-2}
UPDATE_TIMEOUT_S=${APT_UPDATE_TIMEOUT_S:-180}
BACKOFF_S=${APT_BACKOFF_S:-15}
# Sufit na `install` jest celowo szeroki: ma złapać proces, który naprawdę umarł,
# a nie wolne lustro. Węższy sufit jest w `timeout-minutes` na kroku workflow.
INSTALL_TIMEOUT_S=${APT_INSTALL_TIMEOUT_S:-1500}

apt_run() {
    local budget_s="$1"; shift
    local status=0
    # `sudo timeout`, nie `timeout sudo`: sygnał ma trafić w apt-get, a nie w sudo.
    sudo timeout --kill-after=30 "$budget_s" apt-get "${APT_OPTS[@]}" "$@" || status=$?
    if [ "$status" -eq 124 ] || [ "$status" -eq 137 ]; then
        echo "[APT] 'apt-get $*' przekroczyło ${budget_s} s" >&2
    elif [ "$status" -ne 0 ]; then
        echo "[APT] 'apt-get $*' zakończyło się kodem ${status}" >&2
    fi
    return "$status"
}

apt_update() {
    local attempt
    for ((attempt = 1; attempt <= UPDATE_ATTEMPTS; attempt++)); do
        if apt_run "$UPDATE_TIMEOUT_S" update; then
            return 0
        fi
        echo "[APT] update: próba ${attempt}/${UPDATE_ATTEMPTS} nieudana" >&2
        sleep $((attempt * BACKOFF_S))
    done
    echo "[APT] BŁĄD: 'apt-get update' nie powiodło się po ${UPDATE_ATTEMPTS} próbach" >&2
    return 1
}

if [ "$#" -eq 0 ]; then
    echo "użycie: $0 <pakiet> [pakiet...]" >&2
    exit 2
fi

echo "[APT] instaluję: $*"
apt_update
apt_run "$INSTALL_TIMEOUT_S" install -y --no-install-recommends "$@"
echo "[APT] gotowe: $*"
