"""Blender: realistisches Plushie aus einem Minecraft-Skin (wie echtes Stofftier).
python plush.py <skin.png> <outdir> <name>"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import bl_common as C

skin_path, outdir, name = sys.argv[1], sys.argv[2], sys.argv[3]
th = dict(C.THEMES["lila"]); th["world"] = (0.55, 0.5, 0.47)
C.reset()
sc = C.setup(th, res=(1500, 760), samples=64)
sc.view_settings.view_transform = "AgX"; sc.view_settings.exposure = 0.0


def fabric_mat(img):
    m = bpy.data.materials.new("fabric"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.95
    b.inputs["Sheen Weight"].default_value = 1.0
    b.inputs["Sheen Roughness"].default_value = 0.35
    b.inputs["Sheen Tint"].default_value = (1, 1, 1, 1)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900; nz.inputs["Detail"].default_value = 2
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25; bump.inputs["Distance"].default_value = 0.002
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def hat_mat(img):
    m = bpy.data.materials.new("hat"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"]); nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.95
    return m


def plush_box(nm, size, r, skin, mat, res=14, puff=0.035):
    """Abgerundete, leicht aufgeplusterte Box; UVs pro Seite aus dem Skin (u,v,w,h,d in Pixeln).
    Vorne = -Y (zur Kamera), rechte Spielerseite = -X."""
    W, H, D = size
    u, v, sw, sh, sd = skin
    hx, hy, hz = W / 2, D / 2, H / 2
    # Seite: (Ursprung-Funktion a,b in [-1,1] -> Punkt, Normale, Skin-Rechteck (x0,y0,w,h), u-Richtung umkehren?)
    faces = [
        (lambda a, b: Vector((a * hx, -hy, b * hz)), Vector((0, -1, 0)), (u + sd, v + sd, sw, sh)),          # vorne
        (lambda a, b: Vector((-a * hx, hy, b * hz)), Vector((0, 1, 0)), (u + 2 * sd + sw, v + sd, sw, sh)),  # hinten
        (lambda a, b: Vector((-hx, a * hy, b * hz)), Vector((-1, 0, 0)), (u, v + sd, sd, sh)),              # rechts (Spieler)
        (lambda a, b: Vector((hx, -a * hy, b * hz)), Vector((1, 0, 0)), (u + sd + sw, v + sd, sd, sh)),      # links
        (lambda a, b: Vector((a * hx, -b * hy, hz)), Vector((0, 0, 1)), (u + sd, v, sw, sd)),               # oben
        (lambda a, b: Vector((a * hx, b * hy, -hz)), Vector((0, 0, -1)), (u + sd + sw, v, sw, sd)),          # unten
    ]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new()
    inner = Vector((max(0, hx - r), max(0, hy - r), max(0, hz - r)))
    for fn, nrm, (x0, y0, rw, rh) in faces:
        grid = []
        for j in range(res + 1):
            row = []
            for i in range(res + 1):
                a, b = -1 + 2 * i / res, -1 + 2 * j / res
                p = fn(a, b)
                c = Vector((max(-inner.x, min(inner.x, p.x)), max(-inner.y, min(inner.y, p.y)), max(-inner.z, min(inner.z, p.z))))
                d = p - c
                p = c + (d.normalized() * r if d.length > 1e-6 else d)
                p += nrm * puff * (1 - a * a) * (1 - b * b)
                row.append((bm.verts.new(p), ((x0 + (i / res) * rw) / 64, 1 - (y0 + (1 - j / res) * rh) / 64)))
            grid.append(row)
        for j in range(res):
            for i in range(res):
                q = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
                f = bm.faces.new([x[0] for x in q])
                for l, (_, uvc) in zip(f.loops, q):
                    l[uvl].uv = uvc
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(nm); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = C.link_obj(nm, me); o.data.materials.append(mat)
    return o


def plushie(x, img):
    mat = fabric_mat(img)
    parts = []
    head = plush_box("head", (1.0, .92, .94), .26, (0, 0, 8, 8, 8), mat, puff=.04); head.location = (x, 0, 1.27); parts.append(head)
    if HAS_HAT:
        hat = plush_box("hat", (1.04, .96, .98), .27, (32, 0, 8, 8, 8), hat_mat(img), puff=.04); hat.location = (x, 0, 1.27); parts.append(hat)
    body = plush_box("body", (.62, .56, .4), .14, (16, 16, 8, 12, 4), mat, puff=.02); body.location = (x, .02, .56); parts.append(body)
    for side, (u, v) in ((-1, (40, 16)), (1, (32, 48))):
        arm = plush_box(f"arm{side}", (.3, .5, .3), .13, (u, v, 4, 12, 4), mat, puff=.02)
        arm.matrix_world = Matrix.Translation(Vector((x + side * .47, -.08, .64))) @ Matrix.Rotation(math.radians(-side * 14), 4, "Y") @ Matrix.Rotation(math.radians(-38), 4, "X")
        parts.append(arm)
    for side, (u, v) in ((-1, (0, 16)), (1, (16, 48))):
        leg = plush_box(f"leg{side}", (.3, .46, .32), .13, (u, v, 4, 12, 4), mat, puff=.02)
        leg.matrix_world = Matrix.Translation(Vector((x + side * .16, -.16, .17))) @ Matrix.Rotation(math.radians(-82), 4, "X")
        parts.append(leg)
    return parts


img = bpy.data.images.load(os.path.abspath(skin_path))
from PIL import Image as _I
_a = _I.open(skin_path).convert("RGBA").crop((32, 0, 64, 16)).split()[3]
HAS_HAT = _a.getextrema()[1] > 0
views = [(-1.9, 0), (0, 180), (1.9, 90)]   # vorne, hinten, Seite
for x, rz in views:
    ps = plushie(0, img)
    bpy.context.view_layer.update()
    for o in ps:
        o.matrix_world = Matrix.Translation(Vector((x, 0, 0))) @ Matrix.Rotation(math.radians(rz), 4, "Z") @ o.matrix_world
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
bpy.context.object.data.materials.append(C.simple_mat("floor", (.62, .58, .55), .7))
C.area_light("key", (-2.5, -4, 4.5), (math.radians(45), 0, math.radians(-30)), 650, (1, .93, .85), 5)
C.area_light("fill", (3, -3, 2), (math.radians(70), 0, math.radians(45)), 200, (.9, .95, 1), 5)
C.area_light("back", (0, 4, 3), (math.radians(-60), 0, 0), 250, (1, 1, 1), 5)
C.camera((0, -7.6, 1.9), (0, 0, .95), 45)
C.render(os.path.join(outdir, f"plush_{name}.png"))
print("fertig")
