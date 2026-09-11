#!/usr/bin/env python3
"""Testy manifestu, wariantu i bramki akceptacji generatora tunelu.

Ten plik istnieje z powodu, który warto zapisać. Do 03.09.2026 cała ta logika
mieszkała w `tunnel_sweep.py` — module, który importuje `bpy`, więc nie dawał się
zaimportować z `test_all.py`. Przemiatanie mutacji pokazało tam 35 mutacji i 35
ocalałych: 100 % przeżywalności, nie dlatego, że kod był zły, tylko dlatego, że
NIE ISTNIAŁA droga, którą test mógłby go dotknąć. Wyciągnięcie logiki do
`tunnel_manifest.py` otwiera tę drogę; ten plik z niej korzysta.

Każdy test bramki ma kontrolę negatywną: sprawdzam nie tylko, że zdrowe wejście
przechodzi, ale że wejście zepsute w JEDNYM miejscu daje DOKŁADNIE JEDEN problem.
Bramka, która przepuszcza wszystko, przechodzi połowę testów napisanych naiwnie
(`docs/06-worked-example.md`).

Progi są sprawdzane NA GRANICY, nie „gdzieś obok": wartość równa progowi ma
przechodzić albo padać zgodnie z tym, co napisane w kodzie, bo tylko taki test
odróżnia `>` od `>=`.

Agregaty (`lod_levels_header`, `lod_metrics`) dostają ręcznie złożone `records`
o różnych liczbach na każdym poziomie — same sumują, a geometrii, z której te
liczby powstają, pilnuje `test_lod.py`. Siatki do kontroli szwów i normalnych
są za to prawdziwe, z `sweep.sweep` na prostej osi.
"""
import hashlib
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import lod as LD  # noqa: E402
import profiles as PR  # noqa: E402
import sweep as SW  # noqa: E402
import tunnel_manifest as TM  # noqa: E402

BOX = PR.profile_points("box_double")


def _healthy_metrics():
    """Wynik, który bramka ma przepuścić bez jednego słowa."""
    return {
        "vertices": 1200, "faces": 600,
        "chunk_max_gap_m": 0.0,
        "stations_split": [],
        "outward_faces": 0, "degenerate_faces": 0, "non_finite_vertices": 0,
        "frame_twist_deg": 0.4,
        "chunk_length_sum_m": 6700.0, "axis_length_m": 6700.0,
        "lod_outward_faces": 0, "lod_degenerate_faces": 0, "lod_non_finite_vertices": 0,
        "lod_max_gap_any_m": 0.0,
        "collision_max_gap_m": 0.0,
        "collision_outward_faces": 0, "collision_degenerate_faces": 0,
        "collision_non_finite_vertices": 0,
        "collision_closed": True,
        "collision_min_wall_margin_m": 0.05,
        "collision_min_gauge_margin_m": 0.65,
    }


def _broken(**changes):
    metrics = _healthy_metrics()
    metrics.update(changes)
    return TM.geometry_problems(metrics, {"chunks": []})


# --- progi ------------------------------------------------------------------

def test_thresholds_have_the_values_the_gate_was_designed_around():
    """Progi przypięte LICZBĄ, nie odwołaniem do stałej — i to jest cel.

    Reszta testów w tym pliku porównuje z `TM.MAX_GAP_M` i spółką, bo tak się je
    czyta. Ale to znaczy, że podmiana samej stałej przeszłaby przez nie bez śladu.
    Przemiatanie mutacyjne też jej nie złapie: mutuje literały stojące
    W PORÓWNANIACH, a te stoją w przypisaniach. Ten test jest jedynym, co je pilnuje.

    Skąd te liczby: 1 mm to próg szczelności szwu z T-210 (poniżej niej dziura
    jest mniejsza niż błąd zapisu float32 w GLB); 5° to dopuszczalny skręt ramki,
    powyżej którego zamiatanie zaczyna skręcać profil; 1 cm to tolerancja sumy
    długości chunków wobec chainage; 2 punkty to minimum, na którym da się
    wyznaczyć kierunek.
    """
    assert TM.MAX_GAP_M == 0.001, TM.MAX_GAP_M
    assert TM.MAX_TWIST_DEG == 5.0, TM.MAX_TWIST_DEG
    assert TM.CHUNK_LENGTH_TOLERANCE_M == 0.01, TM.CHUNK_LENGTH_TOLERANCE_M
    assert TM.MIN_AXIS_POINTS == 2, TM.MIN_AXIS_POINTS


