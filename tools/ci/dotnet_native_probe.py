#!/usr/bin/env python3
"""Czy trzy biblioteki natywne .NET, których szuka Godot, DAJĄ SIĘ ZAŁADOWAĆ.

Powód, dla którego to nie jest sprawdzenie obecności pliku (6.D60). Sonda
`godot .NET hostfxr` w `doctor.sh` brała się z `find "$DOTNET_ROOT/host/fxr"
-name 'libhostfxr.so'`, czyli z **nazwy pliku w katalogu**. Zmierzone 09.09.2026
przy 6.D24 (`reports/6d24-biblioteka-natywna.md` §5): przy CZTERECH z pięciu
zepsuć, po których Godot pada kodem 134 w 0,19–0,35 s, ta sonda mówiła `ok` —
`libhostfxr.so` obcięty do 200 B, `libcoreclr.so` usunięty, `libcoreclr.so`
obcięty i `libhostpolicy.so` usunięty. Plik o właściwej nazwie leżał na miejscu
albo leżał gdzie indziej, a sonda pytała tylko o nazwę.

Dlaczego ładowanie, a nie próg na rozmiarze albo nagłówku ELF. Obcięcie do 200 B
ZOSTAWIA poprawny nagłówek ELF, więc każdy próg na nagłówku przechodzi; próg na
rozmiarze trzeba by zgadnąć, a zgadnięta liczba w tym projekcie starzeje się po
cichu. `dlopen` nie ma progu do zgadnięcia: albo dynamiczny linker biblioteki
używa, albo odmawia — i to jest dokładnie ta czynność, na której wywraca się
silnik.

Zmierzone 09.09.2026 na sześciu cieniach instalacji (drzewo symlinków z jednym
plikiem zepsutym): kontrola ładuje wszystkie trzy, a każde z pięciu zepsuć daje
`brak` albo `odmowa` DOKŁADNIE na zepsutej bibliotece i na żadnej innej.
"""
import ctypes
import glob
import os
import sys

#: Trzy biblioteki wymienione w komunikacie samego silnika („Typically when the
#: `hostfxr`, `hostpolicy` or `coreclr` dynamic libraries are not present in the
#: expected locations"), z wzorcami ścieżek, pod którymi kładzie je
#: `dotnet-install.sh`. Wersja w ścieżce jest globem, bo zmienia się z każdym SDK.
BIBLIOTEKI = (
    ("hostfxr", "host/fxr/*/libhostfxr.so"),
    ("hostpolicy", "shared/Microsoft.NETCore.App/*/libhostpolicy.so"),
    ("coreclr", "shared/Microsoft.NETCore.App/*/libcoreclr.so"),
)


def stan_biblioteki(root, wzorzec):
    """`(stan, szczegol)` dla jednej biblioteki: `laduje`, `brak` albo `odmowa`."""
    trafienia = sorted(glob.glob(os.path.join(root, wzorzec)))
    if not trafienia:
        return "brak", os.path.join(root, wzorzec)
    sciezka = trafienia[-1]
    try:
        ctypes.CDLL(sciezka)
    except OSError as blad:
        return "odmowa", f"{sciezka}: {blad}"
    return "laduje", sciezka


def powod_odmowy(root):
    """Zdanie o pierwszej bibliotece, która się nie ładuje — albo `None`."""
    if not root:
        return ("nie ma z czego wziąć katalogu .NET: ani DOTNET_ROOT, ani `dotnet` "
                "w PATH")
    if not os.path.isdir(root):
        return f"katalog .NET nie istnieje: {root}"
    zle = []
    for nazwa, wzorzec in BIBLIOTEKI:
        stan, szczegol = stan_biblioteki(root, wzorzec)
        if stan != "laduje":
            zle.append(f"{nazwa}: {stan} ({szczegol})")
    if not zle:
        return None
    return "biblioteka natywna nie ładuje się — " + "; ".join(zle)


def main(argv):
    root = argv[1] if len(argv) > 1 else os.environ.get("DOTNET_ROOT", "")
    powod = powod_odmowy(root)
    if powod is None:
        print(f"trzy biblioteki natywne ładują się z {root}")
        return 0
    print(powod)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
