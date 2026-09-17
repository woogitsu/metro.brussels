#!/usr/bin/env python3
"""Testy bazowych narzędzi Metro BXL, bez Blendera i bez pytest."""
import sys, os, json, tempfile, math, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
# `tree_walk` PRZED importami narzedzi i przed reszta `sys.path` — bo zaraz pod
# spodem kasuje bajtkod, a kasowanie po tamtych importach bylo by spoznione.
sys.path.insert(0,os.path.join(ROOT,"tools","tests"))
import tree_walk as TW

# Raz na proces, nie raz na import: `_discover` ładuje TEN plik jeszcze raz, pod
# nazwą `test_all__mierzony`, więc bez tej wartowni czyszczenie i wypis powtórzyłyby
# się w środku przebiegu — kasując bajtkod, który właśnie powstał, i mówiąc o tym
# drugi raz. Znacznik siedzi na `sys`, bo musi przeżyć import pod inną nazwą.
# --- 6.D165: ile plikow drzewa roboczego lezy POZA zasiegiem bramek czytajacych gita
#
# **Po co ten wypis.** Dwie bramki (`test_conflict_markers.py`, `test_runner_options.py`)
# pytaja o liste plikow `git ls-files`, czyli widza wylacznie to, co jest w INDEKSIE.
# Wybor jest sluszny — pilnowane ma byc to, co moze trafic do `main`, a nie `build/`
# ani katalogi sond — ale do 6.D165 przebieg o tym MILCZAL. Zielony wynik znaczyl wiec
# co innego przed `git add` i po nim, a roznicy nie bylo widac: 12.09.2026 szesc plikow
# jeszcze nie dodanych do indeksu dalo lokalnie 2387/2387 i kod 0, po czym na CI poszlo
# siedem czerwonych jobow naraz (PR #548). To ta sama rodzina, co 6.D27 — przyrzad
# melduje sprawdzenie drzewa, ktorego w tym ksztalcie nie bylo.
#
# Wypis NIE jest bramka i nie zmienia kodu wyjscia: liczba wieksza od zera nie znaczy
# bledu, tylko „tyle plikow ten przebieg pominal". Ocena nalezy do czytajacego.
def poza_zasiegiem_git_ls_files(korzen=None):
    """`(ile, powod)` — pliki drzewa roboczego, ktorych `git ls-files` NIE widzi.

    `ile` jest `None`, gdy nie dalo sie zapytac gita, a `powod` mowi dlaczego —
    **zadeklarowana niewiedza zamiast cichego zera**. Zero wypisane przy zepsutym
    wywolaniu wygladaloby dokladnie tak samo jak zero przy czystym drzewie, czyli
    bylby to kolejny przyrzad meldujacy sprawdzenie, ktorego nie zrobil.

    `korzen` jest parametrem, bo inaczej tej funkcji nie da sie sprawdzic: dzisiejsze
    drzewo repozytorium ma zero plikow niesledzonych, wiec na nim funkcja zwracajaca
    zawsze zero byla by nie do odroznienia od dzialajacej (kontrola przyrzadu
    w `test_conflict_markers.py` wola ja na wlasnym repozytorium probnym).
    """
    import subprocess
    try:
        wypis = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=korzen or ROOT, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as blad:
        return None, "nie udalo sie zapytac gita: %s" % blad
    if wypis.returncode != 0:
        return None, "git zwrocil kod %d" % wypis.returncode
    return len([w for w in wypis.stdout.splitlines() if w.strip()]), ""


if not getattr(sys,"_metro_drzewo_policzone",None):
    sys._metro_drzewo_policzone=True
    _ile,_powod=poza_zasiegiem_git_ls_files()
    if _ile is None:
        print("  [DRZEWO] nie wiadomo, ile plikow lezy poza zasiegiem bramek "
              "czytajacych `git ls-files` (%s) — 6.D165" % _powod)
    else:
        print("  [DRZEWO] %d plikow drzewa roboczego poza zasiegiem bramek "
              "czytajacych `git ls-files` — 6.D165" % _ile)

if not getattr(sys,"_metro_bajtkod_wyczyszczony",None):
    sys._metro_bajtkod_wyczyszczony=TW.wyczysc_bajtkod()
    print("  [BAJTKOD] wyczyszczono %d kat. __pycache__ (%d plikow) pod tools/ — 6.D122"
          % sys._metro_bajtkod_wyczyszczony)

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

