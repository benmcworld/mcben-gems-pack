"""Blender: runde Galaxie-Federfluegel (Cycles). Aufruf: python wings_feather.py <theme> <outdir>"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Matrix, Vector
import bl_common as C

theme = sys.argv[1] if len(sys.argv) > 1 else "lila"
outdir = sys.argv[2] if len(sys.argv) > 2 else "."
th = C.THEMES[theme]
C.reset()
sc = C.setup(th, res=(900, 750), samples=40)

S = 1.0          # Spannweite-Faktor
Z0 = 1.45        # Schulterhoehe
rows = [
    # n, s0, s1, Laenge(s), Breite, Winkel(s) [Grad aus der Senkrechten nach aussen], y-Versatz, Glow
    (11, .20, 1.0, lambda s: .95 + .85 * s, .34, lambda s: -6 + 64 * s, .0, 1.4),
    (10, .04, .86, lambda s: .70 + .32 * s, .34, lambda s: -12 + 54 * s, -.05, .8),
    (12, .00, .92, lambda s: .36 + .10 * s, .30, lambda s: -18 + 46 * s, -.10, .35),
]


def edge(side, s):
    return Vector((side * (.15 + 1.45 * s * S), .06 * s, Z0 + 1.55 * S * math.sin(s * math.pi * .55)))


mats = [C.galaxy_feather_mat(f"f{i}", th, glow=g, seed=i * 1.7) for i, g in enumerate([r[7] for r in rows])]
for side in (1, -1):
    for ri, (n, s0, s1, L, wd, A, dy, gl) in enumerate(rows):
        for i in range(n):
            s = s0 + (s1 - s0) * i / (n - 1)
            f = C.soft_feather(f"feather_{side}_{ri}_{i}", L(s) * S, wd * S, .07 * S, bend=-.12)
            f.data.materials.append(mats[ri])
            p = edge(side, s) + Vector((0, dy - .015 * i * 0, 0))
            rot = Matrix.Rotation(math.radians(-side * A(s)), 4, "Y") @ Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Rotation(math.radians(-8), 4, "X")
            f.matrix_world = Matrix.Translation(p) @ rot
    pts = [tuple(edge(side, k / 30) + Vector((0, -.12, 0))) for k in range(31)]
    C.tube_along(f"edge_{side}", pts, .032 * S, C.emit_mat(f"edgeglow{side}", th["tip"], 3.0))

# Spieler (dunkel, Minecraft-Proportionen; Ruecken zur Kamera)
pm = C.simple_mat("player", (0.025, 0.02, 0.035), 0.7)
def box(name, size, loc):
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.scale = size; o.location = loc
    bpy.context.collection.objects.link(o); o.data.materials.append(pm)
for nm, sz, lc in [("head", (.5, .5, .5), (0, .2, 1.75)), ("body", (.5, .25, .75), (0, .2, 1.125)),
                   ("armL", (.25, .25, .75), (.375, .2, 1.125)), ("armR", (.25, .25, .75), (-.375, .2, 1.125)),
                   ("legL", (.25, .25, .75), (.125, .2, .375)), ("legR", (.25, .25, .75), (-.125, .2, .375))]:
    box(nm, sz, lc)

C.area_light("key", (2.5, -4, 4), (math.radians(50), 0, math.radians(30)), 160, (1, .95, 1), 4)
C.area_light("fill", (-4, -3, 2), (math.radians(70), 0, math.radians(-50)), 60, th["glow"], 4)
C.area_light("rim", (0, 4, 3), (math.radians(-60), 0, 0), 220, th["glow"], 5)

views = {"hinten": ((0, -9.6, 2.2), (0, 0, 1.95)), "schraeg": ((5.6, -7.6, 2.8), (0, 0, 1.9))}
for name, (loc, tgt) in views.items():
    C.camera(loc, tgt, 50)
    raw = os.path.join(outdir, f"feder_{theme}_{name}_raw.png")
    C.render(raw)
    C.bloom(raw, os.path.join(outdir, f"feder_{theme}_{name}.png"), strength=.55)
print("fertig")
