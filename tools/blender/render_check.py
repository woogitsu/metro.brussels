"""Render kontrolny GLB: izometria, bok i wnętrze. Uruchamianie headless w Blenderze.

Dwie rzeczy poza samym renderem:

* każda klatka jest po zapisaniu ZMIERZONA — klatka poniżej podłogi widoczności
  kończy skrypt błędem, bo do tej pory pusty PNG wyglądał dokładnie tak samo jak
  brak geometrii i przechodził z kodem 0;
* `--from-m/--to-m` kadruje wycinek osi, bo kamera na całym bboxie sprowadza detal
  do ułamka piksela.

Podłoga jest podłogą, nie oceną: przechodzi ją także kadr, na którym 5 km tunelu
jest jednopikselową kreską. Obejrzenie PNG zostaje obowiązkowe (`CLAUDE.md` §5) —
„ink=0.0025" nie mówi, czy widać to, co miało być widać.
"""
import bpy, sys, os, math, argparse, json
from mathutils import Vector, Matrix

HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,"..","visual"))
import camera_aim as CA
import placement, sweep
import compare, pngio

def parse_args():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser(); p.add_argument("--in",dest="inp",required=True); p.add_argument("--out",required=True); p.add_argument("--res",type=int,default=960); p.add_argument("--centerline")
    p.add_argument("--from-m",dest="from_m",type=float,help="początek okna kadru w metrach osi (wymaga --centerline)")
    p.add_argument("--to-m",dest="to_m",type=float,help="koniec okna kadru w metrach osi")
    return p.parse_args(argv)

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
    """Środek pionowy przekroju o STAŁYM X. Zostawione dla zgodności wywołań.

    Nowy kod ma używać `vertical_mid_on_axis`: płat o stałym X jest przekrojem tunelu
    tylko wtedy, gdy tunel biegnie wzdłuż X.
    """
    return _vertical_mid(Vector((x,0.0,0.0)),Vector((1.0,0.0,0.0)),vertices,scene_size,f"x={x:.1f}")

def vertical_mid_on_axis(vertices,point,tangent,scene_size):
    """Środek pionowy przekroju PROSTOPADŁEGO do osi trasy w zadanym punkcie.

    Na chunku pakietu A biegnącym pod kątem do X płat o stałym X łapał sam strop
    i zwracał 4,70 m zamiast 1,75 m, przez co oko kamery lądowało w płycie stropowej,
    a render wychodził jednolitą płaszczyzną — i **przechodził** kontrolę pustej klatki.
    """
    normal=Vector(tangent)
    if CA.is_degenerate(tuple(tangent)): return local_vertical_mid(vertices,point.x,scene_size)
    origin=Vector(point)
    return _vertical_mid(origin,normal,vertices,scene_size,
                         f"os=({origin.x:.1f},{origin.y:.1f})")

def _vertical_mid(origin,normal,vertices,scene_size,label):
    zmin,zmax,count=placement.section_vertical_stable([(v.x,v.y,v.z) for v in vertices],
                                               tuple(origin),tuple(normal),
                                               max(1.0,scene_size*0.0015))
    if placement.is_degenerate_section(zmin,zmax):
        raise SystemExit(f"BŁĄD: przekrój {label} ma wysokość {zmax-zmin:.3f} m "
                         f"({count} wierzchołków) — to nie jest przekrój tunelu")
    mid=(zmin+zmax)/2
    print(f"[SECTION-Z] {label} vertices={count} zmin={zmin:.2f} zmax={zmax:.2f} mid={mid:.2f}")
    return mid

def load_centerline(path):
    if not path: return None
    with open(path,encoding="utf-8") as f: data=json.load(f)
    raw=data["points"] if isinstance(data,dict) else data
    points=[Vector(tuple(map(float,p))) for p in raw]
    if not CA.enough_centerline_points(len(points)):
        raise SystemExit(f"BŁĄD: centerline do renderu musi mieć co najmniej {CA.MIN_CENTERLINE_POINTS} punkty")
    return points

def point_on_centerline(points,fraction):
    lo,hi,t=CA.centerline_position(len(points),fraction)
    return points[lo].lerp(points[hi],t)

def level_camera(cam,direction):
    forward=Vector(direction).normalized()
    world_up=Vector(CA.up_reference((direction[0],direction[1],direction[2])))
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