# 6.D138: liczba 170 000 stoi w drzewie CZTERY razy i każda kopia ma inną rolę.
#   1. `data/vehicle/m7-spec.json`  — ŹRÓDŁO, z `source_id` i `approximate: true`
#   2. `tools/physics/reference.py` — DRUGA DROGA: tablica referencyjna, której
#      literały są jej treścią (na nich stoi porównanie C# z Pythonem)
#   3. asercja niżej                — PIN na kopii 2, żeby druga droga nie ruszyła
#      się po cichu; NIE mówi nic o źródle
#   4. `test_m7_spec_registry_provenance` — PIN na kopii 1
# Rozjazd 2 z 1 łapie `test_reczna_kopia_masy_w_referencji_zgadza_sie_z_REJESTREM`
# (6.D124) w `test_braking.py` — i to jest jedyne miejsce, które porównuje kopię
# ze ŹRÓDŁEM, a nie kopię z literałem.
#
# Zmierzone 11.09.2026 na kopii roboczej drzewa, bez zmiany `data/`:
#   podmiana w REJESTRZE (170000 -> 171000)      4 testy z 2346, pin niżej MILCZY
#   podmiana w REFERENCJI (170000 -> 171000)     6 testów, pin niżej JEST wśród nich
# Dawna nazwa brzmiała `test_m7_reference_uses_source_backed_aw0` i obiecywała
# sprawdzenie oparcia o źródło, którego ta asercja nie robi — 6.D27 w miniaturze.
def test_m7_reference_mass_pin_has_not_drifted():
    assert R.MASS["AW0"]==170000.0, (
        "literał masy AW0 w `reference.py` przesunął się na %r — ten pin NIE mówi, "
        "czy zgadza się ze źródłem (od tego jest "
        "`test_reczna_kopia_masy_w_referencji_zgadza_sie_z_REJESTREM`), tylko czy "
        "DRUGA DROGA nie ruszyła się po cichu" % R.MASS["AW0"])

def test_m7_transition_speed_is_derived_from_power_and_force():
    assert math.isclose(R.base_speed_ms(),R.V["installed_power_W"]/R.V["F0_N"],rel_tol=0,abs_tol=1e-12)
    assert 31.2 < R.base_speed_ms()*3.6 < 31.3

def test_m7_spec_registry_provenance():
    d=_m7_spec(); sources=d["sources"]
    assert d["vehicle_id"]=="M7"
    # 6.D138: PIN na ŹRÓDLE (kopia 1). Bez komunikatu ta asercja padała jako
    # `FAIL test_m7_spec_registry_provenance:` — dwukropek i nic dalej, mimo że
    # wartość w rejestrze jest dokładnie tym, co się zmieniło.
    assert d["parameters"]["empty_mass_kg"]["value"]==170000.0, (
        "masa pusta w rejestrze to %r zamiast 170000.0 — jeśli to zmiana świadoma, "
        "przelicz tablicę referencyjną w tym samym commicie"
        % d["parameters"]["empty_mass_kg"]["value"])
    assert d["parameters"]["empty_mass_kg"].get("approximate") is True, (
        "rejestr przestał oznaczać masę pustą jako przybliżoną — `reference.py` "
        "niesie jej kopię bez żadnego znaku i nic by o tym nie powiedziało")
    assert d["parameters"]["traction_installed_power_kw"]["value"]==2160.0, (
        "moc zainstalowana w rejestrze to %r zamiast 2160.0"
        % d["parameters"]["traction_installed_power_kw"]["value"])
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

def _only_path(only):
    """`only` -> pelna sciezka modulu testowego albo `ValueError`.

    Przyjmuje nazwe (`test_runner_options`), nazwe z rozszerzeniem i sciezke — bo
    strazniki `__main__` w modulach podaja `__file__`, a czlowiek w wierszu polecen
    poda nazwe. Nieznany modul jest ODMOWA, nie pustym przebiegiem: pusty przebieg
    to dokladnie ten wynik, ktorego ta gałąź ma nie dawac (6.D25).
    """
    wanted = os.path.basename(only)
    if not wanted.endswith(".py"):
        wanted += ".py"
    # Istniejaca sciezka do pliku `test_*.py` jest brana wprost, takze spoza
    # `AG.paths()` — tak wchodza moduly piaskownicy bramki 6.D25, lezace w katalogu
    # tymczasowym. Literowki to nie przepuszcza: nazwa z bledem nie jest plikiem.
    if wanted.startswith("test_") and os.path.isfile(only):
        return os.path.abspath(only)
    for path in AG.paths():
        if os.path.basename(path) == wanted:
            return path
    raise ValueError(f"nie ma takiego modulu testowego: {only}")

