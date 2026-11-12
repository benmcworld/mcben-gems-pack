"""Blender: Kristallglas-Schilde und -Capes (Produktfoto). python glass_items.py <shields|capes> <theme> <outdir>"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix
import bl_common as C

kind, theme, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
th = C.THEMES[theme]
C.reset()
sc = C.setup(th, res=(1600, 820), samples=72)
sc.cycles.transmission_bounces = 8
sc.cycles.max_bounces = 10
C.studio_floor(th)
lighter = tuple(min(1, .55 + .45 * c) for c in th["main"])


def slab(name, w, h, depth, bevel, mat, x, z, y=0.0, r=.06):
    o = C.shape_curve(name, C.round_rect(w, h, r), depth, bevel, mat)
    o.location = (x, y, z)
    return o


def frame(name, w, h, x, z, mat, radius=.022, y=-.0, r=.07):
    return C.ring_curve(name, [(px + x, pz + z) for px, pz in C.round_rect(w, h, r)], radius, mat, y=y)


def emblem(name, pts, x, z, depth, bevel, mat, y=-.07):
    o = C.shape_curve(name, [(px + x, pz + z) for px, pz in pts], depth, bevel, mat)
    o.location = (0, y, 0)
    return o


def tilt_group(objs, x, z, rz=-18):
    """Gruppe um ihre eigene senkrechte Achse drehen (Produktfoto-Winkel)."""
    bpy.context.view_layer.update()
    R = Matrix.Translation(Vector((x, 0, z))) @ Matrix.Rotation(math.radians(rz), 4, "Z") @ Matrix.Translation(Vector((-x, 0, -z)))
    for o in objs:
        o.matrix_world = R @ o.matrix_world


def new_objs(before):
    return [o for o in bpy.data.objects if o.name not in before]


glass = C.glass_mat("glass", lighter, .02)
metal = C.metal_mat("metal", th, .25, .18)
gold = C.gold_mat("gold")
glowv = C.crystal_mat("core", th, vein=2.6, scale=8.0)
galcore = C.galaxy_mat("galcore", th, scale=2.2, stars=110, glow=3.0)
obs = C.obsidian_mat("obs", th, vein=2.2, scale=6.0)
edge = C.emit_mat("edge", th["tip"], 3.0)
white = C.emit_mat("white", (1, 1, 1), 4.0)

if kind == "shields":
    W, H, Z = .62, 1.12, .62
    xs = [-2.25, -.75, .75, 2.25]
    variants = ["Kristallglas", "Obsidian", "Galaxie-Glas", "Gold + Kristall"]
    for i, x in enumerate(xs):
        before = {o.name for o in bpy.data.objects}
        if i == 0:   # Glas-Huelle mit leuchtendem Adern-Kern
            slab("core", W * .86, H * .9, .02, .01, glowv, x, Z)
            slab("shell", W, H, .045, .03, glass, x, Z)
            frame("fr", W * 1.04, H * 1.03, x, Z, metal, .028)
            s = C.shard_mesh("gem", .34, .1, flat=.6, seed=5); s.data.materials.append(C.crystal_mat("gemm", th, vein=6, scale=12))
            s.matrix_world = Matrix.Translation(Vector((x, -.09, Z + .17)))
        elif i == 1:  # Obsidian mit Leuchtrissen + schmaler Leuchtrand
            slab("ob", W, H, .05, .03, obs, x, Z)
            frame("fr", W * 1.04, H * 1.03, x, Z, metal, .028)
            frame("in", W * .8, H * .86, x, Z, edge, .008, y=-.085)
        elif i == 2:  # Galaxie im Glas + Mondsichel
            slab("core", W * .86, H * .9, .02, .01, galcore, x, Z)
            slab("shell", W, H, .045, .03, glass, x, Z)
            frame("fr", W * 1.04, H * 1.03, x, Z, metal, .028)
            emblem("moon", C.crescent_pts(.15, .125, (.06, .04)), x, Z + .05, .012, .008, white, y=-.085)
        else:         # Gold-Rahmen, dunkles Glas, Kristall-Stern
            slab("core", W * .86, H * .9, .02, .01, obs, x, Z)
            slab("shell", W, H, .045, .03, C.glass_mat("dglass", tuple(c * .5 + .1 for c in th["mid"]), .02), x, Z)
            frame("fr", W * 1.04, H * 1.03, x, Z, gold, .03)
            emblem("star", C.star4_pts(.17, .22), x, Z + .03, .02, .01, gold, y=-.09)
        tilt_group(new_objs(before), x, Z, rz=-14)
    cam = C.camera((-1.0, -8.2, 1.75), (0, 0, .62), 45)
else:
    W, H, Z = .64, 1.02, .58
    xs = [-2.25, -.75, .75, 2.25]
    for i, x in enumerate(xs):
        before = {o.name for o in bpy.data.objects}
        if i == 0:   # Kristall-B
            slab("core", W * .88, H * .9, .015, .008, glowv, x, Z)
            slab("shell", W, H, .03, .022, glass, x, Z)
            cu = bpy.data.curves.new("B", "FONT"); cu.body = "B"; cu.align_x = "CENTER"; cu.align_y = "CENTER"
            cu.size = .55; cu.extrude = .03; cu.bevel_depth = .012; cu.bevel_resolution = 4
            b = C.link_obj("B", cu); b.location = (x, -.08, Z); b.rotation_euler = (math.radians(90), 0, 0)
            b.data.materials.append(C.emit_mat("bm", th["tip"], 2.2))
        elif i == 1:  # schlicht: Obsidian mit einer Leuchtlinie + kleinem Diamanten
            slab("ob", W, H, .035, .022, obs, x, Z)
            C.ring_curve("line", [(x, Z + .38), (x, Z - .38)], .009, edge, y=-.06).data.splines[0].use_cyclic_u = False
            s = C.shard_mesh("dia", .2, .07, flat=.6, seed=9); s.data.materials.append(C.crystal_mat("dm", th, vein=6, scale=14))
            s.matrix_world = Matrix.Translation(Vector((x, -.08, Z + .1)))
        elif i == 2:  # Galaxie-Glas mit Planetenring
            slab("core", W * .88, H * .9, .015, .008, galcore, x, Z)
            slab("shell", W, H, .03, .022, glass, x, Z)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=.12, location=(x, -.1, Z + .05)); bpy.ops.object.shade_smooth()
            bpy.context.object.data.materials.append(C.galaxy_mat("pl", th, scale=9, stars=60, glow=4, seed=5))
            bpy.ops.mesh.primitive_torus_add(major_radius=.21, minor_radius=.01, location=(x, -.1, Z + .05), rotation=(math.radians(78), math.radians(-22), 0))
            bpy.ops.object.shade_smooth(); bpy.context.object.data.materials.append(edge)
        else:         # Gold-Rahmen, dunkel, Stern
            slab("ob", W, H, .035, .022, obs, x, Z)
            frame("fr", W * 1.03, H * 1.02, x, Z, gold, .022)
            emblem("star", C.star4_pts(.15, .22), x, Z + .04, .018, .008, gold, y=-.075)
        # leichter Stoff-Schwung
        for o in new_objs(before):
            pass
        tilt_group(new_objs(before), x, Z, rz=-14)
    cam = C.camera((-1.0, -8.0, 1.65), (0, 0, .58), 45)

C.product_lights(th)
raw = os.path.join(outdir, f"glass_{kind}_{theme}_raw.png")
C.render(raw)
C.bloom(raw, os.path.join(outdir, f"glass_{kind}_{theme}.png"), strength=.45)
print("fertig")
