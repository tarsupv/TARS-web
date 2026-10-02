"""Control de calidad del GLB: lo reimporta y renderiza poses concretas.

Mueve las juntas usando solo los metadatos que lleva el GLB (nombre, tipo y eje
en los extras de cada nodo), igual que hace la web, asi que si una pose sale
bien aqui, el rig de la web tambien es correcto.

Uso:
    blender -b -P tools/qc_render.py -- public/models/rover.glb salida/ \
        'reposo={"arm_joint_2":-1.242,"arm_joint_3":1.9,"arm_joint_5":-0.222}' ...
"""

import json
import math
import sys

import bpy
import mathutils


def setup_scene():
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.9, 0.91, 0.94, 1)
    bg.inputs[1].default_value = 1.0
    bpy.context.scene.world = world

    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.lens = 55
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (2.9, -2.6, 1.7)
    cam.rotation_euler = (mathutils.Vector((0.35, 0.0, 0.45)) - cam.location) \
        .to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam

    for loc, energy in (((3, -3, 4), 700), ((-3, -2, 3), 250), ((0, 3, 3), 200)):
        light = bpy.data.objects.new("l", bpy.data.lights.new("l", "AREA"))
        light.data.energy, light.data.size = energy, 3
        light.location = loc
        light.rotation_euler = (mathutils.Vector((0.3, 0, 0.4)) - mathutils.Vector(loc)) \
            .to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.collection.objects.link(light)

    floor = bpy.data.objects.new("floor", bpy.data.meshes.new("floor"))
    floor.data.from_pydata([(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)], [], [(0, 1, 2, 3)])
    bpy.context.scene.collection.objects.link(floor)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1000, 800
    scene.eevee.taa_render_samples = 32


def joint_nodes():
    return {o["joint"]: o for o in bpy.data.objects if "joint" in o.keys()}


def apply_pose(nodes, pose):
    for name, value in pose.items():
        node = nodes.get(name)
        if node is None:
            print("  AVISO junta ausente:", name)
            continue
        # El eje de los extras esta en marco glTF (Y arriba); el importador ha
        # devuelto la escena a Z arriba, asi que se deshace (x, z, -y).
        gx, gy, gz = node["axis"]
        axis = mathutils.Vector((gx, -gz, gy))
        node.rotation_mode = "QUATERNION"
        if node["type"] == "prismatic":
            node.location = node.location + axis * value
        else:
            node.rotation_quaternion = node.rotation_quaternion @ \
                mathutils.Quaternion(axis, value)
    bpy.context.view_layer.update()


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    glb, out_dir, poses = args[0], args[1].rstrip("/"), args[2:]
    for spec in poses:
        name, _, pose_json = spec.partition("=")
        bpy.ops.wm.read_factory_settings(use_empty=True)
        setup_scene()
        bpy.ops.import_scene.gltf(filepath=glb)
        nodes = joint_nodes()
        if name == poses[0].partition("=")[0]:
            print("JUNTAS EN EL GLB:", sorted(nodes))
        apply_pose(nodes, json.loads(pose_json or "{}"))
        bpy.context.scene.render.filepath = f"{out_dir}/qc_{name}.png"
        bpy.ops.render.render(write_still=True)
        print("RENDER", bpy.context.scene.render.filepath)


if __name__ == "__main__":
    main()