def _sciezki_do_przebiegu(only):
    """`only` -> lista sciezek modulow. `None` znaczy CALY zestaw.

    **Lista, a nie jeden modul, i to jest cala tresc 6.D114.** Do 11.09.2026 galaz
    `__main__` konczyla sie na `main(sys.argv[1])`, wiec `argv[2]` i dalsze byly
    odrzucane BEZ SLOWA: wywolanie `test_all.py a.py b.py c.py d.py` dawalo wynik
    modulu `a.py` i kod zero, czyli wynik, ktory WYGLADA jak wynik tego, o co sie
    prosilo. Zmierzone tak, jak sie tego dowiedzialem — przy 6.D101 wzialem wynik
    jednego modulu za wynik czterech.

    **Wybor: uruchamiamy wszystkie wymienione, a nie odmawiamy.** Pole „Wyjscie"
    6.D114 dopuszcza oba, wiec powod stoi tutaj. Uruchomienie wielu modulow nie jest
    nowa zdolnoscia tego pliku — przebieg bez argumentu robi to samo dla 129 modulow
    i przechodzi ta sama droga (licznik asercji, werdykt, kod wyjscia). Odmowa
    zostawialaby wiec bez odpowiedzi wywolanie, ktore narzedzie umie obsluzyc,
    a ktore czlowiek pisze odruchowo po pierwszej czerwonej bramce.

    **Powtorzony modul jest ODMOWA, nie podwojnym przebiegiem.** Ten sam plik dwa razy
    policzylby swoje testy dwa razy, a `N/M przeszlo` jest liczba, ktora czyta
    `mutation_sweep.run_suite` jako werdykt — zawyzenie mianownika jest tu tego samego
    rodzaju bledem co ciche pominiecie argumentu, tylko w druga strone.
    """
    if only is None:
        return AG.paths()
    nazwy = [only] if isinstance(only, str) else list(only)
    if not nazwy:
        raise ValueError("pusta lista modulow — nie ma czego uruchomic")
    sciezki = []
    for nazwa in nazwy:
        sciezka = _only_path(nazwa)
        if sciezka in sciezki:
            raise ValueError(f"modul podany dwa razy: {nazwa}")
        sciezki.append(sciezka)
    return sciezki


def _discover(only=None):
    """Moduły `tools/tests/test_*.py`, ten plik włącznie — albo JEDEN, gdy `only`.

    `only` (6.D25) zawęża odkrywanie do jednego pliku i jest jedyną różnicą między
    przebiegiem całego zestawu a przebiegiem pojedynczego modułu. Reszta drogi —
    licznik asercji, werdykt, wypis, kod wyjścia — jest ta sama, więc uruchomienie
    jednego modułu nie może być łagodniejsze od uruchomienia wszystkich.

    Każdy idzie przez `assertion_gate.load_instrumented`, czyli z licznikiem asercji
    wstrzykniętym w AST. Ten plik też — inaczej jego własne testy byłyby jedynymi,
    których bramka nie mierzy, a to dokładnie ta luka, którą bramka ma zamykać.
    Kopia dostaje inną nazwę modułu, więc strażnik `__name__=="__main__"` na jej
    końcu nie odpala `main()` rekurencyjnie.

    Zwraca `(tests, module_of, import_failures)`: `tests` jest płaską listą
    `(nazwa, funkcja)` — kształt, którego `len(tests)` używa reszta tego pliku
    i którego literalnie szuka `test_assertion_gate.py` — a `module_of` to lista
    tej samej długości, plik źródłowy (bez `.py`) dla każdego testu na tym samym
    indeksie. Osobna lista, nie słownik `nazwa -> moduł`, bo dwa różne pliki
    testowe mogą mieć funkcję o tej samej nazwie (żaden dziś nie ma, ale nic tego
    nie gwarantuje).

    `import_failures` to lista `(plik, wyjątek)` dla modułów, których
    `AG.load_instrumented` nie zdołało załadować — np. błąd składni. Bez tego
    taki wyjątek leciałby nieprzechwycony z `main()`: proces kończyłby się
    kodem 1 (poprawnie), ale bez ani jednego wiersza `FAIL` i bez wiersza
    `N/M przeszło` — niewidoczne dla `grep -cE '^\\s*FAIL'` (zmierzone 06.09.2026
    przy 6.D15, #301, na module z błędem składni: `SyntaxError` na stderr,
    zero dopasowań na grepie).
    """
    tests=[]
    module_of=[]
    import_failures=[]
    for path in _sciezki_do_przebiegu(only):
        module_file=os.path.basename(path)[:-3]
        name=module_file
        if name=="test_all": name="test_all__mierzony"
        try:
            mod=AG.load_instrumented(path,name)
        except SystemExit as e:
            # 6.D65: DRUGIE drzwi. Patrz `WyjscieZImportu` — bez tej gałęzi moduł
            # wychodzący z procesu przy imporcie kończył CAŁY zestaw kodem z wyjątku
            # i bez ani jednego wiersza wyjścia.
            import_failures.append((module_file,WyjscieZImportu(_powod_wyjscia_importu(e))))
            continue
        except Exception as e:
            import_failures.append((module_file,e))
            continue
        found=[(n,f) for n,f in sorted(vars(mod).items()) if n.startswith("test_") and callable(f)]
        tests+=found
        module_of+=[module_file]*len(found)
    return tests, module_of, import_failures