# --- oś: ile punktów wystarczy ---------------------------------------------

def test_axis_needs_two_points_exactly_at_the_boundary():
    assert TM.enough_points([(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)])
    assert not TM.enough_points([(0.0, 0.0, 0.0)])
    assert not TM.enough_points([])


def test_axis_of_three_points_is_still_fine():
    assert TM.enough_points([(0.0, 0.0, 0.0)] * 3)


# --- wariant ----------------------------------------------------------------

def test_auto_without_vertical_profile_is_flat_preview_and_says_so_in_the_name():
    plan = TM.variant_plan("auto", "none", "L1_A")
    assert plan["variant"] == "flat-preview", plan
    assert plan["production_ready"] is False, plan
    assert plan["scene_name"] == "L1_A_flat_preview", plan


def test_auto_with_modelled_vertical_profile_is_production_under_the_bare_name():
    plan = TM.variant_plan("auto", "modelled", "L1_A")
    assert plan["variant"] == "production", plan
    assert plan["production_ready"] is True, plan
    assert plan["scene_name"] == "L1_A", plan


def test_explicit_production_without_vertical_profile_is_refused_not_downgraded():
    try:
        TM.variant_plan("production", "none", "L1_A")
    except ValueError as err:
        assert "T-112" in str(err), err
    else:
        raise AssertionError("wariant production przeszedł na osi bez profilu pionowego")


def test_explicit_production_with_vertical_profile_passes():
    plan = TM.variant_plan("production", "modelled", "L1_A")
    assert plan["variant"] == "production" and plan["scene_name"] == "L1_A", plan


def test_explicit_flat_preview_stays_flat_even_when_the_axis_could_do_more():
    plan = TM.variant_plan("flat-preview", "modelled", "L1_A")
    assert plan["variant"] == "flat-preview", plan
    assert plan["production_ready"] is False, plan
    assert plan["scene_name"] == "L1_A_flat_preview", plan


def test_auto_na_osi_czastkowej_daje_partial_vertical_i_mowi_to_w_nazwie():
    """6.D120: trzeci stan, nie drugi.

    Oś z rzędnymi na 7 % długości nie jest ani `modelled` (bo 93 % jest wypełniaczem),
    ani `not_modelled` (bo te 7 % jest prawdziwe). Nazwa sceny niesie to w sobie tak
    samo, jak `flat-preview` niesie swoją płaskość.
    """
    plan = TM.variant_plan("auto", "partial", "L1_A")
    assert plan["variant"] == "partial-vertical", plan
    assert plan["production_ready"] is False, (
        "7 % długości ze rzędnymi nie czyni geometrii docelową")
    assert plan["scene_name"] == "L1_A_partial_vertical", plan


def test_production_na_osi_czastkowej_jest_ODMOWA():
    """Oś `partial` stoi po tej samej stronie co `not_modelled` i to jest treść."""
    try:
        TM.variant_plan("production", "partial", "L1_A")
    except ValueError as err:
        assert "T-112" in str(err), err
    else:
        raise AssertionError("wariant production przeszedł na osi cząstkowej")


