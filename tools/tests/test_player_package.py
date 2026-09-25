#!/usr/bin/env python3
"""Paczka dla gracza mówi o grze PRAWDĘ — sterowanie, zasoby i miejsce zapisu.

MB-04, 14.09.2026. Pozycja dokłada do repozytorium `tools/release/package-playable.sh`,
a w nim **drugi w tym projekcie egzemplarz tabeli sterowania** — pierwszym jest
`DriverActions.All`, jedyny, który naprawdę decyduje, co robi klawisz.

**Dlaczego to nie jest przesadna ostrożność, tylko zmierzona rodzina usterek.** Przy
MB-01 dokładnie taka druga kopia stała w `tools/dev/play.sh` („Spacja hamulec · R
reset") i **już była rozjechana** z katalogiem: `input.emergency` brzmi
„hamulec awaryjny (= pełny służbowy)", a `input.reset` — „od nowa". Kopia została wtedy
usunięta, bo nikt jej nie potrzebował. Tutaj usunąć się jej NIE DA: `CZYTAJ-TO-NAJPIERW.txt`
jest jedyną rzeczą, którą gracz dostaje razem z binarką, a binarka nie umie wypisać
sobie README przed własnym zbudowaniem. Skoro kopia musi zostać, musi ją ktoś pilnować.

Ta bramka NIE pyta o styl ani o kompletność opisu — pyta o trzy rzeczy, których
rozjazd jest KŁAMSTWEM wobec gracza:

1. **Klawisze.** Każde wiązanie z `DriverActions.All` ma w README swoją nazwę klawisza
   i swój opis z `UiText`.
2. **Zasoby.** Katalog, do którego skrypt kopiuje zasoby, jest tym samym, którego
   szuka scena (`FirstRun.PackageAssetsDirectory`) — dwie kopie tej nazwy rozjechałyby
   się cicho, a gra szukałaby zasobów tam, gdzie ich nie ma.
3. **Miejsce zapisu.** README nie obiecuje zapisu, którego kod nie robi. To też jest
   zmierzone przy MB-04: pierwsza wersja README głosiła, że „gra zapisuje naciśnięcia
   klawiszy do katalogu użytkownika", podczas gdy `_recorder` powstawał WYŁĄCZNIE przy
   jawnym `--input-log` — czyli paczka obiecywała rzecz, której nie robiła.
"""
import json
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
import assertion_gate

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SKRYPT = os.path.join(ROOT, "tools", "release", "package-playable.sh")
DRIVER_ACTIONS = os.path.join(ROOT, "src", "Game", "Input", "DriverActions.cs")
UI_TEXT = os.path.join(ROOT, "src", "Game", "UI", "UiText.cs")
FIRST_RUN = os.path.join(ROOT, "src", "Game", "FirstRun.cs")


def _czytaj(sciezka):
    with open(sciezka, encoding="utf-8") as uchwyt:
        return uchwyt.read()


def _wymagaj(warunek, komunikat):
    if not warunek:
        raise AssertionError(komunikat)


def readme_z_skryptu(tekst=None):
    """Treść heredoku `CZYTAJ`, czyli DOKŁADNIE to, co dostaje gracz.

    Wycinamy heredok, a nie cały skrypt, i to jest treść, a nie oszczędność: komentarz
    skryptu wymienia te same nazwy plików i katalogów co README, więc bramka czytająca
    cały plik świeciłaby na zgodność KOMENTARZA z kodem — a gracz komentarza nie widzi.
    """
    tekst = _czytaj(SKRYPT) if tekst is None else tekst
    dopasowanie = re.search(r"<<'CZYTAJ'[^\n]*\n(.*?)\nCZYTAJ\n", tekst, re.DOTALL)
    return dopasowanie.group(1) if dopasowanie else None


def katalog_slownika(tekst=None):
    """Wartość `UiText` dla klucza — słownik `input.*` z katalogu tekstów."""
    tekst = _czytaj(UI_TEXT) if tekst is None else tekst
    return dict(re.findall(r'\["(input\.[a-z.]+)"\]\s*=\s*"([^"]*)"', tekst))


KEY_NAMES = os.path.join(ROOT, "src", "Game", "Input", "KeyNames.cs")