class WyjscieZImportu(Exception):
    """Modul zawolal `sys.exit()` PRZY IMPORCIE. Zamieniane na FAIL IMPORTU.

    **6.D65, zmierzone 09.09.2026 na `dafb7a1`.** 6.D54 naprawilo te sama usterke
    na sciezce WYKONANIA testu i zostawilo drugie drzwi otwarte. Petla importu
    w `_discover` lapala `except Exception`, a `SystemExit` dziedziczy
    z `BaseException` — wiec wychodzil z petli, z `main()` i z procesu, z kodem
    z wyjatku. Przy `sys.exit(0)` tym kodem bylo ZERO, a zestaw nie wypisywal ani
    jednego wiersza. Sonda z jednym celowo padajacym testem:

        kod wyjscia calego zestawu: 0
        bajtow wyjscia zestawu: 0
        ile FAIL: 0

    **Dlaczego to bylo najgrozniejsze, co ten zestaw mogl robic.** Milczenie
    zestawu jest nieodroznialne od jego sukcesu, wiec ta jedna galaz uniewazniala
    KAZDE raportowane „kod 0" — nie dlatego, ze ktorys modul tak robil, ale
    dlatego, ze gdyby zaczal, nie byloby o tym ani jednego sygnalu.

    **Dlaczego OSOBNA klasa, a nie `WyjscieZProcesu`.** Tamta mowi o tescie, ktory
    zawolal `sys.exit()` w swoim ciele, i jej komunikat kaze zlapac `SystemExit`
    W TESCIE. Tutaj winowajca jest sam modul przy imporcie i rada jest inna: kod,
    ktory wychodzi z procesu, nie moze stac na poziomie modulu. Jeden komunikat na
    dwie rozne rady bylby mylacy dokladnie w chwili, w ktorej ktos go czyta.

    **Czego to NIE zmienia.** Modul z bledem skladni nadal konczy jako niepowodzenie
    importu (`except Exception` ponizej), a `SystemExit` w ciele testu nadal jest
    FAIL-em testu przez `WyjscieZProcesu`. Rozny jest tylko trzeci przypadek, ktory
    do dzis nie mial zadnej galezi.
    """


def _powod_wyjscia_importu(wyjatek):
    """Komunikat FAIL-a dla modulu, ktory wyszedl z procesu przy imporcie.

    Kod wyjscia jest w komunikacie z tego samego powodu co w `_powod_wyjscia`:
    `sys.exit(0)` i `sys.exit(2)` maja rozne przyczyny. Rada jest jednak inna,
    bo winowajca jest inny — patrz `WyjscieZImportu`.
    """
    return (f"zawolal sys.exit({wyjatek.code!r}) PRZY IMPORCIE modulu — kod na "
            "poziomie modulu nie moze wychodzic z procesu, bo wynosi sterowanie "
            "z calego zestawu. Przenies to wywolanie do `if __name__ == \"__main__\":` "
            "albo do ciala testu, gdzie `SystemExit` jest FAIL-em jednego testu")


