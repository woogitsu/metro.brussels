#!/usr/bin/env python3
"""Bramka metadanych zrzutu z Godota — testowana bez Godota.

Audyt mutacyjny `src/Game` (02.09.2026): 24 z 32 mutacji przeżyły, 75 % — najgorzej
z trzech warstw repo. Siedem z nich to jedna przyczyna: krok „Screenshots must not be
empty frames" woła `compare.py` **bez `--baseline`**, a `check_geometry` przy braku
baseline wychodzi na `new-baseline` zanim porówna cokolwiek. Metadane sceny nie były
porównywane z niczym.

`tools/ci/assert_shot_metadata.py` zamyka tę dziurę i te testy pilnują, żeby zamykał
ją nadal. Sam skrypt jest czystym Pythonem, więc testuje się bez silnika; przebieg
z prawdziwym Godotem robi CI.
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(ROOT, "tools", "ci", "assert_shot_metadata.py")
AXIS = os.path.join(ROOT, "data", "track", "L1_A.json")
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "godot-first-run.yml")

sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import assert_shot_metadata as G  # noqa: E402
import profiles  # noqa: E402


def _healthy():
    """Metadane zmierzone na prawdziwym przebiegu Godota 4.3 na pakiecie A."""
    return {
        "engine": "godot",
        "engine_version": "4.3-stable (official)",
        "manifest_version": "L1_A/flat-preview",
        "resolution": [1280, 720],
        "last_shot": {"view": "Cab", "chainage_m": 2000.068, "steps": 11872},
        "scene": {
            "bbox_min": [-4.4386, -1.2, -910.3813],
            "bbox_max": [5448.105, 4.7, 1076.5525],
            "size_m": [5452.5435, 5.9, 1986.9338],
            "mesh_objects": 12,
            "vertices": 48528,
            "faces": 16176,
            "chunks_loaded": 12,
            "chunks_declared": 12,
            "axis_length_m": 6686.739,
        },
        # Zmierzone na tym samym przebiegu. 11 brył = 6 pudeł + 5 mieszków; długość,
        # szerokość i liczba członów zgadzają się z rejestrem M7 (status `spec`).
        "train": {
            "bodies": 11,
            "length_m": 94.0,
            "width_m": 2.7,
            "roof_height_m": 3.6,
        },
    }


def _check(metadata, resolution=(1280, 720), view="cab", chainage_m=2000.0):
    return G.check(metadata, AXIS, list(resolution) if resolution else None, view, chainage_m)


def _run(metadata):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False)
        path = handle.name
    try:
        return subprocess.run(
            [sys.executable, SCRIPT, "--metadata", path, "--axis", AXIS,
             "--resolution", "1280x720", "--view", "cab", "--at-chainage", "2000"],
            capture_output=True, text=True)
    finally:
        os.unlink(path)


# --- prawda liczona niezależnie -------------------------------------------------


def test_axis_length_is_computed_here_not_read_from_the_metadata():
    """Długość osi musi pochodzić z drugiej implementacji, nie z pliku, który sprawdza.

    Scena raportuje 6686,739 m — długość po zagęszczeniu krzywą Catmull-Rom krokiem
    5 m, a nie 6686,35 m z pola `length_m`. Ten sam krok liczy tu Python, więc obie
    strony porównania są niezależne.
    """
    computed = G.axis_length_m(AXIS)
    assert abs(computed - 6686.739) < 1e-3, computed

    with open(AXIS, encoding="utf-8") as handle:
        declared = json.load(handle)["length_m"]
    assert abs(computed - declared) > 0.3, (
        "gdyby zagęszczenie nic nie zmieniało, ten test nie dowodziłby niezależności")
    assert G.RING_STEP_M == 5.0


def test_scene_bbox_of_the_axis_matches_the_engine_axis_swap():
    """`SceneAxis.ToScene` to (X, Z, −Y). Kotwica bezwzględna stoi na tej zamianie."""
    lo, hi = G.axis_scene_bbox(AXIS)
    healthy = _healthy()["scene"]
    for axis in range(3):
        assert healthy["bbox_min"][axis] <= lo[axis] + 1e-6, axis
        assert healthy["bbox_max"][axis] >= hi[axis] - 1e-6, axis


def test_healthy_metadata_passes():
    assert _check(_healthy()) == []
    result = _run(_healthy())
    assert result.returncode == 0, result.stderr
    assert "policzone niezależnie" in result.stdout, result.stdout


# --- każda z siedmiu mutacji, które przeżyły audyt -----------------------------


def _mutate(**scene_changes):
    metadata = _healthy()
    metadata["scene"].update(scene_changes)
    return metadata


def test_gate_catches_every_mutation_that_survived_the_audit():
    """Siedem mutacji z audytu plus dwie własne. Każda musi dać niepustą listę."""
    healthy = _healthy()
    shifted = _healthy()
    shifted["scene"]["bbox_min"] = [v + 1000.0 for v in healthy["scene"]["bbox_min"]]
    shifted["scene"]["bbox_max"] = [v + 1000.0 for v in healthy["scene"]["bbox_max"]]

    blown = _healthy()
    blown["scene"]["bbox_min"] = [v * 10.0 for v in healthy["scene"]["bbox_min"]]
    blown["scene"]["bbox_max"] = [v * 10.0 for v in healthy["scene"]["bbox_max"]]
    blown["scene"]["size_m"] = [b - a for a, b in
                                zip(blown["scene"]["bbox_min"], blown["scene"]["bbox_max"])]

    wrong_resolution = _healthy()
    wrong_resolution["resolution"] = [640, 480]

    wrong_shot = _healthy()
    wrong_shot["last_shot"] = {"view": "Cab", "chainage_m": 0.0, "steps": 0}

    wrong_view = _healthy()
    wrong_view["last_shot"] = dict(healthy["last_shot"], view="Chase")

    cases = {
        "M01 chunks_loaded +7": _mutate(chunks_loaded=19),
        "M02 mesh_objects 0": _mutate(mesh_objects=0),
        "M03 bbox +1000 m": shifted,
        "M04 vertices/faces 0": _mutate(vertices=0, faces=0),
        "M05 axis_length_m 0": _mutate(axis_length_m=0.0),
        "M06 resolution 640x480": wrong_resolution,
        "M07 last_shot wyzerowany": wrong_shot,
        "size_m zwinięte": _mutate(size_m=[0.0, 0.0, 0.0]),
        "bryła rozdmuchana 10x": blown,
        "widok inny niż żądany": wrong_view,
        "chunks_declared 0": _mutate(chunks_declared=0, chunks_loaded=0),
    }
    survivors = [name for name, metadata in cases.items() if not _check(metadata)]
    assert not survivors, survivors


def test_gate_refuses_metadata_without_a_scene_section():
    problems = _check({"resolution": [1280, 720], "last_shot": {}})
    assert problems and "sekcji" in problems[0], problems


def test_gate_exit_code_is_nonzero_and_says_what_is_wrong():
    result = _run(_mutate(chunks_loaded=19))
    assert result.returncode == 1, result
    assert "19" in result.stderr and "12" in result.stderr, result.stderr


# --- próg wystawania poza oś ---------------------------------------------------


def test_slack_tolerance_is_the_tunnel_cross_section_not_a_round_number():
    """Bryła może wystawać poza oś dokładnie o przekrój tunelu, nie o „coś".

    Zmierzone rozszerzenia na pakiecie A: 1,2–4,7 m przy profilu 9,40 × 5,90 m.
    Próg wzięty z `profiles.dimensions`, więc zmiana profilu pociąga go za sobą.
    """
    width, height = profiles.dimensions("box_double")
    assert max(width, height) == 9.4, (width, height)

    healthy = _healthy()
    # Wystawanie o pół przekroju jest w porządku…
    ok = _healthy()
    ok["scene"]["bbox_max"] = [v + 4.0 for v in healthy["scene"]["bbox_max"]]
    ok["scene"]["size_m"] = [b - a for a, b in
                             zip(ok["scene"]["bbox_min"], ok["scene"]["bbox_max"])]
    assert _check(ok) == [], _check(ok)

    # …a o dwa przekroje już nie.
    too_much = _healthy()
    too_much["scene"]["bbox_max"] = [v + 2.0 * max(width, height) for v in healthy["scene"]["bbox_max"]]
    too_much["scene"]["size_m"] = [b - a for a, b in
                                   zip(too_much["scene"]["bbox_min"], too_much["scene"]["bbox_max"])]
    assert _check(too_much), "bryła dwa razy szersza od tunelu przeszła"


# --- workflow woła tę bramkę ---------------------------------------------------


def test_workflow_actually_runs_the_metadata_gate():
    with open(WORKFLOW, encoding="utf-8") as handle:
        text = handle.read()
    steps = re.split(r"\n {6}- name: ", text)[1:]
    gate = [step for step in steps if step.startswith("Shot metadata must describe this scene")]
    assert len(gate) == 1, "krok bramki metadanych zniknął albo zmienił nazwę"

    body = gate[0]
    assert "tools/ci/assert_shot_metadata.py" in body
    assert "--axis data/track/L1_A.json" in body, "bramka musi dostać oś do policzenia prawdy"
    assert "--resolution 1280x720" in body

    # Bez `--manifest` bramka nie policzy predykatu i cała kontrola streamowania
    # — najmocniejsza rzecz, jaką ten skrypt umie — przechodzi obok, nic nie mówiąc.
    # Skrypt nie może tego wymuszać sam: `--manifest` jest opcjonalny, żeby dało się
    # go wołać na scenie bez tunelu (krok kontroli negatywnej niżej). Dlatego pilnuje
    # tego test, a nie argparse.
    assert "--manifest build/t400/chunks/L1_A-chunks.json" in body, (
        "krok bramki nie podaje manifestu — kontrola okna, rezydencji i LOD nie działa")
    # I manifest musi być tym, który ten job SAM wygenerował, a nie kopią z repo.
    assert text.index("--chunk-manifest build/t400/chunks/L1_A-chunks.json") < text.index(
        "--manifest build/t400/chunks/L1_A-chunks.json")
    # Krok musi stać PO zrzutach, bo inaczej nie ma czego czytać.
    assert text.index("Shot metadata must describe this scene") > text.index("--shot=")


# --- Issue #107: scena bez składu ------------------------------------------------

M7_SPEC = os.path.join(ROOT, "data", "vehicle", "m7-spec.json")


def _train(metadata):
    return G.check_train(metadata, M7_SPEC)


def test_healthy_metadata_has_a_train_the_registry_agrees_with():
    assert _train(_healthy()) == []


def test_gate_refuses_metadata_without_a_train_block():
    """Issue #107 w jednym zdaniu: cały blok `scene` opisuje wyłącznie tunel.

    Mutacja `TrainView.cs:38` — skorupa nie wczytuje się w ogóle — zostawiała
    `godot-first-run.yml` ZIELONY, bo o składzie nie było w metadanych ani słowa.
    Próg pustej klatki tego nie łapie: w widoku `cab` składu nie widać z definicji,
    a w `chase` i `outside` jego brak wygląda jak zwykły kadr tunelu.
    """
    metadata = _healthy()
    del metadata["train"]
    problems = _train(metadata)
    assert problems and "train" in problems[0], problems


def test_body_count_comes_from_the_registry_not_from_a_constant():
    """6 członów daje 11 brył. Gdyby ktoś przepisał liczbę, rozjazd byłby niewidoczny."""
    assert G.expected_bodies(6) == 11
    assert G.expected_bodies(4) == 7
    metadata = _healthy()
    metadata["train"]["bodies"] = 6
    assert _train(metadata), "liczba członów zamiast liczby brył musi zostać odrzucona"


def test_train_dimensions_are_checked_against_the_registry():
    for field, broken in (("length_m", 0.0), ("length_m", 88.0),
                          ("width_m", 2.5), ("roof_height_m", 0.0)):
        metadata = _healthy()
        metadata["train"][field] = broken
        assert _train(metadata), f"{field}={broken} przeszło bramkę"


def test_the_registry_values_must_carry_the_spec_status():
    """Bramka nie ma prawa opierać się na wartości bez źródła.

    Gdyby ktoś zmienił status `length_m` na `design_assumption`, porównanie
    przestałoby być drugą niezależną drogą do tej samej liczby i stałoby się
    porównaniem założenia z założeniem — a wyglądałoby tak samo.

    Pierwsza wersja tego testu sprawdzała tylko WARTOŚCI i przeżyła usunięcie
    kontroli statusu. Teraz sprawdza, że bramka faktycznie odmawia.
    """
    spec = G.m7_spec(M7_SPEC)
    assert spec["cars"] == 6 and spec["length_m"] == 94.0 and spec["width_m"] == 2.7

    with open(M7_SPEC, encoding="utf-8") as handle:
        registry = json.load(handle)
    registry["parameters"]["length_m"]["status"] = "design_assumption"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as h:
        json.dump(registry, h, ensure_ascii=False)
        path = h.name
    try:
        raised = False
        try:
            G.m7_spec(path)
        except SystemExit as exc:
            raised = True
            assert "spec" in str(exc), exc
        assert raised, "rejestr bez statusu spec musi zostać odrzucony"
    finally:
        os.unlink(path)


def test_workflow_gate_would_catch_a_scene_without_a_train():
    """Kontrola całego skryptu, nie samej funkcji — tak jak woła go workflow."""
    metadata = _healthy()
    metadata["train"]["bodies"] = 0
    result = _run(metadata)
    assert result.returncode != 0, result.stdout
    assert "train.bodies" in result.stderr, result.stderr


# --- progi sprawdzane NA GRANICY ------------------------------------------------
#
# Przegląd mutacyjny 03.09.2026: 16 z 33 mutacji tego pliku przeżyło, a czternaście
# z nich to były progi. Testy powyżej sprawdzały wartości DALEKO od progu — bbox
# przesunięty o 1000 m, `mesh_objects: 0`, skład o 6 m za krótki. Takie wejście nie
# odróżnia `>` od `>=` ani 1e-3 od 1,01e-3: przechodzi po obu stronach granicy.
#
# Poniższe testy dotykają granicy DOKŁADNIE, i to jest ich jedyny powód istnienia.
# Każdy ma kontrolę negatywną o jeden `ulp` dalej — bo test, który tylko potwierdza,
# że coś przechodzi, przeszedłby też przy bramce wyłączonej.


def _next_up(value):
    return math.nextafter(value, math.inf)


def _next_down(value):
    return math.nextafter(value, -math.inf)


def _spec_with(length_m, width_m):
    """Kopia rejestru M7 z podmienionymi wymiarami — tylko do arytmetyki progów.

    Zwraca ścieżkę do pliku tymczasowego; woła się ją w `try/finally`.
    """
    with open(M7_SPEC, encoding="utf-8") as handle:
        registry = json.load(handle)
    registry["parameters"]["length_m"]["value"] = length_m
    registry["parameters"]["width_m"]["value"] = width_m
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as h:
        json.dump(registry, h, ensure_ascii=False)
        return h.name


def test_train_tolerance_is_one_percent_and_the_boundary_itself_passes():
    """Rozjazd RÓWNY jednemu procentowi jeszcze przechodzi; o jeden `ulp` więcej — nie.

    **Dlaczego rejestr jest tu podmieniony.** Prawdziwy wymiar to 94,0 m, a próg to
    `94.0 * 0.01`, czyli w double `0.9400000000000001`. Nie istnieje żadna liczba
    zmiennoprzecinkowa `L`, dla której `abs(L - 94.0)` daje dokładnie tę wartość:
    różnice dwóch liczb w okolicy 94,94 są wielokrotnościami 2^-46 (≈ 1,4e-14),
    a próg wymaga rozdzielczości 2^-53. Naiwne `94.0 + 94.0 * 0.01` daje
    `0.9399999999999977` — czyli POD progiem, po tej samej stronie co wartość zdrowa.
    Taki „test granicy" granicy nie dotyka i przepuszcza zamianę `>` na `>=`.

    Dla nominału 100,0 m arytmetyka wychodzi dokładna: `100.0 * 0.01 == 1.0`
    (próg jest potęgą dwójki), a `abs(101.0 - 100.0) == 1.0` bez żadnego błędu.
    Dlatego granica jest badana na podmienionym rejestrze — podmiana dotyczy
    WYŁĄCZNIE arytmetyki, a prawdziwe 94,0 m jest tu zaraz obok potwierdzone.
    """
    assert G.m7_spec(M7_SPEC)["length_m"] == 94.0, "rejestr nie zmienia się przez ten test"
    assert 94.0 * 0.01 != abs(94.0 + 94.0 * 0.01 - 94.0), (
        "gdyby ta granica była osiągalna wprost, podmiana rejestru byłaby zbędna")
    assert 100.0 * 0.01 == 1.0 and abs(101.0 - 100.0) == 100.0 * 0.01

    spec = _spec_with(100.0, 100.0)
    try:
        for field in ("length_m", "width_m"):
            on_edge = _healthy()
            on_edge["train"]["length_m"] = 100.0
            on_edge["train"]["width_m"] = 100.0
            on_edge["train"][field] = 101.0
            assert G.check_train(on_edge, spec) == [], (
                field, G.check_train(on_edge, spec),
                "rozjazd równy dokładnie 1 % musi jeszcze przejść")

            over = json.loads(json.dumps(on_edge))
            over["train"][field] = _next_up(101.0)
            problems = G.check_train(over, spec)
            assert len(problems) == 1 and field in problems[0], (field, problems)

            under = json.loads(json.dumps(on_edge))
            under["train"][field] = 99.0
            assert G.check_train(under, spec) == [], (field, "granica działa w obie strony")
    finally:
        os.unlink(spec)


def test_a_train_of_zero_length_is_reported_as_absent_not_as_a_wrong_size():
    """`length_m == 0.0` to „nie ma składu", nie „skład o złym wymiarze".

    Obie diagnozy kończą się czerwonym CI, więc test liczący same problemy nie
    odróżnia `<= 0.0` od `< 0.0` — przy `<` zero wpada do porównania z rejestrem
    i wychodzi jako rozjazd 94 m. Różni się KOMUNIKAT, a to on trafia do loga
    i mówi, czy szukać złej skorupy, czy jej braku.

    Kontrola negatywna: skład o realnie złej długości musi dać dokładnie tę drugą
    diagnozę, a skład zgodny z rejestrem — żadnej.
    """
    absent = _healthy()
    absent["train"]["length_m"] = 0.0
    problems = _train(absent)
    assert len(problems) == 1, problems
    assert "zwinięty w punkt" in problems[0], problems

    wrong = _healthy()
    wrong["train"]["length_m"] = 88.0
    problems = _train(wrong)
    assert len(problems) == 1 and "rejestr M7" in problems[0], problems
    assert "zwinięty w punkt" not in problems[0], problems

    assert _train(_healthy()) == []


def test_a_scene_of_one_mesh_object_is_still_a_scene():
    """Próg zawartości to „więcej niż zero", nie „więcej niż jeden".

    Scena złożona z jednej scalonej siatki jest normalnym wynikiem eksportu i musi
    przejść. Test dotyka granicy od tej strony, bo poprzednie sprawdzały wyłącznie
    zero — a zero nie odróżnia `<= 0` od `<= 1`.

    Kontrola negatywna: zero na tym samym polu musi dać dokładnie jeden problem,
    i to nazwany po polu.
    """
    for key in ("mesh_objects", "vertices", "faces"):
        one = _mutate(**{key: 1})
        assert _check(one) == [], (key, _check(one))

        zero = _mutate(**{key: 0})
        problems = _check(zero)
        assert len(problems) == 1 and problems[0].startswith(f"{key} = 0"), (key, problems)


def test_size_must_follow_from_the_bbox_down_to_the_millimetre():
    """Niespójność `size_m` z bboxem równa DOKŁADNIE 1 mm jeszcze przechodzi.

    **Gdzie ta granica jest osiągalna.** Różnica `(b - a) - s` jest w double dokładna
    tylko wtedy, gdy operandy są małe: przy bboxie rzędu tysięcy metrów najbliższe
    liczby są oddalone o ~1e-13 i wartość dokładnie `1e-3` nie wypada w tej siatce.
    Ale oś L1_A jest PŁASKA w scenicznym Y (`SceneAxis.ToScene` daje tam składową Z
    danych, a ta jest wszędzie zerowa), więc wzdłuż Y bryła może stać przy samym
    zerze i arytmetyka robi się dokładna:

        (0.001 - (-0.001)) - 0.001 == 1e-3     # dokładnie, bo 2·d − d = d

    Test to sprawdza jawnie, zanim cokolwiek założy.

    Kontrola negatywna: 1,005 mm — wartość leżąca MIĘDZY progiem a progiem
    podniesionym o procent — musi zostać odrzucona.
    """
    lo, hi = G.axis_scene_bbox(AXIS)
    assert lo[1] == hi[1] == 0.0, ("oś nie jest już płaska w scenicznym Y", lo, hi)
    assert (0.001 - (-0.001)) - 0.001 == 1e-3, "arytmetyka granicy przestała być dokładna"

    on_edge = _healthy()
    on_edge["scene"]["bbox_min"][1] = -0.001
    on_edge["scene"]["bbox_max"][1] = 0.001
    on_edge["scene"]["size_m"][1] = 0.001          # o 1 mm mniej, niż wynika z bboxa
    assert _check(on_edge) == [], _check(on_edge)

    over = _healthy()
    over["scene"]["bbox_min"][1] = -0.001
    over["scene"]["bbox_max"][1] = 0.001 + 5e-6    # rozjazd 1,005 mm
    over["scene"]["size_m"][1] = 0.001
    problems = _check(over)
    assert len(problems) == 1 and problems[0].startswith("size_m[1]"), problems
    assert "nie wynika z bboxa" in problems[0], problems


def test_a_scene_axis_collapsed_to_zero_is_reported():
    """`size_m` równe DOKŁADNIE zero to bryła zwinięta — i tak musi być nazwana.

    Poprzedni test zerował całe `size_m`, ale zostawiał bbox bez zmian, więc pierwsza
    zapalała się kontrola spójności z bboxem, nie kontrola zwinięcia. Tutaj bbox jest
    zwinięty razem z rozmiarem, więc zapala się WYŁĄCZNIE ta druga — i widać, że
    granica leży na zerze, a nie tuż pod nim.

    Kontrola negatywna: ta sama scena z niezerową grubością nie może dać ani jednego
    problemu.
    """
    flat = _healthy()
    flat["scene"]["bbox_min"][1] = 0.0
    flat["scene"]["bbox_max"][1] = 0.0
    flat["scene"]["size_m"][1] = 0.0
    problems = _check(flat)
    assert len(problems) == 1, problems
    assert problems[0].startswith("size_m[1] = 0.0") and "zwinięta" in problems[0], problems

    thick = _healthy()
    thick["scene"]["bbox_min"][1] = -0.001
    thick["scene"]["bbox_max"][1] = 0.001
    thick["scene"]["size_m"][1] = 0.002
    assert _check(thick) == [], _check(thick)


def test_the_scene_may_touch_the_axis_exactly_at_the_micrometre_slack():
    """Zapas mikrometra na zawieranie osi jest inkluzywny po obu stronach.

    `1e-6` w tym warunku jest zapasem na zaokrąglenia zapisu, nie miejscem, w którym
    scena ma się urwać. Granica jest tu osiągalna DOKŁADNIE, bo test liczy ją tym
    samym wyrażeniem, co bramka (`axis_lo + 1e-6`), i wstawia wynik do metadanych —
    porównywane są więc dwie identyczne liczby, bez żadnej arytmetyki pośredniej.

    Kontrola negatywna: jeden `ulp` dalej od osi — czyli bryła, która osi już
    nie zawiera — musi dać dokładnie jeden problem, nazwany po osi.
    """
    axis_lo, axis_hi = G.axis_scene_bbox(AXIS)

    touching_lo = _healthy()
    touching_lo["scene"]["bbox_min"][0] = axis_lo[0] + 1e-6
    touching_lo["scene"]["size_m"][0] = (touching_lo["scene"]["bbox_max"][0]
                                         - touching_lo["scene"]["bbox_min"][0])
    assert _check(touching_lo) == [], _check(touching_lo)

    past_lo = json.loads(json.dumps(touching_lo))
    past_lo["scene"]["bbox_min"][0] = _next_up(axis_lo[0] + 1e-6)
    past_lo["scene"]["size_m"][0] = (past_lo["scene"]["bbox_max"][0]
                                     - past_lo["scene"]["bbox_min"][0])
    problems = _check(past_lo)
    assert len(problems) == 1 and "nie zawiera osi wzdłuż X" in problems[0], problems

    touching_hi = _healthy()
    touching_hi["scene"]["bbox_max"][0] = axis_hi[0] - 1e-6
    touching_hi["scene"]["size_m"][0] = (touching_hi["scene"]["bbox_max"][0]
                                         - touching_hi["scene"]["bbox_min"][0])
    assert _check(touching_hi) == [], _check(touching_hi)

    past_hi = json.loads(json.dumps(touching_hi))
    past_hi["scene"]["bbox_max"][0] = _next_down(axis_hi[0] - 1e-6)
    past_hi["scene"]["size_m"][0] = (past_hi["scene"]["bbox_max"][0]
                                     - past_hi["scene"]["bbox_min"][0])
    problems = _check(past_hi)
    assert len(problems) == 1 and "nie zawiera osi wzdłuż X" in problems[0], problems


def test_an_overhang_of_exactly_one_tunnel_cross_section_still_passes():
    """Wystawanie RÓWNE przekrojowi tunelu mieści się w progu; o `ulp` więcej — nie.

    Test powyżej (`test_slack_tolerance_is_the_tunnel_cross_section...`) sprawdza pół
    przekroju i dwa przekroje — po obu stronach granicy, ale nigdy NA niej. Tu granica
    jest trafiona dokładnie, i jest to możliwe wyłącznie dlatego, że oś L1_A zaczyna
    się w scenicznym X równym ZERU: `0.0 - (-9.4)` daje dokładnie `9.4`, podczas gdy
    ta sama różnica policzona przy 5446,6 m zgubiłaby się w zaokrągleniu. Test
    sprawdza to założenie jawnie, zamiast na nim milcząco polegać.
    """
    axis_lo, _axis_hi = G.axis_scene_bbox(AXIS)
    assert axis_lo[0] == 0.0, ("oś nie zaczyna się już w zerze — granica przestała "
                               "być dokładna", axis_lo)
    width = max(profiles.dimensions("box_double"))
    assert width == 9.4
    assert axis_lo[0] - (axis_lo[0] - width) == width, "arytmetyka granicy nie jest dokładna"

    on_edge = _healthy()
    on_edge["scene"]["bbox_min"][0] = axis_lo[0] - width
    on_edge["scene"]["size_m"][0] = (on_edge["scene"]["bbox_max"][0]
                                     - on_edge["scene"]["bbox_min"][0])
    assert _check(on_edge) == [], _check(on_edge)

    over = _healthy()
    over["scene"]["bbox_min"][0] = _next_down(axis_lo[0] - width)
    over["scene"]["size_m"][0] = (over["scene"]["bbox_max"][0]
                                  - over["scene"]["bbox_min"][0])
    problems = _check(over)
    assert len(problems) == 1 and "wystaje poza oś wzdłuż X" in problems[0], problems


def test_axis_length_off_by_exactly_the_tolerance_still_passes():
    """Różnica długości osi RÓWNA tolerancji jeszcze przechodzi, większa — nie.

    **Dlaczego tolerancja jest tu chwilowo podmieniona.** `AXIS_TOLERANCE_M` to
    `1e-3`, a oś ma 6686,74 m. Sąsiednie liczby zmiennoprzecinkowe są tam oddalone
    o 2^-40 (≈ 9,1e-13), więc żadna różnica dwóch takich liczb nie wynosi dokładnie
    `1e-3`: `(oś + 1e-3) - oś` daje `0.0010000000002037268`, czyli NAD progiem.
    Granicy `1e-3` nie da się dotknąć dla osi dłuższej niż około 2 mm i to jest
    własność arytmetyki, nie bramki.

    Potęga dwójki takiego problemu nie ma: `2^-10` (0,977 mm) jest dokładną
    wielokrotnością 2^-40, więc `(oś + 2^-10) - oś == 2^-10` bez błędu. Na czas
    tego jednego sprawdzenia tolerancja jest więc podmieniana na `2^-10`, a zaraz
    obok potwierdzone jest, że w kodzie stoi nadal `1e-3`.

    Kontrola negatywna: jeden `ulp` powyżej granicy musi dać dokładnie jeden problem.
    """
    assert G.AXIS_TOLERANCE_M == 1e-3, "próg produkcyjny musi zostać nietknięty"
    expected = G.axis_length_m(AXIS)
    assert (expected + 1e-3) - expected != 1e-3, (
        "gdyby ta granica była osiągalna wprost, podmiana tolerancji byłaby zbędna")

    tolerance = 2.0 ** -10
    assert (expected + tolerance) - expected == tolerance

    saved = G.AXIS_TOLERANCE_M
    G.AXIS_TOLERANCE_M = tolerance
    try:
        on_edge = _mutate(axis_length_m=expected + tolerance)
        assert _check(on_edge) == [], _check(on_edge)

        under = _mutate(axis_length_m=expected - tolerance)
        assert _check(under) == [], _check(under)

        over = _mutate(axis_length_m=_next_up(expected + tolerance))
        problems = _check(over)
        assert len(problems) == 1 and problems[0].startswith("axis_length_m"), problems
    finally:
        G.AXIS_TOLERANCE_M = saved
    assert G.AXIS_TOLERANCE_M == 1e-3


def test_a_shot_exactly_one_metre_off_is_still_the_same_frame():
    """Metr zapasu na chainage jest inkluzywny; 1,005 m to już inny kadr.

    Granica jest tu osiągalna wprost, bo `1.0` jest potęgą dwójki, a chainage rzędu
    2000 m ma krok siatki 2^-41 — `abs(2001.0 - 2000.0)` daje dokładnie `1.0`.
    To jedyny próg w tym pliku, który nie wymagał żadnej sztuczki.

    Kontrole negatywne dwie: jeden `ulp` nad metrem (odróżnia `>` od `>=`) oraz
    1,005 m (odróżnia próg 1,0 od progu podniesionego o procent). Bez tej drugiej
    test przechodziłby dla bramki tolerującej 1,01 m.
    """
    assert abs(2001.0 - 2000.0) == 1.0

    for chainage in (2001.0, 1999.0):
        on_edge = _healthy()
        on_edge["last_shot"]["chainage_m"] = chainage
        assert _check(on_edge) == [], (chainage, _check(on_edge))

    for chainage in (_next_up(2001.0), 2001.005, 1998.995):
        over = _healthy()
        over["last_shot"]["chainage_m"] = chainage
        problems = _check(over)
        assert len(problems) == 1 and problems[0].startswith("last_shot.chainage_m"), (
            chainage, problems)


# --- streamowanie: bramka porównuje scenę z predykatem, nie z liczbą chunków --------

#: Manifest z `tunnel_sweep.py`, ten sam, którym `StreamingPlanTests.cs` przybija
#: stronę C#. Zakresy chainage, długość osi i progi LOD są identyczne z manifestem,
#: który generuje `godot-first-run.yml`; sprawdzone przed wpisaniem tych liczb.
STREAM_MANIFEST = os.path.join(ROOT, "tests", "Game.Tests", "fixtures", "L1_A-chunks.json")


def _stream_manifest():
    return G.load_manifest(STREAM_MANIFEST)


def _streaming_healthy():
    """Metadane ZMIERZONE na prawdziwym przebiegu Godota 4.3 ze streamowaniem.

    Ujęcie z szwu c01/c02 (żądane 976 m, scena stanęła na 976,180 m), widok z kabiny.
    Dwa chunki rezydentne z dwunastu, 3624 ściany zamiast 16176 z całego pakietu.
    """
    return {
        "engine": "godot",
        "engine_version": "4.3-stable (official)",
        "manifest_version": "L1_A/flat-preview",
        "resolution": [1280, 720],
        "last_shot": {"view": "Cab", "chainage_m": 976.180, "steps": 6343},
        "scene": {
            "bbox_min": [57.4900, -1.2000, -910.3813],
            "bbox_max": [1141.9778, 4.7000, -245.6428],
            "size_m": [1084.4878, 5.9000, 664.7385],
            "mesh_objects": 2,
            "vertices": 10872,
            "faces": 3624,
            "chunks_loaded": 2,
            "chunks_declared": 12,
            "window_low_m": 676.180,
            "window_high_m": 1576.180,
            "axis_length_m": 6686.739,
        },
        "train": {"bodies": 11, "length_m": 94.0, "width_m": 2.7, "roof_height_m": 3.6},
    }


def _check_stream(metadata, chainage_m=976.0):
    return G.check(metadata, AXIS, [1280, 720], "cab", chainage_m, _stream_manifest())


def _mutate_stream(**scene):
    metadata = _streaming_healthy()
    metadata["scene"].update(scene)
    return metadata


def test_shot_gate_accepts_a_real_streamed_run():
    problems = _check_stream(_streaming_healthy())
    assert problems == [], problems


def test_shot_gate_refuses_a_scene_that_loaded_everything_instead_of_streaming():
    """Do 03.09.2026 to był JEDYNY stan, jaki bramka uznawała za poprawny.

    Warunek brzmiał `chunks_loaded != chunks_declared`, więc scena wczytująca cały
    pakiet przechodziła zawsze — także wtedy, gdy okno streamowania było policzone
    źle albo wcale. Teraz porównanie idzie z predykatem, więc „wczytałem wszystko"
    jest tak samo błędne, jak „wczytałem za mało".
    """
    problems = _check_stream(_mutate_stream(chunks_loaded=12, mesh_objects=12))
    assert any("predykat" in p for p in problems), problems


def test_shot_gate_refuses_one_chunk_too_few():
    problems = _check_stream(_mutate_stream(chunks_loaded=1))
    assert any("predykat" in p for p in problems), problems


def test_shot_gate_refuses_a_window_computed_for_the_wrong_direction():
    """Okno 600/300 odwrócone to jazda tyłem: 300 m przed składem, 600 m za nim."""
    problems = _check_stream(_mutate_stream(window_low_m=376.180, window_high_m=1276.180))
    assert sum("scena streamuje z innego okna" in p for p in problems) == 2, problems


def test_shot_gate_refuses_face_counts_taken_from_the_whole_package():
    """`faces` szło z `_manifest.Triangles`, czyli z sumy całego pakietu.

    Przy wczytywaniu wszystkiego liczba przypadkiem się zgadzała. Przy streamowaniu
    byłaby wprost nieprawdą — i to jest dokładnie ten rodzaj metadanych, dla którego
    ta bramka powstała.
    """
    problems = _check_stream(_mutate_stream(faces=16176, vertices=48528))
    assert any("inną geometrię" in p for p in problems), problems


def test_shot_gate_still_catches_a_scene_shifted_by_a_kilometre_while_streaming():
    """Własność, której bramka pilnowała przed streamowaniem, ma zostać w mocy.

    Kotwica jest teraz liczona na zakresie chunków REZYDENTNYCH zamiast na całej osi,
    więc jest ciaśniejsza: trzeba trafić w odcinek 1085-metrowy we właściwym miejscu,
    a nie zawrzeć oś długą na 6,7 km.
    """
    shifted = _streaming_healthy()
    shifted["scene"]["bbox_min"] = [v + 1000.0 for v in shifted["scene"]["bbox_min"]]
    shifted["scene"]["bbox_max"] = [v + 1000.0 for v in shifted["scene"]["bbox_max"]]
    problems = _check_stream(shifted)
    assert any("nie zawiera osi" in p for p in problems), problems


def test_shot_gate_anchors_on_the_resident_span_not_on_the_streaming_window():
    """Chunk wchodzi do pamięci w CAŁOŚCI, więc wystaje poza krawędź okna.

    Zmierzone: przy oknie [1700, 2600] m bryła sięgała 709 m dalej wzdłuż X i było to
    zachowanie poprawne. Kotwica liczona na oknie odrzucałaby zdrowe sceny; liczona
    na sumie zakresów chunków rezydentnych — nie.
    """
    manifest = _stream_manifest()
    expected = G.streaming_expectations(manifest, 976.180)
    window_lo, window_hi = expected["window"]
    span_lo, span_hi = expected["span"]

    # Zakres chunków rezydentnych wystaje poza okno z OBU stron — bo chunk wchodzi
    # do pamięci w całości. Pierwsza wersja tego testu miała tu `span_hi < window_hi`
    # i padła na własnej asercji: 1754,148 m wobec 1576,180 m. Kierunek nierówności
    # jest właśnie tym, co ten test opisuje, więc pomyłka była w teście, nie w bramce.
    assert span_lo < window_lo, (span_lo, window_lo)
    assert span_hi > window_hi, (span_hi, window_hi)

    # Kotwica na oknie zamiast na zakresie odrzuciłaby ten zdrowy przebieg.
    on_window = G.axis_scene_bbox(AXIS, window_lo, window_hi)
    on_span = G.axis_scene_bbox(AXIS, span_lo, span_hi)
    assert on_window != on_span, "okno i zakres chunków dają ten sam bbox — test nic nie rozróżnia"


def test_shot_gate_predicate_agrees_with_the_streaming_fixture_table():
    """Bramka i `StreamingPlanTests.cs` liczą z tego samego predykatu i manifestu.

    Gdyby bramka wołała własny rachunek okna, mogłaby zgadzać się ze sceną i mijać
    się z implementacją wzorcową jednocześnie.
    """
    manifest = _stream_manifest()
    plans = json.load(open(
        os.path.join(ROOT, "tests", "Game.Tests", "fixtures", "L1_A-streaming-plans.json"),
        encoding="utf-8"))

    checked = 0
    for row in plans:
        if row["heading"] != 1.0 or not (0.0 <= row["chainage_m"] <= manifest["axis_length_m"]):
            continue
        expected = G.streaming_expectations(manifest, row["chainage_m"])
        assert expected["window"] == (row["window_low_m"], row["window_high_m"]), row["chainage_m"]
        assert expected["resident_ids"] == row["resident"], row["chainage_m"]
        checked += 1

    assert checked >= 50, checked
