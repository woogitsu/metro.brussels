#!/usr/bin/env bash
# Blender z oficjalnego tarballa, w przypiętej wersji, POZA workspace.
#
# DLACZEGO NIE APT. `apt-get install blender` na Ubuntu 24.04 daje 4.0.2 i będzie
# dawać 4.0.2 do końca życia wydania — noble nie dostanie nowszego. To nie jest
# kwestia wygody: 4.0.2 renderuje LEGACY EEVEE, a projekt trzyma baseline z EEVEE
# Next. `enum_items` dla `engine` zwraca DOKŁADNIE `['BLENDER_EEVEE']` na obu
# wersjach, więc nazwa silnika nie odróżnia jednego od drugiego — rozstrzyga wersja
# Blendera (`tools/visual/capture_plan.py`, `EEVEE_NEXT_SINCE`). Bramka na to jest,
# ale bramka odmawia renderu; nie podnosi wersji.
#
# DLACZEGO POZA WORKSPACE. `actions/checkout` ma `clean` domyślnie `true`, czyli
# `git clean -ffdx`, a `-x` obejmuje pliki ignorowane. Blender rozpakowany
# w workspace znikałby przy każdym checkoucie i schodziłby z sieci raz na przebieg —
# 366 MB. Ta sama decyzja i ten sam katalog co przy Godocie
# (`.github/workflows/godot-first-run.yml`).
#
# DLACZEGO SONDA CZYTA WERSJĘ, A NIE OBECNOŚĆ. `command -v blender` mówi tylko, że
# w PATH coś jest. Na maszynie, która kiedykolwiek miała `apt-get install blender`,
# tym czymś jest 4.0.2 — sonda na obecność uznałaby środowisko za gotowe, a rendery
# wyszłyby z drugiego silnika. Sonda porównuje więc NUMER, i to numer z przypiętego
# pliku, nie wpisany tu z ręki.
#
# Wypisuje na stdout ścieżkę do pliku wykonywalnego. W CI ustaw z tego `BLENDER_BIN`.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIN="$HERE/blender-version.txt"

if [ ! -f "$PIN" ]; then
    echo "[BLENDER] BŁĄD: brak pliku z przypiętą wersją ($PIN)" >&2
    exit 2
fi

VERSION="$(sed -n 's/^version=//p' "$PIN")"
SHA256="$(sed -n 's/^sha256=//p' "$PIN")"
if [ -z "$VERSION" ] || [ -z "$SHA256" ]; then
    echo "[BLENDER] BŁĄD: $PIN nie podaje 'version=' albo 'sha256='" >&2
    exit 2
fi
SERIES="${VERSION%.*}"

# Katalog poza workspace. `RUNNER_TOOL_CACHE` to domyślna zmienna runnera i wskazuje
# rodzeństwo workspace'u; fallback na $HOME, gdyby jakiś runner jej nie ustawił.
# Wersja jest w ścieżce, więc podniesienie pinu daje nowy katalog, zamiast mieszać
# dwa Blendery w jednym.
CACHE="${RUNNER_TOOL_CACHE:-$HOME/.cache/metro-tools}"
DIR="$CACHE/metro-blender/$VERSION"
BIN="$DIR/blender-${VERSION}-linux-x64/blender"

if [ -n "${GITHUB_WORKSPACE:-}" ]; then
    case "$DIR" in
        "$GITHUB_WORKSPACE"/*)
            echo "[BLENDER] BŁĄD: katalog $DIR leży W WORKSPACE — checkout skasuje go przy następnym przebiegu" >&2
            exit 1
            ;;
    esac
fi

# Stderr OSTATNIEGO wywolania `--version`. Nie jest ozdoba diagnostyczna, tylko
# naprawa zmierzonej usterki: `2>/dev/null` w tej funkcji zamienialo TRZY rozne
# przyczyny w jeden nierozroznialny pusty napis. Zmierzone 07.09.2026 na runnerze
# `woogitsu-linux-01` (run 34153517889, job `tunnel-alignment (L1_B)`): pobranie
# udane, suma SHA-256 zgodna, a jedyne, co job powiedzial o przyczynie, to
#
#     [BLENDER] BLAD: po rozpakowaniu .../blender zglasza '', oczekiwano '5.2.1'
#
# Blender, ktory nie startuje, pisze `error while loading shared libraries: <nazwa>`
# WYLACZNIE na stderr i nic na stdout — czyli dokladnie ta jedna informacja, ktora
# jest tu potrzebna, byla wyrzucana.
# PLIK, nie zmienna. Pierwsza wersja tej poprawki trzymala stderr w zmiennej
# `BLENDER_STDERR` i NIE DZIALALA — zlapala to kontrola negatywna, nie przeglad
# kodu. Powod: `installed_version` jest wolane jako `got="$(installed_version)"`,
# czyli w PODSHELLU, a przypisanie do zmiennej w podshellu nie wychodzi do
# rodzica. Komunikat mowil wiec „startuje i nie wypisuje numeru" o Blenderze,
# ktory nie startowal wcale — czyli ta poprawka miala dokladnie te usterke,
# ktora naprawia, tylko o jeden poziom glebiej. Sciezka pliku jest ustawiona
# w rodzicu, wiec zapis z podshella zostaje.
BLENDER_STDERR_FILE="$(mktemp)"
trap 'rm -f "$BLENDER_STDERR_FILE"' EXIT

installed_version() {
    [ -x "$BIN" ] || return 1
    : > "$BLENDER_STDERR_FILE"
    "$BIN" --version 2>"$BLENDER_STDERR_FILE" | sed -n '1s/^Blender \([0-9.]*\).*/\1/p'
}

