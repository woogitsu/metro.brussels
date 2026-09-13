#!/usr/bin/env python3
"""Bramka MB-01: przepis generacji stoi w JEDNYM miejscu, a trening ma jedną komendę.

**Skad.** Do 13.09.2026 przepis generacji zasobow pakietu A stal wylacznie w kroku
`Generate package A geometry` workflowa `godot-first-run.yml`. Czlowiek, ktory chcial
uruchomic trening u siebie, przepisywal szesc polecen z pliku YAML razem z pieciooma
jawnymi parametrami, z ktorych **zaden nie ma wartosci domyslnej** — a pierwsza
literowka dawala scene bez peronu albo perony o metr krotsze od decyzji wlasciciela
(95,0 m z T-212 wobec 94,0 m z R-007) i wygladalo to jak stan repozytorium.

**Czego ta bramka pilnuje.** Nie tego, ze skrypty istnieja — to widac golym okiem.
Tego, ze przepis **nie rozszedl sie na dwa miejsca**: gdyby wrocil do YAML-a obok
wywolania skryptu, oba dzialalyby, CI bylo zielone, a rozjazd wyszedlby dopiero wtedy,
gdy ktos zmieni jeden i nie zmieni drugiego. Rodzina 6.D27: bramka ma mierzyc to,
o czym mowi.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk  # noqa: E402

ROOT = tree_walk.ROOT

#: Skrypty MB-01. Oba maja byc WYKONYWALNE — skrypt bez bitu wykonania uruchamia sie
#: przez `bash x.sh` i nie uruchamia przez `./x.sh`, a instrukcja podaje jedno z dwoch.
SKRYPTY = ("tools/dev/prepare-playable.sh", "tools/dev/play.sh")

#: Generatory, ktore sklada sie na przepis pakietu A. ZMIERZONE 13.09.2026 z kroku
#: `Generate package A geometry`, ktory ten skrypt zastapil — po jednym wywolaniu
#: kazdego, w tej kolejnosci.
GENERATORY = (
    "tools/blender/tunnel_sweep.py",
    "tools/blender/m7_shell.py",
    "tools/track/station_layout.py",
    "tools/blender/station_kit.py",
)

#: Parametry bez wartosci domyslnej, ktore MUSZA stac w przepisie jawnie. Kazdy ma
#: w drzewie swoj powod i kazdy pominiety daje scene, ktora wyglada poprawnie:
#: `--platform-length-m design` bierze decyzje wlasciciela zamiast dolnej granicy
#: R-007, `--platform-gap-m` nie ma zrodla publicznego (R-007), `--profile box_double`
#: rozstrzyga strop tunelu, a `--component` ogranicza zespol stacji do tego, co miesci
#: sie pod tym stropem.
PARAMETRY_JAWNE = (
    "--platform-length-m design",
    "--platform-gap-m 0.08",
    "--profile box_double",
    "--component platform",
    "--component edge",
)

#: Workflow, ktory przepis wolal do 13.09.2026.
WORKFLOW = ".github/workflows/godot-first-run.yml"


def _czytaj(wzgledna):
    with open(os.path.join(ROOT, wzgledna), encoding="utf-8") as handle:
        return handle.read()


def _bez_komentarzy(tekst):
    """Wiersze skryptu shellowego bez komentarzy — `#` w komentarzu nie jest kodem."""
    return "\n".join(w for w in tekst.splitlines()
                     if not w.lstrip().startswith("#"))


def test_oba_skrypty_MB01_istnieja_i_sa_wykonywalne():
    sprawdzonych = 0
    for wzgledna in SKRYPTY:
        sciezka = os.path.join(ROOT, wzgledna)
        assert os.path.exists(sciezka), (
            "nie ma `%s`, a `docs/PLAYABILITY.md` i pasmo M na niego wskazuja"
            % wzgledna)
        assert os.access(sciezka, os.X_OK), (
            "`%s` nie ma bitu wykonania — `./%s` odmowi, a instrukcja podaje "
            "jedna z dwoch drog uruchomienia" % (wzgledna, wzgledna))
        tresc = _czytaj(wzgledna)
        assert tresc.startswith("#!/usr/bin/env bash"), (
            "`%s` nie zaczyna sie od shebanga `#!/usr/bin/env bash`" % wzgledna)
        assert "set -euo pipefail" in tresc, (
            "`%s` nie ma `set -euo pipefail` — blad w srodku przeszedlby cicho, "
            "a skrypt konczylby sie kodem zero" % wzgledna)
        sprawdzonych += 1

    assert sprawdzonych == len(SKRYPTY), (
        "petla po skryptach wykonala sie %d razy zamiast %d — wtedy asercje wyzej "
        "nie sprawdzaja wszystkich (rodzina 6.D193)" % (sprawdzonych, len(SKRYPTY)))


def test_przepis_generacji_stoi_w_DOKLADNIE_JEDNYM_miejscu():
    """**Najwazniejsza asercja tej rodziny.**

    Workflow ma przepis WOLAC, a nie niesc. Gdyby wrocil do YAML-a obok wywolania
    skryptu, oba dzialalyby i CI byloby zielone — a rozjazd wyszedlby dopiero wtedy,
    gdy ktos zmieni jeden i nie zmieni drugiego.
    """
    przepis = _bez_komentarzy(_czytaj("tools/dev/prepare-playable.sh"))
    workflow = _czytaj(WORKFLOW)

    sprawdzonych = 0
    for generator in GENERATORY:
        assert generator in przepis, (
            "`tools/dev/prepare-playable.sh` nie wola `%s` — przepis jest niepelny "
            "i scena dostanie mniej, niz mial krok CI, ktory ten skrypt zastapil"
            % generator)
        # W workflow generator ma stac WYLACZNIE w komentarzu albo wcale.
        w_kodzie = [w for w in workflow.splitlines()
                    if generator in w and not w.lstrip().startswith("#")]
        assert not w_kodzie, (
            "`%s` stoi w KODZIE workflowa `%s`, a nie tylko w `prepare-playable.sh`: "
            "%r. Przepis rozszedl sie na dwa miejsca i od teraz moga sie rozjechac"
            % (generator, WORKFLOW, w_kodzie[:2]))
        sprawdzonych += 1

    assert sprawdzonych == len(GENERATORY), (
        "petla po generatorach wykonala sie %d razy zamiast %d"
        % (sprawdzonych, len(GENERATORY)))

    assert "bash tools/dev/prepare-playable.sh" in workflow, (
        "workflow `%s` nie wola `tools/dev/prepare-playable.sh` — przepis stoi wtedy "
        "w skrypcie, ktorego CI nie uruchamia, czyli w kodzie bez pokrycia" % WORKFLOW)


def test_kazdy_parametr_BEZ_WARTOSCI_DOMYSLNEJ_stoi_w_przepisie_jawnie():
    """Pominiety parametr daje scene, ktora WYGLADA POPRAWNIE — i to jest powod.

    `--platform-length-m design` pominiete daje perony 94,0 m zamiast 95,0 m
    (dolna granica R-007 zamiast decyzji wlasciciela z T-212); `--component` pominiete
    wpuszcza schody i antresole siegajace 8,30 m pod strop 4,70 m. Zadne z tych dwoch
    nie konczy sie bledem.
    """
    przepis = _bez_komentarzy(_czytaj("tools/dev/prepare-playable.sh"))
    sprawdzonych = 0
    for parametr in PARAMETRY_JAWNE:
        assert parametr in przepis, (
            "w `tools/dev/prepare-playable.sh` nie ma `%s`. Ten parametr NIE MA "
            "wartosci domyslnej, a jego pominiecie nie konczy sie bledem — daje "
            "geometrie, ktora wyglada poprawnie i nia nie jest" % parametr)
        sprawdzonych += 1
    assert sprawdzonych == len(PARAMETRY_JAWNE), (
        "petla po parametrach wykonala sie %d razy zamiast %d"
        % (sprawdzonych, len(PARAMETRY_JAWNE)))


def test_trening_wlacza_ATP_i_zapis_wejsc_bo_ich_brak_jest_NIEWIDOCZNY():
    """Scena bez `--signalling` wyglada tak samo i nie chroni.

    Bez `--input-log` przejazdu nie da sie odtworzyc, a punkt 6 odbioru M1
    (`docs/PLAYABILITY.md` §3) zada, zeby ten sam replay dal ten sam wynik.
    """
    play = _bez_komentarzy(_czytaj("tools/dev/play.sh"))
    assert "--signalling=" in play, (
        "`tools/dev/play.sh` nie podaje `--signalling` — scena uruchomi sie, bedzie "
        "wygladac tak samo i NIE BEDZIE CHRONIC")
    assert "classic-2026.json" in play, (
        "`tools/dev/play.sh` nie wskazuje planu `classic-2026.json`")
    assert "--input-log=" in play, (
        "`tools/dev/play.sh` nie podaje `--input-log` — przejazdu nie da sie "
        "odtworzyc, a punkt 6 odbioru M1 tego zada")

    # Trybu NIE podaje sie jawnie: reczny jest domyslny (`src/Game/RunPlan.cs`).
    # Gdyby ktos dopisal tu `--line`, gracz dostalby autopilota i klawisze przestalyby
    # cokolwiek robic — a scena wygladalaby identycznie.
    assert "--line" not in play, (
        "`tools/dev/play.sh` podaje `--line` — to jest AUTOPILOT, klawisze prowadzenia "
        "nie sterowalyby pociagiem, a scena wygladalaby tak samo")
    assert "--shot" not in play and "--telemetry" not in play, (
        "`tools/dev/play.sh` podaje tryb techniczny — trening ma byc interaktywny")


def test_brak_zasobu_konczy_sie_NAZWANYM_bledem_a_nie_pusta_scena():
    """Punkt 7 odbioru M1. Bez tej kontroli brak `build/t400` dawal scene bez tunelu."""
    play = _czytaj("tools/dev/play.sh")
    assert "exit 4" in play, (
        "`tools/dev/play.sh` nie ma osobnego kodu wyjscia dla braku zasobow — "
        "wolajacy nie odrozni go od bledu Godota")
    assert "prepare-playable.sh" in play, (
        "komunikat braku zasobow nie mowi, co uruchomic — a to jest cala roznica "
        "miedzy nazwanym bledem a pusta scena")
    for wymagany in ("L1_A-chunks.json", "M7_shell.glb", "L1_A-platforms.glb"):
        assert wymagany in play, (
            "`tools/dev/play.sh` nie sprawdza obecnosci `%s`" % wymagany)

    przygotowanie = _czytaj("tools/dev/prepare-playable.sh")
    assert "exit 3" in przygotowanie and "BLENDER_BIN" in przygotowanie, (
        "`prepare-playable.sh` nie zglasza braku Blendera osobnym kodem — `CLAUDE.md` "
        "§2 kaze przerwac i powiedziec, a nie probowac obejsc")


def test_czytnik_komentarzy_ODROZNIA_kod_od_komentarza_na_wejsciu_syntetycznym():
    """Bez tego wejscia „generator nie stoi w kodzie workflowa" nie znaczy nic.

    Drzewo tego przypadku nie cwiczy w obie strony: dzis kazde wystapienie generatora
    w workflow stoi w komentarzu, wiec gdyby czytnik bral WSZYSTKIE wiersze za kod,
    bramka wyzej zapalalaby sie stale — ale gdyby bral wszystkie za komentarz, milczalaby
    zawsze i tego nie widac. Rodzina 6.D159.
    """
    wejscie = "kod tools/blender/m7_shell.py\n   # komentarz tools/blender/m7_shell.py\n"
    czyste = _bez_komentarzy(wejscie)
    assert "kod tools/blender/m7_shell.py" in czyste, "czytnik zjadl wiersz KODU"
    assert czyste.count("tools/blender/m7_shell.py") == 1, (
        "czytnik zostawil komentarz — wtedy bramka jednego miejsca zapala sie na "
        "akapicie wyjasniajacym, a nie na powielonym przepisie")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
