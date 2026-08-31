#!/usr/bin/env python3
"""Testy bazowych narzędzi Metro BXL, bez Blendera i bez pytest."""
import sys, os, json, tempfile, math
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
sys.path.insert(0,os.path.join(ROOT,"tools","blender")); sys.path.insert(0,os.path.join(ROOT,"tools","track")); sys.path.insert(0,os.path.join(ROOT,"tools","physics"))
import profiles, validate as V, reference as R, make_test_track as M

def _tmp(d):
    f=tempfile.NamedTemporaryFile("w",suffix=".json",delete=False,encoding="utf-8"); json.dump(d,f,ensure_ascii=False); f.close(); return f.name

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

def main():
    tests=[(n,f) for n,f in sorted(globals().items()) if n.startswith("test_") and callable(f)]; passed=0; failed=[]
    for name,fn in tests:
        try: fn(); print(f"  ok   {name}"); passed+=1
        except Exception as e: print(f"  FAIL {name}: {e}"); failed.append(name)
    print(); print(f"  {passed}/{len(tests)} przeszło"); return 1 if failed else 0

if __name__=="__main__": sys.exit(main())