blender_stderr() {
    cat "$BLENDER_STDERR_FILE" 2>/dev/null || true
}

# Dlaczego numer wyszedl pusty. Cztery przyczyny, kazda z innym dzialaniem po
# stronie czytajacego, i zadnej nie da sie odgadnac z samego pustego napisu:
# brak pliku to zle rozpakowanie, brak `+x` to zle uprawnienia w archiwum,
# brakujace biblioteki to pakiety do doinstalowania NA MASZYNIE, a wypis bez
# numeru wersji to zmiana formatu `--version` po stronie Blendera.
#
# Lista bibliotek jest WYLICZONA przez `ldd`, nie wpisana z reki. Wpisana z reki
# musialaby byc zgadnieta, a zgadnieta lista brakow jest tym samym rodzajem
# usterki co pusty napis: wyglada jak pomiar i nim nie jest.
powod_pustej_wersji() {
    if [ ! -e "$BIN" ]; then
        echo "pliku $BIN nie ma — archiwum rozpakowalo sie inaczej, niz zaklada sciezka"
        return
    fi
    if [ ! -x "$BIN" ]; then
        echo "plik $BIN nie ma prawa wykonywania"
        return
    fi
    local brakujace
    brakujace="$(ldd "$BIN" 2>/dev/null | sed -n 's/^[[:space:]]*\([^ ]*\) => not found$/\1/p' | tr '\n' ' ')"
    if [ -n "${brakujace// /}" ]; then
        echo "Blender nie startuje, bo brakuje bibliotek systemowych: ${brakujace% }"
        return
    fi
    if [ -n "$(blender_stderr)" ]; then
        echo "Blender startuje, ale konczy sie bledem (stderr nizej)"
        return
    fi
    echo "Blender startuje i nie wypisuje numeru w formacie 'Blender <numer>'"
}

have="$(installed_version || true)"
if [ "$have" = "$VERSION" ]; then
    echo "[BLENDER] $VERSION już jest w $DIR" >&2
    echo "$BIN"
    exit 0
fi
if [ -n "$have" ]; then
    echo "[BLENDER] w $DIR stoi $have, a przypięte jest $VERSION — pobieram od nowa" >&2
fi

# TARBALL IDZIE DO KATALOGU RUNNERA, NIE DO WSPÓŁDZIELONEGO /tmp.
# Cztery runnery puli `woogitsu` stoją na JEDNEJ maszynie
# (`~/actions-runner-woogitsu-01` … `-04`), więc dzielą jedno `/tmp`. Przy stałej
# nazwie pliku dwa joby instalujące Blendera równocześnie pisały `curl -o` do tego
# samego pliku, a ten, który skończył pierwszy, kasował go drugiemu — zmierzone
# 05.09.2026 na `tunnel-alignment (L1_A)`, run 33981627757:
#
#     [BLENDER] sprawdzam sumę SHA-256
#     /tmp/blender-5.2.1-linux-x64.tar.xz: OK
#     tar (child): /tmp/blender-5.2.1-linux-x64.tar.xz: Cannot open: No such file
#
# Suma zgadza się, a chwilę później pliku nie ma. Cichszy wariant tego samego
# wyścigu jest gorszy: dwa równoległe `curl -o` do jednego pliku mogą dać tarball,
# który przechodzi `sha256sum` u jednego z nich tylko dlatego, że drugi akurat
# skończył zapis. `RUNNER_TEMP` jest per runner, więc kolizji nie ma z definicji.
TARBALL="${RUNNER_TEMP:-$(mktemp -d)}/blender-${VERSION}-linux-x64.tar.xz"
URL="https://download.blender.org/release/Blender${SERIES}/blender-${VERSION}-linux-x64.tar.xz"

echo "[BLENDER] pobieram $URL" >&2
curl -fL --retry 4 --retry-delay 3 --max-time 1800 -o "$TARBALL" "$URL"

echo "[BLENDER] sprawdzam sumę SHA-256" >&2
echo "$SHA256  $TARBALL" | sha256sum -c - >&2

rm -rf "$DIR"
mkdir -p "$DIR"
tar -xJf "$TARBALL" -C "$DIR"
rm -f "$TARBALL"

got="$(installed_version || true)"
if [ "$got" != "$VERSION" ]; then
    echo "[BLENDER] BŁĄD: po rozpakowaniu $BIN zgłasza '$got', oczekiwano '$VERSION'" >&2
    echo "[BLENDER] powód: $(powod_pustej_wersji)" >&2
    if [ -n "$(blender_stderr)" ]; then
        echo "[BLENDER] stderr Blendera: $(blender_stderr)" >&2
    fi
    exit 1
fi
"$BIN" --version | sed -n '1,2p' >&2
echo "[BLENDER] gotowe: $BIN" >&2
echo "$BIN"
