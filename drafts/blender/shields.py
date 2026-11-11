"""Blender: hohe Schilde mit 4 Texturen nebeneinander. python shields.py <theme> <outdir>"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import bl_common as C

theme, outdir = sys.argv[1], sys.argv[2]
th = C.THEMES[theme]
C.reset()
C.setup(th, res=(1400, 700), samples=40)

designs = [
    ("Kristall-Adern", C.crystal_mat("cr", th, vein=2.2, scale=4.0), C.emit_mat("r1", th["tip"], 1.2)),
    ("Galaxie", C.galaxy_mat("gal", th, scale=2.5, stars=120, glow=3.0), C.emit_mat("r2", th["glow"], 1.2)),
    ("Dark-Metall", C.metal_mat("dm", th, .15, .3), C.emit_mat("r3", th["tip"], 1.6)),
    ("Gold + Galaxie", C.galaxy_mat("gal2", th, scale=3.5, stars=160, glow=2.0, seed=4.0), C.gold_mat("gold")),
]
for i, (name, face, rim) in enumerate(designs):
    x = (i - 1.5) * 1.0
    pts = C.heater_pts()
    body = C.shape_curve(f"sh{i}", pts, .035, .03, face)
    body.location = (x, 0, 1.0)
    r = C.ring_curve(f"rim{i}", [(px * 1.0 + x, pz + 1.0) for px, pz in C.heater_pts(scale=1.02)], .022, rim, y=-.07)
    inner = C.ring_curve(f"in{i}", [(px + x, pz + 1.0) for px, pz in C.heater_pts(scale=.8, dz=.03)], .009, rim, y=-.075)
    # kleiner Buckel in der Mitte
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.07, location=(x, -.07, 1.08))
    bpy.context.object.scale = (1, .5, 1)
    bpy.ops.object.shade_smooth()
    bpy.context.object.data.materials.append(rim if i != 1 else face)
    body.rotation_euler = (math.radians(90), 0, 0)

C.area_light("key", (2, -5, 3.5), (math.radians(60), 0, math.radians(20)), 260, (1, .96, 1), 5)
C.area_light("rim", (0, 3, 2.5), (math.radians(-70), 0, 0), 220, th["glow"], 6)
C.area_light("fill", (-4, -3, 1), (math.radians(80), 0, math.radians(-50)), 60, th["glow"], 4)
C.camera((1.3, -6.2, 1.5), (0, 0, 1.0), 50)
raw = os.path.join(outdir, f"schilde_{theme}_raw.png")
C.render(raw)
C.bloom(raw, os.path.join(outdir, f"schilde_{theme}.png"), strength=.5)
print("fertig")
