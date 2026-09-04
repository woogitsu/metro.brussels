#!/usr/bin/env python3
"""Bramki regresji wizualnej sprawdzane NA GRANICY — `compare.py` i `framing.py`.

**Po co ten plik istnieje.** Te dwa moduły są jedynym mechanicznym okiem projektu:
`compare.py` rozstrzyga, czy render różni się od baseline'u, a `framing.py` — czy
kadr w ogóle pokazuje geometrię, czy pustkę. CLAUDE.md §5 mówi wprost, że skrypt bez
błędu potrafi wyprodukować pustą scenę; bramka, która tego nie łapie, usypia mocniej
niż brak bramki.

Przegląd mutacyjny na 737d592 pokazał, że tak właśnie było:

    tools/visual/compare.py    16 z 24 mutacji przeżyło
    tools/visual/framing.py    16 z 22 mutacji przeżyło

Przyczyna była jedna i ta sama w obu modułach: istniejące testy dotykały progów
DALEKO od granicy. Obraz przesunięty o 6 pikseli przekracza wszystkie trzy progi
regresji naraz, płat +-12 m łapie pierścień z zapasem, a bbox przesunięty o 1,5 m
leży setki tolerancji od 1 mm. Takie wejście nie odróżnia `>` od `>=` ani `<=` od `<`,
bo leży po tej samej stronie w obu wariantach. Testy tutaj trafiają w granicę
dokładnie: wartość jest RÓWNA progowi, więc jedna wersja operatora przepuszcza,
a druga odrzuca.

**Pułapka zmiennoprzecinkowa.** `abs((6700.0 + 0.01) - 6700.0)` daje
0,010000000000218 — czyli NAD progiem 0,01. Naiwny test „na granicy" granicy nie
dotyka. Różnica jest dokładna tylko wtedy, gdy jedna strona jest zerem albo gdy próg
jest potęgą dwójki. Każdy test, który tak kombinuje, wyjaśnia to w swoim docstringu.

**Dlaczego osobny plik, a nie dopisek do `test_visual.py`.** Równolegle triażowany
`pngio.py` dopisuje swój blok na końcu `test_visual.py` (PR #149). Oba dopiski
w tym samym miejscu tego samego pliku zderzyłyby się przy scalaniu, a `test_all.py`
i tak zbiera testy przez `glob("test_*.py")`, więc nowy plik wchodzi sam.
"""
import contextlib
import io
import json
import math
import os
import shutil
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "visual"))

import compare  # noqa: E402
import framing  # noqa: E402
import pngio  # noqa: E402

MANIFEST = compare.load_manifest(os.path.join(ROOT, "tools", "visual", "cameras.json"))

#: Mały kadr testowy. Wystarczy, żeby przejść bramkę pustki, a liczy się w ułamku
#: sekundy — `check_image` jest czystym Pythonem i skaluje się z liczbą pikseli.
GW, GH = 40, 24


def _frame(shift=0):
    """Syntetyczny render: tło z gradientem i jaśniejszy prostokąt."""
    pixels = []
    for y in range(GH):
        for x in range(GW):
            inside = (8 + shift) <= x < (24 + shift) and 6 <= y < 18
            value = (0.85 if inside else 0.30) + 0.12 * y / GH
            pixels.append((value, value, value))
    return pixels


def _thresholds():
    return dict(MANIFEST["scene_sets"]["vehicle"]["thresholds"])


def _loose():
    """Progi, przy których ŻADNE kryterium regresji nie może się odezwać."""
    thresholds = _thresholds()
    thresholds.update({"mean_abs_diff": 2.0, "p95_abs_diff": 2.0, "ssim_min": -1.0})
    return thresholds


# --- compare.py: bramka pustej klatki ------------------------------------------


def test_gate_ink_counts_a_pixel_exactly_at_the_background_tolerance():
    """`abs(value - background) > 0.02` — piksel DOKŁADNIE na tolerancji nie jest tuszem.

    Granica jest tu osiągalna tylko dlatego, że jedna strona odejmowania jest zerem:
    tło wypada na 0,0 (99 pikseli czarnych), a jasny piksel ma wartość 0,02, więc
    `abs(0.02 - 0.0)` to dokładnie 0,02 — ten sam double co stała
    `BACKGROUND_TOLERANCE`. Przy tle w dowolnym innym miejscu różnica byłaby
    o kilka ulp obok i test nie dotykałby granicy.

    Obrazu o takich wartościach NIE DA SIĘ zapisać przez `pngio.write_gray`:
    8 bitów daje wielokrotności 1/255, a 0,02 * 255 = 5,1. Dlatego `pngio.Image`
    jest budowany wprost — to zwykła klasa modułu, a `image_stats` przyjmuje
    dowolny obiekt o polach `width`, `height`, `gray`.

    Co to łapie: mutant `>=` policzyłby ten piksel jako tusz i podniósł
    `ink_fraction` z 0,0 do 0,01 — czyli pustą klatkę uznałby za mającą treść.
    """
    assert compare.BACKGROUND_TOLERANCE == 0.02, compare.BACKGROUND_TOLERANCE
    at_boundary = pngio.Image(10, 10, [0.0] * 99 + [0.02])
    stats = compare.image_stats(at_boundary)
    assert stats["background_level"] == 0.0, stats
    assert stats["ink_fraction"] == 0.0, (
        "piksel dokładnie na tolerancji nie jest tuszem", stats)

    # Kontrola w drugą stronę: o jeden ulp dalej piksel JEST już tuszem, więc test
    # wyżej mówi o granicy, a nie o tym, że licznik tuszu w ogóle nie działa.
    above = pngio.Image(10, 10, [0.0] * 99 + [math.nextafter(0.02, 1.0)])
    assert compare.image_stats(above)["ink_fraction"] == 0.01, compare.image_stats(above)


