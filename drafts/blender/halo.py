"""Blender: Heiligenschein in 3 Helligkeiten. python halo.py <theme> <outdir>"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import bl_common as C

theme, outdir = sys.argv[1], sys.argv[2]
th = C.THEMES[theme]
C.reset()
C.setup(th, res=(1500, 640), samples=40)
pm = C.simple_mat("player", (0.03, 0.025, 0.04), 0.7)
for i, (name, k) in enumerate((("dunkel", .5), ("normal", 1.6), ("hell", 4.5))):
    x = (i - 1) * 1.45
    for nm, sz, lc in [("head", (.5, .5, .5), (x, 0, 1.75)), ("body", (.5, .25, .75), (x, 0, 1.125))]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=lc); o = bpy.context.object; o.scale = sz; o.data.materials.append(pm)
    bpy.ops.mesh.primitive_torus_add(major_radius=.3, minor_radius=.032, major_segments=96, minor_segments=24, location=(x, 0, 2.28), rotation=(math.radians(8), 0, 0))
    bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(C.emit_mat(f"h{i}", th["tip"], k))
    bpy.ops.mesh.primitive_torus_add(major_radius=.37, minor_radius=.008, major_segments=96, minor_segments=12, location=(x, 0, 2.28), rotation=(math.radians(8), 0, 0))
    bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(C.emit_mat(f"h2{i}", th["glow"], k * .8))
    for j in range(6):
        a = j / 6 * math.tau
        bpy.ops.mesh.primitive_ico_sphere_add(radius=.025, subdivisions=1, location=(x + math.cos(a) * .37, math.sin(a) * .37, 2.28 + math.sin(a) * .05))
        bpy.context.object.data.materials.append(C.emit_mat(f"s{i}{j}", (1, 1, 1), k * 1.2))
C.area_light("key", (2, -5, 4), (math.radians(55), 0, math.radians(20)), 120, (1, .96, 1), 5)
C.area_light("rim", (0, 3, 3), (math.radians(-60), 0, 0), 100, th["glow"], 6)
C.camera((0.6, -6.0, 2.6), (0, 0, 1.95), 45)
raw = os.path.join(outdir, f"halo_{theme}_raw.png")
C.render(raw)
C.bloom(raw, os.path.join(outdir, f"halo_{theme}.png"), strength=.55)
print("fertig")