def test_partial_vertical_na_osi_bez_profilu_jest_ODMOWA():
    """Wariant nie może twierdzić o osi czegoś, czego oś nie mówi.

    Bez tej odmowy `--variant partial-vertical` na osi płaskiej dałby scenę
    o nazwie obiecującej rzędne, których w punktach nie ma — czyli nazwę mówiącą
    co innego niż geometria.
    """
    for status in ("not_modelled", "none", "modelled"):
        try:
            TM.variant_plan("partial-vertical", status, "L1_A")
        except ValueError as err:
            assert "partial" in str(err), err
        else:
            raise AssertionError(f"partial-vertical przeszedł na osi `{status}`")


def test_nieznany_wariant_jest_ODMOWA_a_nie_cichym_sufiksem():
    """Literówka w nazwie wariantu ma się zatrzymać, a nie zbudować scenę bez sufiksu."""
    try:
        TM.variant_plan("partial_vertical", "partial", "L1_A")
    except ValueError as err:
        assert "nieznany wariant" in str(err), err
    else:
        raise AssertionError("wariant spoza zbioru został przyjęty")


def test_tylko_production_nie_ma_sufiksu():
    """Scena bez sufiksu znaczy geometrię docelową — i tylko ona."""
    bez_sufiksu = [w for w, s in TM.SUFIKSY_WARIANTOW.items() if not s]
    assert bez_sufiksu == ["production"], TM.SUFIKSY_WARIANTOW
    assert set(TM.WARIANT_DLA_STATUSU.values()) <= set(TM.SUFIKSY_WARIANTOW), (
        "status osi wskazuje wariant, którego nie ma w tabeli sufiksów")


# --- bramka akceptacji: zdrowe wejście --------------------------------------

def test_healthy_result_has_no_problems():
    assert TM.geometry_problems(_healthy_metrics(), {"chunks": []}) == []


def test_healthy_result_has_no_problems_without_a_manifest_either():
    assert TM.geometry_problems(_healthy_metrics(), None) == []


def test_without_a_manifest_lod_and_collision_checks_are_skipped():
    """Bez `--chunk-dir` LOD-ów i kolizji NIE MA — nie wolno ich udawać ani zgłaszać."""
    metrics = _healthy_metrics()
    metrics.update({"lod_outward_faces": 99, "lod_max_gap_any_m": 1.0,
                    "collision_closed": False, "collision_min_gauge_margin_m": -1.0})
    assert TM.geometry_problems(metrics, None) == []
    assert len(TM.geometry_problems(metrics, {"chunks": []})) == 4


# --- bramka akceptacji: każda kontrola osobno -------------------------------

def test_empty_geometry_is_caught_by_vertices_and_by_faces():
    assert _broken(vertices=0) == ["geometria pusta"]
    assert _broken(faces=0) == ["geometria pusta"]


def test_a_single_vertex_is_not_empty():
    """Bramka pilnuje pustki, nie rozmiaru — jeden wierzchołek to nie zero."""
    assert _broken(vertices=1, faces=1) == []


def test_seam_gap_is_measured_against_one_millimetre_at_the_boundary():
    assert _broken(chunk_max_gap_m=TM.MAX_GAP_M) == []
    assert len(_broken(chunk_max_gap_m=TM.MAX_GAP_M * 1.01)) == 1


def test_lod_gap_is_measured_against_one_millimetre_at_the_boundary():
    assert _broken(lod_max_gap_any_m=TM.MAX_GAP_M) == []
    assert len(_broken(lod_max_gap_any_m=TM.MAX_GAP_M * 1.01)) == 1


def test_collision_gap_is_measured_against_one_millimetre_at_the_boundary():
    assert _broken(collision_max_gap_m=TM.MAX_GAP_M) == []
    assert len(_broken(collision_max_gap_m=TM.MAX_GAP_M * 1.01)) == 1


def test_touching_the_tunnel_wall_is_allowed_sticking_out_of_it_is_not():
    """Zapas do ściany `< 0` — dotknięcie jest legalne, wyjście poza światło nie."""
    assert _broken(collision_min_wall_margin_m=0.0) == []
    assert _broken(collision_min_wall_margin_m=-1e-9) == \
        ["bryła kolizyjna wystaje poza światło tunelu"]


