#!/usr/bin/env python3
"""Testy bazowych narzędzi Metro BXL, bez Blendera i bez pytest."""
import sys, os, json, tempfile, math, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
sys.path.insert(0,os.path.join(ROOT,"tools","blender")); sys.path.insert(0,os.path.join(ROOT,"tools","track")); sys.path.insert(0,os.path.join(ROOT,"tools","physics")); sys.path.insert(0,os.path.join(ROOT,"tools","data")); sys.path.insert(0,os.path.join(ROOT,"tools","tests"))
import profiles, validate as V, reference as R, make_test_track as M, provenance as P
import assertion_gate as AG

def _tmp(d):
    f=tempfile.NamedTemporaryFile("w",suffix=".json",delete=False,encoding="utf-8"); json.dump(d,f,ensure_ascii=False); f.close(); return f.name

def _signalling_ground_truth():
    return json.load(open(os.path.join(ROOT,"data","signalling","ground-truth.json"),encoding="utf-8"))
def _infrastructure_ground_truth():
    return json.load(open(os.path.join(ROOT,"data","infrastructure","metro-system.json"),encoding="utf-8"))

def _network():
    return json.load(open(os.path.join(ROOT,"data","network","lines.json"),encoding="utf-8"))

def _m7_spec():
    return json.load(open(os.path.join(ROOT,"data","vehicle","m7-spec.json"),encoding="utf-8"))

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

def test_reference_acceleration_run_stops_at_its_declared_time_limit():
    """Limit 300 s w `sim_accel` jest bramką przeciw zawieszeniu, a nie ozdobą.

    Zmierzone 03.09.2026 audytem mutacyjnym: podniesienie limitu z 300 na 301
    przechodziło przez całą suitę. Każdy test rozruchu zadaje 80 km/h, które model
    osiąga po ~25 s — pętla kończy się wtedy na prędkości docelowej i liczba 300
    nie bramkuje niczego. Przy 500 km/h opór Davisa zjada całą trakcję, przyspieszenie
    schodzi do zera i przebieg kończy się WYŁĄCZNIE na limicie; dopiero to wejście
    tę liczbę mierzy.
    """
    dt=1/120
    t,s=R.sim_accel(R.MASS["AW0"],500.0)
    assert 300.0 <= t < 300.0+2*dt, t
    assert s > 12000.0, s
    # Kontrola: przy prędkości, którą model dowozi, limit nie jest tym, co kończy
    # przebieg — inaczej powyższe mierzyłoby co innego, niż mówi.
    t80,_=R.sim_accel(R.MASS["AW0"],80.0); assert t80 < 100.0, t80

def test_reference_braking_run_stops_at_its_declared_time_limit():
    """Ten sam limit po stronie hamowania: 120 s w `sim_brake`.

    Zmierzone 03.09.2026: 120 -> 121 przechodziło. Wszystkie testy hamowania zadają
    opóźnienie, przy którym pociąg staje po ~20 s, więc limit nigdy nie był osiągany.
    Hamulec zadany jako 0 m/s² nie zatrzymuje pociągu nigdy — to jedyne wejście,
    przy którym ta liczba o czymkolwiek decyduje.
    """
    dt=1/120
    t,s=R.sim_brake(R.MASS["AW0"],80.0,0.0)
    assert 120.0 <= t < 120.0+2*dt, t
    # Zerowy hamulec nie zmienia prędkości, więc droga to v0 * czas.
    assert abs(s-(80/3.6)*t) < 1e-6, (s,t)
    ts,_=R.sim_brake(R.MASS["AW0"],80.0,R.V["b_service"]); assert ts < 60.0, ts

def test_traction_power_plausible(): assert R.power_kW()==2160.0

def test_m7_reference_uses_source_backed_aw0(): assert R.MASS["AW0"]==170000.0