def make_normals_material():
    """Material, w ktorym TYL sciany swieci, a przod nie.

    **Po co osobny material, skoro §5 mowi „widac przez sciane\".** Bo materialu
    kontrolnego nie wolno zmienic na jednostronny: `render_check.py` renderuje takze
    pudlo pojazdu i przekroje stacji, ogladane legalnie od tylu. Kulling na wspolnym
    materiale zapalalby sie na poprawnej geometrii, a bramka, ktora falszywie alarmuje,
    zostaje wylaczona przez pierwszego zirytowanego czlowieka (6.D27). Osobna klatka
    nic nie ukrywa i nic nie odbiera — DODAJE sygnal.

    **Dlaczego emisja, a nie kolor bazowy.** Emisja nie zalezy od kata swiatla, wiec
    ta sama sciana daje ten sam poziom niezaleznie od tego, gdzie stoi slonce. Odczyt
    idzie po luminancji, a nie po barwie, bo czytnik PNG tego repozytorium zwraca
    skale szarosci — magenta i szarosc bylyby dla niego tym samym.
    """
    mat=bpy.data.materials.new("verification_normals"); mat.use_nodes=True
    mat.use_backface_culling=False
    tree=mat.node_tree
    for node in list(tree.nodes):
        if node.type!="OUTPUT_MATERIAL": tree.nodes.remove(node)
    out=next(n for n in tree.nodes if n.type=="OUTPUT_MATERIAL")
    geo=tree.nodes.new("ShaderNodeNewGeometry")
    przod=tree.nodes.new("ShaderNodeEmission"); przod.inputs["Color"].default_value=(0.10,0.10,0.10,1.0); przod.inputs["Strength"].default_value=1.0
    tyl=tree.nodes.new("ShaderNodeEmission"); tyl.inputs["Color"].default_value=(0.95,0.95,0.95,1.0); tyl.inputs["Strength"].default_value=1.0
    mix=tree.nodes.new("ShaderNodeMixShader")
    tree.links.new(geo.outputs["Backfacing"],mix.inputs["Fac"])
    tree.links.new(przod.outputs["Emission"],mix.inputs[1])
    tree.links.new(tyl.outputs["Emission"],mix.inputs[2])
    tree.links.new(mix.outputs["Shader"],out.inputs["Surface"])
    return mat

def setup_normals_material():
    mat=make_normals_material(); objects=mesh_objects()
    for o in objects: o.data.materials.clear(); o.data.materials.append(mat)
    print(f"[NORMALNE] material orientacji przypisany do {len(objects)} obiektow")

def normals_verdict(path):
    """Wypisuje udzial tylnej strony. NIE stosuje podlogi pustej klatki.

    Podloga z `frame_verdict` mierzy „czy jest sie czemu przyjrzec\" przez rozrzut
    poziomow szarosci — a ta klatka ma z zalozenia dwa poziomy i przy poprawnej
    geometrii jest niemal jednolita. Puszczenie jej przez tamta podloge zamienialoby
    POPRAWNY wynik w blad, czyli dokladnie odwrotnie niz trzeba.
    """
    udzial=compare.backface_fraction(pngio.read_gray(path))
    print(f"[NORMALNE] {os.path.basename(path)} tylna_strona={udzial:.5f}"
          f"{'  <-- SCIANY ODWROCONE' if udzial>0.5 else ''}")
    print("[NORMALNE] liczba jest podloga, nie ocena — OBEJRZENIE tej klatki jest "
          "nadal obowiazkowe (CLAUDE.md §5)")
    return udzial

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

def frame_verdict(path):
    """Mierzy zapisaną klatkę. Zwraca opis, gdy klatka jest poniżej podłogi, inaczej None.

    Podłoga jest wspólna z pipeline'em wizualnym (`compare.EMPTY_FRAME_FLOOR`), żeby
    render kontrolny i regresja wizualna nie miały dwóch różnych definicji.

    To jest PODŁOGA, nie miara czytelności: prosty tunel widziany z boku ląduje pod
    nią jako jednopikselowa kreska, ale ta sama kreska ustawiona po skosie przechodzi,
    bo antyaliasing daje jej więcej poziomów szarości. Klatka nad podłogą nie znaczy
    więc „widać, co miało być widać" — znaczy tylko „jest się czemu przyjrzeć".
    """
    stats=compare.image_stats(pngio.read_gray(path))
    below=compare.empty_frame_reason(stats,compare.EMPTY_FRAME_FLOOR) is not None
    numbers=(f"ink={stats['ink_fraction']:.5f} std={stats['luma_std']:.5f} "
             f"poziomy={stats['distinct_levels']}")
    print(f"[KLATKA] {os.path.basename(path)} {stats['width']}x{stats['height']} {numbers}"
          f"{' PONIŻEJ PODŁOGI' if below else ''}")
    return f"{os.path.basename(path)} — {numbers}" if below else None

def resolve_window(points,args):
    """Okno kadru z argumentów. Brak obu argumentów => kadr po całym bboxie."""
    if args.from_m is None and args.to_m is None: return None
    if args.from_m is None or args.to_m is None: raise SystemExit("BŁĄD: --from-m i --to-m podaje się razem")
    if not points: raise SystemExit("BŁĄD: okno kadru liczy się po osi — brakuje --centerline")
    try: return placement.axis_window([tuple(p) for p in points],args.from_m,args.to_m)
    except ValueError as bad: raise SystemExit(f"BŁĄD: {bad}")

