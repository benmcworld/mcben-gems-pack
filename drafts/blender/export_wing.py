"""Exportiert einen Federfluegel (rechte Seite) als OBJ im Minecraft-Modellraum.
Modellraum (wie ModelPart 'body'): Einheit = 1 Block, Ursprung = Oberkante Koerpermitte,
+y = nach unten, +z = Ruecken (hinten), +x = linke Spielerseite.
python export_wing.py <out.obj>"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Matrix, Vector
import bl_common as C

out = sys.argv[1]
C.reset()
S, Z0 = 0.82, 1.45
rows = [
    (11, .20, 1.0, lambda s: .95 + .85 * s, .34, lambda s: -6 + 64 * s, .0),
    (10, .04, .86, lambda s: .70 + .32 * s, .34, lambda s: -12 + 54 * s, -.05),
    (12, .00, .92, lambda s: .36 + .10 * s, .30, lambda s: -18 + 46 * s, -.10),
]
def edge(s):
    return Vector((.15 + 1.45 * s * S, .06 * s, Z0 + 1.55 * S * math.sin(s * math.pi * .55)))

objs = []
for ri, (n, s0, s1, L, wd, A, dy) in enumerate(rows):
    for i in range(n):
        s = s0 + (s1 - s0) * i / (n - 1)
        f = C.soft_feather(f"f{ri}_{i}", L(s) * S, wd * S, .07 * S, bend=-.12, nu=6, nv=10)
        f.modifiers.remove(f.modifiers["sub"])
        rot = Matrix.Rotation(math.radians(-A(s)), 4, "Y") @ Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Rotation(math.radians(-8), 4, "X")
        f.matrix_world = Matrix.Translation(edge(s) + Vector((0, dy, 0))) @ rot
        f["mat"] = "feather"
        objs.append(f)
pts = [tuple(edge(k / 24) + Vector((0, -.12, 0))) for k in range(25)]
t = C.tube_along("edge", pts, .03 * S, C.emit_mat("e", (1, 1, 1)))
t.data.bevel_resolution = 2
t["mat"] = "glow"
objs.append(t)

bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
BODY_TOP_Z, BODY_Y = 1.5, 0.2
def to_model(p):
    # Blender: +X = rechte Spielerseite (Blick von hinten), -Y = Ruecken, +Z = oben
    return (-p.x, -(p.z - BODY_TOP_Z), -(p.y - BODY_Y))

vlines, vt, vn, faces = [], [], [], {"feather": [], "glow": []}
vi = 0
for o in objs:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    uvl = me.uv_layers.active.data if me.uv_layers.active else None
    M = o.matrix_world
    N = M.to_3x3().inverted().transposed()
    me_corner_normals = me.corner_normals
    for tri in me.loop_triangles:
        idx = []
        for li in tri.loops:
            v = me.vertices[me.loops[li].vertex_index]
            p = to_model(M @ v.co)
            n = N @ me_corner_normals[li].vector; n.normalize()
            nm = (-n.x, -n.z, -n.y)
            uv = uvl[li].uv if uvl else (0.5, 0.5)
            vlines.append(p); vn.append(nm); vt.append((uv[0], uv[1]))
            vi += 1
            idx.append(vi)
        # Wicklung: Spiegelung (x und y negiert) -> Reihenfolge bleibt; Achsentausch y<->z kehrt um
        faces[o["mat"]].append((idx[0], idx[2], idx[1]))
    ev.to_mesh_clear()

with open(out, "w") as fh:
    fh.write("# McBen Galaxie-Fluegel (rechte Seite), Minecraft-Modellraum\n")
    for p in vlines: fh.write("v %.5f %.5f %.5f\n" % p)
    for t_ in vt: fh.write("vt %.5f %.5f\n" % t_)
    for n in vn: fh.write("vn %.4f %.4f %.4f\n" % n)
    for mat, fl in faces.items():
        fh.write(f"usemtl {mat}\n")
        for a, b, c in fl: fh.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
print("exportiert", len(vlines) // 3, "Dreiecke")
