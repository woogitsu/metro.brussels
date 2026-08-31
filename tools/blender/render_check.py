"""Render kontrolny GLB: izometria, bok i wnętrze. Uruchamianie headless w Blenderze."""
import bpy, sys, os, math, argparse
from mathutils import Vector

def parse_args():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument("--in",dest="inp",required=True); p.add_argument("--out",required=True); p.add_argument("--res",type=int,default=960); return p.parse_args(argv)

def clear_scene(): bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)

def scene_bounds():
    mins=Vector((1e9,1e9,1e9)); maxs=Vector((-1e9,-1e9,-1e9)); found=False
    for o in bpy.context.scene.objects:
        if o.type!="MESH": continue
        found=True
        for c in o.bound_box:
            w=o.matrix_world@Vector(c); mins=Vector((min(mins[i],w[i]) for i in range(3))); maxs=Vector((max(maxs[i],w[i]) for i in range(3)))
    if not found: raise SystemExit("BŁĄD: scena nie zawiera siatki")
    return mins,maxs

def add_camera(loc,look_at,name):
    cam_data=bpy.data.cameras.new(name); cam_data.lens=32; cam=bpy.data.objects.new(name,cam_data); bpy.context.collection.objects.link(cam); cam.location=loc; direction=(Vector(look_at)-Vector(loc)).normalized(); cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler(); return cam

def setup_world():
    world=bpy.data.worlds.new("W"); bpy.context.scene.world=world; world.use_nodes=True; world.node_tree.nodes["Background"].inputs[0].default_value=(0.05,0.06,0.08,1); world.node_tree.nodes["Background"].inputs[1].default_value=1.0
    sun_data=bpy.data.lights.new("Sun",type="SUN"); sun_data.energy=3.0; sun=bpy.data.objects.new("Sun",sun_data); bpy.context.collection.objects.link(sun); sun.rotation_euler=(math.radians(55),0,math.radians(35))

def render_to(cam,path):
    scn=bpy.context.scene; scn.camera=cam; scn.render.filepath=path; scn.render.image_settings.file_format="PNG"; bpy.ops.render.render(write_still=True); print(f"[RENDER] {path}")

def main():
    args=parse_args(); clear_scene(); bpy.ops.import_scene.gltf(filepath=args.inp); setup_world(); scn=bpy.context.scene
    try: scn.render.engine="BLENDER_EEVEE_NEXT"
    except Exception: scn.render.engine="BLENDER_EEVEE"
    scn.render.resolution_x=args.res; scn.render.resolution_y=int(args.res*0.6); mins,maxs=scene_bounds(); center=(mins+maxs)/2; size=max((maxs-mins).x,(maxs-mins).y,(maxs-mins).z,1.0); os.makedirs(os.path.dirname(args.out) or ".",exist_ok=True)
    render_to(add_camera(center+Vector((size*0.9,-size*0.9,size*0.7)),center,"cam_iso"),f"{args.out}_iso.png")
    render_to(add_camera(center+Vector((0,-size*1.4,size*0.15)),center,"cam_side"),f"{args.out}_side.png")
    eye=Vector((mins.x+(maxs.x-mins.x)*0.05,center.y,mins.z+2.0)); target=Vector((maxs.x,center.y,mins.z+2.0)); render_to(add_camera(eye,target,"cam_inside"),f"{args.out}_inside.png")
    print(f"[RAPORT] bbox_min=({mins.x:.1f},{mins.y:.1f},{mins.z:.1f}) bbox_max=({maxs.x:.1f},{maxs.y:.1f},{maxs.z:.1f})")

if __name__=="__main__": main()