def test_touching_the_m7_gauge_is_already_a_problem():
    """Zapas do skrajni `<= 0` — asymetria wobec ściany jest celowa: w skrajnię
    wjeżdża pociąg, a zerowy zapas znaczy kontakt, nie „ledwo się mieści"."""
    assert _broken(collision_min_gauge_margin_m=0.0) == \
        ["bryła kolizyjna nie mieści skrajni M7"]
    assert _broken(collision_min_gauge_margin_m=0.0005) == []


def test_frame_twist_is_measured_against_five_degrees_at_the_boundary():
    assert _broken(frame_twist_deg=TM.MAX_TWIST_DEG) == []
    assert len(_broken(frame_twist_deg=TM.MAX_TWIST_DEG + 0.01)) == 1


def test_chunk_lengths_must_add_up_to_chainage_within_a_centimetre():
    """Granicę testuję przy zerowym chainage, i to nie jest wygodnictwo.

    Bramka ogląda WYŁĄCZNIE różnicę, więc zero jest tu tak samo dobrym punktem
    jak 6700 m — a przy 6700 m `6700.0 + 0.01` nie jest liczbą reprezentowalną
    w double i różnica wychodzi 0.010000000000218, czyli NAD progiem. Test
    „na granicy" napisany naiwnie nigdy by tej granicy nie dotknął i nie
    odróżniłby `>` od `>=`. Przy zerze różnica jest dokładnie 0.01.
    """
    assert abs(TM.CHUNK_LENGTH_TOLERANCE_M - 0.0) == TM.CHUNK_LENGTH_TOLERANCE_M
    assert _broken(axis_length_m=0.0,
                   chunk_length_sum_m=TM.CHUNK_LENGTH_TOLERANCE_M) == []
    assert _broken(axis_length_m=0.0,
                   chunk_length_sum_m=-TM.CHUNK_LENGTH_TOLERANCE_M) == []
    assert _broken(axis_length_m=0.0,
                   chunk_length_sum_m=TM.CHUNK_LENGTH_TOLERANCE_M * 1.01) == \
        ["suma długości chunków nie zgadza się z chainage"]


def test_chunk_lengths_off_by_half_a_metre_are_a_problem_on_the_real_axis():
    axis = _healthy_metrics()["axis_length_m"]
    assert _broken(chunk_length_sum_m=axis + 0.5) == \
        ["suma długości chunków nie zgadza się z chainage"]
    assert _broken(chunk_length_sum_m=axis + 0.005) == []


def test_a_seam_cutting_through_a_station_is_a_problem():
    assert len(_broken(stations_split=["Schuman"])) == 1


def test_outward_normals_degenerate_faces_and_nan_are_each_caught():
    assert len(_broken(outward_faces=3)) == 1
    assert len(_broken(degenerate_faces=3)) == 1
    assert len(_broken(non_finite_vertices=3)) == 1
    assert len(_broken(lod_outward_faces=3)) == 1
    assert len(_broken(lod_degenerate_faces=3)) == 1
    assert len(_broken(lod_non_finite_vertices=3)) == 1
    assert len(_broken(collision_outward_faces=3)) == 1
    assert len(_broken(collision_degenerate_faces=3)) == 1
    assert len(_broken(collision_non_finite_vertices=3)) == 1


def test_an_open_collision_solid_is_a_problem():
    assert _broken(collision_closed=False) == \
        ["bryła kolizyjna nie jest zamknięta poprzecznie"]


def test_several_broken_things_are_all_reported_not_just_the_first():
    problems = _broken(vertices=0, outward_faces=2, collision_closed=False)
    assert len(problems) == 3, problems


# --- nagłówek poziomów LOD --------------------------------------------------

