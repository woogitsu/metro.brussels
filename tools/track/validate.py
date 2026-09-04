#!/usr/bin/env python3
"""Walidator osi trasy data/track/*.json. Kod 0 = OK, 1 = błędy."""
import json, sys, math, argparse, os

LIMITS = {"max_grade_pct":4.0,"min_radius_m":90.0,"max_point_gap_m":25.0,"duplicate_point_gap_m":1e-6,"min_point_gap_m":0.5,"max_station_spacing_m":2200.0,"min_station_spacing_m":250.0,"length_tolerance_m":0.01}
NET = os.path.join(os.path.dirname(__file__), "..", "..", "data", "network", "lines.json")

class Report:
    def __init__(self): self.err, self.warn, self.info = [], [], []
    def E(self,m): self.err.append(m)
    def W(self,m): self.warn.append(m)
    def I(self,m): self.info.append(m)
    def ok(self): return not self.err
    def dump(self):
        for m in self.info: print(f"  ·   {m}")
        for m in self.warn: print(f"  !   {m}")
        for m in self.err: print(f"  X   {m}")
        print(); print(f"  {len(self.err)} błędów, {len(self.warn)} ostrzeżeń")
        return 0 if self.ok() else 1

def dist(a,b): return math.dist(a[:2], b[:2])

def radius3(a,b,c):
    (x1,y1),(x2,y2),(x3,y3)=a[:2],b[:2],c[:2]
    d=2*(x1*(y2-y3)+x2*(y3-y1)+x3*(y1-y2))
    if abs(d)<1e-9: return float("inf")
    ux=((x1**2+y1**2)*(y2-y3)+(x2**2+y2**2)*(y3-y1)+(x3**2+y3**2)*(y1-y2))/d
    uy=((x1**2+y1**2)*(x3-x2)+(x2**2+y2**2)*(x1-x3)+(x3**2+y3**2)*(x2-x1))/d
    return math.dist((ux,uy),(x1,y1))

def _is_subsequence(sub,seq):
    it=iter(seq); return all(any(s==x for x in it) for s in sub)

