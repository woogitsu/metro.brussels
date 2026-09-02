#!/usr/bin/env bash
# Instalacja pakietów systemowych na runnerze, odporna na zawieszone lustro apt.
#
# Powód powstania: 02.09.2026 krok "Install Blender" stanął trzy razy, na trzech
# różnych runnerach GitHuba, za każdym razem na ponad 20 minut — i to ZANIM ciało
# testu w ogóle ruszyło. Domyślny `apt-get` nie ma limitu czasu na pobranie, więc
# zerwane połączenie wisi, aż zabije je timeout joba. Z zewnątrz wygląda to
# dokładnie tak samo jak długo liczący się test, co jest najgorszym możliwym
# rodzajem awarii: nie odróżnisz zepsutej zależności od zepsutej zmiany.
#
# To NIE jest obejście czerwonego testu. Zmienia wyłącznie sposób pobrania
# zależności; nie pomija, nie wycisza i nie skraca żadnej kontroli.
set -euo pipefail

# Acquire::*::Timeout zamienia zawieszone gniazdo w błąd; Retries obsługuje
# pojedynczy nieudany plik bez powtarzania całej instalacji.
APT_OPTS=(-o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30)
ATTEMPTS=${APT_ATTEMPTS:-3}
BACKOFF_S=${APT_BACKOFF_S:-10}
# Limit na POJEDYNCZĄ próbę, nie na cały krok. Limit tylko na kroku workflow zabija
# instalację w połowie pierwszego podejścia i powtórka nigdy nie dostaje szansy —
# zmierzone na `visual-regression` 02.09.2026: krok padł po 10 min 13 s, wciąż
# w pierwszym `apt-get`. Osobny limit na próbę przerywa zawieszone pobranie i wraca
# po świeże połączenie. `update` dostaje mniej niż `install`, bo pobiera indeksy,
# a nie pakiety — dzięki temu najgorszy przypadek mieści się w budżecie kroku.
UPDATE_TIMEOUT_S=${APT_UPDATE_TIMEOUT_S:-90}
INSTALL_TIMEOUT_S=${APT_INSTALL_TIMEOUT_S:-240}

apt_try() {
    local budget_s="$1"; shift
    local attempt status
    for ((attempt = 1; attempt <= ATTEMPTS; attempt++)); do
        # `sudo timeout`, nie `timeout sudo`: sygnał ma trafić w apt-get, a nie w sudo.
        status=0
        sudo timeout --kill-after=30 "$budget_s" apt-get "${APT_OPTS[@]}" "$@" || status=$?
        if [ "$status" -eq 0 ]; then
            return 0
        fi
        if [ "$status" -eq 124 ] || [ "$status" -eq 137 ]; then
            echo "[APT] próba ${attempt}/${ATTEMPTS} przekroczyła ${budget_s} s: apt-get $*" >&2
        else
            echo "[APT] próba ${attempt}/${ATTEMPTS} nieudana (kod ${status}): apt-get $*" >&2
        fi
        sleep $((attempt * BACKOFF_S))
    done
    echo "[APT] BŁĄD: 'apt-get $*' nie powiodło się po ${ATTEMPTS} próbach" >&2
    return 1
}

if [ "$#" -eq 0 ]; then
    echo "użycie: $0 <pakiet> [pakiet...]" >&2
    exit 2
fi

echo "[APT] instaluję: $*"
apt_try "$UPDATE_TIMEOUT_S" update
apt_try "$INSTALL_TIMEOUT_S" install -y --no-install-recommends "$@"
echo "[APT] gotowe: $*"