def test_m7_transition_speed_is_derived_from_power_and_force():
    assert math.isclose(R.base_speed_ms(),R.V["installed_power_W"]/R.V["F0_N"],rel_tol=0,abs_tol=1e-12)
    assert 31.2 < R.base_speed_ms()*3.6 < 31.3

def test_m7_spec_registry_provenance():
    d=_m7_spec(); sources=d["sources"]
    assert d["vehicle_id"]=="M7"
    assert d["parameters"]["empty_mass_kg"]["value"]==170000.0
    assert d["parameters"]["empty_mass_kg"].get("approximate") is True
    assert d["parameters"]["traction_installed_power_kw"]["value"]==2160.0
    for name,rec in d["parameters"].items():
        if rec.get("status")=="spec":
            sid=rec.get("source_id"); assert sid in sources,(name,sid)
            assert sources[sid].get("url","").startswith("https://"),(name,sid)

def test_m7_registry_matches_reference_transition():
    d=_m7_spec(); rec=d["reference_model"]["force_power_transition_speed_kmh"]
    assert rec["status"]=="design_model"
    assert math.isclose(rec["value"],R.base_speed_ms()*3.6,rel_tol=0,abs_tol=1e-12)
    assert "base_speed_kmh" not in d["reference_model"]
    assert set(rec["derived_from"])=={"parameters.traction_installed_power_kw","reference_model.startup_force_n"}

def test_unverified_m7_values_are_not_spec():
    d=_m7_spec()
    assert d["parameters"]["max_speed_kmh"]["status"]=="design_model"
    assert d["parameters"]["powered_mass_fraction"]["status"]=="design_model"
    assert d["reference_model"]["aw2_model_mass_kg"]["status"]=="design_model"
    assert d["reference_model"]["startup_force_n"]["status"]=="design_model"
    assert d["reference_model"]["force_power_transition_speed_kmh"]["status"]=="design_model"

def test_network_json_consistent():
    net=_network(); assert len(net["lines"])==4
    for l in net["lines"]: assert len(l["stops"])==l["stations"]
    uniq={s for l in net["lines"] for s in l["stops"]}; assert len(uniq)==net["station_notes"]["counting_rules"]["unique_stop_names"]

def test_shared_trunk_is_really_shared():
    net=_network(); l1=next(l for l in net["lines"] if l["id"]=="L1")["stops"]; l5=next(l for l in net["lines"] if l["id"]=="L5")["stops"]; assert len([s for s in l1 if s in l5])==12

def test_source_registry_has_primary_geometry_sources():
    src=json.load(open(os.path.join(ROOT,"data","network","sources.json"),encoding="utf-8")); ids={x["id"] for x in src["sources"]}; assert {"stib_shapefiles","stib_gtfs","brussels_mobility_metro","openstreetmap"}<=ids

def test_r002_sources_have_required_audit_fields():
    src=json.load(open(os.path.join(ROOT,"data","network","sources.json"),encoding="utf-8")); by_id={x["id"]:x for x in src["sources"]}
    ids={"belgian_mobility_netex","belgian_mobility_inspire_rails","brussels_mobility_metro_access","urbis_topo_tunnel_line","paradigm_lidar_2021","urbis_dsm"}
    required={"id","class","publisher","url","role","license","update_frequency","access","checked_at","limitations"}
    for sid in ids:
        assert sid in by_id,sid
        row=by_id[sid]; missing=required-set(row); assert not missing,(sid,sorted(missing))
        assert isinstance(row["role"],list) and row["role"],sid
        assert isinstance(row["access"],dict) and row["access"],sid
        assert row["license"]!="see dataset metadata",sid