class WyjscieZProcesu(Exception):
    """Test zawołał `sys.exit()`. Zamieniane na FAIL TESTU, nie na koniec przebiegu.

    **6.D54, zmierzone 08.09.2026.** `SystemExit` dziedziczy z `BaseException`,
    a nie z `Exception`, więc `except Exception` w pętli go NIE łapał — wychodził
    z pętli i z `main()`, a Python kończył proces kodem z wyjątku. Przy
    `sys.exit(0)` tym kodem było **zero**. Sonda z trzema testami, w której drugi
    woła `sys.exit(0)`, dawała:

        ok   test_aaa_pierwszy_zwykly
        kod: 0

    Jeden wiersz `ok`, **ani jednego** wiersza `N/M przeszło` ani `RAZEM`, i kod 0.
    Cały wypis przebiegu miał **jeden wiersz**. Kod wyjścia tego zestawu jest wyrocznią
    zieloności całego projektu (`CLAUDE.md` §5), więc wyrocznia mówiła „zielono"
    o przebiegu, który się nie odbył.

    **Ile testów przez to nie wykonało się, zależy od MIEJSCA winnego testu
    w sortowaniu, i dlatego stoi tu jako przedział, nie jedna liczba.** Moduły idą
    alfabetycznie: sonda nazwana `test_aaa_…` zabiła przebieg po **jednym** teście
    z 2041 odkrytych (2040 bez werdyktu), a ta sama sonda nazwana `test_zzz_…` — po
    2039 (2 bez werdyktu). Kod wyjścia był **0 w obu wypadkach**, i to jest niezmiennik
    usterki; liczba utraconych testów niezmiennikiem nie jest.

    **Kłamstwo było jednostronne w WERDYKCIE, ale nie w SKUTKU**, i to rozróżnienie
    jest powodem, dla którego przechwyt jest tu, a nie w kodzie wyjścia: `sys.exit(1)`
    dawał kod 1, czyli czerwono — ale zestaw równie dobrze się nie wykonał, bez
    podsumowania. Naprawa kodu wyjścia załatwiłaby tylko połowę; dlatego obok tej
    klasy stoi w `main()` osobny FAIL zestawu na „wykonano mniej, niż odkryto".

    **Zmierzone też to, co widać było mimo usterki:** przy pierwszej wersji sondy
    (bez strażnika `__main__`) wypisały się DWA wiersze `FAIL` od innych bramek,
    a kod wyjścia i tak wyszedł **0** — wyrocznia nie zgadzała się z własnym wypisem.

    **Osiągalne realnie, nie teoretycznie:** `argparse` woła `sys.exit` przy złym
    argumencie i przy `--help`, a testy bramek wołają `main()` narzędzi. Pułapka
    uderzyła 08.09.2026 w pracy nad `crosscheck_alignment.py`: przebieg skończył się
    kodem 2 na trzecim teście i osiem następnych nie wykonało się wcale.
    """


def _powod_wyjscia(wyjatek):
    """Komunikat FAIL-a dla testu, który zawołał `sys.exit()`.

    Kod wyjścia jest w komunikacie, bo `sys.exit(0)` i `sys.exit(2)` mają różne
    przyczyny: pierwsze to zwykle `--help` albo pomyłkowe `main()` narzędzia,
    drugie to `argparse` odrzucający argument. Bez tej liczby czytający widziałby
    „test wyszedł z procesu" i nie wiedziałby, czego szukać.
    """
    return (f"zawołał sys.exit({wyjatek.code!r}) — wyjście z procesu WEWNĄTRZ testu "
            "jest usterką tego testu, nie werdyktem o zestawie. Jeżeli test sprawdza "
            "narzędzie, które woła sys.exit (argparse, `main()` z bramką), złap "
            "SystemExit w teście i sprawdź jego kod asercją")


