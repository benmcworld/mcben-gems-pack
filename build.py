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
import sys
import zipfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent / "drafts"))

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
# Packs
# --------------------------------------------------------------------------- #
def pack_dir(name):
    d = BUILD / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


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
    from hud_pack import hud_sprites
    save(make_icon(hud_sprites("blau")["armor_full.png"], rgba("#0B1A2E"), rgba("#2E62C9")), d / "pack.png")
    return d, {}


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


def build_hud():
    """McBen-HUD-<Farbe>: Hotbar, Auswahl, Herzen, Ruestung, Hunger, XP (Designs: drafts/hud_pack.py)."""
    from hud_pack import hud_sprites, pack_icon
    from hud_galaxy import THEMES
    out = {}
    for theme in THEMES:
        name = "McBen-HUD-" + "-".join(p.capitalize() for p in theme.split("-"))
        d = pack_dir(name)
        hud = d / "assets" / "minecraft" / "textures" / "gui" / "sprites" / "hud"
        sprites = hud_sprites(theme)
        for rel, img in sprites.items():
            save(img, hud / rel)
        write_json(d / "pack.mcmeta", pack_mcmeta(f"§dMcBen §fHUD §7- {theme.capitalize()}"))
        save(pack_icon(theme), d / "pack.png")
        out[d] = {f"{theme}: hotbar": sprites["hotbar.png"],
                  f"{theme}: auswahl": sprites["hotbar_selection.png"],
                  f"{theme}: herz": sprites["heart/full.png"],
                  f"{theme}: schild": sprites["armor_full.png"],
                  f"{theme}: apfel": sprites["food_full.png"]}
    return out


def main():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    textures = {}
    dirs = []
    for builder in (build_low_fire, build_low_shield):
        d, tex = builder()
        dirs.append(d)
        textures.update(tex)
    for d, tex in build_hud().items():
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
