"""Generuje geometrię tunelu przez zamiatanie profilu wzdłuż osi trasy. Uruchamianie headless."""
import bpy, bmesh, json, sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profiles import PROFILES, profile_points, dimensions, fits_gauge

def parse_args():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument("--centerline",required=True); p.add_argument("--profile",default="box_double",choices=list(PROFILES)); p.add_argument("--out",required=True); p.add_argument("--name",default="tunnel"); return p.parse_args(argv)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)

def make_profile_curve(profile_name,name="profile"):
    curve=bpy.data.curves.new(name,type="CURVE"); curve.dimensions="2D"; spline=curve.splines.new("POLY"); pts=profile_points(profile_name); spline.points.add(len(pts)-1)
    for i,(x,y) in enumerate(pts): spline.points[i].co=(x,y,0.0,1.0)
    spline.use_cyclic_u=True; obj=bpy.data.objects.new(name,curve); bpy.context.collection.objects.link(obj); return obj

def make_centerline_curve(points,name="centerline"):
    curve=bpy.data.curves.new(name,type="CURVE"); curve.dimensions="3D"; curve.resolution_u=12; spline=curve.splines.new("NURBS"); spline.points.add(len(points)-1)
    for i,(x,y,z) in enumerate(points): spline.points[i].co=(x,y,z,1.0)
    spline.order_u=4; spline.use_endpoint_u=True; obj=bpy.data.objects.new(name,curve); bpy.context.collection.objects.link(obj); return obj

def main():
    args=parse_args(); clear_scene()
    with open(args.centerline,encoding="utf-8") as f: data=json.load(f)
    points=data["points"] if isinstance(data,dict) else data
    if len(points)<2: raise SystemExit("BŁĄD: oś trasy musi mieć co najmniej 2 punkty")
    ok,msg=fits_gauge(args.profile)
    if not ok: raise SystemExit(f"BŁĄD: profil {args.profile} nie mieści skrajni M7 — {msg}")
    profile=make_profile_curve(args.profile); center=make_centerline_curve(points,args.name); center.data.bevel_mode="OBJECT"; center.data.bevel_object=profile; center.data.use_fill_caps=False
    bpy.context.view_layer.objects.active=center; center.select_set(True); bpy.ops.object.convert(target="MESH"); mesh_obj=bpy.context.active_object; mesh_obj.name=args.name
    bm=bmesh.new(); bm.from_mesh(mesh_obj.data); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(mesh_obj.data); bm.free(); bpy.data.objects.remove(profile,do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT"); mesh_obj.select_set(True); bpy.context.view_layer.objects.active=mesh_obj; bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    os.makedirs(os.path.dirname(args.out) or ".",exist_ok=True); bpy.ops.export_scene.gltf(filepath=args.out,export_format="GLB",use_selection=True)
    verts=len(mesh_obj.data.vertices); faces=len(mesh_obj.data.polygons); dims=mesh_obj.dimensions; pw,ph=dimensions(args.profile)
    print(f"[RAPORT] plik={args.out}"); print(f"[RAPORT] profil={args.profile} ({pw:.2f} x {ph:.2f} m) punkty_osi={len(points)}"); print(f"[RAPORT] wierzcholki={verts} sciany={faces}"); print(f"[RAPORT] wymiary_m: X={dims.x:.1f} Y={dims.y:.1f} Z={dims.z:.1f}")
    if verts==0 or faces==0: raise SystemExit("BŁĄD: geometria pusta")

if __name__=="__main__": main()