def zapisz_czasy(sciezka, module_seconds, module_counts, wall_s, odkryte):
    """Maszynowy zapis czasu przebiegu: moduły, commit, runner, wersja Pythona.

    **Po co (6.D93).** Wypis „czas per moduł (malejąco)" istniał wyłącznie w logu
    pojedynczego przebiegu, a `python-tests.yml` nie miał ANI JEDNEGO kroku
    `upload-artifact` — trendu nie było z czego zbudować, a lista `POMIARY`
    w `test_suite_runtime_budget.py` była i jest uzupełniana ręcznie.

    **Czego tu NIE MA i dlaczego.** Czasu CPU: mierzy go powłoka wbudowanym `times`
    wokół całego procesu (6.D42), bo w `$(...)` daje zera i bo interesuje nas CPU
    DZIECI, a nie tego interpretera. Dokłada go `tools/ci/timing_record.py`, który
    dostaje jedno i drugie od kroku CI. Rozdział jest celowy: ten plik wie o modułach,
    tamten o maszynie.

    Wpisów modułów jest tyle, ile modułów przebieg WYKONAŁ — nie tyle, ile odkrył.
    Obie liczby są w pliku (`modulow`, `odkryte`), bo różnica między nimi jest
    dokładnie tym, co 6.D54 kazało uczynić niemożliwym do pominięcia.
    """
    dane = {
        "schema": 1,
        "commit": os.environ.get("GITHUB_SHA", ""),
        "runner": os.environ.get("RUNNER_NAME", ""),
        "workflow": os.environ.get("GITHUB_WORKFLOW", ""),
        "python": sys.version.split()[0],
        "wall_s": round(wall_s, 3),
        "odkryte": odkryte,
        "wykonane": sum(module_counts.values()),
        "modulow": len(module_seconds),
        "moduly": [
            {"modul": m + ".py",
             "sekundy": round(module_seconds[m], 3),
             "testow": module_counts[m]}
            for m in sorted(module_seconds, key=lambda m: -module_seconds[m])
        ],
    }
    katalog = os.path.dirname(os.path.abspath(sciezka))
    if katalog:
        os.makedirs(katalog, exist_ok=True)
    with open(sciezka, "w", encoding="utf-8") as uchwyt:
        json.dump(dane, uchwyt, ensure_ascii=False, indent=1)
    return dane