def test_gate_empty_frame_floor_accepts_stats_exactly_equal_to_the_thresholds():
    """Trzy progi pustki są MINIMAMI — wartość równa progowi ma przechodzić.

    Wszystkie trzy człony (`ink_fraction`, `luma_std`, `distinct_levels`) używają
    `>=` i żaden dotychczasowy test nie postawił statystyki dokładnie na progu.
    Granica jest osiągalna wprost, bez sztuczek na liczbach: progi są argumentem
    funkcji, więc podaje się DOKŁADNIE te wartości, które zwróciło `image_stats`
    (już zaokrąglone do 6 miejsc) — po obu stronach porównania stoi ten sam double.

    Co to łapie: każdy z trzech mutantów `>` odrzuciłby kadr leżący równo na progu,
    czyli bramka byłaby ostrzejsza, niż deklaruje manifest. Tuż pod progiem kadr ma
    polec i to sprawdza druga połowa testu — inaczej test przechodziłby też wtedy,
    gdyby bramka przepuszczała wszystko.
    """
    image = pngio.Image(4, 2, [0.0, 0.25, 0.5, 0.75, 1.0, 0.3, 0.6, 0.9])
    stats = compare.image_stats(image)
    exact = {"min_ink_fraction": stats["ink_fraction"],
             "min_luma_std": stats["luma_std"],
             "min_distinct_levels": stats["distinct_levels"]}
    assert compare.empty_frame_reason(stats, exact) is None, (stats, exact)

    for key in exact:
        stricter = dict(exact)
        stricter[key] = math.nextafter(exact[key], math.inf) if key != "min_distinct_levels" \
            else exact[key] + 1
        reason = compare.empty_frame_reason(stats, stricter)
        assert reason is not None and "pusty" in reason, (key, reason)


def test_gate_missing_render_is_reported_as_missing_not_as_a_broken_png():
    """Plik zerowej długości ma polec na `exists`, a nie wywalić dekoder PNG.

    `os.path.getsize(path) == 0` to jedyne miejsce, w którym pusty plik zostaje
    odróżniony od renderu. Bramka musi zwrócić werdykt, bo `run()` zbiera wyniki
    do raportu; wyjątek z `pngio` przerwałby cały przebieg i nie powiedział, KTÓRA
    kamera nie ma pliku.

    Co to łapie: mutant `getsize(path) == 1` przepuściłby pusty plik dalej,
    do `pngio.read_gray`, i zamiast statusu `fail` z czytelnym powodem poleciałby
    `PngError`. Kontrola negatywna: plik jednobajtowy MA wyjść poza tę gałąź
    (jest „obecny", tylko nie jest PNG-iem) — inaczej test nie odróżniałby zera
    od jedynki.
    """
    tmp = tempfile.mkdtemp()
    try:
        empty = os.path.join(tmp, "pusty.png")
        open(empty, "wb").close()
        result = compare.check_image(empty, [GW, GH], _thresholds())
        assert result["checks"]["exists"] is False, result
        assert result["status"] == "fail" and "pust" in result["reason"], result

        one_byte = os.path.join(tmp, "jeden.png")
        with open(one_byte, "wb") as handle:
            handle.write(b"\x89")
        broken = compare.check_image(one_byte, [GW, GH], _thresholds())
        # Ten test PRZEKIEROWANO, a nie usunięto. Do 03.09.2026 wymagał, żeby
        # `check_image` PODNIOSŁO `PngError` — i to było zachowanie, które
        # wywracało cały `run()`, kasując raport z pozostałych kamer. Gwarancja
        # jest ta sama („plik jednobajtowy nie może przejść jako render"), tylko
        # wyrażona statusem, nie wyjątkiem. Usunięcie tego testu przeszłoby na
        # zielono, bo usunięty test nie pada — a wtedy nikt by nie zauważył, że
        # granica między „nie ma pliku" a „plik nie jest PNG-iem" przestała być
        # pilnowana.
        assert broken["checks"]["exists"] is True, broken
        assert broken["checks"]["readable"] is False, broken
        assert broken["status"] == "fail", broken
        assert "nie da się wczytać renderu" in broken["reason"], broken
        # Kontrola negatywna z pierwotnego testu zostaje: plik jednobajtowy MUSI
        # wyjść poza gałąź „pusty", inaczej test nie odróżnia zera od jedynki.
        assert broken["reason"] != result["reason"], (broken, result)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- compare.py: metryki różnicowe ---------------------------------------------


def test_gate_changed_fraction_counts_only_pixels_strictly_over_two_percent():
    """`changed_fraction` liczy piksele z różnicą OSTRO większą niż 0,02.

    Ta metryka nie wchodzi do żadnego werdyktu — trafia wyłącznie do raportu — więc
    nie ruszał jej ani jeden test i przeżywały tu dwie mutacje: operator i sama
    stała progu. Raport z bramki wizualnej jest tym, na co patrzy człowiek, gdy
    bramka jest czerwona; liczba w nim ma znaczyć to, co deklaruje.

    Granica: różnica jest dokładna, bo baseline jest wszędzie zerem
    (`abs(0.02 - 0.0) == 0.02`). Takich wartości nie da się zapisać w 8-bitowym PNG
    (0,02 * 255 = 5,1), więc obrazy powstają jako `pngio.Image` wprost.

    Cztery piksele o różnicach 0,02 / 0,0201 / 0,0199 / 0,0 dają:
      * oryginał (`> 0.02`)      -> 1/4 = 0,25,
      * mutant  (`>= 0.02`)      -> 2/4 = 0,50,
      * mutant  (`> 0.0202`)     -> 0/4 = 0,00.
    Jedna asercja na dokładną wartość rozstrzyga wszystkie trzy przypadki.
    """
    current = pngio.Image(4, 1, [0.02, 0.0201, 0.0199, 0.0])
    baseline = pngio.Image(4, 1, [0.0, 0.0, 0.0, 0.0])
    metrics = compare.diff_metrics(current, baseline)
    assert metrics["changed_fraction"] == 0.25, metrics
    assert metrics["max_abs_diff"] == 0.0201, metrics


