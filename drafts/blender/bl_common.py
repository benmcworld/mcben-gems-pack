"""Gemeinsame Blender-Helfer: weiche Federn, Materialien, Licht, Rendern, Bloom."""
import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix

THEMES = {
    "lila":  dict(deep=(0.03, 0.005, 0.07), mid=(0.20, 0.04, 0.45), main=(0.62, 0.15, 0.95), tip=(1.0, 0.35, 0.95), glow=(0.85, 0.3, 1.0), world=(0.012, 0.004, 0.03)),
    "gruen": dict(deep=(0.005, 0.03, 0.01), mid=(0.02, 0.2, 0.07), main=(0.1, 0.75, 0.3), tip=(0.6, 1.0, 0.5), glow=(0.3, 1.0, 0.45), world=(0.003, 0.015, 0.006)),
    "blau":  dict(deep=(0.005, 0.015, 0.06), mid=(0.03, 0.12, 0.4), main=(0.15, 0.45, 0.95), tip=(0.5, 0.9, 1.0), glow=(0.35, 0.75, 1.0), world=(0.003, 0.006, 0.025)),
    "dark":  dict(deep=(0.01, 0.01, 0.012), mid=(0.06, 0.06, 0.07), main=(0.35, 0.35, 0.4), tip=(1.0, 1.0, 1.0), glow=(0.9, 0.9, 1.0), world=(0.004, 0.004, 0.005)),
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ------------------------------------------------------------------ Materialien
def node(nt, kind, loc=(0, 0), **kw):
    n = nt.nodes.new(kind)
    n.location = loc
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def ramp(nt, colors, loc=(0, 0)):
    r = node(nt, "ShaderNodeValToRGB", loc)
    cr = r.color_ramp
    while len(cr.elements) < len(colors):
        cr.elements.new(0.5)
    for el, (pos, col) in zip(cr.elements, colors):
        el.position = pos
        el.color = (*col, 1)
    return r


def galaxy_feather_mat(name, th, glow=6.0, seed=0.0):
    """Glaenzende Galaxie-Feder: Nebel-Farbe, Spitzen leuchten, Sternfunken."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = node(nt, "ShaderNodeOutputMaterial", (900, 0))
    bsdf = node(nt, "ShaderNodeBsdfPrincipled", (600, 0))
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    tc = node(nt, "ShaderNodeTexCoord", (-900, 0))
    uv = node(nt, "ShaderNodeSeparateXYZ", (-700, 200))
    nt.links.new(tc.outputs["UV"], uv.inputs[0])
    noise = node(nt, "ShaderNodeTexNoise", (-700, -50))
    noise.inputs["Scale"].default_value = 6.0
    noise.inputs["Detail"].default_value = 8.0
    noise.noise_dimensions = "4D"
    noise.inputs["W"].default_value = seed
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    # Farbe: Nebel (Noise) gemischt mit Verlauf Wurzel->Spitze (UV y)
    mix = node(nt, "ShaderNodeMath", (-450, 100), operation="MULTIPLY_ADD")
    nt.links.new(uv.outputs["Y"], mix.inputs[0]); mix.inputs[1].default_value = 0.55
    nt.links.new(noise.outputs["Fac"], mix.inputs[2])
    col = ramp(nt, [(0.35, th["deep"]), (0.62, th["mid"]), (0.86, th["main"]), (1.0, th["tip"])], (-250, 100))
    nt.links.new(mix.outputs[0], col.inputs[0])
    nt.links.new(col.outputs[0], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.2
    bsdf.inputs["Metallic"].default_value = 0.15
    bsdf.inputs["Coat Weight"].default_value = 0.6
    bsdf.inputs["Coat Roughness"].default_value = 0.08
    # Sterne: Voronoi-Punkte
    vor = node(nt, "ShaderNodeTexVoronoi", (-700, -350))
    vor.inputs["Scale"].default_value = 260.0
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    st = node(nt, "ShaderNodeMath", (-450, -350), operation="LESS_THAN")
    nt.links.new(vor.outputs["Distance"], st.inputs[0]); st.inputs[1].default_value = 0.06
    # Spitzen-Leuchten: UV y^4
    tipg = node(nt, "ShaderNodeMath", (-450, -150), operation="POWER")
    nt.links.new(uv.outputs["Y"], tipg.inputs[0]); tipg.inputs[1].default_value = 5.0
    add = node(nt, "ShaderNodeMath", (-250, -250), operation="ADD")
    nt.links.new(tipg.outputs[0], add.inputs[0]); nt.links.new(st.outputs[0], add.inputs[1])
    emc = node(nt, "ShaderNodeMix", (100, -250)); emc.data_type = "RGBA"
    nt.links.new(st.outputs[0], emc.inputs["Factor"])
    emc.inputs["A"].default_value = (*th["tip"], 1); emc.inputs["B"].default_value = (1, 1, 1, 1)
    nt.links.new(emc.outputs["Result"], bsdf.inputs["Emission Color"])
    sc = node(nt, "ShaderNodeMath", (100, -450), operation="MULTIPLY")
    nt.links.new(add.outputs[0], sc.inputs[0]); sc.inputs[1].default_value = glow
    nt.links.new(sc.outputs[0], bsdf.inputs["Emission Strength"])
    return m


def emit_mat(name, color, strength=8.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength
    return m


def simple_mat(name, color, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


# ------------------------------------------------------------------ Geometrie
def soft_feather(name, length, width, thick, bend=0.15, nu=14, nv=28):
    """Weiche, gewoelbte Feder (Kissen-Form) mit UV (x quer, y Wurzel->Spitze). Spitze zeigt -Y."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    def wprof(v):  # Breite entlang der Feder
        return width * min(1.0, (v * 4.0) ** 0.6) * math.sqrt(max(0.0, 1 - max(0.0, (v - 0.5) / 0.5) ** 2.2))
    rows = []
    for side in (1, -1):  # Ober- und Unterseite
        grid = []
        for j in range(nv + 1):
            v = j / nv
            w = wprof(v)
            row = []
            for i in range(nu + 1):
                u = -1 + 2 * i / nu
                t = thick * math.sqrt(max(0.0, 1 - u * u)) * (0.4 + 0.6 * math.sin(math.pi * min(1, v * 1.1)))
                x = u * w / 2
                y = -v * length
                z = side * t / 2 + bend * (v * length) ** 2 + 0.06 * width * (1 - u * u) * 0
                row.append(bm.verts.new((x, y, z)))
            grid.append(row)
        rows.append(grid)
    top, bot = rows
    def face(vs, uvs):
        try:
            f = bm.faces.new(vs)
        except ValueError:
            return
        for l, uvc in zip(f.loops, uvs):
            l[uvl].uv = uvc
    for g, flip in ((top, False), (bot, True)):
        for j in range(nv):
            for i in range(nu):
                q = [g[j][i], g[j][i + 1], g[j + 1][i + 1], g[j + 1][i]]
                uvs = [(i / nu, j / nv), ((i + 1) / nu, j / nv), ((i + 1) / nu, (j + 1) / nv), (i / nu, (j + 1) / nv)]
                if flip:
                    q.reverse(); uvs.reverse()
                face(q, uvs)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    sub = ob.modifiers.new("sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
    return ob


def tube_along(name, pts, radius, mat):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 6
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (*c, 1)
        p.radius = 1.0
    sp.use_smooth = True
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


# ------------------------------------------------------------------ Szene
def setup(th, res=(1000, 800), samples=64):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.exposure = -0.3
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*th["world"], 1); bg.inputs[1].default_value = 1.0
    return sc


def area_light(name, loc, rot, energy, color=(1, 1, 1), size=3):
    l = bpy.data.lights.new(name, "AREA"); l.energy = energy; l.color = color; l.size = size
    o = bpy.data.objects.new(name, l); o.location = loc; o.rotation_euler = rot
    bpy.context.collection.objects.link(o)
    return o


def camera(loc, target, lens=50):
    c = bpy.data.cameras.new("cam"); c.lens = lens
    o = bpy.data.objects.new("cam", c); o.location = loc
    bpy.context.collection.objects.link(o)
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o
    return o


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def bloom(path, out, strength=0.9, radius=18):
    """Bloom als Nachbearbeitung (helle Bereiche weich ueberstrahlen)."""
    from PIL import Image, ImageFilter, ImageChops
    im = Image.open(path).convert("RGB")
    bright = im.point(lambda v: max(0, v - 185) * 3.0)
    glow = bright.filter(ImageFilter.GaussianBlur(radius))
    glow2 = bright.filter(ImageFilter.GaussianBlur(radius * 3))
    res = ImageChops.add(im, glow.point(lambda v: v * strength))
    res = ImageChops.add(res, glow2.point(lambda v: v * strength * 0.6))
    res.save(out)