def test_r002_download_metadata_distinction_is_explicit():
    src=json.load(open(os.path.join(ROOT,"data","network","sources.json"),encoding="utf-8")); by_id={x["id"]:x for x in src["sources"]}
    metro=by_id["brussels_mobility_metro_access"]
    assert metro["metadata_url"]==metro["url"]
    assert metro["api_layer"]=="bm_public_transport:metro_access"
    assert "download_url" in metro and "download_url_status" in metro
    dsm=by_id["urbis_dsm"]
    assert dsm["license"]=="unknown"
    assert dsm["license_status"].startswith("requires_verification_before_data_reuse")
    lidar=by_id["paradigm_lidar_2021"]
    assert lidar["license"]=="CC BY 4.0"
    assert lidar["download_portal_url"].startswith("https://")

def test_cbtc_2026_not_marked_as_fully_operational():
    net=_network(); assert net["signalling"]["cbtc"]["status_2026_08"]["operational_full_lines_1_5"] is False

def test_provenance_identical_bytes_have_same_hash_and_one_byte_changes():
    a=b"metro-data\n"; b=b"metro-data!\n"
    assert P.sha256_bytes(a)==P.sha256_bytes(bytes(a))
    assert P.sha256_bytes(a)!=P.sha256_bytes(b)

def test_provenance_html_instead_of_zip_is_rejected():
    try: P.validate_payload(b"<!doctype html><title>login</title>","zip","text/html")
    except P.ProvenanceError: pass
    else: raise AssertionError("HTML login page accepted as ZIP")

def test_provenance_zip_magic_is_checked():
    P.validate_payload(b"PK\x03\x04payload","zip","application/zip")
    try: P.validate_payload(b"not-a-zip","zip","application/octet-stream")
    except P.ProvenanceError: pass
    else: raise AssertionError("bad ZIP magic accepted")

def test_provenance_secrets_are_sanitized_or_rejected():
    u=P.sanitize_url("https://example.test/feed.zip?token=abc&line=1&api_key=xyz")
    assert "abc" not in u and "xyz" not in u and "REDACTED" in u and "line=1" in u
    try: P.sanitize_headers({"Authorization":"Bearer secret"})
    except P.ProvenanceError: pass
    else: raise AssertionError("Authorization header was accepted for persistence")

def test_provenance_every_sensitive_key_is_redacted_one_by_one():
    """Każdy klucz z listy osobno, a nie dwa przykładowe.

    Zmierzone 02.09.2026 audytem mutacyjnym: obcięcie SENSITIVE_HEADER_KEYS do
    {"authorization"} i SENSITIVE_QUERY_KEYS do {"api_key","token"} przechodziło,
    bo test używał tylko tych dwóch. Manifesty źródeł są commitowane do repo,
    więc sekret w `requested_url` wszedłby do historii gita.
    """
    assert len(P.SENSITIVE_QUERY_KEYS)>=12 and len(P.SENSITIVE_HEADER_KEYS)>=4
    for key in sorted(P.SENSITIVE_QUERY_KEYS):
        u=P.sanitize_url(f"https://example.test/feed.zip?{key}=poufne&line=1")
        assert "poufne" not in u and "REDACTED" in u and "line=1" in u, (key,u)
    # Klucz spoza listy zostaje nietknięty — inaczej redakcja zjadałaby wszystko
    # i test przechodziłby także dla pustej listy.
    plain=P.sanitize_url("https://example.test/feed.zip?line=1&limit=10")
    assert "REDACTED" not in plain and "limit=10" in plain, plain
    for key in sorted(P.SENSITIVE_HEADER_KEYS):
        try: P.sanitize_headers({key:"poufne"})
        except P.ProvenanceError: pass
        else: raise AssertionError(f"naglowek {key} przeszedl do zapisu")
        try: P.sanitize_headers({key.upper():"poufne"})
        except P.ProvenanceError: pass
        else: raise AssertionError(f"naglowek {key} w wersji WIELKIMI przeszedl do zapisu")
    P.sanitize_headers({"Accept":"application/json"})

