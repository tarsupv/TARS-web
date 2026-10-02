"""Monta el rover TARS a partir de su URDF y lo exporta como GLB para la web.

Cada eslabon del URDF se convierte en un nodo del GLB, colgado de su padre con
el `origin` de su junta. Las juntas moviles guardan en `extras` (que three.js
expone como `userData`) su tipo, eje y limites, asi que la web puede mover
cualquier junta sin conocer la geometria:

    node.quaternion = base * rotacion(axis, q)       (revolute / continuous)
    node.position   = base + axis * q                (prismatic)

Uso (antes, tools/prepare_rover_source.sh para copiar URDF y mallas):
    blender -b -P tools/build_rover_glb.py -- \
        tools/model-source/rover/rover.urdf public/models/rover.glb
"""

import math
import os
import sys
import xml.etree.ElementTree as ET

import bpy
import mathutils

# Presupuesto de triangulos por malla de origen. Las mallas por debajo se dejan
# intactas; las de encima se decima hasta el objetivo. Las ruedas se instancian
# (una sola malla para las cuatro), asi que pesan una vez en el fichero.
TRI_TARGETS = {
    "base_link.obj": 52000,
    "arm_link_1.obj": 16000,
    "arm_link_2.obj": 18000,
    "arm_link_3.obj": 15000,
    "arm_link_4.obj": 9000,
    "arm_link_5.obj": 9000,
    "arm_mount.obj": 10000,
    "wheel_link.obj": 11000,
    "rslidar_frame.obj": 6000,
}

MOVABLE = {"revolute", "continuous", "prismatic"}


def parse_vec(text, default=(0.0, 0.0, 0.0)):
    return tuple(float(v) for v in text.split()) if text else default


def origin_matrix(element):
    """`<origin xyz rpy>` de URDF -> Matrix. rpy es roll/pitch/yaw en ejes fijos,
    que es justo el orden XYZ de Blender (R = Rz @ Ry @ Rx)."""
    if element is None:
        return mathutils.Matrix.Identity(4)
    xyz = parse_vec(element.get("xyz"))
    rpy = parse_vec(element.get("rpy"))
    rot = mathutils.Euler(rpy, "XYZ").to_matrix().to_4x4()
    return mathutils.Matrix.Translation(xyz) @ rot


def to_gltf_axis(axis):
    """El exportador pasa de Z-arriba (URDF/Blender) a Y-arriba (glTF) con
    (x, y, z) -> (x, z, -y) en todos los nodos; el eje guardado en extras no lo
    toca, asi que se convierte aqui igual."""
    x, y, z = axis
    return [x, z, -y]


