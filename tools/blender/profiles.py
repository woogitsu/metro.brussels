"""Profile projektowe przekrojów tuneli — czysty Python, bez bpy."""
import math

M7_WIDTH_M=2.70
M7_HEIGHT_M=3.60
M7_ROOF_CHAMFER_M=0.35
CLEARANCE_M=0.30

def vehicle_gauge(clearance=CLEARANCE_M):
    hw=M7_WIDTH_M/2+clearance; h=M7_HEIGHT_M+clearance; ch=M7_ROOF_CHAMFER_M
    return [(-hw,-0.10),(hw,-0.10),(hw,h-ch),(hw-ch,h),(-hw+ch,h),(-hw,h-ch)]

PROFILES={
 "bore_single":{"kind":"arc","radius":3.05,"center_y":1.45,"floor_offset":-1.20,"segments":28,"tracks":1,"track_offsets":[0.0],"source_level":"design","desc":"projektowy tunel drążony jednotorowy"},
 "box_double":{"kind":"poly","points":[(-4.70,-1.20),(4.70,-1.20),(4.70,4.30),(4.15,4.70),(-4.15,4.70),(-4.70,4.30)],"tracks":2,"track_offsets":[-2.10,2.10],"source_level":"design","desc":"projektowy tunel dwutorowy"},
 "station":{"kind":"poly","points":[(-7.60,-1.20),(7.60,-1.20),(7.60,4.60),(6.80,5.30),(-6.80,5.30),(-7.60,4.60)],"tracks":2,"track_offsets":[-2.10,2.10],"platform_height_m":1.05,"platform_edge_x":[-4.05,4.05],"source_level":"design","desc":"projektowa komora stacyjna"}
}

def profile_points(name):
    spec=PROFILES[name]
    if spec["kind"]=="poly": return list(spec["points"])
    r,cy,floor,segs=spec["radius"],spec["center_y"],spec["floor_offset"],spec["segments"]
    half=math.sqrt(r**2-(cy-floor)**2); a0=math.atan2(floor-cy,half)
    pts=[(-half,floor),(half,floor)]
    for i in range(segs+1):
        a=a0+(math.pi-2*a0)*i/segs; pts.append((round(r*math.cos(a),4),round(cy+r*math.sin(a),4)))
    return _dedupe(pts)

def _dedupe(pts,eps=0.01):
    out=[]
    for p in pts:
        if not out or math.dist(p,out[-1])>eps: out.append(p)
    if len(out)>2 and math.dist(out[0],out[-1])<=eps: out.pop()
    return out

def bbox(name):
    pts=profile_points(name); xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return min(xs),min(ys),max(xs),max(ys)

def dimensions(name):
    x0,y0,x1,y1=bbox(name); return x1-x0,y1-y0

def _vertical_hits(name,x):
    pts=profile_points(name); hits=[]
    for i in range(len(pts)):
        x1,y1=pts[i]; x2,y2=pts[(i+1)%len(pts)]
        if x1==x2: continue
        if min(x1,x2)<=x<=max(x1,x2):
            t=(x-x1)/(x2-x1); hits.append(y1+t*(y2-y1))
    return hits

def _inside(name,x,y):
    x0,_,x1,_=bbox(name)
    if not x0<=x<=x1: return False
    hits=_vertical_hits(name,x)
    return bool(hits) and min(hits)<=y<=max(hits)

def fits_gauge(name,clearance=CLEARANCE_M,samples=40):
    gauge=vehicle_gauge(clearance)
    for off in PROFILES[name].get("track_offsets",[0.0]):
        for i in range(len(gauge)):
            x1,y1=gauge[i]; x2,y2=gauge[(i+1)%len(gauge)]
            for k in range(samples+1):
                t=k/samples; px=off+x1+t*(x2-x1); py=y1+t*(y2-y1)
                if not _inside(name,px,py): return False,f"skrajnia wychodzi poza {name}"
    return True,"ok"

def min_clearance(name,lo=0.0,hi=1.5,eps=0.005):
    if not fits_gauge(name,lo)[0]: return 0.0
    while hi-lo>eps:
        mid=(lo+hi)/2
        if fits_gauge(name,mid)[0]: lo=mid
        else: hi=mid
    return round(lo,3)

def report():
    out=[]
    for name in PROFILES:
        w,h=dimensions(name); ok,msg=fits_gauge(name); cl=min_clearance(name) if ok else 0
        out.append(f"{name:<14} {w:>5.2f} x {h:>5.2f} m  tory={PROFILES[name]['tracks']}  skrajnia={'OK' if ok else msg}  luz_max={cl:.2f} m")
    return "\n".join(out)

if __name__=="__main__": print(report())
