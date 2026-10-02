#!/usr/bin/env bash
# Copia el modelo del rover (URDF expandido + mallas) desde el workspace ROS a
# tools/model-source/rover/, que es lo que lee build_rover_glb.py.
#
# Solo LEE del workspace de origen: el modelo en ~/Documents/Codex no se toca.
# Requiere ROS 2 (xacro). Uso:
#   tools/prepare_rover_source.sh [ruta/al/workspace/src]
set -euo pipefail

SRC="${1:-$HOME/Documents/Codex/2026-09-06/hi/ruben_arm_6dof/src}"
ENTRY="$SRC/tars_arm_description/urdf/rover_mobile_arm.urdf.xacro"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/model-source/rover"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# xacro resuelve $(find pkg) con el indice de ament; se monta uno temporal que
# apunta a los paquetes del workspace sin necesidad de compilarlo.
mkdir -p "$TMP/share/ament_index/resource_index/packages"
for pkg in tars_arm_description swerve_gazebo mobile_description; do
  ln -s "$SRC/$pkg" "$TMP/share/$pkg"
  touch "$TMP/share/ament_index/resource_index/packages/$pkg"
done

set +u; source /opt/ros/jazzy/setup.bash; set -u
export AMENT_PREFIX_PATH="$TMP:${AMENT_PREFIX_PATH:-}"

rm -rf "$OUT"
mkdir -p "$OUT/meshes"
xacro "$ENTRY" > "$OUT/rover.urdf"

# Copia cada malla referenciada (con su .mtl y texturas) y reescribe la ruta en
# el URDF a relativa, para que la copia sea autocontenida.
python3 - "$OUT" <<'PY'
import os, re, shutil, sys
out = sys.argv[1]
urdf_path = os.path.join(out, "rover.urdf")
urdf = open(urdf_path).read()
copied = set()

def copy_mesh(match):
    src = os.path.realpath(match.group(1))
    name = os.path.basename(src)
    if name not in copied:
        shutil.copy2(src, os.path.join(out, "meshes", name))
        mtl = os.path.splitext(src)[0] + ".mtl"
        if os.path.exists(mtl):
            shutil.copy2(mtl, os.path.join(out, "meshes", os.path.basename(mtl)))
        tex = os.path.join(os.path.dirname(src), "textures")
        dst_tex = os.path.join(out, "meshes", "textures")
        if os.path.isdir(tex):
            os.makedirs(dst_tex, exist_ok=True)
            for f in os.listdir(tex):
                shutil.copy2(os.path.join(tex, f), dst_tex)
        copied.add(name)
    return 'filename="meshes/' + name + '"'

urdf = re.sub(r'filename="file://([^"]+)"', copy_mesh, urdf)
open(urdf_path, "w").write(urdf)
print(f"{len(copied)} mallas copiadas en {out}/meshes")
PY