def validate(path, expect_line=None, expect_package=None):
    r=Report()
    try:
        with open(path,encoding="utf-8") as f: d=json.load(f)
    except Exception as e:
        r.E(f"nie da się wczytać pliku: {e}"); return r
    for key in ("id","points"):
        if key not in d: r.E(f"brak wymaganego pola '{key}'")
    if r.err: return r
    if "crs" not in d: r.W("brak pola 'crs' — udokumentuj układ współrzędnych")
    pts=d["points"]
    if len(pts)<3: r.E(f"oś ma {len(pts)} punktów, potrzeba co najmniej 3"); return r
    for i,p in enumerate(pts):
        if len(p)!=3: r.E(f"punkt {i} ma {len(p)} współrzędnych, oczekiwano 3 [x, y, z]"); return r
    gaps=[dist(pts[i],pts[i+1]) for i in range(len(pts)-1)]; total=sum(gaps)
    r.I(f"punktów: {len(pts)}, długość osi: {total:.1f} m")
    # Deklarowana długość kontra policzona z łamanej. Plik zapisuje length_m zaokrąglone,
    # więc zgodność poniżej centymetra jest maksimum, jakie ten zapis potrafi potwierdzić.
    # Rozjazd większy znaczy, że length_m pochodzi z innej łamanej niż points — a wtedy
    # wszystko, co liczy kilometraż z tego pliku, liczy go z czegoś innego niż geometria.
    declared=d.get("length_m")
    if declared is not None:
        drift=abs(float(declared)-total)
        if drift>LIMITS["length_tolerance_m"]:
            r.E(f"length_m = {declared:.3f} m nie zgadza się z łamaną ({total:.3f} m), różnica {drift:.3f} m")
        else:
            r.I(f"length_m zgodne z łamaną, różnica {drift*1000:.1f} mm")
    # „Bardzo gęsto" i „zdublowany wierzchołek" to DWIE różne rzeczy i do 03.09.2026
    # miały jeden status: ostrzeżenie. Gęste punkty w danych STIB są normalne, więc
    # ostrzeżenie jest dla nich właściwe. Wierzchołek powtórzony daje segment o zerowej
    # długości, a z niego zerowy mianownik: `tools/visual/capture_plan.py`
    # (`point_at_chainage`) ma na to osobną gałąź `span <= 0.0`, a
    # `build_alignment.slice_polyline` ostre `<` w obu warunkach cięcia (#143). To są
    # obrony PRZED danymi, które ten walidator wpuszczał — więc oś z duplikatem szła
    # do wszystkich narzędzi i każde musiało się bronić samo.
    #
    # Próg nie jest nowy: `slice_polyline` odrzuca punkt bliższy niż `1e-6` m od
    # poprzedniego, czyli każda oś WYPRODUKOWANA przez `build_alignment.py` już
    # gwarantuje odstęp co najmniej mikrometrowy. Duplikat, który tu dojedzie, powstał
    # więc poza tą ścieżką. Warunek jest ostry po tej samej stronie co tam: odstęp
    # równy dokładnie mikrometrowi to nadal dwa punkty.
    #
    # Odstęp jest liczony w 2D, tak samo jak cały kilometraż w tym projekcie, więc
    # czysto pionowy uskok (te same x, y, inne z) też jest błędem. To jest zamierzone:
    # taki uskok daje dwa punkty o identycznym kilometrażu, czyli dokładnie ten sam
    # zerowy mianownik.
    for i,g in enumerate(gaps):
        if g>LIMITS["max_point_gap_m"]: r.E(f"odstęp punktów {i}→{i+1} = {g:.1f} m, maks. {LIMITS['max_point_gap_m']} m")
        elif g<LIMITS["duplicate_point_gap_m"]: r.E(f"odstęp punktów {i}→{i+1} = {g:.9f} m — zdublowany wierzchołek, segment o zerowej długości (próg {LIMITS['duplicate_point_gap_m']:g} m to ten sam, co przy sklejaniu w build_alignment.slice_polyline)")
        elif g<LIMITS["min_point_gap_m"]: r.W(f"odstęp punktów {i}→{i+1} = {g:.2f} m — bardzo gęsto, sprawdź duplikaty")
    worst_g,worst_i=0.0,-1
    for i in range(len(pts)-1):
        h=dist(pts[i],pts[i+1])
        if h<1e-6: continue
        g=abs(pts[i+1][2]-pts[i][2])/h*100
        if g>abs(worst_g): worst_g,worst_i=g,i
        if g>LIMITS["max_grade_pct"]: r.E(f"pochylenie {g:.2f}% między punktami {i}→{i+1}, maks. {LIMITS['max_grade_pct']}%")
    if worst_i>=0: r.I(f"największe pochylenie: {worst_g:.2f}% (punkt {worst_i})")
    worst_r,worst_ri=float("inf"),-1
    for i in range(1,len(pts)-1):
        rad=radius3(pts[i-1],pts[i],pts[i+1])
        if rad<worst_r: worst_r,worst_ri=rad,i
        if rad<LIMITS["min_radius_m"]: r.E(f"promień łuku {rad:.0f} m w punkcie {i}, min. {LIMITS['min_radius_m']} m")
    if worst_ri>=0 and worst_r!=float("inf"): r.I(f"najmniejszy promień: {worst_r:.0f} m (punkt {worst_ri})")
    st=d.get("stations",[])
    if not st: r.W("brak listy stacji — dopisz ją zanim użyjesz tej osi do geometrii")
    else:
        ch=[s.get("chainage_m") for s in st]
        if any(c is None for c in ch): r.E("każda stacja musi mieć 'chainage_m'")
        else:
            if ch!=sorted(ch): r.E("kilometraż stacji nie jest rosnący")
            for i in range(len(ch)-1):
                sp=ch[i+1]-ch[i]
                if sp>LIMITS["max_station_spacing_m"]: r.W(f"odstęp stacji {st[i].get('name')} → {st[i+1].get('name')} = {sp:.0f} m — nietypowo dużo")
                if sp<LIMITS["min_station_spacing_m"]: r.E(f"odstęp stacji {st[i].get('name')} → {st[i+1].get('name')} = {sp:.0f} m — za mało")
            # Zapis `chainage_m` i `length_m` jest zaokrąglony do centymetra, więc
            # rozjazd poniżej `length_tolerance_m` nie jest przekroczeniem, tylko granicą
            # rozdzielczości pliku — dokładnie ten sam próg, co przy kontroli `length_m`.
            #
            # Rzut ostatniej stacji potrafi wypaść ZA ostatnim wierzchołkiem osi: punkt
            # przystanku leży nieco dalej niż koniec łamanej, a rzut na przedłużenie
            # ostatniego odcinka daje kilometraż większy niż całość. Tolerancją nie jest
            # więc okrągła liczba, tylko **długość ostatniego odcinka łamanej**: rzut
            # dalszy niż jeden odcinek nie jest artefaktem rzutowania, tylko stacją,
            # która nie leży na tej osi.
            #
            # Poprzednia wersja dawała tu 50 m bez uzasadnienia i przez to przepuszczała
            # milczkiem przekroczenia rzędu pół metra we WSZYSTKICH sześciu pakietach.
            # Pół metra jest nieszkodliwe, ale TrackAxis.PointAt obcina kilometraż do
            # długości osi, więc skład stojący na ostatniej stacji ma w symulacji inny
            # kilometraż niż pozycję w scenie — i nikt się o tym nie dowiaduje.
            if ch:
                over=ch[-1]-total
                if over>gaps[-1]:
                    r.E(f"kilometraż ostatniej stacji ({ch[-1]:.2f} m) wykracza poza oś ({total:.2f} m) "
                        f"o {over:.2f} m — więcej niż ostatni odcinek łamanej ({gaps[-1]:.2f} m)")
                elif over>LIMITS["length_tolerance_m"]:
                    r.W(f"rzut ostatniej stacji wypada {over:.3f} m za końcem osi "
                        f"({ch[-1]:.2f} m wobec {total:.2f} m); mieści się w ostatnim odcinku "
                        f"({gaps[-1]:.2f} m), ale kilometraż jest obcinany przy odczycie pozycji")
                if ch[0]<-gaps[0]:
                    r.E(f"kilometraż pierwszej stacji ({ch[0]:.2f} m) wypada {-ch[0]:.2f} m przed osią — "
                        f"więcej niż pierwszy odcinek łamanej ({gaps[0]:.2f} m)")
                elif ch[0]<-LIMITS["length_tolerance_m"]:
                    r.W(f"rzut pierwszej stacji wypada {-ch[0]:.3f} m przed początkiem osi")
        interp=sum(1 for s in st if s.get("interpolated"))
        if interp: r.I(f"{interp} z {len(st)} głębokości stacji jest interpolowanych")
        missing=[s.get("name") for s in st if s.get("depth_m") is None]
        if missing: r.W(f"brak głębokości dla: {', '.join(str(m) for m in missing[:5])}" + (" …" if len(missing)>5 else ""))
    if expect_line and st:
        try:
            with open(NET,encoding="utf-8") as f: net=json.load(f)
            line=next((l for l in net["lines"] if l["id"]==expect_line),None)
            if not line: r.E(f"linia {expect_line} nie istnieje w lines.json")
            else:
                names=[s.get("name") for s in st]
                # lines.json wypisuje stacje w jedną stronę, a pakiet budowy ma własny
                # kierunek from->to (C: Jacques Brel->Erasme, F: Belgica->Roi Baudouin
                # idą pod prąd tej listy). Oś nie jest kierunkiem jazdy, więc zgodność
                # z listą odwróconą jest tak samo poprawna — ale ma być widoczna.
                if _is_subsequence(names,line["stops"]): r.I(f"kolejność stacji zgodna z lines.json ({expect_line})")
                elif _is_subsequence(names,list(reversed(line["stops"]))): r.I(f"kolejność stacji zgodna z lines.json ({expect_line}), oś biegnie odwrotnie do kolejności z listy")
                else: r.E(f"kolejność stacji niezgodna z lines.json dla {expect_line}")
        except FileNotFoundError: r.W("nie znaleziono data/network/lines.json — pominięto kontrolę zgodności")
    for i,sl in enumerate(d.get("speed_limits",[])):
        if sl["from_m"]>=sl["to_m"]: r.E(f"ograniczenie {i}: from_m >= to_m")
        if not (5<=sl["kmh"]<=80): r.E(f"ograniczenie {i}: {sl['kmh']} km/h poza zakresem 5–80")
    return r

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("path"); ap.add_argument("--line"); ap.add_argument("--package")
    a=ap.parse_args(); print(f"\nWALIDACJA: {a.path}"); print("-"*60); sys.exit(validate(a.path,a.line,a.package).dump())

if __name__=="__main__": main()
