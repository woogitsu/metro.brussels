"""Render kontrolny GLB: izometria, bok i wnętrze. Uruchamianie headless w Blenderze."""
import bpy, sys, os, math, argparse, json
from mathutils import Vector, Matrix

def parse_args():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument("--in",dest="inp",required=True); p.add_argument("--out",required=True); p.add_argument("--res",type=int,default=960); p.add_argument("--centerline"); return p.parse_args(argv)

def clear_scene(): bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)

def mesh_objects(): return [o for o in bpy.context.scene.objects if o.type=="MESH"]

def mesh_world_vertices():
    vertices=[]
    for o in mesh_objects(): vertices.extend(o.matrix_world@v.co for v in o.data.vertices)
    if not vertices: raise SystemExit("BŁĄD: scena nie zawiera siatki")
    return vertices

def scene_bounds(vertices):
    mins=Vector((min(v.x for v in vertices),min(v.y for v in vertices),min(v.z for v in vertices)))
    maxs=Vector((max(v.x for v in vertices),max(v.y for v in vertices),max(v.z for v in vertices)))
    return mins,maxs

def local_vertical_mid(vertices,x,scene_size):
    tolerance=max(1.0,scene_size*0.0015)
    section=[v for v in vertices if abs(v.x-x)<=tolerance]
    if not section:
        nearest=min(vertices,key=lambda v:abs(v.x-x)).x
        section=[v for v in vertices if abs(v.x-nearest)<=1e-4]
    zmin=min(v.z for v in section); zmax=max(v.z for v in section); mid=(zmin+zmax)/2
    print(f"[SECTION-Z] x={x:.1f} vertices={len(section)} zmin={zmin:.2f} zmax={zmax:.2f} mid={mid:.2f}")
    return mid

def load_centerline(path):
    if not path: return None
    with open(path,encoding="utf-8") as f: data=json.load(f)
    raw=data["points"] if isinstance(data,dict) else data
    points=[Vector(tuple(map(float,p))) for p in raw]
    if len(points)<2: raise SystemExit("BŁĄD: centerline do renderu musi mieć co najmniej 2 punkty")
    return points

def point_on_centerline(points,fraction):
    pos=(len(points)-1)*fraction; lo=int(math.floor(pos)); hi=min(lo+1,len(points)-1); t=pos-lo
    return points[lo].lerp(points[hi],t)

def level_camera(cam,direction):
    forward=Vector(direction).normalized(); world_up=Vector((0.0,0.0,1.0))
    if abs(forward.dot(world_up))>0.995: world_up=Vector((0.0,1.0,0.0))
    right=forward.cross(world_up).normalized(); up=right.cross(forward).normalized(); back=-forward
    rotation=Matrix((right,up,back)).transposed()
    cam.rotation_mode="QUATERNION"; cam.rotation_quaternion=rotation.to_quaternion()

def add_camera(loc,look_at,name,scene_size,lens=32,keep_level=False):
    cam_data=bpy.data.cameras.new(name); cam_data.lens=lens
    direction=Vector(look_at)-Vector(loc); distance=direction.length
    cam_data.clip_start=max(0.01,min(0.1,scene_size/100000.0))
    cam_data.clip_end=max(1000.0,scene_size*8.0,distance*3.0)
    cam=bpy.data.objects.new(name,cam_data); bpy.context.collection.objects.link(cam); cam.location=loc
    if keep_level: level_camera(cam,direction)
    else: cam.rotation_euler=direction.normalized().to_track_quat("-Z","Y").to_euler()
    actual=(cam.rotation_quaternion@Vector((0,0,-1))).normalized() if cam.rotation_mode=="QUATERNION" else direction.normalized()
    print(f"[CAMERA] {name} loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) target=({look_at.x:.1f},{look_at.y:.1f},{look_at.z:.1f}) distance_m={distance:.1f} clip_start_m={cam_data.clip_start:.3f} clip_end_m={cam_data.clip_end:.1f} level={keep_level} aim_dot={actual.dot(direction.normalized()):.5f}")
    return cam

def setup_world():
    world=bpy.data.worlds.new("W"); bpy.context.scene.world=world; world.use_nodes=True; world.node_tree.nodes["Background"].inputs[0].default_value=(0.05,0.06,0.08,1); world.node_tree.nodes["Background"].inputs[1].default_value=1.0
    sun_data=bpy.data.lights.new("Sun",type="SUN"); sun_data.energy=3.0; sun=bpy.data.objects.new("Sun",sun_data); bpy.context.collection.objects.link(sun); sun.rotation_euler=(math.radians(55),0,math.radians(35))