def load_mesh(path, cache):
    """Importa un OBJ una sola vez y devuelve su malla fusionada y decimada.
    Las siguientes apariciones (ruedas, balancines, camaras) reutilizan la misma
    malla, y el exportador la escribe una unica vez."""
    name = os.path.basename(path)
    if name in cache:
        return cache[name]

    before = set(bpy.data.objects)
    # Ejes identidad: las mallas ya estan en el marco del eslabon (Z arriba),
    # tal y como las lee ROS.
    bpy.ops.wm.obj_import(filepath=path, forward_axis="Y", up_axis="Z")
    parts = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]

    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active

    tris_before = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    target = TRI_TARGETS.get(name)
    if target and tris_before > target:
        mod = obj.modifiers.new("dec", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = target / tris_before
        bpy.ops.object.modifier_apply(modifier=mod.name)
    tris_after = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    print(f"        {name:24s} {tris_before:7d} -> {tris_after:7d} tris")

    mesh = obj.data
    mesh.name = os.path.splitext(name)[0]
    bpy.data.objects.remove(obj, do_unlink=True)
    cache[name] = mesh
    return mesh


def dedupe_materials():
    """El importador crea `Material.001`, `Material.002`... por fichero aunque
    sean el mismo; se colapsan por nombre base para no multiplicar primitivas."""
    canon = {}
    for mat in bpy.data.materials:
        canon.setdefault(mat.name.split(".")[0], mat)
    for mat in list(bpy.data.materials):
        target = canon[mat.name.split(".")[0]]
        if mat is not target:
            mat.user_remap(target)
            bpy.data.materials.remove(mat)
    return len(canon)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    urdf_path, out_path = os.path.abspath(args[0]), os.path.abspath(args[1])
    base_dir = os.path.dirname(urdf_path)

    bpy.ops.wm.read_factory_settings(use_empty=True)

    robot = ET.parse(urdf_path).getroot()
    links = {link.get("name"): link for link in robot.findall("link")}
    joints = robot.findall("joint")
    joint_of_child = {j.find("child").get("link"): j for j in joints}
    children = {}
    for j in joints:
        children.setdefault(j.find("parent").get("link"), []).append(j.find("child").get("link"))
    roots = [name for name in links if name not in joint_of_child]
    print(f"[1/4] {len(links)} eslabones, {len(joints)} juntas, raiz: {roots}")

    # --- nodos: un empty por eslabon con el origin de su junta --------------
    nodes = {}

    def build(link_name, parent):
        empty = bpy.data.objects.new(link_name, None)
        bpy.context.scene.collection.objects.link(empty)
        empty.empty_display_size = 0.05
        joint = joint_of_child.get(link_name)
        if parent:
            empty.parent = parent
        if joint is not None:
            empty.matrix_basis = origin_matrix(joint.find("origin"))
            kind = joint.get("type")
            if kind in MOVABLE:
                axis = mathutils.Vector(parse_vec(joint.find("axis").get("xyz"), (1, 0, 0))).normalized()
                empty["joint"] = joint.get("name")
                empty["type"] = kind
                empty["axis"] = to_gltf_axis(axis)
                limit = joint.find("limit")
                if limit is not None and kind != "continuous":
                    empty["lower"] = float(limit.get("lower", 0))
                    empty["upper"] = float(limit.get("upper", 0))
        nodes[link_name] = empty
        for child in children.get(link_name, []):
            build(child, empty)

    for root in roots:
        build(root, None)

    # --- mallas visuales ----------------------------------------------------
    print("[2/4] mallas:")
    cache = {}
    placed = 0
    for link_name, link in links.items():
        for i, visual in enumerate(link.findall("visual")):
            mesh_el = visual.find("geometry/mesh")
            if mesh_el is None:
                continue  # primitivas de colision/relleno: no se ven en la web
            mesh = load_mesh(os.path.join(base_dir, mesh_el.get("filename")), cache)
            obj = bpy.data.objects.new(f"{link_name}_visual{i}", mesh)
            bpy.context.scene.collection.objects.link(obj)
            obj.parent = nodes[link_name]
            scale = parse_vec(mesh_el.get("scale"), (1.0, 1.0, 1.0))
            obj.matrix_basis = origin_matrix(visual.find("origin")) @ \
                mathutils.Matrix.Diagonal((*scale, 1.0))
            placed += 1

    n_mats = dedupe_materials()
    unique_tris = sum(sum(len(p.vertices) - 2 for p in m.polygons) for m in cache.values())
    scene_tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
                     for o in bpy.data.objects if o.type == "MESH")
    print(f"[3/4] {placed} visuales de {len(cache)} mallas unicas, {n_mats} materiales; "
          f"{unique_tris} tris en fichero, {scene_tris} en escena")

    # --- exportacion --------------------------------------------------------
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        use_selection=True,
        export_extras=True,
        export_yup=True,
        export_apply=True,
        export_image_format="WEBP",
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=10,
        export_draco_position_quantization=12,
        export_draco_normal_quantization=8,
        export_draco_texcoord_quantization=12,
    )
    print(f"[4/4] exportado {out_path} ({os.path.getsize(out_path) / 1048576:.2f} MB)")


if __name__ == "__main__":
    main()
