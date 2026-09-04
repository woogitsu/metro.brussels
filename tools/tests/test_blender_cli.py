#!/usr/bin/env python3
"""Testy `glb_roundtrip.py` i `place_vehicle.py` — modułów, które do 02.09.2026
nie miały żadnych testów.

Audyt mutacyjny: 43 z 43 i 55 z 55 mutantów przeżyło, bo nie importował ich ani
jeden test, ani jeden workflow.

**Co tu jest testowane, a co nie.** Oba moduły robią `import bpy` na poziomie
modułu, więc bez atrapy nie dają się nawet zaimportować. Atrapa poniżej jest
minimalna i celowo NIE udaje Blendera: pozwala tylko dojść do funkcji, które
liczą coś bez silnika — parsowanie argumentów, domyślne wartości, wczytanie osi.
Wszystko, co realnie dotyka scenki (`import_glb`, `local_span`, sam round-trip
i pomiar luzu), weryfikuje Blender w CI — `blender-smoke.yml`, `m7-shell.yml`
i `tunnel-alignment.yml`. Ta sama konwencja co w `test_m7_shell.py`.

Wartość tych testów jest konkretna: domyślne wartości CLI to jedyne, co realnie
dostaje pipeline, a każdy inny test podawał je jawnie w wywołaniu.
"""
import json
import os
import sys
import tempfile
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))


def _stub_blender():
    """Atrapa `bpy` i `mathutils` — tylko tyle, żeby import modułu się udał.

    Nie ma tu emulacji niczego. Każda funkcja, która sięgnie do scenki, wywali
    się na atrapie — i tak ma być: te ścieżki należą do CI z Blenderem, a nie
    do tego pliku.
    """
    if "bpy" not in sys.modules:
        bpy = types.ModuleType("bpy")
        bpy.ops = types.SimpleNamespace()
        bpy.data = types.SimpleNamespace(objects=[])
        bpy.context = types.SimpleNamespace()
        sys.modules["bpy"] = bpy
    if "mathutils" not in sys.modules:
        mathutils = types.ModuleType("mathutils")

        class _Unavailable:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("mathutils dostępne tylko w Blenderze")

        mathutils.Matrix = _Unavailable
        mathutils.Vector = _Unavailable
        sys.modules["mathutils"] = mathutils


_stub_blender()

import glb_report as GRP  # noqa: E402
import glb_roundtrip as GR  # noqa: E402
import place_vehicle as PV  # noqa: E402
import profiles  # noqa: E402


def _with_argv(argv, function):
    """Blender przekazuje argumenty skryptu PO `--`; oba moduły na tym stoją."""
    saved = sys.argv
    sys.argv = argv
    try:
        return function()
    finally:
        sys.argv = saved


# --- glb_roundtrip -------------------------------------------------------------


def test_glb_roundtrip_tolerances_are_pinned():
    """Tolerancje round-tripu to bramka, nie ozdoba.

    0,01 m na bboxie i 10 % na licznikach. Liczniki mają tolerancję, bo eksporter
    glTF dzieli wierzchołki na duplikaty w innej kolejności przy każdym przebiegu:
    ta sama geometria M7 dała 5360 i 5386 wierzchołków po imporcie
    (`tools/visual/compare.py`). Bbox tolerancję ma dziesięć razy luźniejszą niż
    kontrola wizualna — i to jest ŚWIADOMA różnica, nie rozjazd:

    * `compare.GEOMETRY_TOLERANCE_M` = 0,001 m porównuje dwa **pliki metadanych**
      z tego samego generatora, więc mierzy powtarzalność samego generatora;
    * `GRP.TOLERANCE_M` = 0,01 m porównuje bbox **po przejściu przez glTF**, czyli
      po zapisie i odczycie w formacie o skończonej precyzji.

    Wymaganie od round-tripu milimetra byłoby wymaganiem od formatu czegoś, czego
    format nie obiecuje. Ten test przypina obie liczby i ich RELACJĘ, żeby żadna
    nie pojechała po cichu w drugą stronę.

    Progi przeprowadziły się do `glb_report.py` razem z werdyktem, który je czyta.
    Ten test celuje w nowy adres, a nie został usunięty: usunięty test nie pada,
    więc jego brak przeszedłby na zielono i nikt by nie zauważył, że relacja
    między tolerancjami przestała być pilnowana.
    """
    assert GRP.TOLERANCE_M == 0.01
    assert GRP.COUNT_TOLERANCE == 0.10

    sys.path.insert(0, os.path.join(ROOT, "tools", "visual"))
    import compare  # noqa: E402
    assert compare.GEOMETRY_TOLERANCE_M == 0.001
    assert GRP.TOLERANCE_M > compare.GEOMETRY_TOLERANCE_M, (
        "round-trip przez glTF nie może być pilnowany ostrzej niż powtarzalność "
        "samego generatora — to by znaczyło, że wymagamy od formatu więcej, "
        "niż obiecuje")
    assert GRP.TOLERANCE_M <= 10.0 * compare.GEOMETRY_TOLERANCE_M, (
        "luz round-tripu urósł ponad dziesięciokrotność tolerancji generatora — "
        "przy takim progu utrata geometrii przestaje być wykrywalna")
    assert GRP.COUNT_TOLERANCE == compare.GEOMETRY_COUNT_TOLERANCE, (
        "obie kontrole liczą te same wierzchołki i ściany, więc ich tolerancja "
        "licznikowa musi być ta sama")


def test_glb_roundtrip_reads_arguments_after_the_double_dash():
    args = _with_argv(
        ["blender", "--background", "--python", "glb_roundtrip.py", "--", "--in", "build/T.glb"],
        GR.parse_args)
    assert args.inp == "build/T.glb"
    assert args.expect_objects is None
    assert args.expect_metrics is None
    assert args.out is None


