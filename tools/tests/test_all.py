#!/usr/bin/env python3
"""Testy bazowych narzędzi Metro BXL, bez Blendera i bez pytest."""
import sys, os, json, tempfile, math
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
sys.path.insert(0,os.path.join(ROOT,"tools","blender")); sys.path.insert(0,os.path.join(ROOT,"tools","track")); sys.path.insert(0,os.path.join(ROOT,"tools","physics"))
import profiles, validate as V, reference as R, make_test_track as M

def _tmp(d):
    f=tempfile.NamedTemporaryFile("w",suffix=".json",delete=False,encoding="utf-8"); json.dump(d,f,ensure_ascii=False); f.close(); return f.name

def _visual_style():
    return json.load(open(os.path.join(ROOT,"data","design","visual-style.json"),encoding="utf-8"))

def test_profile_dimensions_sane():
    for n in profiles.PROFILES:
        w,h=profiles.dimensions(n); assert 4<w<25 and 3.5<h<12

def test_every_profile_fits_m7():
    for n in profiles.PROFILES: assert profiles.fits_gauge(n)[0]

def test_tunnel_profiles_are_marked_as_design_values():
    for n,s in profiles.PROFILES.items(): assert s.get("source_level")=="design",n

def test_validator_accepts_good_track():
    p=_tmp(M.build(False)); r=V.validate(p); os.unlink(p); assert r.ok(),r.err

def test_validator_rejects_broken_track():
    p=_tmp(M.build(True)); r=V.validate(p); os.unlink(p); assert not r.ok() and len(r.err)>=3

def test_validator_requires_three_coords():
    p=_tmp({"id":"X","points":[[0,0],[10,0],[20,0]]}); r=V.validate(p); os.unlink(p); assert not r.ok()

def test_loaded_train_accelerates_slower():
    t0,s0=R.sim_accel(R.MASS["AW0"],80); t2,s2=R.sim_accel(R.MASS["AW2"],80); assert t2>t0 and s2>s0

def test_uphill_slower_than_downhill():
    tu,_=R.sim_accel(R.MASS["AW2"],80,3); td,_=R.sim_accel(R.MASS["AW2"],80,-3); assert tu>td

def test_emergency_brake_shorter_than_service():
    _,ss=R.sim_brake(R.MASS["AW2"],80,R.V["b_service"]); _,se=R.sim_brake(R.MASS["AW2"],80,R.V["b_emergency"]); assert se<ss

def test_wet_rail_hurts_acceleration():
    td,_=R.sim_accel(R.MASS["AW0"],80,mu=.25); tw,_=R.sim_accel(R.MASS["AW0"],80,mu=.13); assert tw>td

def test_traction_power_plausible(): assert 1500<R.power_kW()<3500

def test_network_json_consistent():
    net=json.load(open(os.path.join(ROOT,"data","network","lines.json"),encoding="utf-8")); assert len(net["lines"])==4
    for l in net["lines"]: assert len(l["stops"])==l["stations"]
    uniq={s for l in net["lines"] for s in l["stops"]}; assert len(uniq)==net["station_notes"]["counting_rules"]["unique_stop_names"]

def test_shared_trunk_is_really_shared():
    net=json.load(open(os.path.join(ROOT,"data","network","lines.json"),encoding="utf-8")); l1=next(l for l in net["lines"] if l["id"]=="L1")["stops"]; l5=next(l for l in net["lines"] if l["id"]=="L5")["stops"]; assert len([s for s in l1 if s in l5])==12

def test_source_registry_has_primary_geometry_sources():
    src=json.load(open(os.path.join(ROOT,"data","network","sources.json"),encoding="utf-8")); ids={x["id"] for x in src["sources"]}; assert {"stib_shapefiles","stib_gtfs","brussels_mobility_metro","openstreetmap"}<=ids

def test_cbtc_2026_not_marked_as_fully_operational():
    net=json.load(open(os.path.join(ROOT,"data","network","lines.json"),encoding="utf-8")); assert net["signalling"]["cbtc"]["status_2026_08"]["operational_full_lines_1_5"] is False

def test_visual_style_has_three_layer_pipeline():
    d=_visual_style(); assert d["pipeline"]==["technical","neutral_realistic","licensed_stib_optional"]
    assert d["current_default"]=="technical"
    assert d["layers"]["licensed_stib_optional"]["rights_gate"]=="data/legal/rights-matrix.json"

def test_visual_material_presets_are_neutral_design_values():
    d=_visual_style(); ids=[]
    for m in d["material_presets"]:
        ids.append(m["id"]); assert m["status"]=="design_model",m["id"]
        assert "stib" not in m["id"].lower(),m["id"]
        assert len(m["base_color"])==4
        assert 0.0<=m.get("metallic",0.0)<=1.0
        assert 0.0<=m.get("roughness",0.5)<=1.0
    assert len(ids)==len(set(ids))
    assert {"concrete_clean","brushed_metal","glass","rubber","rail_steel","generic_safety_strip"}<=set(ids)

def test_visual_external_sources_have_licence_and_provenance_policy():
    d=_visual_style()
    for src in d["external_asset_sources"]:
        assert src["license"],src["id"]
        if src["id"]!="project_procedural": assert src.get("url") and src.get("checked_at"),src["id"]
    fields=set(d["asset_metadata_required"])
    assert {"asset_id","source_url","license","source_hash","redistribution_allowed"}<=fields

def test_visual_regression_baseline_is_deterministic():
    r=_visual_style()["render_baseline"]
    assert r["auto_exposure"] is False
    assert r["temporal_jitter"] is False
    assert r["resolution"]==[960,576]
    assert isinstance(r["deterministic_seed"],int)

def test_visual_performance_budgets_wait_for_measurement():
    p=_visual_style()["performance_policy"]
    assert p["status"]=="measure_first"
    for key in ("poly_budget","draw_call_budget","texture_budget","shadow_light_budget","lod_distances"): assert p[key] is None,key

def main():
    tests=[(n,f) for n,f in sorted(globals().items()) if n.startswith("test_") and callable(f)]; passed=0; failed=[]
    for name,fn in tests:
        try: fn(); print(f"  ok   {name}"); passed+=1
        except Exception as e: print(f"  FAIL {name}: {e}"); failed.append(name)
    print(); print(f"  {passed}/{len(tests)} przeszło"); return 1 if failed else 0

if __name__=="__main__": sys.exit(main())