def test_gate_metrics_exactly_on_the_thresholds_are_not_a_regression():
    """Trzy progi regresji są ostre: MAE i p95 muszą PRZEKROCZYĆ, SSIM SPAŚĆ PONIŻEJ.

    Dotąd żaden test nie postawił metryki równo na progu — jedyna klatka „różna"
    przekraczała wszystkie trzy progi z ogromnym zapasem. Granica jest tu osiągalna
    bez sztuczek na liczbach: progi są argumentem `check_image`, więc podaje się
    dokładnie te wartości, które policzyło `diff_metrics` (już zaokrąglone do
    8 miejsc). Po obu stronach porównania stoi wtedy ten sam double.

    Każde kryterium badane osobno — pozostałe dwa są wyłączone — bo ta implementacja
    SSIM reaguje na wszystko, co porusza p95, i bez izolacji „fail" nie wskazywałby
    winnego.

    Co to łapie: mutanty `>=`, `>=` i `<=` uznałyby render leżący równo na progu
    za regresję. Kontrola w drugą stronę: o jeden ulp po złej stronie progu render
    MA polec — inaczej test przechodziłby też przy bramce, która nigdy nie zgłasza
    regresji.
    """
    tmp = tempfile.mkdtemp()
    try:
        current = os.path.join(tmp, "c.png")
        baseline = os.path.join(tmp, "b.png")
        pngio.write_rgb(current, GW, GH, _frame(shift=3))
        pngio.write_rgb(baseline, GW, GH, _frame())
        measured = compare.check_image(current, [GW, GH], _loose(), baseline)["metrics"]

        for name, metric, worse in (("mean_abs_diff", "mean_abs_diff", -1.0),
                                    ("p95_abs_diff", "p95_abs_diff", -1.0),
                                    ("ssim_min", "ssim", math.inf)):
            on_edge = _loose()
            on_edge[name] = measured[metric]
            result = compare.check_image(current, [GW, GH], on_edge, baseline)
            assert result["status"] == "pass", (name, measured[metric], result)
            assert result["checks"]["regression"] is True, (name, result)

            over_edge = _loose()
            over_edge[name] = math.nextafter(measured[metric], worse)
            failed = compare.check_image(current, [GW, GH], over_edge, baseline)
            assert failed["status"] == "fail", (name, failed)
            assert failed["checks"]["regression"] is False, (name, failed)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- compare.py: kontrola wymiarowa z metadanych --------------------------------


def _meta(bbox_min=(0.0, -1.35, 0.0), bbox_max=(94.0, 1.35, 3.6),
          vertices=100, faces=50, mesh_objects=6):
    return {
        "manifest_version": MANIFEST["manifest_version"],
        "blender_version": "4.0.2",
        "resolution": [GW, GH],
        "scene": {
            "bbox_min": list(bbox_min),
            "bbox_max": list(bbox_max),
            "size_m": [round(bbox_max[i] - bbox_min[i], 6) for i in range(3)],
            "mesh_objects": mesh_objects,
            "vertices": vertices,
            "faces": faces,
        },
    }


def _meta_file(directory, name, payload):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return path