def nazwy_klawiszy(tekst=None, katalog=None):
    """Mapa `Key.X -> napis`, którą gra POKAZUJE człowiekowi (`KeyNames.Nazwy`).

    Bez niej bramka nazywałaby klawisz wyjścia „Escape", a gra pisze „Esc" — czyli
    zapaliłaby się na zgodnym README. Napisy bywają tu stałą albo wołaniem `UiText`
    (Spacja), więc bierzemy oba warianty.
    """
    tekst = _czytaj(KEY_NAMES) if tekst is None else tekst
    katalog = katalog_slownika() if katalog is None else katalog
    wynik = {}
    for klucz, wprost, przez_katalog in re.findall(
        r'\[Key\.(\w+)\]\s*=\s*(?:"([^"]*)"|UiText\.Get\("([^"]+)"\))', tekst):
        wynik[klucz] = wprost or katalog.get(przez_katalog, przez_katalog)
    return wynik


def wiazania(tekst=None, katalog=None, nazwy=None):
    """Lista `(napis klawisza, opis)` z `DriverActions.All`.

    **Napis klawisza wyprowadzamy z KODU KLAWISZA, a nie z literału obok.** To jest
    wybór, nie wygoda: literał w `DriverBinding` jest tym, co gra WYPISUJE, a
    `(int)Key.…` tym, co gra CZYTA — i to drugie rozstrzyga, co się stanie po
    naciśnięciu. Bramka porównująca README z literałem przepuściłaby wiersz, w którym
    gra pisze „X", czyta `Key.Z`, a README posłusznie powtarza „X" za literałem.
    Dwa wiązania nie mają literału wcale (`EmergencyBrake.KeyName`,
    `KeyNames.For(Key.Escape)`), więc wzorzec na literał i tak by ich nie zobaczył.
    """
    tekst = _czytaj(DRIVER_ACTIONS) if tekst is None else tekst
    katalog = katalog_slownika() if katalog is None else katalog
    nazwy = nazwy_klawiszy(katalog=katalog) if nazwy is None else nazwy

    ogon = tekst[tekst.index("All = new[]"):] if "All = new[]" in tekst else tekst
    wynik = []
    for blok in ogon.split("new DriverBinding(")[1:]:
        blok = blok[:blok.index("}")] if "}" in blok else blok
        opis = re.search(r'UiText\.Get\("(input\.[a-z.]+)"\)', blok)
        kod = re.search(r"\(int\)Key\.(\w+)", blok)
        if opis is None or kod is None:
            continue
        wynik.append((nazwy.get(kod.group(1), kod.group(1)),
                      katalog.get(opis.group(1), opis.group(1))))
    return wynik


def test_kazdy_klawisz_z_DriverActions_stoi_w_README_paczki():
    readme = readme_z_skryptu()
    assert readme is not None, f"w {SKRYPT} nie ma heredoku CZYTAJ — README gracza zniknęło"

    pary = wiazania()
    assert len(pary) >= 7, (
        f"z DriverActions.All wyszło tylko {len(pary)} wiązań — wzorzec przestał pasować "
        "i bramka sprawdzałaby mniej, niż mówi jej nazwa"
    )

    for klawisz, opis in pary:
        assert opis in readme, (
            f"README paczki nie mówi, co robi klawisz {klawisz}: brakuje opisu „{opis}” "
            f"z UiText. Tabela sterowania w {os.path.relpath(SKRYPT, ROOT)} rozjechała się "
            "z DriverActions.All — gracz dostaje wtedy opis klawisza, którego gra nie ma."
        )


def test_README_nie_nazywa_klawisza_INACZEJ_niz_gra():
    """Opis się zgadza, a litera nie — to rozjazd, którego test wyżej NIE łapie.

    Pytanie jest inne niż wyżej i dlatego jest osobne: tamten sprawdza, czy README
    wspomina o DZIAŁANIU, ten — czy litera obok tego działania jest tą, którą gra
    naprawdę czyta. Zamiana `X` na `Z` przy „wybieg" przechodzi pierwszy test w całości.
    """
    readme = readme_z_skryptu()
    for klawisz, opis in wiazania():
        wiersz = [w for w in readme.splitlines() if opis in w]
        assert wiersz, f"brak wiersza z opisem „{opis}”"
        assert any(re.search(rf"(?<![\w]){re.escape(klawisz)}(?![\w])", w) for w in wiersz), (
            f"README opisuje „{opis}”, ale w tym wierszu nie stoi klawisz {klawisz}: "
            f"{wiersz!r}. Gra czyta {klawisz} — gracz naciśnie to, co przeczytał."
        )


