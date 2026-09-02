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
# Katalog cache'a pakietów. Puste = bez cache'a (tak działa lokalnie).
# Prawdziwym lekarstwem na wolne lustro nie jest czekanie, tylko NIEPOBIERANIE
# 190 MB przy każdym jobie. Cache trzyma same pliki .deb, a apt i tak sprawdza
# indeksy w lustrze i użyje pliku z cache'a tylko przy zgodnej wersji i sumie —
# nieświeży cache może więc najwyżej nie trafić, nie może podstawić złej wersji.
APT_CACHE_DIR=${APT_CACHE_DIR:-}
ARCHIVES=/var/cache/apt/archives

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

# `cp -n` wypisuje na nowszych coreutils ostrzeżenie o nieprzenośności, a w logu
# CI szum jest kosztem, nie informacją. Pętla robi to samo bez ostrzeżenia.
copy_missing() {
    local source_dir="$1" target_dir="$2" copied=0 file target
    for file in "$source_dir"/*.deb; do
        [ -e "$file" ] || continue
        target="$target_dir/$(basename "$file")"
        if [ ! -e "$target" ]; then
            sudo cp "$file" "$target"
            copied=$((copied + 1))
        fi
    done
    echo "$copied"
}

cache_restore() {
    [ -n "$APT_CACHE_DIR" ] && [ -d "$APT_CACHE_DIR" ] || return 0
    local have copied
    have=$(find "$APT_CACHE_DIR" -maxdepth 1 -name '*.deb' | wc -l)
    if [ "$have" -eq 0 ]; then
        echo "[APT] cache: katalog pusty"
        return 0
    fi
    copied=$(copy_missing "$APT_CACHE_DIR" "$ARCHIVES")
    echo "[APT] cache: przywrócono ${copied} z ${have} plików .deb"
}

cache_save() {
    [ -n "$APT_CACHE_DIR" ] || return 0
    mkdir -p "$APT_CACHE_DIR"
    sudo chown -R "$(id -u):$(id -g)" "$APT_CACHE_DIR"
    local copied
    copied=$(copy_missing "$ARCHIVES" "$APT_CACHE_DIR")
    sudo chown -R "$(id -u):$(id -g)" "$APT_CACHE_DIR"
    echo "[APT] cache: dołożono ${copied}, w cache $(find "$APT_CACHE_DIR" -maxdepth 1 -name '*.deb' | wc -l) plików .deb"
}

usage() {
    echo "użycie: $0 <pakiet> [pakiet...]  albo  $0 --set <nazwa-zestawu>" >&2
}

if [ "${1:-}" = "--set" ]; then
    # Walidacja PRZED podstawieniem: `exit` w $(...) kończy tylko podpowłokę,
    # więc skrypt szedłby dalej z pustą listą pakietów i mylącym komunikatem.
    if [ -z "${2:-}" ]; then
        usage
        exit 2
    fi
    SET_FILE="$(dirname "$0")/apt-packages/$2.txt"
    if [ ! -f "$SET_FILE" ]; then
        echo "[APT] BŁĄD: nie ma zestawu pakietów '$2' ($SET_FILE)" >&2
        exit 2
    fi
    # shellcheck disable=SC2046
    set -- $(grep -vE '^[[:space:]]*(#|$)' "$SET_FILE")
    if [ "$#" -eq 0 ]; then
        echo "[APT] BŁĄD: zestaw '$SET_FILE' nie zawiera ani jednego pakietu" >&2
        exit 2
    fi
fi

if [ "$#" -eq 0 ]; then
    usage
    exit 2
fi

echo "[APT] instaluję: $*"
cache_restore
apt_update
apt_run "$INSTALL_TIMEOUT_S" install -y --no-install-recommends "$@"
cache_save
echo "[APT] gotowe: $*"