def test_provenance_etag_does_not_change_content_hash():
    common=dict(source_id="stib_gtfs",requested_url="https://example.test/a.zip",final_url="https://example.test/a.zip",content=b"PK\x03\x04x",retrieved_at="2026-09-01T00:00:00Z",data_format="zip")
    a=P.build_manifest(etag='"one"',**common); b=P.build_manifest(etag='"two"',**common)
    assert a["content_sha256"]==b["content_sha256"]

def test_provenance_diff_detects_upstream_byte_change():
    common=dict(source_id="stib_gtfs",requested_url="https://example.test/a.json",final_url="https://example.test/a.json",retrieved_at="2026-09-01T00:00:00Z",data_format="json")
    a=P.build_manifest(content=b'{"x":1}',**common); b=P.build_manifest(content=b'{"x":2}',**common)
    d=P.diff_manifests(a,b); assert d["status"]=="changed" and d["source_changed"] and "content_sha256" in d["changes"]

def test_provenance_redirect_records_final_url():
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path=="/start": self.send_response(302); self.send_header("Location","/data"); self.end_headers(); return
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(b'{"ok":true}')
        def log_message(self,*args): pass
    srv=HTTPServer(("127.0.0.1",0),H); t=threading.Thread(target=srv.serve_forever,daemon=True); t.start()
    try:
        url=f"http://127.0.0.1:{srv.server_port}/start"; data,final,_=P.fetch_url(url,expected_format="json",timeout=2)
        assert data==b'{"ok":true}' and final.endswith("/data")
    finally:
        srv.shutdown(); srv.server_close(); t.join(timeout=2)

def test_provenance_osm_query_is_hashed_not_stored():
    m=P.build_manifest(source_id="openstreetmap",requested_url="https://example.test/osm",final_url="https://example.test/osm",content=b"osm",retrieved_at="2026-09-01T00:00:00Z",data_format="pbf",query_text="[out:json];way[railway=subway];out;")
    assert len(m["query_sha256"])==64 and "query" not in m

def test_source_manifest_schema_has_core_required_fields():
    schema=json.load(open(os.path.join(ROOT,"data","schema","source-manifest.schema.json"),encoding="utf-8")); req=set(schema["required"])
    assert {"source_id","final_url","retrieved_at","content_sha256","size_bytes","format","parser_version","transformations","input_sources"}<=req

def test_signalling_ground_truth_sources_exist():
    gt=_signalling_ground_truth(); src=json.load(open(os.path.join(ROOT,"data","network","sources.json"),encoding="utf-8")); ids={x["id"] for x in src["sources"]}
    referenced={sid for f in gt["facts"] for sid in f.get("source_ids",[])}
    assert referenced<=ids, sorted(referenced-ids)

def test_signalling_source_backed_facts_have_provenance():
    gt=_signalling_ground_truth()
    for f in gt["facts"]:
        if f["status"] in {"spec","observed"}: assert f.get("source_ids"), f["id"]

def test_signalling_modes_reference_real_facts():
    gt=_signalling_ground_truth(); fact_ids={f["id"] for f in gt["facts"]}
    for name,mode in gt["modes"].items():
        refs=mode.get("source_fact_ids"); assert refs,(name,"missing source_fact_ids")
        assert set(refs)<=fact_ids,(name,sorted(set(refs)-fact_ids))
        assert "source_backed" not in mode,(name,"free-form source_backed labels are not auditable")
    assert "cbtc_test_method_and_beekkant" in gt["modes"]["cbtc_test"]["source_fact_ids"]
    assert "cbtc_variable_separation_concept" in gt["modes"]["cbtc_future"]["source_fact_ids"]

def test_signalling_historical_default_is_classic_2026():
    gt=_signalling_ground_truth(); assert gt["as_of"]=="2026-08-31"; assert gt["historical_default"]=="classic_2026"
    defaults=[name for name,mode in gt["modes"].items() if mode.get("historical_default")]
    assert defaults==["classic_2026"],defaults
    assert gt["modes"]["cbtc_test"]["passenger_service_network_wide"] is False