def test_gate_bbox_delta_exactly_at_the_millimetre_tolerance_still_passes():
    """`abs(d) <= 0.001` — przesunięcie o DOKŁADNIE milimetr mieści się w tolerancji.

    Istniejący test tolerancji milimetrowej używa 0,5 mm i 2 mm, czyli dwóch punktów
    po przeciwnych stronach granicy, ale ani jednego NA niej. Taka para nie odróżnia
    `<=` od `<`.

    Granica jest osiągalna, bo bryła stoi przy zerze: baseline ma `bbox_min[2] = 0.0`,
    a wariant 0,001, więc `round(0.001 - 0.0, 6)` to dokładnie 0,001 — ten sam double
    co `GEOMETRY_TOLERANCE_M`. Gdyby bryła stała np. na wysokości 6700 m, ta sama
    różnica wyszłaby 0,0010000000000218 i leżała NAD progiem.

    `size_m` zmienia się przy tym o dokładnie -0,001, więc obie kontrole leżą na
    granicy naraz i obie muszą przejść.

    Co to łapie: mutant `<` odrzuciłby regenerację różniącą się o równy milimetr,
    czyli bramka byłaby ostrzejsza, niż deklaruje `GEOMETRY_TOLERANCE_M`.
    Kontrola w drugą stronę: jeden ulp powyżej milimetra MA polec.
    """
    assert compare.GEOMETRY_TOLERANCE_M == 0.001, compare.GEOMETRY_TOLERANCE_M
    tmp = tempfile.mkdtemp()
    try:
        base = _meta_file(tmp, "base.json", _meta())
        edge = _meta_file(tmp, "edge.json", _meta(bbox_min=(0.0, -1.35, 0.001)))
        result = compare.check_geometry(edge, base)
        assert result["deltas_m"]["bbox_min"][2] == 0.001, result["deltas_m"]
        assert result["deltas_m"]["size_m"][2] == -0.001, result["deltas_m"]
        assert result["status"] == "pass", result

        over = compare.check_geometry(edge, base,
                                      tolerance=math.nextafter(0.001, -1.0))
        assert over["status"] == "fail" and over["checks"]["bbox_min"] is False, over
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gate_vertex_delta_exactly_at_the_allowed_count_still_passes():
    """`abs(delta) <= allowed` — różnica równa dopuszczalnej mieści się w tolerancji.

    Istniejące testy liczników używają delty 26 przy dopuszczalnej 536 (przechodzi
    z zapasem) i delty 3360 przy tej samej dopuszczalnej (pada z zapasem). Ani jeden
    punkt nie leży NA granicy, więc `<=` i `<` dawały ten sam wynik.

    Granica jest osiągalna dzięki podłodze `max(1.0, base * 0.10)`: dla bazy 5
    wierzchołków iloczyn 0,5 zostaje przycięty do 1,0 — liczby całkowitej, a więc
    dokładnej. Delta 1 leży wtedy równo na dopuszczalnej. Tolerancja produkcyjna
    (10 %) NIE jest podmieniana; test korzysta z tej samej ścieżki co bramka.

    Co to łapie: mutant `<` odrzuciłby przebieg różniący się o jeden wierzchołek —
    a właśnie po to ta tolerancja istnieje, bo eksporter glTF dzieli wierzchołki
    inaczej przy każdym przebiegu. Kontrola w drugą stronę: delta 2 MA polec.
    """
    assert compare.GEOMETRY_COUNT_TOLERANCE == 0.10, compare.GEOMETRY_COUNT_TOLERANCE
    tmp = tempfile.mkdtemp()
    try:
        base = _meta_file(tmp, "base.json", _meta(vertices=5, faces=5))
        edge = _meta_file(tmp, "edge.json", _meta(vertices=6, faces=6))
        result = compare.check_geometry(edge, base)
        assert result["counts"]["vertices"]["allowed_delta"] == 1.0, result["counts"]
        assert result["counts"]["vertices"]["delta"] == 1, result["counts"]
        assert result["status"] == "pass", result

        over = _meta_file(tmp, "over.json", _meta(vertices=7, faces=7))
        beyond = compare.check_geometry(over, base)
        assert beyond["status"] == "fail", beyond
        assert beyond["checks"]["vertices"] is False, beyond["checks"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- compare.py: `main()`, czyli to, co widzi CI --------------------------------


def _cli_fixture(tmp, shift=0):
    """Kompletne wejście dla `compare.main()`: manifest, render, baseline, metadane."""
    manifest = json.loads(json.dumps(MANIFEST))
    manifest["scene_sets"]["vehicle"]["resolution"] = [GW, GH]
    manifest_path = os.path.join(tmp, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle)

    current = os.path.join(tmp, "cur")
    baseline = os.path.join(tmp, "base")
    os.makedirs(current, exist_ok=True)
    os.makedirs(baseline, exist_ok=True)
    pngio.write_rgb(os.path.join(current, "t_side.png"), GW, GH, _frame(shift=shift))
    pngio.write_rgb(os.path.join(baseline, "t_side.png"), GW, GH, _frame())
    _meta_file(current, "t_metadata.json", _meta())
    _meta_file(baseline, "t_metadata.json", _meta())
    return manifest_path, current, baseline


def _run_cli(argv):
    """Uruchamia `compare.main()` z podanym `argv`; zwraca (kod wyjścia, stdout)."""
    saved = sys.argv
    buffer = io.StringIO()
    try:
        sys.argv = ["compare.py"] + argv
        with contextlib.redirect_stdout(buffer):
            code = compare.main()
    finally:
        sys.argv = saved
    return code, buffer.getvalue()


def test_gate_cli_returns_zero_and_counts_every_entry_as_passed():
    """Podsumowanie i kod wyjścia `main()` — czyli JEDYNE, co widzi CI.

    Cała funkcja `main()` nie była wykonywana przez żaden test: cztery mutacje
    w niej przeżyły, w tym `report["status"] == "pass"` sterujące kodem wyjścia.
    Bramka, która zawsze kończy się zerem, jest zielona niezależnie od renderów.

    Sprawdzane są obie strony bramki naraz — przebieg zgodny z baseline musi dać
    kod 0 i podsumowanie bez ani jednego `fail`, a ten sam przebieg z przesuniętym
    obiektem kod 1 i dokładnie jeden `fail`.

    Co to łapie:
      * `status == "fail"`         -> `!=`: zgodny przebieg trafiłby w całości
        na listę „padło", raport wyszedłby `fail`, kod 1;
      * `status == "new-baseline"` -> `!=`: jak wyżej, przez `fresh`;
      * `status == "pass"`         -> `!=`: licznik `pass` pokazałby 0 zamiast 2;
      * `report["status"] == "pass"` -> `!=`: kody wyjścia zamieniłyby się miejscami.
    """
    tmp = tempfile.mkdtemp()
    try:
        manifest, current, baseline = _cli_fixture(tmp)
        out = os.path.join(tmp, "raport.json")
        argv = ["--manifest", manifest, "--set", "vehicle", "--current", current,
                "--prefix", "t", "--baseline", baseline, "--cameras", "side",
                "--out", out]

        code, printed = _run_cli(argv)
        with open(out, encoding="utf-8") as handle:
            report = json.load(handle)
        assert code == 0, (code, printed)
        assert report["status"] == "pass", report["status"]
        assert report["summary"] == {"total": 2, "pass": 2, "fail": 0,
                                     "new_baseline": 0}, report["summary"]

        # Kontrola negatywna: ten sam przebieg z przesuniętym obiektem.
        pngio.write_rgb(os.path.join(current, "t_side.png"), GW, GH, _frame(shift=5))
        code, printed = _run_cli(argv)
        with open(out, encoding="utf-8") as handle:
            report = json.load(handle)
        assert code == 1, (code, printed)
        assert report["summary"] == {"total": 2, "pass": 1, "fail": 1,
                                     "new_baseline": 0}, report["summary"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gate_cli_treats_a_missing_baseline_as_failure_unless_allowed():
    """Brak baseline'u to `new-baseline`, a ten bez jawnej zgody kończy się kodem 1.

    Druga połowa polityki baseline'u: `test_visual.py` sprawdza, że `run()` nadaje
    status `new-baseline`, ale nikt nie sprawdzał, co z tym statusem robi `main()`.
    A robi rzecz najważniejszą — decyduje, czy CI jest zielone.

    Co to łapie: mutant `status != "new-baseline"` policzyłby świeży przebieg jako
    zerowy zbiór `fresh` i przepuścił brak baseline'u bez `--allow-new-baseline`.
    """
    tmp = tempfile.mkdtemp()
    try:
        manifest, current, _ = _cli_fixture(tmp)
        argv = ["--manifest", manifest, "--set", "vehicle", "--current", current,
                "--prefix", "t", "--cameras", "side"]
        code, printed = _run_cli(argv)
        assert code == 1, (code, printed)
        assert "new-baseline" in printed, printed

        allowed, printed = _run_cli(argv + ["--allow-new-baseline"])
        assert allowed == 0, (allowed, printed)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- framing.py: baza kamery ----------------------------------------------------


def test_gate_norm_rejects_only_vectors_shorter_than_the_epsilon():
    """`length < 1e-12` — wektor o długości DOKŁADNIE 1e-12 ma jeszcze kierunek.

    Granica jest tu osiągalna wprost: `sqrt((1e-12)**2)` daje bit w bit `1e-12`
    (sprawdzone; pierwiastek jest poprawnie zaokrąglony, a podniesienie do kwadratu
    i z powrotem nie gubi tu ani jednego ulp). Nie trzeba więc żadnej podmiany progu.

    Co to łapie:
      * mutant `<=`        odrzuciłby wektor równy progowi,
      * mutant `< 1.01e-12` odrzuciłby go tak samo.
    Jedna asercja rozstrzyga obie. Kontrola w drugą stronę: wektor krótszy
    (i wektor zerowy) MUSZĄ dać `ValueError` — inaczej test przechodziłby też
    wtedy, gdyby strażnik zniknął zupełnie.
    """
    assert math.sqrt(sum(c * c for c in (1e-12, 0.0, 0.0))) == 1e-12, "granica nieosiągalna"
    assert framing._norm((1e-12, 0.0, 0.0)) == (1.0, 0.0, 0.0)

    for shorter in ((math.nextafter(1e-12, 0.0), 0.0, 0.0), (0.0, 0.0, 0.0)):
        try:
            framing._norm(shorter)
        except ValueError:
            continue
        raise AssertionError(f"wektor {shorter} nie ma kierunku, a przeszedł")


def test_gate_camera_basis_keeps_world_up_exactly_at_the_parallel_epsilon():
    """`abs(dot) > 0.995` — kierunek DOKŁADNIE na progu jeszcze nie jest pionowy.

    Ten warunek wybiera zapasowy wektor „góry" dla kamer patrzących niemal pionowo
    (`top`, `plan`). Wybór jest binarny i całkowicie zmienia obrót kadru: przy
    `world_up = (0,0,1)` kamera dostaje `right = (0,-1,0)`, przy podmienionym
    `(0,1,0)` — `right = (-0.995, 0, 0.0999)`. Klatka jest wtedy obrócona, a różnica
    względem baseline'u ogromna, więc pomyłka o jeden ulp na tej granicy wywraca
    bramkę bez zmiany geometrii.

    Granica jest osiągalna wprost i BEZ podmieniania stałej: dla kierunku
    `(sqrt(1 - 0.995**2), 0, 0.995)` normalizacja zwraca składową Z równą bit w bit
    `0.995` — czyli dokładnie `UP_PARALLEL_EPS`. (Sprawdzone; nie jest to regułą,
    dla skali 10x ta sama konstrukcja daje 0,9949999999999999.)

    Co to łapie: mutant `>=` przełączyłby `world_up` już na progu i obrócił kadr.
    Kontrola w drugą stronę: kierunek jeden ulp WYŻEJ ma przełączyć bazę.
    """
    assert framing.UP_PARALLEL_EPS == 0.995, framing.UP_PARALLEL_EPS
    flat = math.sqrt(1.0 - 0.995 ** 2)
    right, up, forward = framing.camera_basis((flat, 0.0, 0.995))
    assert forward[2] == framing.UP_PARALLEL_EPS, ("granica nieosiągalna", forward)
    assert right == (0.0, -1.0, 0.0), right
    assert abs(up[2] - flat) < 1e-12, up

    steeper = math.nextafter(0.995, 1.0)
    right2, _, forward2 = framing.camera_basis((math.sqrt(1.0 - steeper ** 2), 0.0, steeper))
    assert forward2[2] > framing.UP_PARALLEL_EPS, forward2
    assert right2 != right, ("powyżej progu baza MA się przełączyć", right2)


def test_gate_fov_is_the_same_on_both_sides_of_the_square_resolution():
    """Kadr kwadratowy: obie gałęzie `res_x >= res_y` dają IDENTYCZNY sensor.

    Ten test nie zabija mutanta `>` — i nie może, bo nie ma czego zabić. Dla
    `res_x == res_y` gałąź „pozioma" liczy `sensor_y = 36 * n / n = 36`, a gałąź
    „pionowa" `sensor_x = 36 * n / n = 36`; wynik jest ten sam co do bitu.
    Utrwalamy to jako fakt, żeby następny przegląd mutacyjny nie musiał tego
    odkrywać po raz drugi, i żeby zmiana, która uczyni gałęzie NIErównoważnymi,
    zapaliła się tutaj.

    Przy okazji sprawdzana jest właściwa treść funkcji: 36 mm siada na DŁUŻSZYM
    boku, więc kadr poziomy ma szerszy kąt w poziomie, a pionowy w pionie.
    """
    square = framing.fov(50.0, 512, 512)
    assert square[0] == square[1], square

    wide = framing.fov(50.0, 1920, 1080)
    tall = framing.fov(50.0, 1080, 1920)
    assert wide[0] > wide[1], wide
    assert tall[1] > tall[0], tall
    assert wide[0] == tall[1] and wide[1] == tall[0], (wide, tall)


# --- framing.py: płat przekroju -------------------------------------------------


def _slab_spec(**extra):
    spec = {"id": "section", "projection": "ORTHO", "fit": "slab",
            "slab_thickness_m": 10.0, "direction": [1.0, 0.0, 0.0], "margin": 1.0,
            "anchor": {"mode": "named", "name": "cut"}}
    spec.update(extra)
    return spec


SLAB_BMIN, SLAB_BMAX = (0.0, -50.0, -50.0), (100.0, 50.0, 50.0)
SLAB_ANCHOR = {"cut": [0.0, 0.0, 0.0]}


def test_gate_slab_keeps_a_point_exactly_at_its_half_thickness():
    """`abs(dot(offset, forward)) > thickness` — punkt równo na krawędzi płata JEST w płacie.

    Płat rośnie podwojeniami, dopóki nie złapie geometrii, i mówi w metadanych,
    o ile urósł. Punkt leżący dokładnie na deklarowanej grubości musi wystarczyć,
    żeby nie rósł wcale — inaczej `slab_thickness_used_m` w `visual-metadata.json`
    kłamie o tym, jak szeroki wycinek trasy naprawdę widać w kadrze.

    Granica jest osiągalna wprost, bo kotwica stoi w zerze: punkt o X = 10,0 daje
    `dot(offset, forward)` równe dokładnie 10,0, czyli `slab_thickness_m`.

    Co to łapie: mutant `>=` wyrzuciłby ten punkt z płata, płat urósłby do 20 m
    i metadane zaraportowałyby dwukrotnie szerszy wycinek, niż wynika z manifestu.
    Kontrola w drugą stronę: punkt jeden ulp dalej MA wymusić wzrost płata.
    """
    on_edge = framing.solve_camera(
        _slab_spec(), SLAB_BMIN, SLAB_BMAX, 100, 100,
        named_anchors=SLAB_ANCHOR, points=[(10.0, -3.0, 4.0), (10.0, 3.0, -4.0)])
    assert on_edge["fit_fallback"] is False, on_edge
    assert on_edge["slab_thickness_used_m"] == 10.0, on_edge

    just_outside = math.nextafter(10.0, math.inf)
    grown = framing.solve_camera(
        _slab_spec(), SLAB_BMIN, SLAB_BMAX, 100, 100,
        named_anchors=SLAB_ANCHOR,
        points=[(just_outside, -3.0, 4.0), (just_outside, 3.0, -4.0)])
    assert grown["slab_thickness_used_m"] == 20.0, grown


def test_gate_slab_keeps_a_point_exactly_on_its_radius():
    """`r**2 + u**2 <= radius**2` — punkt równo na promieniu należy do przekroju.

    Promień odcina drugą stronę zawracającej trasy: bez niego kadr formalnie
    „znajduje geometrię", a pokazuje pustkę. Odcinać ma jednak to, co JEST dalej
    niż promień, a nie to, co leży równo na nim — inaczej realny przekrój tunelu
    o półszerokości równej deklarowanemu promieniowi wypadłby z kadru w całości.

    Granica jest osiągalna dokładnie, bo trójka jest pitagorejska: dla bazy kamery
    przy kierunku `(1,0,0)` (`right = (0,-1,0)`, `up = (0,0,1)`) punkt
    `(0, -3, 4)` daje `3**2 + 4**2 = 25`, a `radius**2` to `5.0**2 = 25.0`.
    Wszystkie te liczby są w double dokładne, więc obie strony są równe co do bitu.

    Co to łapie: mutant `<` wyrzuciłby punkt z płata; płat rósłby przez sześć
    podwojeń (promień nie rośnie razem z nim), aż kadr spadłby na `fit_fallback`,
    czyli na bbox całego chunka. Kontrola w drugą stronę: punkt jeden ulp dalej
    MA wypaść i dać właśnie taki fallback.
    """
    right, up, forward = framing.camera_basis((1.0, 0.0, 0.0))
    assert (right, up, forward) == ((0.0, -1.0, 0.0), (-0.0, 0.0, 1.0), (1.0, 0.0, 0.0))

    on_edge = framing.solve_camera(
        _slab_spec(slab_radius_m=5.0), SLAB_BMIN, SLAB_BMAX, 100, 100,
        named_anchors=SLAB_ANCHOR, points=[(0.0, -3.0, 4.0)])
    assert on_edge["fit_fallback"] is False, on_edge
    assert on_edge["anchor_shift_right_up"] == (3.0, 4.0), on_edge

    outside = framing.solve_camera(
        _slab_spec(slab_radius_m=math.nextafter(5.0, 0.0)),
        SLAB_BMIN, SLAB_BMAX, 100, 100,
        named_anchors=SLAB_ANCHOR, points=[(0.0, -3.0, 4.0)])
    assert outside["fit_fallback"] is True, outside


# --- framing.py: płaszczyzna bliska --------------------------------------------


def test_gate_near_clip_switches_exactly_at_twenty_centimetres():
    """`near > 0.2` — geometria równo 20 cm przed kamerą idzie gałęzią „blisko".

    Płaszczyzna bliska decyduje, czy kamera we wnętrzu tunelu widzi ścianę tuż
    przed sobą, czy przecina ją i pokazuje pustkę. Gałęzie dają tu wartości
    różniące się o rząd wielkości (0,1 m kontra 0,01 m), więc pomyłka na tej
    granicy jest widoczna w kadrze.

    Granica jest osiągalna wprost, bo kamera `place_at_anchor` stoi w kotwicy
    (`distance = 0.0`), a `near = distance + depth_min`. Przy kotwicy w zerze
    i bryle zaczynającej się na X = 0,2 wychodzi `0.0 + 0.2`, czyli bit w bit
    literał `0.2` z kodu bramki.

    Co to łapie:
      * mutant `>=`     wziąłby gałąź „daleko" i dał `clip_start` 0,01 zamiast 0,1;
      * mutant `> 0.202` przy `near = 0.201` zrobiłby to samo na odwrót — dlatego
        drugi punkt pomiarowy leży w przedziale (0,2; 0,202].
    """
    spec = {"id": "eye", "projection": "PERSP", "place_at_anchor": True,
            "anchor": {"mode": "named", "name": "eye"},
            "aim": {"mode": "named", "name": "target"}, "lens": 50.0}
    anchors = {"eye": [0.0, 0.0, 0.0], "target": [10.0, 0.0, 0.0]}

    def clip_start(x_min):
        solved = framing.solve_camera(spec, (x_min, -1.0, -1.0), (5.0, 1.0, 1.0),
                                      100, 100, anchors)
        assert solved["distance_m"] == 0.0, solved
        return solved["clip_start"]

    assert clip_start(0.2) == 0.1, "near == 0.2 to jeszcze gałąź `blisko`"
    assert clip_start(0.201) == 0.01, "near tuż nad progiem to już gałąź `daleko`"
    assert clip_start(0.19) == 0.095, "gałąź `blisko` liczy near * 0.5"


# --- framing.py: widoczność narożników ------------------------------------------


def _cam(projection, **extra):
    """Kamera złożona ręcznie: prosta baza w osiach świata, kadr 100x100.

    `corner_visibility` czyta wyłącznie słownik, więc nie trzeba przepuszczać
    wejścia przez `solve_camera` — a dzięki temu narożniki da się postawić
    DOKŁADNIE na krawędzi kadru, zamiast tam, gdzie wypadną z kadrowania bboxa.
    """
    cam = {"right": [0.0, 1.0, 0.0], "up": [0.0, 0.0, 1.0],
           "direction": [1.0, 0.0, 0.0], "location": [0.0, 0.0, 0.0],
           "resolution": [100, 100], "projection": projection}
    cam.update(extra)
    return cam


def test_gate_ortho_visibility_counts_corners_exactly_on_the_frame_edge():
    """Kadr ortho: narożnik DOKŁADNIE na krawędzi jest w kadrze, przed kamerą — nie.

    `corner_visibility` jest miarą, na której stoją testy kadrowania („czy kamera
    obejmuje całą bryłę"). Jeśli sama miara myli się o krawędź, wszystkie testy
    kadrowania mierzą coś innego, niż deklarują.

    Granica jest osiągalna dokładnie, bo `ortho_scale` przekłada się na połowę
    kadru zwykłym dzieleniem przez potęgi dziesiątki bez reszty: dla `ortho_scale`
    4,0 i kadru 100x100 połowa kadru to 2,0. Narożniki stoją na `y = +-2.0`
    i `z = +-2.0`, czyli równo na `half_w` i `half_h`.

    Co to łapie (trzy mutacje jedną asercją, bo każda zmienia wynik inaczej):
      * `abs(r) <= half_w` -> `<`  : 1,0 spada do 0,0;
      * `abs(u) <= half_h` -> `<`  : 1,0 spada do 0,0;
      * `d > 0` -> `d > 1`         : 1,0 spada do 0,5 (ściana bliższa ma d = 1,0).
    """
    cam = _cam("ORTHO", ortho_scale=4.0)
    assert framing.corner_visibility(cam, (1.0, -2.0, -2.0), (2.0, 2.0, 2.0)) == 1.0

    outside = math.nextafter(2.0, math.inf)
    assert framing.corner_visibility(cam, (1.0, -outside, -2.0), (2.0, outside, 2.0)) == 0.0
    assert framing.corner_visibility(cam, (1.0, -2.0, -outside), (2.0, 2.0, outside)) == 0.0


def test_gate_ortho_visibility_drops_corners_exactly_in_the_camera_plane():
    """Kadr ortho: `d > 0` — narożnik w płaszczyźnie kamery jest ZA nią, nie w kadrze.

    Osobny przypadek, bo test wyżej ma wszystkie narożniki przed kamerą i nie
    odróżnia `>` od `>=`. Bryła rozpięta od X = 0 (czyli dotykająca kamery) ma
    cztery narożniki dokładnie w płaszczyźnie kamery; te cztery nie są widoczne.

    Co to łapie: mutant `d >= 0` policzyłby je jako widoczne i podniósł wynik
    z 0,5 do 1,0 — czyli uznałby za „w pełni skadrowaną" bryłę, którą kamera
    przecina.
    """
    cam = _cam("ORTHO", ortho_scale=4.0)
    assert framing.corner_visibility(cam, (0.0, -1.0, -1.0), (3.0, 1.0, 1.0)) == 0.5


def test_gate_perspective_visibility_skips_corners_exactly_at_the_depth_epsilon():
    """Kadr perspektywiczny: `d <= 1e-9` — punkt równo na epsilonie jest odrzucany.

    Ten strażnik chroni dzielenie przez głębokość bliską zeru. Ma odrzucać punkt
    LEŻĄCY na epsilonie, a przepuszczać dopiero to, co jest dalej.

    Granica jest osiągalna wprost: bryła zdegenerowana do punktu na X = 1e-9 daje
    wszystkim ośmiu narożnikom `d` równe bit w bit literałowi `1e-9` z bramki
    (kamera stoi w zerze, więc odejmowanie jest dokładne).

    Co to łapie:
      * mutant `<`         przepuściłby narożniki równo na epsilonie: 0,0 -> 1,0;
      * mutant `<= 1.01e-9` odrzuciłby narożniki na 1,005e-9, czyli już poza
        epsilonem: 1,0 -> 0,0. Dlatego drugi punkt pomiarowy leży w przedziale
        (1e-9; 1,01e-9].
    """
    cam = _cam("PERSP", fov_x_deg=90.0, fov_y_deg=90.0)
    assert framing.corner_visibility(cam, (1e-9, 0.0, 0.0), (1e-9, 0.0, 0.0)) == 0.0
    assert framing.corner_visibility(cam, (1.005e-9, 0.0, 0.0), (1.005e-9, 0.0, 0.0)) == 1.0


def test_gate_perspective_visibility_counts_corners_exactly_on_the_frustum_wall():
    """Kadr perspektywiczny: narożnik DOKŁADNIE na ścianie ostrosłupa jest widoczny.

    Granica jest tu osiągalna tylko dlatego, że test liczy limit TYM SAMYM
    wyrażeniem co bramka — `d * math.tan(math.radians(fov)/2)` — zamiast wpisywać
    jego wartość dziesiętnie. Wprost się nie da: `tan(radians(90)/2)` to
    0,9999999999999999, a nie 1,0, więc „narożnik na 45 stopniach" wpisany jako
    okrągła liczba leżałby o kilka ulp obok ściany. Kamera stoi w zerze, więc
    `dot(rel, right)` zwraca współrzędną narożnika bez straty bitu i obie strony
    porównania są równe co do bitu.

    Co to łapie: dwa mutanty `<` (osobno dla poziomu i dla pionu) obcięłyby
    narożniki leżące równo na krawędzi kadru — 1,0 spada do 0,0. Kontrola
    w drugą stronę: jeden ulp poza ścianą MA wypaść z kadru.
    """
    cam = _cam("PERSP", fov_x_deg=90.0, fov_y_deg=90.0)
    depth = 2.0
    limit_x = depth * math.tan(math.radians(cam["fov_x_deg"]) / 2.0)
    limit_y = depth * math.tan(math.radians(cam["fov_y_deg"]) / 2.0)

    assert framing.corner_visibility(
        cam, (depth, -limit_x, 0.0), (depth, limit_x, 0.0)) == 1.0
    assert framing.corner_visibility(
        cam, (depth, 0.0, -limit_y), (depth, 0.0, limit_y)) == 1.0

    over_x = math.nextafter(limit_x, math.inf)
    over_y = math.nextafter(limit_y, math.inf)
    assert framing.corner_visibility(
        cam, (depth, -over_x, 0.0), (depth, over_x, 0.0)) == 0.0
    assert framing.corner_visibility(
        cam, (depth, 0.0, -over_y), (depth, 0.0, over_y)) == 0.0


def test_gate_one_broken_frame_does_not_erase_the_report_for_the_others():
    """Sedno znaleziska 3: `run()` musi opisać WSZYSTKIE kamery, nie paść na pierwszej.

    Do 03.09.2026 `check_image` puszczało `PngError` w górę, więc jeden uszkodzony
    plik wywracał cały `run()` — raport z pozostałych kamer nie powstawał, a komunikat
    nie mówił nawet, o którą kamerę chodzi, bo `camera` dokłada `run()` DOPIERO po
    powrocie z `check_image`.

    Ten test podstawia jedną kamerę z plikiem, który nie jest PNG-iem, i wymaga:
    wpisu dla każdej kamery, statusu `fail` dokładnie na tej jednej, i nazwy kamery
    przy tym wpisie. Bez tego naprawa jest niesprawdzalna — samo „nie leci wyjątek"
    nie mówi, że pozostałe kamery zostały opisane.
    """
    tmp = tempfile.mkdtemp()
    try:
        current = os.path.join(tmp, "cur")
        os.makedirs(current)
        manifest = json.loads(json.dumps(MANIFEST))
        set_name, prefix = "vehicle", "t"
        manifest["scene_sets"][set_name]["resolution"] = [GW, GH]
        cameras = [c["id"] for c in manifest["scene_sets"][set_name]["cameras"]]
        assert len(cameras) >= 2, "test wymaga zestawu z więcej niż jedną kamerą"

        # Wszystkie kamery dostają poprawny render, jedna dostaje śmieci.
        for camera_id in cameras:
            pngio.write_rgb(os.path.join(current, f"{prefix}_{camera_id}.png"),
                            GW, GH, _frame())
        _meta_file(current, f"{prefix}_metadata.json", _meta())
        broken_id = cameras[0]
        with open(os.path.join(current, f"{prefix}_{broken_id}.png"), "wb") as handle:
            handle.write(b"\x89PNG-to-nie-jest")

        report = compare.run(manifest, set_name, current, prefix, None, None)

        assert len(report["images"]) == len(cameras), report["images"]
        by_camera = {entry["camera"]: entry for entry in report["images"]}
        assert sorted(by_camera) == sorted(cameras), by_camera

        assert by_camera[broken_id]["status"] == "fail", by_camera[broken_id]
        assert "nie da się wczytać renderu" in by_camera[broken_id]["reason"]
        for camera_id in cameras[1:]:
            assert by_camera[camera_id]["status"] != "fail", by_camera[camera_id]
            assert "metrics" in by_camera[camera_id] and by_camera[camera_id]["metrics"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