def test_katalog_zasobow_ma_JEDNA_nazwe_po_obu_stronach():
    """Skrypt kopiuje tam, gdzie scena szuka.

    Rozjazd tej nazwy nie wywala ani eksportu, ani budowy — wychodzi dopiero przy
    uruchomieniu paczki, komunikatem `[ASSETS] brak manifestu`, u gracza.
    """
    first_run = _czytaj(FIRST_RUN)
    dopasowanie = re.search(
        r'PackageAssetsDirectory\s*=\s*"([^"]+)"', first_run)
    assert dopasowanie, "w FirstRun.cs nie ma stałej PackageAssetsDirectory"
    katalog = dopasowanie.group(1)

    skrypt = _czytaj(SKRYPT)
    assert re.search(rf'ZASOBY="\$DOCELOWY/{re.escape(katalog)}"', skrypt), (
        f"scena szuka zasobów w „{katalog}”, a skrypt pakujący kopiuje je gdzie indziej"
    )
    assert re.search(rf'mkdir -p "\$OUT/\$NAZWA/{re.escape(katalog)}/', skrypt), (
        f"skrypt nie zakłada katalogu „{katalog}”, którego scena szuka"
    )


def test_README_nie_obiecuje_zapisu_ktorego_kod_nie_robi():
    """README mówi o zapisie wejść — więc kod musi go robić BEZ pytania o argument.

    Zmierzone przy MB-04: README powstało pierwsze i głosiło zapis do katalogu
    użytkownika, a `_recorder` powstawał wyłącznie przy jawnym `--input-log`. Obietnica
    była nieprawdą przez dokładnie tyle czasu, ile trwało jej sprawdzenie.
    """
    readme = readme_z_skryptu()
    if "ZAPIS WEJŚĆ" not in readme:
        return

    first_run = _czytaj(FIRST_RUN)
    assert "DomyslnyZapisWejsc" in first_run, (
        "README paczki obiecuje zapis wejść bez podawania argumentu, a FirstRun nie ma "
        "domyślnej ścieżki zapisu — obietnica jest nieprawdziwa"
    )
    assert re.search(
        r"_inputLogPath\s*=\s*plan\.InputLogPath\s*\?\?\s*DomyslnyZapisWejsc\(", first_run), (
        "DomyslnyZapisWejsc istnieje, ale nie jest wpięte w ustalanie _inputLogPath"
    )
    assert 'const string katalog = "user://' in first_run, (
        "domyślny zapis nie idzie do user:// — README obiecuje katalog użytkownika"
    )


def test_skrypt_NIE_kopiuje_calego_katalogu_wyjsciowego():
    """`cp -r build/t400` wsadziłoby do paczki telemetrię CI i monolit, którego nikt nie czyta.

    To jest jedyna asercja tej bramki pilnująca czegoś, co NIE jest napisem — i stoi tu,
    bo przy pierwszym odruchu „przecież łatwiej skopiować cały katalog" nikt nie zobaczy
    `godot.csv` w paczce gracza.
    """
    skrypt = _czytaj(SKRYPT)
    assert not re.search(r"cp\s+-[a-zA-Z]*r[a-zA-Z]*\s+\"?\$ZASOBY_SRC\"?(/\*)?\s", skrypt), (
        "skrypt kopiuje CAŁY katalog wyjściowy generatorów; do paczki wchodzi wtedy "
        "godot.csv (telemetria CI) i monolit L1_A.glb, którego scena nie czyta"
    )