def _records(count=2):
    """Dwa chunki, trzy poziomy, LICZBY RÓŻNE NA KAŻDYM POZIOMIE.

    Różne celowo: gdyby poziomy miały te same liczby, test nie odróżniłby
    filtrowania po właściwym poziomie od filtrowania po dowolnym innym.
    """
    per_level = {0: (1000, 0.0, 0.0), 1: (400, 0.16, 0.02), 2: (200, 0.40, 0.03)}
    records = []
    for _ in range(count):
        records.append({
            "lods": [{"level": level, "triangles": tri,
                      "max_deviation_m": worst, "median_deviation_m": median,
                      "bbox_growth_m": 0.001 * level, "bbox_shrink_m": 0.002 * level}
                     for level, (tri, worst, median) in per_level.items()],
            "collision": {"triangles": 300, "outward_faces": 0, "degenerate_faces": 0,
                          "wall_margin_m": 0.05, "gauge_margin_m": 0.65,
                          "transversally_closed": True},
        })
    return records


def test_lod_header_sums_triangles_of_its_own_level_only():
    header = TM.lod_levels_header(_records())
    assert [h["level"] for h in header] == [0, 1, 2], header
    assert [h["triangles"] for h in header] == [2000, 800, 400], header


def test_lod_header_shares_are_relative_to_level_zero():
    header = TM.lod_levels_header(_records())
    assert header[0]["triangle_share_pct"] == 100.0, header[0]
    assert header[1]["triangle_share_pct"] == 40.0, header[1]
    assert header[2]["triangle_share_pct"] == 20.0, header[2]


def test_lod_header_reports_the_worst_measured_deviation_of_its_level():
    header = TM.lod_levels_header(_records())
    assert [h["max_deviation_m"] for h in header] == [0.0, 0.16, 0.4], header
    assert [h["median_deviation_m"] for h in header] == [0.0, 0.02, 0.03], header


def test_only_level_zero_is_described_as_the_base_level():
    header = TM.lod_levels_header(_records())
    assert header[0]["switch_distance_source"].startswith("poziom bazowy"), header[0]
    for entry in header[1:]:
        assert not entry["switch_distance_source"].startswith("poziom bazowy"), entry
        assert f"{entry['max_deviation_m']:.4f}" in entry["switch_distance_source"], entry


def test_lod_header_switch_distance_comes_from_the_measured_deviation():
    header = TM.lod_levels_header(_records())
    for entry in header:
        assert entry["switch_distance_m"] == \
            round(LD.switch_distance_m(entry["max_deviation_m"]), 1), entry
    assert all(h["status"] == "design_assumption" for h in header), header


# --- metryki zbiorcze -------------------------------------------------------

def _swept(count=40, length=400.0):
    points = [(length * i / count, 0.0, 0.0) for i in range(count + 1)]
    return SW.sweep(points, BOX, 10.0, [], 150.0, 40.0)


def _metrics_of(records):
    """Metryki na PRAWDZIWYCH siatkach: każdy poziom udaje siatkę bazową.

    Szwy i normalne muszą być liczone na czymś, co naprawdę wyszło ze `sweep`;
    podstawienie siatki bazowej pod wszystkie trzy poziomy jest legalne, bo
    LOD 0 nią JEST, a test pyta tu o agregację, nie o decymację.
    """
    result = _swept()
    chunks, frames, columns = result["chunks"], result["frames"], result["columns"]
    lod_meshes = [[chunk] * 3 for chunk in chunks]
    return TM.lod_metrics(records, lod_meshes, chunks, frames, columns, columns)


def test_lod_metrics_split_triangles_and_deviations_per_level():
    metrics = _metrics_of(_records())
    assert metrics["lod_level_ids"] == [0, 1, 2], metrics
    assert metrics["lod_triangles"] == {"0": 2000, "1": 800, "2": 400}, metrics
    assert metrics["lod_max_deviation_m"] == {"0": 0.0, "1": 0.16, "2": 0.4}, metrics


