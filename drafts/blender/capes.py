"""Blender: Custom-Capes mit 3D-Emblem + Rahmen. python capes.py <theme> <outdir>"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix
import bl_common as C

theme, outdir = sys.argv[1], sys.argv[2]
th = C.THEMES[theme]
C.reset()
C.setup(th, res=(1500, 760), samples=40)
W, H = .62, 1.0


def rect(w, h, r=.04, n=6):
    pts = []
    for cx, cz, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + math.cos(a) * r, cz + math.sin(a) * r))
    return pts


def cape_base(i, x, face, frame):
    group = []
    b = C.shape_curve(f"cape{i}", rect(W, H), .02, .012, face)
    b.location = (x, 0, 1.0); group.append(b)
    fr = C.ring_curve(f"frame{i}", [(px + x, pz + 1.0) for px, pz in rect(W * 1.02, H * 1.02)], .018, frame, y=-.04)
    group.append(fr)
    return group


def emblem_B(x, mat):
    cu = bpy.data.curves.new("B", "FONT")
    cu.body = "B"; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.size = .62; cu.extrude = .035; cu.bevel_depth = .012; cu.bevel_resolution = 4
    ob = C.link_obj("B", cu)
    ob.location = (x, -.07, 1.02); ob.rotation_euler = (math.radians(90), 0, 0)
    ob.data.materials.append(mat)
    return ob


def emblem_planet(x, th):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.17, location=(x, -.12, 1.03), segments=48, ring_count=24)
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(C.galaxy_mat("pl", th, scale=4, stars=60, glow=5.0, seed=7))
    bpy.ops.mesh.primitive_torus_add(major_radius=.3, minor_radius=.012, location=(x, -.12, 1.03), rotation=(math.radians(78), math.radians(-24), 0))
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(C.emit_mat("ring", th["tip"], 2.0))
    moon = [(math.cos(a) * .07 + .17, math.sin(a) * .07 + .33) for a in [math.radians(t) for t in range(40, 321, 10)]]
    moon += [(math.cos(a) * .055 + .2, math.sin(a) * .055 + .345) for a in [math.radians(t) for t in range(300, 49, -10)]]
    m = C.shape_curve("moon", [(px + x, pz + 1.0) for px, pz in moon], .01, .006, C.emit_mat("moon", th["glow"], 1.6))
    m.location = (0, -.06, 0)


def star_pts(cx, cz, r):
    pts = []
    for k in range(8):
        a = math.pi / 2 + k * math.pi / 4
        rr = r if k % 2 == 0 else r * .28
        pts.append((cx + math.cos(a) * rr, cz + math.sin(a) * rr))
    return pts


def emblem_wings(x, th):
    fm = C.galaxy_feather_mat("fw", th, glow=1.0)
    for side in (1, -1):
        for j in range(6):
            f = C.soft_feather(f"ef{side}{j}", .25 + .05 * (5 - j) * .6, .07, .02, bend=-.05)
            f.data.materials.append(fm)
            ang = -side * (35 + j * 18)
            rot = Matrix.Rotation(math.radians(ang), 4, "Y") @ Matrix.Rotation(math.radians(90), 4, "X")
            f.matrix_world = Matrix.Translation(Vector((x + side * .05, -.06 - .004 * j, 1.1))) @ rot
    d = C.shard_mesh("dia", .3, .08, flat=.6, seed=3)
    d.data.materials.append(C.crystal_mat("dcr", th, vein=2.5, scale=12))
    d.matrix_world = Matrix.Translation(Vector((x, -.09, 1.22))) @ Matrix.Rotation(math.radians(0), 4, "X")


def emblem_moon(x, th):
    cres = [(math.cos(a) * .2, math.sin(a) * .2 + .05) for a in [math.radians(t) for t in range(30, 331, 6)]]
    cres += [(math.cos(a) * .17 + .08, math.sin(a) * .17 + .08) for a in [math.radians(t) for t in range(318, 41, -6)]]
    C.shape_curve("cres", [(px + x, pz + 1.0) for px, pz in cres], .025, .01, C.emit_mat("cm", th["tip"], 1.8)).location = (0, -.07, 0)
    for (sx, sz, r) in ((.15, .3, .07), (-.16, -.22, .05), (.12, -.3, .035), (-.18, .32, .03)):
        C.shape_curve("st", star_pts(sx + x, sz + 1.0, r), .01, .005, C.emit_mat("sm", (1, 1, 1), 2.5)).location = (0, -.06, 0)


designs = [
    ("Kristall-B", C.crystal_mat("vein", th, vein=1.6, scale=5), C.crystal_mat("frame", th, vein=1.0, scale=20), lambda x: emblem_B(x, C.crystal_mat("bm", th, vein=6.0, scale=9))),
    ("Planet", C.galaxy_mat("g1", th, scale=2.5, stars=140, glow=2.2), C.emit_mat("f2", th["tip"], 1.2), lambda x: emblem_planet(x, th)),
    ("Fluegel-Wappen", C.galaxy_mat("g2", th, scale=3, stars=160, glow=1.8, seed=3), C.gold_mat("gold"), lambda x: emblem_wings(x, th)),
    ("Mond & Sterne", C.galaxy_mat("g3", th, scale=2, stars=120, glow=2.0, seed=9), C.emit_mat("f4", th["glow"], 1.2), lambda x: emblem_moon(x, th)),
]
for i, (name, face, frame, emb) in enumerate(designs):
    x = (i - 1.5) * .95
    cape_base(i, x, face, frame)
    emb(x)

C.area_light("key", (2, -5, 3.5), (math.radians(60), 0, math.radians(20)), 260, (1, .96, 1), 5)
C.area_light("rim", (0, 3, 2.5), (math.radians(-70), 0, 0), 200, th["glow"], 6)
C.area_light("fill", (-4, -3, 1), (math.radians(80), 0, math.radians(-50)), 60, th["glow"], 4)
C.camera((1.0, -5.6, 1.35), (0, 0, 1.0), 48)
raw = os.path.join(outdir, f"capes_{theme}_raw.png")
C.render(raw)
C.bloom(raw, os.path.join(outdir, f"capes_{theme}.png"), strength=.5)
print("fertig")
