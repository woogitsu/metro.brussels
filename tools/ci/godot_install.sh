#!/usr/bin/env bash
# Godot mono w przypiętej wersji, ze sprawdzoną sumą, POZA workspace.
#
# Wzorzec i powody są te same co w `tools/ci/blender_install.sh`, i to jest cała
# treść 6.D68: do 09.09.2026 Blender schodził z sieci ze sprawdzaną sumą, a Godot
# bez żadnej — na tym samym runnerze i przy tym samym modelu zagrożenia.
#
# SUMA SPRAWDZANA PRZED ROZPAKOWANIEM, nie po. Archiwum, którego nie sprawdzono,
# jest rozpakowane, zanim ktokolwiek zapyta, co w nim było; `unzip` na cudzej
# zawartości to już wykonanie decyzji, nie jej przygotowanie.
#
# Wypisuje na stdout ścieżkę do pliku wykonywalnego. W CI ustaw z tego `GODOT_BIN`.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIN="$HERE/godot-version.txt"

if [ ! -f "$PIN" ]; then
    echo "[GODOT] BŁĄD: brak pliku z przypiętą wersją ($PIN)" >&2
    exit 2
fi

VERSION="$(sed -n 's/^version=//p' "$PIN")"
SHA512="$(sed -n 's/^sha512=//p' "$PIN")"
# Tag wydania ma MYŚLNIK (`4.7.2-stable`) i tak nazywa się plik do pobrania, a sam
# silnik melduje KROPKĘ (`4.7.2.stable.mono.official.…`). Zmierzone 09.09.2026:
# pierwsza wersja tego skryptu porównywała jedno z drugim i odmawiała instalacji,
# której suma SHA-512 przed chwilą przeszła — czyli myliła „archiwum jest nie to"
# z „nazwa kanału pisze się inaczej po obu stronach".
VERSION_REPORTED="${VERSION//-/.}"
if [ -z "$VERSION" ] || [ -z "$SHA512" ]; then
    echo "[GODOT] BŁĄD: $PIN nie podaje 'version=' albo 'sha512='" >&2
    exit 2
fi

# Katalog poza workspace — `actions/checkout` robi `git clean -ffdx`, a `-x` obejmuje
# pliki ignorowane. Wersja jest w ścieżce, więc podniesienie pinu daje nowy katalog.
CACHE="${RUNNER_TOOL_CACHE:-$HOME/.cache/metro-tools}"
DIR="$CACHE/metro-godot/$VERSION"
BIN="$DIR/Godot_v${VERSION}_mono_linux.x86_64"

if [ -n "${GITHUB_WORKSPACE:-}" ]; then
    case "$DIR" in
        "$GITHUB_WORKSPACE"/*)
            echo "[GODOT] BŁĄD: katalog $DIR leży W WORKSPACE — checkout skasuje go przy następnym przebiegu" >&2
            exit 1
            ;;
    esac
fi

# Stderr ostatniego `--version` idzie do PLIKU, nie do zmiennej: `installed_version`
# wołane jest w podshellu, a przypisanie do zmiennej w podshellu nie wychodzi do
# rodzica. Ta sama poprawka i ten sam powód co w instalatorze Blendera.
GODOT_STDERR_FILE="$(mktemp)"
trap 'rm -f "$GODOT_STDERR_FILE"' EXIT

installed_version() {
    [ -x "$BIN" ] || return 1
    : > "$GODOT_STDERR_FILE"
    "$BIN" --headless --version 2>"$GODOT_STDERR_FILE" | sed -n '1s/^\([0-9][0-9.]*\.\(stable\|beta\|rc\)[0-9]*\)\..*/\1/p'
}

godot_stderr() {
    cat "$GODOT_STDERR_FILE" 2>/dev/null || true
}

powod_pustej_wersji() {
    if [ ! -e "$BIN" ]; then
        echo "pliku $BIN nie ma — archiwum rozpakowało się inaczej, niż zakłada ścieżka"
        return
    fi
    if [ ! -x "$BIN" ]; then
        echo "plik $BIN nie ma prawa wykonywania"
        return
    fi
    local brakujace
    brakujace="$(ldd "$BIN" 2>/dev/null | sed -n 's/^[[:space:]]*\([^ ]*\) => not found$/\1/p' | tr '\n' ' ')"
    if [ -n "${brakujace// /}" ]; then
        echo "Godot nie startuje, bo brakuje bibliotek systemowych: ${brakujace% }"
        return
    fi
    if [ -n "$(godot_stderr)" ]; then
        echo "Godot startuje, ale kończy się błędem (stderr niżej)"
        return
    fi
    echo "Godot startuje i nie wypisuje numeru w formacie '<wersja>.stable.mono…'"
}

have="$(installed_version || true)"
if [ "$have" = "$VERSION_REPORTED" ]; then
    echo "[GODOT] $VERSION już jest w $DIR" >&2
    echo "$BIN"
    exit 0
fi
if [ -n "$have" ]; then
    echo "[GODOT] w $DIR stoi $have, a przypięte jest $VERSION — pobieram od nowa" >&2
fi

# Archiwum do katalogu RUNNERA, nie do współdzielonego `/tmp` — runnery jednej puli
# stoją na jednej maszynie i dzielą `/tmp`, a przy stałej nazwie dwa joby pobierające
# równocześnie kasują sobie plik nawzajem. Ta sama zmierzona usterka co przy Blenderze.
ZIP="${RUNNER_TEMP:-$(mktemp -d)}/Godot_v${VERSION}_mono_linux_x86_64.zip"
UNPACK="${RUNNER_TEMP:-$(dirname "$ZIP")}/godot-mono-${VERSION}"
URL="https://github.com/godotengine/godot/releases/download/${VERSION}/Godot_v${VERSION}_mono_linux_x86_64.zip"

echo "[GODOT] pobieram $URL" >&2
curl -fL --retry 4 --retry-delay 3 --max-time 1800 -o "$ZIP" "$URL"

echo "[GODOT] sprawdzam sumę SHA-512" >&2
echo "$SHA512  $ZIP" | sha512sum -c - >&2

rm -rf "$DIR" "$UNPACK"
mkdir -p "$DIR" "$UNPACK"
unzip -q "$ZIP" -d "$UNPACK"
mv "$UNPACK/Godot_v${VERSION}_mono_linux_x86_64"/* "$DIR/"
rm -rf "$ZIP" "$UNPACK"

got="$(installed_version || true)"
if [ "$got" != "$VERSION_REPORTED" ]; then
    echo "[GODOT] BŁĄD: po rozpakowaniu $BIN zgłasza '$got', oczekiwano '$VERSION_REPORTED'" >&2
    echo "[GODOT] powód: $(powod_pustej_wersji)" >&2
    if [ -n "$(godot_stderr)" ]; then
        echo "[GODOT] stderr Godota: $(godot_stderr)" >&2
    fi
    exit 1
fi
"$BIN" --headless --version >&2
echo "[GODOT] gotowe: $BIN" >&2
echo "$BIN"