def test_lod_metrics_check_the_seam_for_every_pair_of_levels():
    metrics = _metrics_of(_records())
    assert sorted(metrics["lod_max_gap_m"]) == \
        ["0->0", "0->1", "0->2", "1->0", "1->1", "1->2", "2->0", "2->1", "2->2"], metrics
    assert metrics["lod_max_gap_any_m"] == max(metrics["lod_max_gap_m"].values()), metrics
    assert metrics["lod_max_gap_any_m"] <= TM.MAX_GAP_M, metrics


def test_lod_metrics_carry_the_collision_summary_from_the_records():
    metrics = _metrics_of(_records())
    assert metrics["collision_triangles"] == 600, metrics
    assert metrics["collision_closed"] is True, metrics
    assert metrics["collision_min_wall_margin_m"] == 0.05, metrics
    assert metrics["collision_min_gauge_margin_m"] == 0.65, metrics


def test_lod_metrics_take_the_worst_collision_margin_not_the_first():
    records = _records()
    records[1]["collision"]["gauge_margin_m"] = 0.11
    records[1]["collision"]["wall_margin_m"] = 0.01
    records[1]["collision"]["transversally_closed"] = False
    metrics = _metrics_of(records)
    assert metrics["collision_min_gauge_margin_m"] == 0.11, metrics
    assert metrics["collision_min_wall_margin_m"] == 0.01, metrics
    assert metrics["collision_closed"] is False, metrics


def test_lod_metrics_on_a_real_sweep_report_no_bad_normals():
    metrics = _metrics_of(_records())
    assert metrics["lod_outward_faces"] == 0, metrics
    assert metrics["lod_degenerate_faces"] == 0, metrics
    assert metrics["lod_non_finite_vertices"] == 0, metrics
    assert metrics["collision_max_gap_m"] <= TM.MAX_GAP_M, metrics


def test_lod_metrics_feed_a_gate_that_passes_on_this_sweep():
    """Domknięcie pętli: to, co liczy `lod_metrics`, czyta `geometry_problems`."""
    metrics = _healthy_metrics()
    metrics.update(_metrics_of(_records()))
    assert TM.geometry_problems(metrics, {"chunks": []}) == [], metrics


# --- opis siatki chunka -----------------------------------------------------

def test_chunk_size_is_the_bounding_box_span():
    chunk = _swept()["chunks"][0]
    lo, hi = SW.bounding_box([chunk])
    assert TM.chunk_size(chunk) == [hi[i] - lo[i] for i in range(3)]


def test_geometry_record_counts_come_from_the_generator_not_from_the_file():
    """Liczniki mają być z generatora: eksporter glTF rozszczepia wierzchołki
    na szwach UV, więc liczba w GLB jest większa i nie sumuje się do metryk."""
    chunk = _swept()["chunks"][0]
    payload = b"nie-jest-glb-ale-ma-bajty"
    handle = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
    handle.write(payload)
    handle.close()
    try:
        record = TM.geometry_record(chunk, handle.name)
        assert record["vertices"] == len(chunk["vertices"]), record
        assert record["faces"] == len(chunk["faces"]), record
        assert record["triangles"] == 2 * len(chunk["faces"]), record
        assert record["rings"] == len(chunk["ring_indices"]), record
        assert record["bytes"] == len(payload), record
        assert record["sha256"] == TM.sha256_file(handle.name), record
        assert record["geometry_sha256"] == SW.chunk_geometry_sha256(chunk), record
        assert record["file"] == os.path.basename(handle.name), record
        assert record["bbox_size_m"] == [round(v, 4) for v in TM.chunk_size(chunk)], record
    finally:
        os.unlink(handle.name)


def test_sha256_of_a_file_matches_hashlib_over_its_bytes():
    payload = b"x" * 200000  # ponad jeden blok czytania (65536 B)
    handle = tempfile.NamedTemporaryFile(delete=False)
    handle.write(payload)
    handle.close()
    try:
        assert TM.sha256_file(handle.name) == hashlib.sha256(payload).hexdigest()
    finally:
        os.unlink(handle.name)

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
