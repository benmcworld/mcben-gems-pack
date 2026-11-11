"""Blender: weitere Fluegel (Kristall, Ketten, Daemon). Aufruf: python wings_more.py <design> <theme> <outdir>"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Matrix, Vector
import bl_common as C

design, theme, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
th = C.THEMES[theme]
C.reset()
C.setup(th, res=(900, 750), samples=40)
Z0 = 1.45


def edge(side, s, span=1.45, lift=1.55):
    return Vector((side * (.15 + span * s), .06 * s, Z0 + lift * math.sin(s * math.pi * .55)))


def hang(side, angle_deg, extra_tilt=-8):
    """Rotation: lokale -Y zeigt nach unten, gefaechert nach aussen."""
    return Matrix.Rotation(math.radians(-side * angle_deg), 4, "Y") @ Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Rotation(math.radians(extra_tilt), 4, "X")


def crystal_wings():
    cm = C.crystal_mat("crystal", th, vein=6.0, scale=6.0)
    for side in (1, -1):
        rows = [(10, .18, 1.0, lambda s: .9 + .8 * s, .11, lambda s: -4 + 62 * s, 0.0),
                (9, .04, .85, lambda s: .65 + .3 * s, .1, lambda s: -10 + 52 * s, -.06),
                (11, .0, .92, lambda s: .35 + .12 * s, .09, lambda s: -16 + 44 * s, -.12)]
        seed = 0 if side > 0 else 500
        for n, s0, s1, L, R, A, dy in rows:
            for i in range(n):
                s = s0 + (s1 - s0) * i / (n - 1)
                ob = C.shard_mesh(f"cr{side}_{seed}", L(s), R, flat=.5, seed=seed); seed += 1
                ob.data.materials.append(cm)
                C.place(ob, edge(side, s) + Vector((0, dy, 0)), hang(side, A(s)))
        # Rueckgrat aus Kristall
        for k in range(14):
            s = k / 13
            a = edge(side, s); b = edge(side, min(1, s + 1 / 13))
            d = (b - a)
            ob = C.shard_mesh(f"sp{side}_{k}", max(.12, d.length * 1.6), .07, flat=.8, seed=900 + k + (0 if side > 0 else 50))
            ob.data.materials.append(cm)
            rot = (Vector((0, -1, 0))).rotation_difference(d.normalized()).to_matrix().to_4x4()
            C.place(ob, a + Vector((0, -.1, 0)), rot)


def chain_wings():
    metal = C.metal_mat("metal", th, .5, .2)
    glow = C.emit_mat("glowlink", th["glow"], 5.0)
    cm = C.crystal_mat("crystal", th, vein=6.0, scale=8.0)
    for side in (1, -1):
        # Fluegelknochen: dicke Kette entlang der Vorderkante
        pts = [edge(side, k / 40) for k in range(41)]
        acc = 0.0
        prev = pts[0]
        k = 0
        for p in pts[1:]:
            acc += (p - prev).length
            if acc >= .16:
                d = (p - prev).normalized()
                ob = C.chain_link(f"bone{side}_{k}", .055, .02)
                ob.data.materials.append(glow if k % 4 == 0 else metal)
                rot = Vector((0, 1, 0)).rotation_difference(d).to_matrix().to_4x4() @ Matrix.Rotation(math.radians(90 * (k % 2)), 4, "Y")
                C.place(ob, p + Vector((0, -.08, 0)), rot)
                acc = 0.0; k += 1
            prev = p
        # haengende Ketten mit Kristallspitze
        n = 11
        for i in range(n):
            s = .08 + .92 * i / (n - 1)
            top = edge(side, s)
            ang = math.radians(-side * (-4 + 60 * s))
            d = Vector((math.sin(-ang) * -1, 0, -math.cos(ang)))
            d = Vector((-math.sin(ang), 0, -math.cos(ang)))
            length = .7 + .9 * s
            nl = int(length / .17)
            for j in range(nl):
                ob = C.chain_link(f"ch{side}_{i}_{j}", .04, .012)
                ob.data.materials.append(glow if j == nl - 1 else metal)
                rot = Vector((0, 1, 0)).rotation_difference(d).to_matrix().to_4x4() @ Matrix.Rotation(math.radians(90 * (j % 2)), 4, "Y")
                C.place(ob, top + d * (j * .17 + .08), rot)
            tip = C.shard_mesh(f"tip{side}_{i}", .32 + .12 * s, .07, flat=.7, seed=300 + i + (0 if side > 0 else 40))
            tip.data.materials.append(cm)
            rot = Vector((0, -1, 0)).rotation_difference(d).to_matrix().to_4x4()
            C.place(tip, top + d * (nl * .17 + .02), rot)


def demon_wings():
    bone = C.metal_mat("bone", th, .35, .35)
    mem = C.crystal_mat("membrane", th, vein=3.5, scale=4.0)
    mem.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.5
    mem.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.3
    for side in (1, -1):
        sh = Vector((side * .15, 0, Z0))
        el = Vector((side * .95, -.05, Z0 + 1.0))
        tips = [Vector((side * x, -.25, Z0 + z)) for x, z in ((1.75, 1.35), (2.0, .55), (1.75, -.2), (1.2, -.7))]
        def tube(a, b, r, name):
            pts = [tuple(a.lerp(b, t)) for t in (0, .5, 1)]
            o = C.tube_along(name, pts, r, bone)
            return o
        tube(sh, el, .06, f"arm{side}")
        for i, t in enumerate(tips):
            tube(el, t, .032 - i * .003, f"fin{side}{i}")
            cl = C.shard_mesh(f"claw{side}{i}", .16, .03, flat=1, seed=70 + i)
            cl.data.materials.append(bone)
            C.place(cl, t, Vector((0, -1, 0)).rotation_difference((t - el).normalized()).to_matrix().to_4x4())
        bpy.ops.mesh.primitive_uv_sphere_add(radius=.09, location=el)
        bpy.context.object.data.materials.append(bone)
        horn = C.shard_mesh(f"horn{side}", .3, .05, flat=1, seed=88)
        horn.data.materials.append(bone)
        C.place(horn, el, Vector((0, -1, 0)).rotation_difference(Vector((side * .3, 0, 1)).normalized()).to_matrix().to_4x4())
        # Membran: Faecher zwischen den Fingern, leicht durchhaengend
        bm = bmesh.new()
        ring = tips + [Vector((side * .5, -.15, Z0 - .65)), sh]
        steps = 10
        verts = {}
        def V(i, k):
            key = (i, k)
            if key not in verts:
                a = ring[i % len(ring)]; b = ring[(i + 1) % len(ring)]
                if k == 0:
                    p = el.copy()
                else:
                    t = k / steps
                    outer = a.lerp(b, .5) if False else None
                    p = el.lerp(a, t)
                verts[key] = p
            return verts[key]
        faces = []
        for i in range(len(ring) - 1):
            a, b = ring[i], ring[i + 1]
            for k in range(steps):
                for m_ in range(steps):
                    pass
        # einfache Dreiecks-Faecher mit Unterteilung + Durchhang
        for i in range(len(ring) - 1):
            a, b = ring[i], ring[i + 1]
            n = 12
            grid = []
            for r_ in range(n + 1):
                t = r_ / n
                row = []
                for c_ in range(r_ + 1):
                    u = c_ / max(1, r_)
                    p = el.lerp(a.lerp(b, u), t)
                    sag = math.sin(math.pi * u) * t * .22
                    p = p + Vector((0, sag, -sag * .4))
                    row.append(bm.verts.new(p))
                grid.append(row)
            for r_ in range(n):
                for c_ in range(r_ + 1):
                    bm.faces.new([grid[r_][c_], grid[r_ + 1][c_], grid[r_ + 1][c_ + 1]])
                    if c_ < r_:
                        bm.faces.new([grid[r_][c_], grid[r_ + 1][c_ + 1], grid[r_][c_ + 1]])
        me = bpy.data.meshes.new(f"mem{side}")
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bm.to_mesh(me); bm.free()
        for p in me.polygons:
            p.use_smooth = True
        o = C.link_obj(f"mem{side}", me)
        o.data.materials.append(mem)
        so = o.modifiers.new("sol", "SOLIDIFY"); so.thickness = .015


{"kristall": crystal_wings, "ketten": chain_wings, "daemon": demon_wings}[design]()
C.player_boxes(C.simple_mat("player", (0.025, 0.02, 0.035), 0.7))
C.standard_lights(th)
views = {"hinten": ((0, -9.6, 2.2), (0, 0, 1.95)), "schraeg": ((5.6, -7.6, 2.8), (0, 0, 1.9))}
for name, (loc, tgt) in views.items():
    C.camera(loc, tgt, 50)
    raw = os.path.join(outdir, f"{design}_{theme}_{name}_raw.png")
    C.render(raw)
    C.bloom(raw, os.path.join(outdir, f"{design}_{theme}_{name}.png"), strength=.55)
print("fertig")
