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
BACKOFF_S=${APT_BACKOFF_S:-15}

apt_try() {
    local attempt
    for ((attempt = 1; attempt <= ATTEMPTS; attempt++)); do
        if sudo apt-get "${APT_OPTS[@]}" "$@"; then
            return 0
        fi
        echo "[APT] próba ${attempt}/${ATTEMPTS} nieudana: apt-get $*" >&2
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
apt_try update
apt_try install -y --no-install-recommends "$@"
echo "[APT] gotowe: $*"