def test_signalling_unknowns_remain_explicit():
    gt=_signalling_ground_truth(); unknown=" ".join(gt["unknown_parameters"]).lower()
    for term in ("block","telegram","braking","interlocking","failover"): assert term in unknown,term
def test_infrastructure_source_backed_facts_have_provenance():
    gt=_infrastructure_ground_truth(); src=json.load(open(os.path.join(ROOT,"data","network","sources.json"),encoding="utf-8")); ids={x["id"] for x in src["sources"]}
    for f in gt["facts"]:
        if f["status"] in {"spec","observed"}:
            assert f.get("source_ids"),f["id"]
            assert set(f["source_ids"])<=ids,(f["id"],set(f["source_ids"])-ids)

def test_infrastructure_900v_and_third_rail_are_source_backed():
    gt=_infrastructure_ground_truth(); facts={f["id"]:f for f in gt["facts"]}
    assert facts["traction_voltage"]["value"]==900
    assert facts["current_collection"]["value"]=="third_rail"

def test_network_snapshot_does_not_overstate_infrastructure_ground_truth():
    gt=_infrastructure_ground_truth(); net=_network()["network"]
    gauge=gt["unknown_parameters"]["track_gauge_mm"]
    assert net["gauge_mm"]==gauge["reference_value"]
    assert net["gauge_status"]==gauge["reference_status"]=="secondary_reference_only"
    assert net["gauge_ground_truth_registry"]=="data/infrastructure/metro-system.json"
    power=net["metro_power"]
    assert power["voltage_v"]==900 and power["voltage_status"]=="observed"
    assert power["collection"]=="third_rail" and power["collection_status"]=="observed"
    assert power["contact_geometry"]=="unknown"
    assert "top" not in power["collection"].lower()
    assert power["ground_truth_registry"]=="data/infrastructure/metro-system.json"
    assert power["type_status"]=="legacy_reference_only"

def test_infrastructure_speed_statements_are_not_global_hardcodes():
    gt=_infrastructure_ground_truth(); facts={f["id"]:f for f in gt["facts"]}
    assert facts["tunnel_speed_public_safety_statement"]["value"]==72
    assert facts["station_entry_speed_public_safety_statement"]["value"]==40
    assert facts["tunnel_speed_public_safety_statement"]["global_hardcode"] is False
    assert facts["station_entry_speed_public_safety_statement"]["global_hardcode"] is False

def test_infrastructure_unverified_values_stay_non_spec():
    gt=_infrastructure_ground_truth(); unknown=gt["unknown_parameters"]
    assert unknown["track_gauge_mm"]["status"]=="unknown_primary_source_not_confirmed"
    assert unknown["m7_design_vmax_kmh"]["status"]=="unknown_primary_source_not_confirmed"
    assert unknown["third_rail_contact_geometry"]["status"]=="unknown"

def test_traction_substation_count_not_claimed_as_metro_only():
    gt=_infrastructure_ground_truth(); facts={f["id"]:f for f in gt["facts"]}; f=facts["traction_substations_stib_network_2024"]
    assert f["value"]==120
    assert "unsplit" in f["scope"]