def main():
    args=parse_args(); clear_scene(); bpy.ops.import_scene.gltf(filepath=args.inp); setup_world(); setup_verification_material(); scn=bpy.context.scene
    try: scn.render.engine="BLENDER_EEVEE_NEXT"
    except Exception: scn.render.engine="BLENDER_EEVEE"
    scn.render.resolution_x=args.res; scn.render.resolution_y=int(args.res*0.6)
    vertices=mesh_world_vertices(); mins,maxs=scene_bounds(vertices); os.makedirs(os.path.dirname(args.out) or ".",exist_ok=True)
    points=load_centerline(args.centerline); window=resolve_window(points,args)
    if window:
        center=Vector(window["center"]); size=window["size"]
        print(f"[OKNO] os {window['from_m']:.1f}-{window['to_m']:.1f} m (dlugosc {window['length_m']:.1f} m) "
              f"center=({center.x:.1f},{center.y:.1f},{center.z:.1f}) size_m={size:.1f}")
        # 6.D140: KTORE kamery okno zawezasz — bo wpis pozycji twierdzil, ze tylko
        # `_inside`, a pomiar pokazal wszystkie cztery. Nazwy ida z `camera_aim`,
        # zeby ten wypis nie byl druga kopia tej wiedzy.
        print("[OKNO] zaweza kamery: " + ", ".join(CA.KAMERY_POD_OKNEM))
        proporcje=CA.proporcje_okna(window["length_m"],(maxs-mins).z)
        if proporcje is not None:
            print(f"[OKNO] proporcje okna {proporcje:.0f} : 1 (dlugosc {window['length_m']:.1f} m "
                  f"/ wysokosc {(maxs-mins).z:.1f} m) — im wieksze, tym bardziej `_side` "
                  "jest kreska; progu tu nie ma, patrz camera_aim.proporcje_okna")
    else:
        center=(mins+maxs)/2; size=max((maxs-mins).x,(maxs-mins).y,(maxs-mins).z,1.0)
    blank=[]
    def shoot(cam,path):
        render_to(cam,path); reason=frame_verdict(path)
        if reason is not None: blank.append(reason)
    shoot(add_camera(center+Vector((size*0.9,-size*0.9,size*0.7)),center,"cam_iso",size),f"{args.out}_iso.png")
    shoot(add_camera(center+Vector((0,-size*1.4,size*0.15)),center,"cam_side",size),f"{args.out}_side.png")
    if points:
        if window:
            # Oko wjeżdża w oknie, nie na 5% całej osi: inaczej widok z wnętrza
            # pokazywałby zupełnie inny kawałek trasy niż izometria i bok.
            axis=[tuple(p) for p in points]; stations=sweep.chainages(axis)
            eye=Vector(placement.frame_at(axis,stations,window["from_m"])[0])
            target=Vector(placement.frame_at(axis,stations,window["from_m"]+0.1*window["length_m"])[0])
        else:
            eye=point_on_centerline(points,0.05); target=point_on_centerline(points,0.055)
        eye.z=target.z=vertical_mid_on_axis(vertices,eye,target-eye,size)
        print(f"[INSIDE] exact centerline points={len(points)} local_chord_m={(target-eye).length:.1f}")
    else:
        eye=Vector((mins.x+(maxs.x-mins.x)*0.05,center.y,center.z)); target=Vector((mins.x+(maxs.x-mins.x)*0.055,center.y,center.z))
        print("[INSIDE] WARN no --centerline supplied; using bbox fallback")
    # Klatka orientacji idzie PRZED nakladka siatki i przed przywroceniem materialu
    # kontrolnego: duplikaty siatki maja wlasne sciany, wiec liczylyby sie do udzialu
    # tylnej strony i mierzylibysmy nakladke zamiast geometrii.
    setup_normals_material()
    render_to(add_camera(eye,target,"cam_normals",size,lens=35,keep_level=True),f"{args.out}_normals.png")
    normals_verdict(f"{args.out}_normals.png")
    setup_verification_material()
    add_inside_wire_overlay()
    shoot(add_camera(eye,target,"cam_inside",size,lens=35,keep_level=True),f"{args.out}_inside.png")
    print(f"[RAPORT] bbox_min=({mins.x:.1f},{mins.y:.1f},{mins.z:.1f}) bbox_max=({maxs.x:.1f},{maxs.y:.1f},{maxs.z:.1f}) size_m={size:.1f}")
    print("[KLATKA] podłoga, nie ocena — obejrzenie PNG jest nadal obowiązkowe (CLAUDE.md §5)")
    if blank:
        raise SystemExit("BŁĄD: klatki poniżej podłogi widoczności geometrii: "+"; ".join(blank)
                         +"\n  kadr po całym bboxie sprowadza obiekt do włosa — zawęź --from-m/--to-m albo renderuj chunk")

if __name__=="__main__": main()