def make_material(name,base,emission=None,strength=0.0):
    mat=bpy.data.materials.new(name); mat.use_nodes=True; mat.use_backface_culling=False
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs: bsdf.inputs["Base Color"].default_value=base
        if "Roughness" in bsdf.inputs: bsdf.inputs["Roughness"].default_value=0.9
        if emission is not None:
            if "Emission Color" in bsdf.inputs: bsdf.inputs["Emission Color"].default_value=emission
            elif "Emission" in bsdf.inputs: bsdf.inputs["Emission"].default_value=emission
            if "Emission Strength" in bsdf.inputs: bsdf.inputs["Emission Strength"].default_value=strength
    return mat

def setup_verification_material():
    mat=make_material("verification_surface",(0.42,0.46,0.52,1.0),(0.18,0.21,0.26,1.0),1.2)
    objects=mesh_objects()
    for o in objects: o.data.materials.clear(); o.data.materials.append(mat)
    print(f"[MATERIAL] verification surface assigned to {len(objects)} mesh object(s)")

def add_inside_wire_overlay():
    edge_mat=make_material("verification_wire",(0.015,0.02,0.03,1.0),(0.005,0.008,0.012,1.0),0.2)
    originals=list(mesh_objects()); count=0
    for o in originals:
        dup=o.copy(); dup.data=o.data.copy(); dup.name=f"{o.name}_verification_wire"; bpy.context.collection.objects.link(dup)
        dup.data.materials.clear(); dup.data.materials.append(edge_mat)
        wire=dup.modifiers.new("verification_wire","WIREFRAME"); wire.thickness=0.025; wire.use_replace=True; wire.use_even_offset=True
        count+=1
    print(f"[WIRE] verification wire overlay created for {count} mesh object(s)")

def render_to(cam,path):
    scn=bpy.context.scene; scn.camera=cam; scn.render.filepath=path; scn.render.image_settings.file_format="PNG"; bpy.ops.render.render(write_still=True); print(f"[RENDER] {path}")

def main():
    args=parse_args(); clear_scene(); bpy.ops.import_scene.gltf(filepath=args.inp); setup_world(); setup_verification_material(); scn=bpy.context.scene
    try: scn.render.engine="BLENDER_EEVEE_NEXT"
    except Exception: scn.render.engine="BLENDER_EEVEE"
    scn.render.resolution_x=args.res; scn.render.resolution_y=int(args.res*0.6)
    vertices=mesh_world_vertices(); mins,maxs=scene_bounds(vertices); center=(mins+maxs)/2; size=max((maxs-mins).x,(maxs-mins).y,(maxs-mins).z,1.0); os.makedirs(os.path.dirname(args.out) or ".",exist_ok=True)
    render_to(add_camera(center+Vector((size*0.9,-size*0.9,size*0.7)),center,"cam_iso",size),f"{args.out}_iso.png")
    render_to(add_camera(center+Vector((0,-size*1.4,size*0.15)),center,"cam_side",size),f"{args.out}_side.png")
    points=load_centerline(args.centerline)
    if points:
        eye=point_on_centerline(points,0.05); target=point_on_centerline(points,0.055)
        eye.z=local_vertical_mid(vertices,eye.x,size); target.z=local_vertical_mid(vertices,target.x,size)
        print(f"[INSIDE] exact centerline points={len(points)} local_chord_m={(target-eye).length:.1f}")
    else:
        eye=Vector((mins.x+(maxs.x-mins.x)*0.05,center.y,center.z)); target=Vector((mins.x+(maxs.x-mins.x)*0.055,center.y,center.z))
        print("[INSIDE] WARN no --centerline supplied; using bbox fallback")
    add_inside_wire_overlay()
    render_to(add_camera(eye,target,"cam_inside",size,lens=35,keep_level=True),f"{args.out}_inside.png")
    print(f"[RAPORT] bbox_min=({mins.x:.1f},{mins.y:.1f},{mins.z:.1f}) bbox_max=({maxs.x:.1f},{maxs.y:.1f},{maxs.z:.1f}) size_m={size:.1f}")

if __name__=="__main__": main()
