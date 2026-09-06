#!/usr/bin/env python3
"""Bramka wzorcowego śladu: sześć osi, przebieg rdzenia, porównanie co do bajtu.

**Po co osobne narzędzie, skoro `sha256sum -c` porównuje pliki.** Bo suma mówi
wyłącznie „różni się" — a przy śladzie o stu tysiącach wierszy zdanie „różni się"
nie pozwala zacząć szukać. `Sim.Runner compare` umie wskazać wiersz rozjazdu, ale
potrzebuje DRUGIEGO PEŁNEGO PLIKU, a pełne wzorce sześciu osi to 32,0 MiB
(zmierzone 06.09.2026) — `CLAUDE.md` §4.8 zabrania komitować plików > 10 MB.

Wzorzec jest więc **dwuczęściowy** i obie części robią co innego:

  1. **suma SHA-256 całego pliku** — WYKRYWA rozjazd, co do bajtu, bez wyjątków;
  2. **próbka co `krok_probki` wierszy**, leżąca w repozytorium — LOKALIZUJE go.

Sama próbka nie wystarcza: rozjazd między próbkami by przez nią przeszedł. Sama suma
nie wystarcza: nie ma z niej jak wyczytać, GDZIE. Dopiero para daje jedno i drugie,
mieszcząc się w repozytorium — próbka sześciu osi to rząd setek kilobajtów.

**Czego ta bramka nie umie i dlaczego to jest zapisane, a nie przemilczane.** Gdy
rozjazd wypadnie MIĘDZY dwoma wierszami próbki, narzędzie poda przedział o długości
`krok_probki`, a nie pojedynczy numer wiersza. Dokładny numer odzyskuje `compare`
na pełnym pliku — i po to workflow wystawia świeże ślady jako artefakt przy porażce.

**Wersja środowiska uruchomieniowego jest częścią wzorca, nie metadanymi.** Zmierzone
06.09.2026: drzewo commita `90a8c31`, zbudowane i uruchomione DZISIAJ, daje na osi
L5_D 56 733 wiersze — czyli tyle, co `main`, a nie 49 893 z tabeli w treści tamtego
commita. Źródło się nie zmieniło; zmieniło się środowisko uruchomieniowe. Wzorzec bez
zapisanej wersji .NET jest więc wzorcem, który po następnej podmiance środowiska
zaświeci jako regres rdzenia, którym nie będzie.

Przybita jest **rodzina** (`10.0`), nie łatka: workflow pina `dotnet-version: '10.0.x'`,
czyli łatkę i tak puszcza, a bramka żądająca zgodności co do łatki zaświeciłaby przy
pierwszej aktualizacji runtime i skłamała o powodzie.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

#: Co ile wierszy danych trafia wiersz do próbki. Kompromis, a nie liczba z gustu:
#: przy 100 próbka sześciu osi ma rząd setek kilobajtów, a przedział lokalizacji ma
#: 100 wierszy — przy 120 Hz śladu to poniżej sekundy przebiegu.
SAMPLE_STEP = 100

#: Nazwa pliku wzorca w katalogu wzorców.
MANIFEST_NAME = "manifest.json"

#: Co narzędzie zwraca, gdy nie umie odczytać wersji runtime. **Osobna wartość, nie
#: pusty napis ani komunikat błędu:** komunikat wstawiony w miejsce wersji dawał
#: „rozjazd RODZINY środowiska" — zdanie prawdziwe formalnie i mylące co do przyczyny,
#: bo prawdziwą przyczyną był brak `dotnet` w PATH. Zmierzone 06.09.2026 na własnej
#: skórze: kontrola negatywna uruchomiona bez PATH zgłosiła rodzinę
#: „nieznana ([Errno 2] …)" i wyglądała na sukces kontroli.
UNKNOWN_RUNTIME = "?"


def sha256_of(path):
    """Suma SHA-256 całego pliku, czytana blokami — ślad bywa wielomegabajtowy."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sample_lines(lines, step=SAMPLE_STEP):
    """Nagłówek plus co `step`-ty wiersz danych, licząc od pierwszego.

    Zwraca listę par (numer wiersza w pliku, treść). Numer jest 1-based i liczy
    nagłówek jako wiersz 1 — tak samo, jak liczy je `sed -n 'Np'` i każdy edytor.
    """
    if not lines:
        return []
    out = [(1, lines[0])]
    for index in range(0, len(lines) - 1, step):
        out.append((index + 2, lines[index + 1]))
    return out


