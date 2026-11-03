#!/usr/bin/env python3
"""
MCBen Gems Pack - Generator.

Erzeugt alle Resource Packs aus config.json und legt sie als fertige
.zip-Dateien in dist/ ab. Benoetigt Python 3 + Pillow (pip install pillow).

    python3 build.py
"""
import json
import math
import random
import shutil
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
DIST = ROOT / "dist"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

# Formate: 18 = 1.20.2 (Hotbar-Sprites, Overlays), 46 = 1.21.4 (neue Item-Modelle)
MIN_FORMAT = 18
MAX_FORMAT = 999
CURRENT_FORMAT = 46


# --------------------------------------------------------------------------- #
# Helfer
# --------------------------------------------------------------------------- #
def rgba(hex_str):
    h = hex_str.lstrip("#")
    if len(h) == 6:
        h += "FF"
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4, 6))


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4))


def shade(c, f):
    return tuple(max(0, min(255, int(c[i] * f))) for i in range(3)) + (c[3],)


def new_img(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def rect(img, x0, y0, x1, y1, col):
    """Gefuelltes Rechteck, x1/y1 exklusiv."""
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            img.putpixel((x, y), col)


def frame(img, x0, y0, x1, y1, col, t=1):
    rect(img, x0, y0, x1, y0 + t, col)
    rect(img, x0, y1 - t, x1, y1, col)
    rect(img, x0, y0, x0 + t, y1, col)
    rect(img, x1 - t, y0, x1, y1, col)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def pack_mcmeta(description, overlays=None):
    pack = {
        "description": description,
        "pack_format": CURRENT_FORMAT,
        "supported_formats": [MIN_FORMAT, MAX_FORMAT],
        "min_format": MIN_FORMAT,
        "max_format": MAX_FORMAT,
    }
    data = {"pack": pack}
    if overlays:
        data["overlays"] = {"entries": overlays}
    return data


def make_icon(sprite, bg_top, bg_bottom):
    """64x64 pack.png: Farbverlauf + hochskaliertes Sprite."""
    icon = new_img(64, 64)
    for y in range(64):
        c = mix(bg_top, bg_bottom, y / 63)
        rect(icon, 0, y, 64, y + 1, c)
    s = sprite.copy()
    s.thumbnail((48, 48), Image.NEAREST)
    scale = max(1, 48 // max(sprite.size))
    s = sprite.resize((sprite.width * scale, sprite.height * scale), Image.NEAREST)
    if s.width > 60 or s.height > 60:
        s.thumbnail((60, 60), Image.NEAREST)
    icon.alpha_composite(s, ((64 - s.width) // 2, (64 - s.height) // 2))
    return icon


# --------------------------------------------------------------------------- #
# Krone (ersetzt den geschnitzten Kuerbis)
# --------------------------------------------------------------------------- #
def crown_texture(c):
    gl, g, gd = rgba(c["gold_light"]), rgba(c["gold"]), rgba(c["gold_dark"])
    gems = [rgba(x) for x in c["gems"]]
    img = new_img(16, 16)
    # Reihen 0-3: Band
    rect(img, 0, 0, 16, 4, g)
    rect(img, 0, 0, 16, 1, gl)
    rect(img, 0, 3, 16, 4, gd)
    for x in range(1, 16, 4):
        img.putpixel((x, 1), gl)
        img.putpixel((x + 2, 2), gd)
    # Reihen 4-7: Zacken (Verlauf)
    for y in range(4, 8):
        rect(img, 0, y, 16, y + 1, mix(gl, g, (y - 4) / 3))
    for x in range(0, 16, 2):
        img.putpixel((x, 7), gd)
    # Reihen 8-11: Edelsteine (je 4x4)
    for i, gem in enumerate(gems[:4]):
        x0 = i * 4
        rect(img, x0, 8, x0 + 4, 12, gem)
        rect(img, x0, 8, x0 + 2, 10, mix(gem, (255, 255, 255, 255), 0.55))
        rect(img, x0 + 2, 10, x0 + 4, 12, shade(gem, 0.6))
    # Reihen 12-15: Innenseite / Oberseite
    rect(img, 0, 12, 16, 16, gd)
    return img


def cube(frm, to, uv):
    faces = {f: {"uv": uv, "texture": "#crown"} for f in
             ("north", "south", "east", "west", "up", "down")}
    return {"from": frm, "to": to, "faces": faces}


def crown_model():
    BAND = [0, 0, 16, 4]
    SPIKE = [0, 4, 16, 8]
    INNER = [0, 12, 16, 16]
    GEMS = [[0, 8, 4, 12], [4, 8, 8, 12], [8, 8, 12, 12]]
    y0, y1 = 13, 17          # Band sitzt auf dem Kopf (Kopf-Oberkante ~ y 14.4)
    lo, hi = 0.75, 15.25     # knapp ausserhalb der Hut-Ebene
    t = 1.0                  # Wandstaerke
    els = [
        cube([lo, y0, lo], [hi, y1, lo + t], BAND),              # Nord
        cube([lo, y0, hi - t], [hi, y1, hi], BAND),              # Sued
        cube([lo, y0, lo + t], [lo + t, y1, hi - t], BAND),      # West
        cube([hi - t, y0, lo + t], [hi, y1, hi - t], BAND),      # Ost
    ]
    # Zacken: aussen klein, Mitte gross
    for (a, b, top) in ((lo, lo + 2, y1 + 2.5), (7, 9, y1 + 4), (hi - 2, hi, y1 + 2.5)):
        els.append(cube([a, y1, lo], [b, top, lo + t], SPIKE))
        els.append(cube([a, y1, hi - t], [b, top, hi], SPIKE))
        els.append(cube([lo, y1, a], [lo + t, top, b], SPIKE))
        els.append(cube([hi - t, y1, a], [hi, top, b], SPIKE))
    # Kugeln auf den mittleren Zacken
    for (x0, z0) in ((7.5, lo - 0.25), (7.5, hi - t - 0.25), (lo - 0.25, 7.5), (hi - t - 0.25, 7.5)):
        els.append(cube([x0, y1 + 4, z0], [x0 + 1.5, y1 + 5.5, z0 + 1.5], GEMS[0]))
    # Edelsteine vorne auf dem Band
    gem_cycle = [GEMS[0], GEMS[1], GEMS[2], GEMS[1]]
    sides = [
        ([7, y0 + 1, lo - 0.5], [9, y1 - 1, lo]),
        ([7, y0 + 1, hi], [9, y1 - 1, hi + 0.5]),
        ([lo - 0.5, y0 + 1, 7], [lo, y1 - 1, 9]),
        ([hi, y0 + 1, 7], [hi + 0.5, y1 - 1, 9]),
    ]
    for i, (f, tt) in enumerate(sides):
        els.append(cube(f, tt, gem_cycle[i]))
    for x in (3.5, 11.5):
        els.append(cube([x, y0 + 1.25, lo - 0.5], [x + 1, y1 - 1.25, lo], GEMS[2]))
        els.append(cube([x, y0 + 1.25, hi], [x + 1, y1 - 1.25, hi + 0.5], GEMS[2]))
    return {
        "parent": "minecraft:block/block",
        "textures": {"crown": "minecraft:item/mcben_crown",
                     "particle": "minecraft:item/mcben_crown"},
        "elements": els,
        "display": {
            "gui": {"rotation": [30, 225, 0], "translation": [0, -6.5, 0], "scale": [0.85, 0.85, 0.85]},
            "ground": {"rotation": [0, 0, 0], "translation": [0, -2, 0], "scale": [0.4, 0.4, 0.4]},
            "fixed": {"rotation": [0, 0, 0], "translation": [0, -6, 0], "scale": [0.8, 0.8, 0.8]},
            "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, -1.5, 2.5], "scale": [0.375, 0.375, 0.375]},
            "thirdperson_lefthand": {"rotation": [75, 45, 0], "translation": [0, -1.5, 2.5], "scale": [0.375, 0.375, 0.375]},
            "firstperson_righthand": {"rotation": [0, 45, 0], "translation": [0, -3, 0], "scale": [0.4, 0.4, 0.4]},
            "firstperson_lefthand": {"rotation": [0, 225, 0], "translation": [0, -3, 0], "scale": [0.4, 0.4, 0.4]},
        },
    }


# --------------------------------------------------------------------------- #
# Fluegel (Elytra)
# --------------------------------------------------------------------------- #
def wings_texture(c):
    top, mid, tip, line = rgba(c["top"]), rgba(c["middle"]), rgba(c["tip"]), rgba(c["feather_line"])

    def grad(t):
        return mix(top, mid, t / 0.5) if t < 0.5 else mix(mid, tip, (t - 0.5) / 0.5)

    img = new_img(64, 32)
    # Box 10x20x2 bei UV (22,0): Oberseite/Unterseite, Seiten, Vorder- und Rueckseite
    rect(img, 24, 0, 34, 2, top)
    rect(img, 34, 0, 44, 2, shade(top, 0.8))
    for y in range(2, 22):
        t = (y - 2) / 19
        rect(img, 22, y, 24, y + 1, shade(grad(t), 0.75))
        rect(img, 34, y, 36, y + 1, shade(grad(t), 0.75))
    for face_x, dark in ((24, 1.0), (36, 0.85)):
        for y in range(2, 22):
            for x in range(10):
                fy = y - 2
                # Fluegelform: unten zur Spitze hin abgerundet
                if fy > 12 and x < (fy - 12) * 1.2:
                    continue
                col = shade(grad(fy / 19), dark)
                # Federlinien (diagonal)
                if (x + fy) % 5 == 0 and fy > 2:
                    col = mix(col, line, 0.55)
                # Federspitzen-Kante
                if fy > 12 and x < (fy - 12) * 1.2 + 1:
                    col = mix(col, tip, 0.5)
                img.putpixel((face_x + x, y), col)
    return img


# --------------------------------------------------------------------------- #
# Schild
# --------------------------------------------------------------------------- #
def shield_texture(c):
    field, fl = rgba(c["field"]), rgba(c["field_light"])
    border, bd = rgba(c["border"]), rgba(c["border_dark"])
    gem, gl = rgba(c["gem"]), rgba(c["gem_light"])
    handle = rgba(c["handle"])
    img = new_img(64, 64)
    # Kanten der Platte (12x22x1 bei UV 0,0)
    rect(img, 1, 0, 25, 1, border)
    rect(img, 0, 1, 1, 23, bd)
    rect(img, 13, 1, 14, 23, bd)
    # Vorderseite (1,1)-(13,23)
    for y in range(1, 23):
        for x in range(1, 13):
            t = ((x - 1) + (y - 1)) / 32
            img.putpixel((x, y), mix(fl, field, t))
    frame(img, 1, 1, 13, 23, border)
    rect(img, 1, 22, 13, 23, bd)
    rect(img, 12, 1, 13, 23, bd)
    # Edelstein-Emblem (Raute) in der Mitte
    cx, cy = 6.5, 11.5
    for y in range(3, 21):
        for x in range(2, 12):
            d = abs(x - cx) / 4.0 + abs(y - cy) / 7.0
            if d <= 1.0:
                col = gem
                if x < cx and y < cy:
                    col = gl
                elif x > cx and y > cy:
                    col = shade(gem, 0.6)
                if d > 0.82:
                    col = border
                img.putpixel((x, y), col)
    # Ecknieten
    for (x, y) in ((2, 2), (11, 2), (2, 21), (11, 21)):
        img.putpixel((x, y), rgba("#FFFFFF"))
    # Rueckseite (14,1)-(26,23): Holz-/Lederoptik
    for y in range(1, 23):
        for x in range(14, 26):
            img.putpixel((x, y), shade(handle, 0.9 if (y // 3) % 2 else 1.05))
    frame(img, 14, 1, 26, 23, bd)
    # Griff (2x6x6 bei UV 26,0)
    rect(img, 26, 0, 42, 12, handle)
    for y in range(0, 12, 2):
        rect(img, 26, y, 42, y + 1, shade(handle, 0.75))
    return img


# --------------------------------------------------------------------------- #
# Schwerter
# --------------------------------------------------------------------------- #
def sword_texture(c):
    blade, bdark = rgba(c["blade"]), rgba(c["blade_dark"])
    guard, handle, gem = rgba(c["guard"]), rgba(c["handle"]), rgba(c["gem"])
    outline = shade(bdark, 0.35)
    outline = (outline[0], outline[1], outline[2], 255)
    px = {}
    for t in range(10):
        px[(5 + t, 10 - t)] = mix(blade, (255, 255, 255, 255), 0.35) if t > 6 else blade
        if t < 9:
            px[(6 + t, 10 - t)] = bdark
    for (x, y) in ((2, 9), (3, 10), (5, 12), (6, 13)):
        px[(x, y)] = guard
    px[(4, 11)] = gem                      # Edelstein im Parier
    px[(3, 12)] = handle
    px[(2, 13)] = handle
    px[(1, 14)] = gem                      # Knauf-Edelstein
    img = new_img(16, 16)
    for (x, y) in list(px):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in px and 0 <= n[0] < 16 and 0 <= n[1] < 16:
                img.putpixel(n, outline)
    for (x, y), col in px.items():
        img.putpixel((x, y), col)
    return img


# --------------------------------------------------------------------------- #
# Low Fire
# --------------------------------------------------------------------------- #
def fire_strip(height, seed, frames=16):
    rnd = random.Random(seed)
    phases = [rnd.uniform(0, math.tau) for _ in range(16)]
    speeds = [rnd.choice((1, 2)) for _ in range(16)]
    hot = rgba("#FFF7B5")
    yellow = rgba("#FFD23F")
    orange = rgba("#FF8A1E")
    red = rgba("#D7261E")
    img = new_img(16, 16 * frames)
    for f in range(frames):
        a = f / frames * math.tau
        for x in range(16):
            wave = (math.sin(a * speeds[x] + phases[x]) + 1) / 2
            nb = (math.sin(a * 2 + x * 0.9) + 1) / 2
            h = max(1, round(height * (0.55 + 0.3 * wave + 0.15 * nb)))
            for k in range(h):              # k = Hoehe ueber dem Boden
                t = k / max(1, h - 1)
                if t < 0.25:
                    col = mix(hot, yellow, t / 0.25)
                elif t < 0.6:
                    col = mix(yellow, orange, (t - 0.25) / 0.35)
                else:
                    col = mix(orange, red, (t - 0.6) / 0.4)
                if k == h - 1:
                    col = col[:3] + (170,)
                img.putpixel((x, f * 16 + 15 - k), col)
    return img


# --------------------------------------------------------------------------- #
# Hotbar
# --------------------------------------------------------------------------- #
def hotbar_textures(c):
    bg, slot = rgba(c["bg"]), rgba(c["slot"])
    border, bd = rgba(c["border"]), rgba(c["border_dark"])
    sel, sd = rgba(c["select"]), rgba(c["select_dark"])
    bar = new_img(182, 22)
    rect(bar, 0, 0, 182, 22, bg)
    frame(bar, 0, 0, 182, 22, border)
    rect(bar, 0, 21, 182, 22, bd)
    rect(bar, 181, 0, 182, 22, bd)
    for i in range(9):
        x0 = 1 + i * 20
        rect(bar, x0 + 1, 2, x0 + 19, 20, slot)
        frame(bar, x0 + 1, 2, x0 + 19, 20, bd)
        bar.putpixel((x0 + 1, 2), border)
    selection = new_img(24, 23)
    frame(selection, 0, 0, 24, 24, sd)
    frame(selection, 1, 1, 23, 23, sel, t=2)
    for (x, y) in ((1, 1), (22, 1)):
        selection.putpixel((x, y), (255, 255, 255, 255))
    return bar, selection


# --------------------------------------------------------------------------- #
# Packs
# --------------------------------------------------------------------------- #
def pack_dir(name):
    d = BUILD / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


def build_cosmetics():
    d = pack_dir("McBen-Cosmetics")
    a = d / "assets" / "minecraft"
    # Krone
    crown = crown_texture(CFG["crown"])
    save(crown, a / "textures/item/mcben_crown.png")
    write_json(a / "models/item/mcben_crown.json", crown_model())
    write_json(a / "items/carved_pumpkin.json",                       # 1.21.4+
               {"model": {"type": "minecraft:model", "model": "minecraft:item/mcben_crown"}})
    write_json(a / "models/item/carved_pumpkin.json",                 # 1.20.2 - 1.21.3
               {"parent": "minecraft:item/mcben_crown"})
    save(new_img(16, 16), a / "textures/misc/pumpkinblur.png")       # kein Kuerbis-Overlay
    # Fluegel
    wings = wings_texture(CFG["wings"])
    save(wings, a / "textures/entity/equipment/wings/elytra.png")     # 1.21.2+
    save(wings, a / "textures/entity/elytra.png")                     # aeltere Versionen
    # Schild
    shield = shield_texture(CFG["shield"])
    save(shield, a / "textures/entity/shield_base_nopattern.png")
    save(shield, a / "textures/entity/shield_base.png")
    # Schwerter
    swords = {}
    for name, c in CFG["swords"].items():
        swords[name] = sword_texture(c)
        save(swords[name], a / f"textures/item/{name}.png")
    write_json(d / "pack.mcmeta", pack_mcmeta("§dMcBen §6Cosmetics §7- Krone, Fluegel, Schild, Schwerter"))
    save(make_icon(crown_preview(crown), rgba("#2B1150"), rgba("#8E3FE0")), d / "pack.png")
    return d, {"crown": crown, "wings": wings, "shield": shield, **swords}


def crown_preview(tex):
    """Einfache 2D-Vorschau der Krone fuer das Pack-Icon."""
    img = new_img(16, 12)
    band = tex.crop((0, 0, 16, 4))
    img.alpha_composite(band, (0, 8))
    spike = tex.crop((0, 4, 2, 8))
    for x, h in ((0, 3), (7, 5), (14, 3)):
        for y in range(h):
            img.alpha_composite(spike.crop((0, 0, 2, 1)).resize((2, 1)), (x, 7 - y))
    gem = tex.crop((0, 8, 2, 2 + 8))
    img.alpha_composite(tex.crop((0, 8, 2, 10)), (7, 1))
    img.alpha_composite(tex.crop((4, 8, 6, 10)), (7, 9))
    img.alpha_composite(tex.crop((8, 8, 10, 10)), (3, 9))
    img.alpha_composite(tex.crop((8, 8, 10, 10)), (11, 9))
    return img


def build_low_fire():
    d = pack_dir("McBen-LowFire")
    a = d / "assets" / "minecraft"
    h = int(CFG["low_fire"]["height"])
    strips = []
    for i, name in enumerate(("fire_0", "fire_1")):
        strip = fire_strip(h, seed=i + 1)
        strips.append(strip)
        save(strip, a / f"textures/block/{name}.png")
        write_json(a / f"textures/block/{name}.png.mcmeta", {"animation": {"frametime": 2}})
    write_json(d / "pack.mcmeta", pack_mcmeta(f"§dMcBen §cLow Fire §7- Feuer nur {h}/16 hoch"))
    save(make_icon(strips[1].crop((0, 0, 16, 16)), rgba("#1A0B05"), rgba("#4A1A05")), d / "pack.png")
    return d, {"fire": strips[1].crop((0, 0, 16, 16))}


SHIELD_DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [10, 6, -4], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [10, 6, 12], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [0, 180, 5], "translation": [-10, 2, -10], "scale": [1.25, 1.25, 1.25]},
    "firstperson_lefthand": {"rotation": [0, 180, 5], "translation": [10, 0, -10], "scale": [1.25, 1.25, 1.25]},
    "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65, 0.65, 0.65]},
    "fixed": {"rotation": [0, 180, 0], "translation": [-4.5, 4.5, -5], "scale": [0.55, 0.55, 0.55]},
    "ground": {"rotation": [0, 0, 0], "translation": [2, 4, 2], "scale": [0.25, 0.25, 0.25]},
}
SHIELD_BLOCKING_DISPLAY = {
    "thirdperson_righthand": {"rotation": [45, 135, 0], "translation": [3.51, 11, -2], "scale": [1, 1, 1]},
    "thirdperson_lefthand": {"rotation": [45, 135, 0], "translation": [13.51, 3, 5], "scale": [1, 1, 1]},
    "firstperson_righthand": {"rotation": [0, 180, -5], "translation": [-15, 5, -11], "scale": [1.25, 1.25, 1.25]},
    "firstperson_lefthand": {"rotation": [0, 180, -5], "translation": [5, 5, -11], "scale": [1.25, 1.25, 1.25]},
    "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65, 0.65, 0.65]},
}


def lowered(display, off):
    out = json.loads(json.dumps(display))
    for k in ("firstperson_righthand", "firstperson_lefthand"):
        out[k]["translation"][1] -= off
    return out


def build_low_shield():
    d = pack_dir("McBen-LowShield")
    off = float(CFG["low_shield"]["offset_down"])
    a = d / "assets" / "minecraft" / "models" / "item"
    base = {"gui_light": "front", "textures": {"particle": "minecraft:block/dark_oak_planks"}}
    # 1.21.4+ (Spezialmodell ueber items/shield.json)
    write_json(a / "shield.json", {**base, "display": lowered(SHIELD_DISPLAY, off)})
    write_json(a / "shield_blocking.json", {**base, "display": lowered(SHIELD_BLOCKING_DISPLAY, off)})
    # 1.20.2 - 1.21.3 (builtin/entity) als Overlay
    la = d / "legacy" / "assets" / "minecraft" / "models" / "item"
    write_json(la / "shield.json", {
        "parent": "builtin/entity", **base,
        "display": lowered(SHIELD_DISPLAY, off),
        "overrides": [{"predicate": {"blocking": 1}, "model": "item/shield_blocking"}],
    })
    write_json(la / "shield_blocking.json", {
        "parent": "builtin/entity", **base,
        "display": lowered(SHIELD_BLOCKING_DISPLAY, off),
    })
    overlays = [{"formats": [MIN_FORMAT, 45], "min_format": MIN_FORMAT, "max_format": 45,
                 "directory": "legacy"}]
    write_json(d / "pack.mcmeta", pack_mcmeta("§dMcBen §bLow Shield §7- Schild tiefer in 1st-Person", overlays))
    save(make_icon(shield_icon(), rgba("#0B1A2E"), rgba("#2E62C9")), d / "pack.png")
    return d, {}


def shield_icon():
    tex = shield_texture(CFG["shield"])
    return tex.crop((1, 1, 13, 23))


def build_hotbars():
    out = {}
    for theme, c in CFG["hotbars"].items():
        d = pack_dir(f"McBen-Hotbar-{theme.capitalize()}")
        a = d / "assets" / "minecraft" / "textures" / "gui" / "sprites" / "hud"
        bar, sel = hotbar_textures(c)
        save(bar, a / "hotbar.png")
        save(sel, a / "hotbar_selection.png")
        write_json(d / "pack.mcmeta", pack_mcmeta(f"§dMcBen §eHotbar §7- {theme.capitalize()}"))
        preview = new_img(64, 24)
        preview.alpha_composite(bar.crop((0, 0, 62, 22)), (1, 1))
        preview.alpha_composite(sel, (20, 0))
        save(make_icon(preview, rgba("#101010"), rgba(c["border"])), d / "pack.png")
        out[d] = {"hotbar_" + theme: bar, "hotbar_selection_" + theme: sel}
    return out


def zip_pack(d):
    DIST.mkdir(exist_ok=True)
    z = DIST / f"{d.name}.zip"
    if z.exists():
        z.unlink()
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(d.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(d).as_posix())
    return z


def preview_sheet(textures):
    """Alle Texturen hochskaliert auf ein Bild (preview.png)."""
    scale, pad = 6, 12
    items = list(textures.items())
    rows, x, y, row_h, width = [], pad, pad, 0, 1200
    placed = []
    for name, img in items:
        w, h = img.width * scale, img.height * scale
        if w > 400:
            w, h = img.width * 3, img.height * 3
        if x + w + pad > width:
            x, y = pad, y + row_h + pad
            row_h = 0
        placed.append((img, x, y, w, h))
        x += w + pad
        row_h = max(row_h, h)
    sheet = Image.new("RGBA", (width, y + row_h + pad), rgba("#3A3A3A"))
    for img, x, y, w, h in placed:
        for yy in range(0, h, 12):         # Karo-Hintergrund fuer Transparenz
            for xx in range(0, w, 12):
                c = rgba("#555555") if (xx // 12 + yy // 12) % 2 else rgba("#666666")
                rect(sheet, x + xx, y + yy, min(x + xx + 12, x + w), min(y + yy + 12, y + h), c)
        sheet.alpha_composite(img.resize((w, h), Image.NEAREST), (x, y))
    sheet.save(ROOT / "preview.png")


def main():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    textures = {}
    dirs = []
    for builder in (build_cosmetics, build_low_fire, build_low_shield):
        d, tex = builder()
        dirs.append(d)
        textures.update(tex)
    for d, tex in build_hotbars().items():
        dirs.append(d)
        textures.update(tex)
    if DIST.exists():
        shutil.rmtree(DIST)
    for d in dirs:
        print("gebaut:", zip_pack(d).relative_to(ROOT))
    preview_sheet(textures)
    print("Vorschau: preview.png")


if __name__ == "__main__":
    main()