def main(only=None):
    """Uruchom zestaw — albo jeden moduł, gdy `only`. Test, który przeszedł bez asercji, jest awarią, nie sukcesem.

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
    tests,module_of,import_failures=_discover(only); passed=0; skipped=[]; failed=[]; checks_total=0
    module_seconds={}; module_counts={}
    suite_start=time.perf_counter()
    for module_file,error in import_failures:
        line=f"<import>{module_file}"
        print(f"  FAIL {line}: {error.__class__.__name__}: {error}")
        failed.append(line)
    przerwane=None
    try:
        for (name,fn),module_file in zip(tests,module_of):
            AG.reset(); outcome=None
            test_start=time.perf_counter()
            try: fn()
            except SystemExit as e: outcome=WyjscieZProcesu(_powod_wyjscia(e))
            except Exception as e: outcome=e
            module_seconds[module_file]=module_seconds.get(module_file,0.0)+(time.perf_counter()-test_start)
            module_counts[module_file]=module_counts.get(module_file,0)+1
            checks=AG.hits(); checks_total+=checks
            state,message=AG.verdict(outcome,checks)
            if state=="ok": print(f"  ok   {name}"); passed+=1
            elif state=="skip": print(f"  SKIP {name}: {message}"); skipped.append(name)
            else: print(f"  FAIL {name}: {message}"); failed.append(name)
    except BaseException as e:
        # `KeyboardInterrupt` (i cokolwiek innego z `BaseException`) DALEJ przerywa
        # przebieg — ale nie wolno mu wynieść sterowania z `main()`, bo wtedy nie
        # wypisze się podsumowanie i kod procesu weźmie się z wyjątku. Pętla staje,
        # podsumowanie leci, kod wychodzi niezerowy. `SystemExit` tu nie dochodzi:
        # jest złapany per test wyżej i jest FAIL-em testu, nie końcem przebiegu.
        przerwane=e
    suite_elapsed=time.perf_counter()-suite_start
    print(); print(f"  {passed}/{len(tests)-len(skipped)} przeszło")
    if skipped: print(f"  pominięto (nie liczy się jako zaliczone): {len(skipped)} — {', '.join(skipped)}")
    print(); print("  czas per moduł (malejąco):")
    for module_file in sorted(module_seconds,key=lambda m:-module_seconds[m]):
        secs=module_seconds[module_file]; n=module_counts[module_file]
        print(f"    {secs:8.3f} s  {module_file}.py  ({n} testów)")
    print(f"  RAZEM {suite_elapsed:.3f} s, {len(tests)} testów, {len(module_seconds)} modułów")
    # 6.D93: ten sam pomiar, co wiersze wyżej, ale MASZYNOWO — i tylko wtedy, gdy
    # ktoś o to poprosi zmienną `METRO_TIMING_OUT`. Bez zmiennej nie powstaje żaden
    # plik: zapis do drzewa przy każdym przebiegu byłby dokładnie tym oknem, które
    # 6.D90 zmierzyło jako mylące dla równoległej kontroli czystości. Krok CI wskazuje
    # `$RUNNER_TEMP`, czyli miejsce poza workspace'em, którego `git clean` nie widzi.
    #
    # Kod wyjścia NIE zależy od tego zapisu i to jest warunek, nie szczegół:
    # `mutation_sweep.run_suite` czyta z tego procesu wyłącznie `N/M przeszło`
    # i kod, więc awaria zapisu nie ma prawa zamienić się w falę fałszywych „zabić".
    zapis_czasu = os.environ.get("METRO_TIMING_OUT")
    if zapis_czasu:
        try:
            zapisz_czasy(zapis_czasu, module_seconds, module_counts,
                         suite_elapsed, len(tests))
            # Wiersz jest tu po to, żeby dało się z ZEWNĄTRZ odróżnić przebieg,
            # który czegoś nie zapisał, od przebiegu, który zapisał gdzie indziej.
            # Bez niego kontrola „bez zmiennej nie ma pliku" sprawdza wyłącznie
            # ścieżkę, o którą sama poprosiła — zmierzone: zapis pod ustaloną nazwą
            # w /tmp przechodził ją bez mrugnięcia.
            print(f"  [CZAS] zapisano {zapis_czasu}")
        except OSError as e:
            print(f"  UWAGA: nie zapisano czasów do {zapis_czasu}: {e}")
    # 6.D54: podsumowanie musi być NIEMOŻLIWE do pominięcia. Powyższe wiersze mówią
    # o testach, które doszły do werdyktu; ten mówi, czy doszły WSZYSTKIE odkryte.
    # Komunikat mówi „nie doszło do werdyktu", a NIE „nie wykonało się wcale":
    # test, który rzucił `KeyboardInterrupt`, zaczął się i zginął w połowie, więc
    # zdanie o niewykonaniu byłoby o nim nieprawdziwe. Zmierzone kontrolą: sonda
    # z `KeyboardInterrupt` w drugim z trzech testów daje 2039 z 2041, czyli dwa
    # bez werdyktu — przerywający i ten po nim.
    # Bez tego przebieg urwany w środku wyglądał jak przebieg pełny o mniejszej
    # liczbie testów — a `mutation_sweep.py` czyta wyłącznie `N/M przeszło` i kod.
    wykonane=sum(module_counts.values())
    if przerwane is not None:
        print(f"  FAIL <przebieg>: przerwany przez {przerwane.__class__.__name__}"
              f"{': '+str(przerwane) if str(przerwane) else ''} — wykonano {wykonane} "
              f"z {len(tests)} odkrytych testów")
        failed.append("<przebieg>")
    if wykonane<len(tests):
        print(f"  FAIL <zestaw>: wykonano {wykonane} z {len(tests)} odkrytych testów, "
              f"czyli {len(tests)-wykonane} nie doszło do werdyktu — podsumowania wyżej "
              "NIE wolno czytać jako werdyktu o całym zestawie")
        failed.append("<zestaw>")
    broken=AG.suite_verdict(len(tests),checks_total)
    if broken: print(f"  FAIL <bramka asercji>: {broken}"); return 1
    return 1 if failed else 0

# `main()` bez argumentu zostaje przebiegiem CAŁEGO zestawu i to jest warunek, pod
# ktorym wolno bylo dopisac `only`: wolaja je tak `mutation_sweep.py` (podproces bez
# argumentow) i `test_assertion_gate.py` (wprost, w tym samym procesie). Rozbior
# wiersza polecen stoi wiec TUTAJ, a nie w `main()` — w `main()` wyjmowalby argumenty
# spod tamtych dwoch wywolan.
if __name__=="__main__": sys.exit(main(sys.argv[1:]) if len(sys.argv)>1 else main())