def test_paczka_windows_ma_osobny_preset_i_instrukcje_startu():
    """Paczka ma plik EXE i instrukcję dla gracza po przejściu całego skryptu."""
    if os.name == "nt":
        assertion_gate.skip("test eksportu ze stubem wymaga ścieżek powłoki Linux")

    with tempfile.TemporaryDirectory() as temp:
        src = os.path.join(temp, "zasoby")
        os.makedirs(os.path.join(src, "chunks"))
        for nazwa in ("M7_shell.glb", "M7_cab.glb", "L1_A-platforms.glb",
                      "L1_A-station-board.glb", "L1_A-visual-tail.glb",
                      "L1_A-visual-tail-detail.glb", "L1_A-visual-tail-axis.json"):
            open(os.path.join(src, nazwa), "wb").close()
        for nazwa in ("L1_A_000.glb", "L1_A_000_detail.glb"):
            open(os.path.join(src, "chunks", nazwa), "wb").close()
        with open(os.path.join(src, "chunks", "L1_A-chunks.json"), "w",
                  encoding="utf-8") as uchwyt:
            json.dump({"chunks": [{"id": "L1_A_000"}]}, uchwyt)

        bin_dir = os.path.join(temp, "bin")
        os.makedirs(bin_dir)
        with open(os.path.join(bin_dir, "dotnet"), "w", encoding="utf-8") as uchwyt:
            uchwyt.write("#!/bin/sh\nexit 0\n")
        godot = os.path.join(bin_dir, "godot")
        with open(godot, "w", encoding="utf-8") as uchwyt:
            uchwyt.write('#!/bin/sh\nprintf "%s\\n" "$@" > "$GODOT_ARGS"\n'
                         'for ostatni; do :; done\nprintf "MZ" > "$ostatni"\n')
        os.chmod(godot, 0o755)
        os.chmod(os.path.join(bin_dir, "dotnet"), 0o755)

        args = os.path.join(temp, "godot-args.txt")
        bazowe_env = dict(os.environ, GODOT_BIN=godot, GODOT_TEMPLATES_DIR=temp,
                          GODOT_ARGS=args, PATH=bin_dir + os.pathsep + os.environ["PATH"])
        for system, plik, preset in ((None, "MetroBXL.x86_64", "Linux"),
                                     ("windows", "MetroBXL.exe", "Windows Desktop")):
            out = os.path.join("build", "test-paczka-" + uuid.uuid4().hex)
            env = dict(bazowe_env)
            env.pop("PACZKA_SYSTEM", None)
            if system is not None:
                env["PACZKA_SYSTEM"] = system
            try:
                wynik = subprocess.run(["bash", SKRYPT, out, src], cwd=ROOT, env=env,
                                       capture_output=True, text=True, timeout=30)
                assert wynik.returncode == 0, wynik.stdout + wynik.stderr
                paczka = os.path.join(ROOT, out, "MetroBXL")
                assert os.path.isfile(os.path.join(paczka, plik)), (
                    f"paczka {system or 'linux'} nie zawiera pliku {plik}")
                manifest_path = os.path.join(paczka, "release-manifest.json")
                assert os.path.isfile(manifest_path), "paczka nie zawiera release-manifest.json"
                with open(manifest_path, encoding="utf-8") as uchwyt:
                    manifest = json.load(uchwyt)
                _wymagaj(manifest["schema_version"] == 1, "nieznana wersja manifestu")
                _wymagaj(manifest["package_system"] == (system or "linux"), "zły system w manifeście")
                _wymagaj(manifest["godot_preset"] == preset, "zły preset w manifeście")
                _wymagaj(manifest["executable"] == plik, "zła binarka w manifeście")
                wpisy = {w["path"]: w for w in manifest["files"]}
                _wymagaj("release-manifest.json" not in wpisy, "manifest opisuje sam siebie")
                rzeczywiste = {
                    sciezka.relative_to(Path(paczka)).as_posix(): str(sciezka)
                    for sciezka in Path(paczka).rglob("*")
                    if sciezka.is_file() and sciezka.name != "release-manifest.json"
                }
                _wymagaj(set(wpisy) == set(rzeczywiste), "manifest nie opisuje dokładnie zawartości paczki")
                for sciezka, wpis in wpisy.items():
                    dane = open(rzeczywiste[sciezka], "rb").read()
                    _wymagaj(wpis["bytes"] == len(dane), f"zły rozmiar {sciezka}")
                    _wymagaj(wpis["sha256"] == hashlib.sha256(dane).hexdigest(), f"zły hash {sciezka}")
                assert os.path.isfile(os.path.join(paczka, "zasoby",
                                                   "L1_A-station-board.glb")), (
                    f"paczka {system or 'linux'} nie zawiera tablicy stacji")
                for tail_file in ("L1_A-visual-tail.glb", "L1_A-visual-tail-detail.glb",
                                  "L1_A-visual-tail-axis.json"):
                    assert os.path.isfile(os.path.join(paczka, "zasoby", tail_file)), (
                        f"paczka {system or 'linux'} nie zawiera {tail_file}")
                assert plik in _czytaj(os.path.join(paczka, "CZYTAJ-TO-NAJPIERW.txt")), (
                    f"README paczki {system or 'linux'} nie wskazuje pliku {plik}")
                assert preset in _czytaj(args), (
                    f"eksport {system or 'linux'} nie wybrał presetu {preset}")
            finally:
                shutil.rmtree(os.path.join(ROOT, out), ignore_errors=True)

        presety = _czytaj(os.path.join(ROOT, "src", "Game", "export_presets.cfg"))
        assert re.search(r'\[preset\.1\]\s+name="Windows Desktop"\s+platform="Windows Desktop"', presety), (
            "brak osobnego presetu Windows Desktop w konfiguracji eksportu")
        opcje_windows = presety.split("[preset.1.options]", 1)[-1]
        assert "codesign/enable=false" in opcje_windows, (
            "preset Windows wymaga podpisywania bez skonfigurowanego certyfikatu")
        assert "application/modify_resources=false" in opcje_windows, (
            "preset Windows wymaga rcedit podczas eksportu na Linuksie")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