def _discover():
    """Wszystkie moduły `tools/tests/test_*.py`, ten plik włącznie.

    Każdy idzie przez `assertion_gate.load_instrumented`, czyli z licznikiem asercji
    wstrzykniętym w AST. Ten plik też — inaczej jego własne testy byłyby jedynymi,
    których bramka nie mierzy, a to dokładnie ta luka, którą bramka ma zamykać.
    Kopia dostaje inną nazwę modułu, więc strażnik `__name__=="__main__"` na jej
    końcu nie odpala `main()` rekurencyjnie.

    Zwraca `(tests, module_of)`: `tests` jest płaską listą `(nazwa, funkcja)` —
    kształt, którego `len(tests)` używa reszta tego pliku i którego literalnie
    szuka `test_assertion_gate.py` — a `module_of` to lista tej samej długości,
    plik źródłowy (bez `.py`) dla każdego testu na tym samym indeksie. Osobna
    lista, nie słownik `nazwa -> moduł`, bo dwa różne pliki testowe mogą mieć
    funkcję o tej samej nazwie (żaden dziś nie ma, ale nic tego nie gwarantuje).
    """
    tests=[]
    module_of=[]
    for path in AG.paths():
        module_file=os.path.basename(path)[:-3]
        name=module_file
        if name=="test_all": name="test_all__mierzony"
        mod=AG.load_instrumented(path,name)
        found=[(n,f) for n,f in sorted(vars(mod).items()) if n.startswith("test_") and callable(f)]
        tests+=found
        module_of+=[module_file]*len(found)
    return tests, module_of

def main():
    """Uruchom zestaw. Test, który przeszedł bez asercji, jest awarią, nie sukcesem.

    Licznik `przeszło` liczy WYŁĄCZNIE testy, które coś sprawdziły. Pominięte mają
    własną linię i własny mianownik — dopisanie `skip()` nie może po cichu poprawić
    statystyki.

    6.D11: obok werdyktu każdego testu mierzony jest jego czas, zsumowany per plik
    źródłowy. To WYŁĄCZNIE wypis — próg czasu żyje w `test_suite_runtime_budget.py`
    i w kroku CI, nie tutaj. Powód jest zmierzony na `mutation_sweep.py` (którego
    nie wolno mi dotykać w tym zadaniu): `run_suite` czyta z tego procesu WYŁĄCZNIE
    linię `N/M przeszło` i kod wyjścia, i uznaje mutację za PRZEŻYTĄ dokładnie wtedy,
    gdy oba mówią „ok". Kod wyjścia zależny od czasu zamieniłby zwykłe spowolnienie
    maszyny w setki fałszywych „zabić" naraz — tej samej klasy usterki, jaką opisuje
    `reports/wyrocznia-mutacyjna-falszywe-zabicia.md`, tylko odwróconej w drugą stronę.
    """
    tests,module_of=_discover(); passed=0; skipped=[]; failed=[]; checks_total=0
    module_seconds={}; module_counts={}
    suite_start=time.perf_counter()
    for (name,fn),module_file in zip(tests,module_of):
        AG.reset(); outcome=None
        test_start=time.perf_counter()
        try: fn()
        except Exception as e: outcome=e
        module_seconds[module_file]=module_seconds.get(module_file,0.0)+(time.perf_counter()-test_start)
        module_counts[module_file]=module_counts.get(module_file,0)+1
        checks=AG.hits(); checks_total+=checks
        state,message=AG.verdict(outcome,checks)
        if state=="ok": print(f"  ok   {name}"); passed+=1
        elif state=="skip": print(f"  SKIP {name}: {message}"); skipped.append(name)
        else: print(f"  FAIL {name}: {message}"); failed.append(name)
    suite_elapsed=time.perf_counter()-suite_start
    print(); print(f"  {passed}/{len(tests)-len(skipped)} przeszło")
    if skipped: print(f"  pominięto (nie liczy się jako zaliczone): {len(skipped)} — {', '.join(skipped)}")
    print(); print("  czas per moduł (malejąco):")
    for module_file in sorted(module_seconds,key=lambda m:-module_seconds[m]):
        secs=module_seconds[module_file]; n=module_counts[module_file]
        print(f"    {secs:8.3f} s  {module_file}.py  ({n} testów)")
    print(f"  RAZEM {suite_elapsed:.3f} s, {len(tests)} testów, {len(module_seconds)} modułów")
    broken=AG.suite_verdict(len(tests),checks_total)
    if broken: print(f"  FAIL <bramka asercji>: {broken}"); return 1
    return 1 if failed else 0

if __name__=="__main__": sys.exit(main())