def test_glb_roundtrip_requires_an_input_file():
    for argv in (["blender", "--", "--out", "x.json"], ["blender", "--"]):
        try:
            _with_argv(argv, GR.parse_args)
        except SystemExit:
            continue
        raise AssertionError(f"brak --in przeszedł: {argv}")


def test_glb_roundtrip_demands_uv_unless_told_otherwise():
    """Brak UV jest domyślnie błędem. Tunel ich wymaga; skorupa M7 jeszcze nie ma,
    i właśnie dlatego zgoda musi być JAWNA, a nie domyślna."""
    strict = _with_argv(["blender", "--", "--in", "a.glb"], GR.parse_args)
    assert strict.allow_missing_uv is False

    lenient = _with_argv(["blender", "--", "--in", "a.glb", "--allow-missing-uv"], GR.parse_args)
    assert lenient.allow_missing_uv is True


def test_glb_roundtrip_missing_file_stops_before_touching_the_scene():
    """`main()` sprawdza istnienie pliku PRZED pierwszym wywołaniem bpy.

    Kolejność ma znaczenie: gdyby najpierw czyścił scenkę, a potem sprawdzał
    plik, komunikat błędu przychodziłby po zniszczeniu stanu. Atrapa bpy nie ma
    `ops.object`, więc dojście do niej wywala się inaczej niż na SystemExit —
    i to jest dowód, że sprawdzenie pliku było pierwsze.
    """
    missing = os.path.join(tempfile.mkdtemp(), "nie-ma.glb")
    try:
        _with_argv(["blender", "--", "--in", missing], GR.main)
    except SystemExit as error:
        assert missing in str(error), error
    else:
        raise AssertionError("brakujący plik wejściowy przeszedł")


# --- place_vehicle -------------------------------------------------------------


def test_place_vehicle_defaults_are_pinned():
    args = _with_argv(
        ["blender", "--", "--tunnel", "t.glb", "--vehicle", "v.glb",
         "--centerline", "c.json", "--out", "o.json"],
        PV.parse_args)

    assert args.profile == "box_double", args.profile
    assert args.track == 1, args.track
    assert args.chainage == "worst", args.chainage
    assert args.ring_step == PV.DEFAULT_RING_STEP_M
    assert PV.DEFAULT_RING_STEP_M == 5.0
    assert args.report is None
    # Zero znaczy „nie wywracaj się na żadnym luzie". To jest świadomy wybór:
    # próg podaje zadanie, bo najgorszy zmierzony luz w pakiecie A to 0,8999 m
    # i wpisanie go tutaj na sztywno przebazowałoby wszystkie pakiety naraz.
    assert args.min_clearance_m == 0.0, args.min_clearance_m


def test_place_vehicle_ring_step_matches_the_generator():
    """Ta sama krzywa co w generatorze tuneli, inaczej skład jedzie po innej osi."""
    import sweep as SW
    assert PV.DEFAULT_RING_STEP_M == SW.DEFAULT_RING_STEP_M, (
        "osadzenie pojazdu zagęszcza oś innym krokiem niż tunel — "
        "pomiar luzu porównywałby dwie różne geometrie")


def test_place_vehicle_profile_choices_come_from_the_registry():
    """Lista profili nie jest przepisana — jest tą samą listą co w `profiles.py`."""
    for name in profiles.PROFILES:
        args = _with_argv(
            ["blender", "--", "--tunnel", "t.glb", "--vehicle", "v.glb",
             "--centerline", "c.json", "--out", "o.json", "--profile", name],
            PV.parse_args)
        assert args.profile == name

    try:
        _with_argv(
            ["blender", "--", "--tunnel", "t.glb", "--vehicle", "v.glb",
             "--centerline", "c.json", "--out", "o.json", "--profile", "rura_z_sufitu"],
            PV.parse_args)
    except SystemExit:
        pass
    else:
        raise AssertionError("nieznany profil przeszedł")


def test_place_vehicle_requires_every_input_path():
    complete = ["--tunnel", "t.glb", "--vehicle", "v.glb", "--centerline", "c.json",
                "--out", "o.json"]
    for drop in ("--tunnel", "--vehicle", "--centerline", "--out"):
        index = complete.index(drop)
        partial = complete[:index] + complete[index + 2:]
        try:
            _with_argv(["blender", "--"] + partial, PV.parse_args)
        except SystemExit:
            continue
        raise AssertionError(f"brak {drop} przeszedł")


def test_place_vehicle_loads_the_axis_through_the_generator_curve():
    """`load_axis` liczy bez Blendera — zagęszczenie, ramki i kilometraż z `sweep`."""
    axis = {"id": "T", "points": [[i * 15.0, 0.0, 0.0] for i in range(12)]}
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(axis, handle)
    handle.close()
    try:
        document, points, frames, chainages = PV.load_axis(handle.name, PV.DEFAULT_RING_STEP_M)

        assert document["id"] == "T"
        assert len(points) == len(frames) == len(chainages)
        assert len(points) > len(axis["points"]), "krok 5 m ma zagęścić łamaną 15 m"
        assert chainages[0] == 0.0
        assert abs(chainages[-1] - 165.0) < 1e-6, chainages[-1]
        # Kilometraż jest niemalejący — inaczej „chainage" nie znaczy odległości.
        assert all(b >= a for a, b in zip(chainages, chainages[1:]))

        # Krok 0 to tryb wierny: żadnego zagęszczania.
        _, faithful, _, _ = PV.load_axis(handle.name, 0.0)
        assert len(faithful) == len(axis["points"]), len(faithful)
    finally:
        os.unlink(handle.name)