def read_lines(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read().splitlines()


def runtime_version():
    """Wersja środowiska URUCHOMIENIOWEGO — najwyższy `Microsoft.NETCore.App`.

    **Nie `dotnet --version`**, bo ta podaje wersję SDK, a bajty śladu produkuje
    runtime. Na maszynie z dwoma SDK i jednym runtime pierwsza liczba potrafi się
    zmienić bez najmniejszego wpływu na wynik — a druga nie.
    """
    try:
        got = subprocess.run(["dotnet", "--list-runtimes"], capture_output=True,
                             text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return UNKNOWN_RUNTIME
    wersje = []
    for line in got.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "Microsoft.NETCore.App":
            wersje.append(parts[1])
    if not wersje:
        return UNKNOWN_RUNTIME

    def klucz(v):
        return [int(x) if x.isdigit() else -1 for x in v.split("-")[0].split(".")]

    return max(wersje, key=klucz)


def family(version):
    """`10.0.4` -> `10.0`. Rodzina jest tym, co wolno przybić; łatka nie.

    **Dlaczego nie cała wersja.** Workflow pina `dotnet-version: '10.0.x'`, czyli
    łatkę PUSZCZA. Bramka żądająca zgodności co do łatki świeciłaby więc na czerwono
    przy pierwszej aktualizacji runtime na maszynie właściciela i mówiłaby „regres
    rdzenia" o czymś, co regresem nie jest. Rodzina łapie to, co się naprawdę
    zdarzyło (.NET 8 -> .NET 10), i nie łapie tego, czego pin i tak nie trzyma.
    """
    parts = version.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else version


def measure(path):
    lines = read_lines(path)
    return {
        "wiersze": len(lines),
        "bajty": os.path.getsize(path),
        "sha256": sha256_of(path),
    }


def localise(fresh_path, golden_path, step):
    """Pierwszy rozjazd między świeżym śladem a próbką wzorca.

    Zwraca opis po polsku albo None, gdy próbka się zgadza — a to znaczy, że rozjazd
    leży MIĘDZY wierszami próbki i trzeba po niego sięgnąć do pełnego pliku.
    """
    fresh = sample_lines(read_lines(fresh_path), step)
    golden = read_lines(golden_path)
    for position, (row, text) in enumerate(fresh):
        if position >= len(golden):
            return ("świeży ślad jest DŁUŻSZY niż wzorzec: próbka wzorca kończy się "
                    "na %d wierszach, świeża ma ich co najmniej %d (wiersz %d pliku)"
                    % (len(golden), position + 1, row))
        if text != golden[position]:
            first = max(1, row - step + 1) if position else 1
            return ("pierwszy rozjazd w przedziale wierszy %d..%d pliku; "
                    "wiersz %d próbki:\n    wzorzec: %s\n    świeży:  %s"
                    % (first, row, row, golden[position], text))
    if len(golden) > len(fresh):
        return ("świeży ślad jest KRÓTSZY niż wzorzec: próbka wzorca ma %d wierszy, "
                "świeża %d" % (len(golden), len(fresh)))
    return None


def check(golden_dir, trace_dir, runtime=None):
    """Zwraca listę problemów; pusta znaczy, że ślad zgadza się co do bajtu.

    `runtime` istnieje dla testów: bramka ma dać się sprawdzić na maszynie BEZ .NET,
    a `tools/tests/` chodzi właśnie na takiej (`doctor.sh` przepuszcza brak SDK jako
    „pomijam"). Bez tego parametru testy bramki wymagałyby narzędzia, którego bramka
    Pythona nie ma prawa wymagać.
    """
    with open(os.path.join(golden_dir, MANIFEST_NAME), encoding="utf-8") as handle:
        manifest = json.load(handle)
    step = manifest["krok_probki"]
    problems = []

    runtime = runtime_version() if runtime is None else runtime
    wzorcowy = manifest["srodowisko"]["runtime"]
    uwaga = None
    if runtime == UNKNOWN_RUNTIME:
        problems.append(
            "nie umiem odczytać wersji runtime .NET (`dotnet --list-runtimes`) — "
            "to NIE jest rozjazd śladu, to brak narzędzia. Wzorzec powstał na %s."
            % wzorcowy)
    elif family(runtime) != family(wzorcowy):
        problems.append(
            "runtime .NET to %s (rodzina %s), a wzorzec powstał na %s (rodzina %s) — "
            "rozjazd śladu po zmianie RODZINY środowiska NIE jest regresem rdzenia "
            "i bramka nie ma prawa udawać, że jest. Przelicz wzorzec (--update) "
            "w commicie, który zmienia wersję, i opisz to w jego treści."
            % (runtime, family(runtime), wzorcowy, family(wzorcowy)))
    elif runtime != wzorcowy:
        # Sama różnica łatki NIE jest problemem — pin `10.0.x` jej nie trzyma.
        # Ale gdy ślad SIĘ rozjedzie, to jest pierwsza rzecz, o której trzeba
        # wiedzieć, zamiast szukać w rdzeniu zmiany, której tam nie ma. Dlatego
        # uwaga dopisuje się do listy problemów TYLKO wtedy, gdy lista jest niepusta.
        uwaga = ("uwaga: runtime %s, wzorzec liczony na %s — ta sama rodzina, inna "
                 "łatka" % (runtime, wzorcowy))

    for axis, expected in sorted(manifest["osie"].items()):
        fresh = os.path.join(trace_dir, axis + ".csv")
        if not os.path.isfile(fresh):
            problems.append("%s: brak świeżego śladu %s" % (axis, fresh))
            continue
        got = measure(fresh)
        if got["sha256"] == expected["sha256"]:
            continue
        where = localise(fresh, os.path.join(golden_dir, axis + ".csv"), step)
        if where is None:
            where = ("próbka co %d wierszy się zgadza, więc rozjazd leży MIĘDZY jej "
                     "wierszami — dokładny numer da `Sim.Runner compare` na pełnym "
                     "pliku wystawionym przez workflow jako artefakt" % step)
        problems.append(
            "%s: ślad rozjechał się z wzorcem\n  wzorzec: %d wierszy, %d bajtów, %s\n"
            "  świeży:  %d wierszy, %d bajtów, %s\n  %s"
            % (axis, expected["wiersze"], expected["bajty"], expected["sha256"][:16],
               got["wiersze"], got["bajty"], got["sha256"][:16], where))
    if problems and uwaga:
        problems.append(uwaga)
    return problems


def update(golden_dir, trace_dir, axes, przebieg):
    os.makedirs(golden_dir, exist_ok=True)
    osie = {}
    for axis in axes:
        fresh = os.path.join(trace_dir, axis + ".csv")
        osie[axis] = measure(fresh)
        sample = sample_lines(read_lines(fresh))
        osie[axis]["wiersze_probki"] = len(sample)
        with open(os.path.join(golden_dir, axis + ".csv"), "w", encoding="utf-8") as out:
            out.write("\n".join(text for _, text in sample) + "\n")
    manifest = {
        "opis": ("Wzorzec śladu przejazdu liniowego. Suma SHA-256 wykrywa rozjazd, "
                 "próbka co krok_probki wierszy go lokalizuje. Pełne ślady mają "
                 "32,0 MiB i do repozytorium nie wchodzą (CLAUDE.md §4.8)."),
        "przebieg": przebieg,
        "srodowisko": {"runtime": runtime_version()},
        "krok_probki": SAMPLE_STEP,
        "osie": osie,
    }
    with open(os.path.join(golden_dir, MANIFEST_NAME), "w", encoding="utf-8") as out:
        json.dump(manifest, out, ensure_ascii=False, indent=2, sort_keys=True)
        out.write("\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--golden", default="tests/data/golden-trace")
    parser.add_argument("--traces", default="build/trace")
    parser.add_argument("--update", action="store_true",
                        help="przelicz wzorzec ze świeżych śladów zamiast go sprawdzać")
    parser.add_argument("--axes", default="L1_A,L1_B,L2_E,L5_C,L5_D,L6_F")
    parser.add_argument("--limit-kmh", default="72")
    parser.add_argument("--exchange-s", default="20")
    args = parser.parse_args(argv)

    if args.update:
        manifest = update(args.golden, args.traces, args.axes.split(","),
                          {"limit_kmh": args.limit_kmh, "exchange_s": args.exchange_s})
        total = sum(o["wiersze"] for o in manifest["osie"].values())
        print("wzorzec przeliczony: %d osi, %d wierszy razem, .NET %s"
              % (len(manifest["osie"]), total, manifest["srodowisko"]["runtime"]))
        return 0

    problems = check(args.golden, args.traces)
    if problems:
        print("[SLAD] ROZJAZD z wzorcem:", file=sys.stderr)
        for problem in problems:
            print("  " + problem, file=sys.stderr)
        return 1
    print("[SLAD] sześć osi zgadza się z wzorcem co do bajtu")
    return 0


if __name__ == "__main__":
    sys.exit(main())
