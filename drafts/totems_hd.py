"""Totem-Entwuerfe v2 (64x64) im Galaxy-Cosmetic-Stil:
dunkler Nebel, leuchtendes Magenta, Sterne, Federfluegel, leuchtende Raender, Kristalle.
Wird in hoher Aufloesung gemalt und dann auf 64x64 verkleinert."""
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, str(Path(__file__).parent))
from hud_galaxy import THEMES, hexc
from galaxy import fbm

OUT = Path(__file__).parent / "hud"
S = 512          # Mal-Aufloesung
N = 64           # Endgroesse der Textur
PX = S / N       # 1 Endpixel in Mal-Pixeln


# --------------------------------------------------------------------------- #
# Grundbausteine
# --------------------------------------------------------------------------- #
def blank(mode="RGBA"):
    return Image.new(mode, (S, S))


def neb(t, seed, bright=1.0, stars=True):
    rng = np.random.default_rng(seed)
    v = fbm(S, S, rng, base=S // 3, octaves=7)
    w = fbm(S, S, rng, base=S // 5, octaves=5)
    v = np.clip((v * .7 + w * .3 - .28) * 2.0, 0, 1) ** 1.35 * bright
    cols = [hexc(c) for c in (t["nebula"][0], t["nebula"][1], t["nebula"][2], t["icon_dark"], t["icon"], t["icon_light"])]
    stops = np.linspace(0, 1, len(cols))
    rgb = np.stack([np.interp(np.clip(v, 0, 1), stops, [c[i] for c in cols]) for i in range(3)], -1)
    img = Image.fromarray(rgb.astype(np.uint8)).convert("RGBA")
    if stars:
        st = blank()
        d = ImageDraw.Draw(st)
        for _ in range(55):
            x, y = rng.random() * S, rng.random() * S
            r = rng.choice([PX * .5, PX * .7, PX * 1.1], p=[.6, .3, .1])
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 245, 255, 255))
        img.alpha_composite(st.filter(ImageFilter.GaussianBlur(PX * .8)))
        img.alpha_composite(st)
    return img


def fill(mask, tex):
    out = blank()
    out.paste(tex, (0, 0), mask)
    return out


def shade_dir(mask, t, strength=75):
    """Licht von oben-links, Schatten unten-rechts (innerhalb der Maske)."""
    g = Image.linear_gradient("L").rotate(45, expand=False).resize((S, S))
    dark = Image.new("RGBA", (S, S), hexc(t["nebula"][0]))
    dark.putalpha(ImageChops.multiply(mask, g.point(lambda v: v * strength // 255)))
    return dark


def rim(mask, t, width=PX * 1.2, glow_r=PX * 2.5, col=None):
    """Leuchtender Rand innen + Glow aussen."""
    col = hexc(col or t["icon_light"])
    inner = mask.filter(ImageFilter.MinFilter(int(width) * 2 + 1))
    ring = ImageChops.subtract(mask, inner)
    out = blank()
    gl = Image.new("RGBA", (S, S), hexc(t["border_glow"]))
    gl.putalpha(ring.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: min(255, v * 2)))
    out.alpha_composite(gl)
    r = Image.new("RGBA", (S, S), col)
    r.putalpha(ring)
    out.alpha_composite(r)
    return out


def outline(mask, t, width=PX * 1.0):
    big = mask.filter(ImageFilter.MaxFilter(int(width) * 2 + 1))
    o = Image.new("RGBA", (S, S), hexc(t["icon_line"]))
    o.putalpha(ImageChops.subtract(big, mask))
    return o


def body(mask, t, seed, bright=1.0, rim_col=None):
    """Kompletter Galaxy-Koerper: Nebel, Schattierung, Umriss, Leuchtrand."""
    out = blank()
    out.alpha_composite(outline(mask, t))
    out.alpha_composite(fill(mask, neb(t, seed, bright * 1.5)))
    out.alpha_composite(shade_dir(mask, t))
    out.alpha_composite(rim(mask, t, col=rim_col))
    return out


def poly_mask(pts):
    m = blank("L")
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def sc(pts):
    """Koordinaten in Endpixeln (0-64) -> Mal-Pixel."""
    return [(x * PX, y * PX) for x, y in pts]


# --------------------------------------------------------------------------- #
# Federfluegel
# --------------------------------------------------------------------------- #
def feather(root, ang_deg, length, width, curve, side):
    a = math.radians(ang_deg)
    dx, dy = math.cos(a) * side, math.sin(a)
    px, py = -dy * side, dx * side           # Senkrechte (zeigt "nach unten" vom Fluegel weg)
    left, right = [], []
    steps = 24
    for i in range(steps + 1):
        s = i / steps
        bend = curve * math.sin(math.pi * s * .9) * length
        cx = root[0] + dx * s * length + px * bend
        cy = root[1] + dy * s * length + py * bend
        w = width * (math.sin(math.pi * min(1, s * 1.05)) ** .55) * (1 - .35 * s)
        left.append((cx + px * w, cy + py * w))
        right.append((cx - px * w, cy - py * w))
    return left + right[::-1]


def wing(t, root, scale, side, seed, layers=None):
    """Ein Fluegel aus 3 Federreihen, jede Feder einzeln mit Verlauf + Umriss."""
    layers = layers or [
        # (Winkel-Liste, Laenge, Breite, Kruemmung, Helligkeit)
        ([-72, -58, -44, -30, -16, -2, 12, 26], 30, 4.0, .12, 1.25),
        ([-62, -46, -30, -14, 2, 18], 21, 4.2, .10, 1.1),
        ([-52, -32, -12, 8], 12, 4.6, .06, .95),
    ]
    out = blank()
    rng = np.random.default_rng(seed)
    for li, (angles, L, W, curve, br) in enumerate(layers):
        for j, ang in enumerate(angles):
            Lj = L * scale * (1 - .045 * j) * PX
            m = poly_mask(feather(root, ang, Lj, W * scale * PX, curve, side))
            tex = neb(t, int(rng.integers(1e6)), br * (1.15 - .1 * li), stars=(li == 0))
            # Verlauf entlang der Feder: Wurzel dunkel -> Spitze hell
            grad = Image.linear_gradient("L").resize((S, S))
            grad = grad.rotate(-ang * side + (90 if side > 0 else -90), center=root)
            f = fill(m, tex)
            tip = Image.new("RGBA", (S, S), hexc(t["icon"]))
            tip.putalpha(ImageChops.multiply(m, grad.point(lambda v: v * 120 // 255)))
            out.alpha_composite(outline(m, t, PX * .8))
            out.alpha_composite(f)
            out.alpha_composite(tip)
            # Feder-Kiel (helle Mittellinie)
            a = math.radians(ang)
            d = ImageDraw.Draw(out)
            d.line([root, (root[0] + math.cos(a) * side * Lj * .85, root[1] + math.sin(a) * Lj * .85)],
                   fill=hexc(t["icon_light"], 140), width=max(1, int(PX * .45)))
    # Leuchtpunkte auf dem Fluegel
    sp = blank()
    d = ImageDraw.Draw(sp)
    for _ in range(10):
        ang = math.radians(rng.uniform(-60, 10))
        r = rng.uniform(.25, .9) * 30 * scale * PX
        x, y = root[0] + math.cos(ang) * side * r, root[1] + math.sin(ang) * r
        rr = PX * rng.uniform(.5, .9)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(255, 220, 255, 255))
    out.alpha_composite(sp.filter(ImageFilter.GaussianBlur(PX)))
    out.alpha_composite(sp)
    return out


def wings(t, root_l, root_r, scale, seed):
    out = blank()
    out.alpha_composite(wing(t, root_l, scale, -1, seed))
    out.alpha_composite(wing(t, root_r, scale, 1, seed + 1))
    return out


# --------------------------------------------------------------------------- #
# Formen
# --------------------------------------------------------------------------- #
def heater_shield(cx, top, w, h):
    pts = [(cx - w / 2, top + h * .06), (cx, top), (cx + w / 2, top + h * .06)]
    for i in range(1, 31):
        s = i / 30
        pts.append((cx + w / 2 * (1 - s ** 2.2), top + h * .06 + h * .94 * s))
    for i in range(29, 0, -1):
        s = i / 30
        pts.append((cx - w / 2 * (1 - s ** 2.2), top + h * .06 + h * .94 * s))
    return pts


def heart_mask(cx, cy, size):
    m = blank("L")
    d = ImageDraw.Draw(m)
    r = size * .28
    d.ellipse((cx - size * .5, cy - size * .38, cx - size * .5 + 2 * r * 1.0, cy - size * .38 + 2 * r), fill=255)
    d.ellipse((cx + size * .5 - 2 * r, cy - size * .38, cx + size * .5, cy - size * .38 + 2 * r), fill=255)
    d.polygon([(cx - size * .49, cy - size * .12), (cx + size * .49, cy - size * .12), (cx, cy + size * .5)], fill=255)
    return m


def crystal_pts(cx, cy, w, h, tilt=0):
    pts = [(0, -h / 2), (w / 2, -h / 2 + w * .45), (w / 2, h / 2 - w * .45), (0, h / 2),
           (-w / 2, h / 2 - w * .45), (-w / 2, -h / 2 + w * .45)]
    a = math.radians(tilt)
    return [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in pts]


def crystal(t, cx, cy, w, h, tilt, seed):
    pts = crystal_pts(cx, cy, w, h, tilt)
    m = poly_mask(pts)
    out = body(m, t, seed, 1.25)
    # Facetten: rechte Haelfte dunkler, Mittelkante hell
    half = poly_mask([pts[0], pts[1], pts[2], pts[3]])
    dk = Image.new("RGBA", (S, S), hexc(t["nebula"][0], 110))
    dk.putalpha(ImageChops.multiply(half, Image.new("L", (S, S), 110)))
    out.alpha_composite(dk)
    ImageDraw.Draw(out).line([pts[0], pts[3]], fill=hexc(t["icon_light"]), width=int(PX * .7))
    return out


def planet(t, cx, cy, r, seed, ring_on=True):
    m = blank("L")
    ImageDraw.Draw(m).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    out = blank()
    if ring_on:  # hinterer Ring
        ImageDraw.Draw(out).ellipse((cx - r * 1.7, cy - r * .45, cx + r * 1.7, cy + r * .45),
                                    outline=hexc(t["icon_light"], 200), width=int(PX * .9))
    out.alpha_composite(body(m, t, seed, 1.35))
    # Kugel-Licht
    hl = blank("L")
    ImageDraw.Draw(hl).ellipse((cx - r * .7, cy - r * .75, cx + r * .1, cy - r * .05), fill=110)
    hl = ImageChops.multiply(hl.filter(ImageFilter.GaussianBlur(r * .25)), m)
    w = Image.new("RGBA", (S, S), (255, 230, 255, 255))
    w.putalpha(hl)
    out.alpha_composite(w)
    if ring_on:  # vorderer Ring (untere Haelfte)
        fr = blank()
        ImageDraw.Draw(fr).ellipse((cx - r * 1.7, cy - r * .45, cx + r * 1.7, cy + r * .45),
                                   outline=hexc(t["icon_light"]), width=int(PX * 1.1))
        cut = blank("L")
        ImageDraw.Draw(cut).rectangle((0, cy, S, S), fill=255)
        fr.putalpha(ImageChops.multiply(fr.split()[3], cut))
        g = fr.filter(ImageFilter.GaussianBlur(PX * 1.5))
        out.alpha_composite(g)
        out.alpha_composite(fr)
    return out


def sparkle(img, t, pts):
    sp = blank()
    d = ImageDraw.Draw(sp)
    for (x, y, r) in pts:
        x, y, r = x * PX, y * PX, r * PX
        d.polygon([(x, y - r), (x + r * .22, y - r * .22), (x + r, y), (x + r * .22, y + r * .22),
                   (x, y + r), (x - r * .22, y + r * .22), (x - r, y), (x - r * .22, y - r * .22)],
                  fill=(255, 255, 255, 255))
    g = Image.new("RGBA", (S, S), hexc(t["border_glow"]))
    g.putalpha(sp.split()[3].filter(ImageFilter.GaussianBlur(PX * 1.2)))
    img.alpha_composite(g)
    img.alpha_composite(sp)


# --------------------------------------------------------------------------- #
# Designs (Koordinaten in Endpixeln 0..64)
# --------------------------------------------------------------------------- #
def t_shield_wings(t):
    img = blank()
    img.alpha_composite(wings(t, (26 * PX, 22 * PX), (38 * PX, 22 * PX), 1.0, 11))
    m = poly_mask(sc(heater_shield(32, 10, 30, 46)))
    img.alpha_composite(body(m, t, 3, 0.95))
    inner = poly_mask(sc(heater_shield(32, 14.5, 22, 36)))
    img.alpha_composite(rim(inner, t, width=PX * .6, glow_r=PX * 1.2, col=t["icon"]))
    sparkle(img, t, [(13, 9, 2.2), (54, 46, 1.8)])
    return img


def t_wings_crystal(t):
    img = blank()
    img.alpha_composite(wings(t, (28 * PX, 26 * PX), (36 * PX, 26 * PX), 1.12, 21))
    img.alpha_composite(crystal(t, 32 * PX, 34 * PX, 12 * PX, 34 * PX, 0, 5))
    sparkle(img, t, [(32, 13, 3), (12, 50, 1.6), (52, 52, 1.6)])
    return img


def t_cape_planet(t):
    img = blank()
    pts = sc([(14, 6), (48, 4), (52, 58), (12, 60)])
    m = poly_mask(pts)
    img.alpha_composite(body(m, t, 7, 0.75))
    clip = blank()
    clip.alpha_composite(planet(t, 33 * PX, 30 * PX, 11 * PX, 8))
    ImageDraw.Draw(clip).ellipse(sc([(39, 8), (47, 16)])[0] + sc([(39, 8), (47, 16)])[1], fill=hexc(t["icon_light"], 230))
    clip.putalpha(ImageChops.multiply(clip.split()[3], m))
    img.alpha_composite(clip)
    sparkle(img, t, [(20, 48, 1.8), (44, 50, 1.2), (19, 14, 1.2)])
    return img


def t_crystal_cluster(t):
    img = blank()
    for (cx, cy, w, h, tilt, sd) in ((20, 38, 10, 26, -28, 1), (44, 38, 10, 26, 28, 2),
                                     (32, 32, 14, 44, 0, 3)):
        img.alpha_composite(crystal(t, cx * PX, cy * PX, w * PX, h * PX, tilt, sd))
    for (cx, cy, w, h, tilt, sd) in ((10, 14, 5, 9, 20, 4), (54, 12, 5, 9, -25, 5), (52, 58, 4, 7, 40, 6)):
        img.alpha_composite(crystal(t, cx * PX, cy * PX, w * PX, h * PX, tilt, sd))
    sparkle(img, t, [(20, 8, 1.8), (40, 60, 1.5)])
    return img


def t_planet_wings(t):
    img = blank()
    img.alpha_composite(wings(t, (24 * PX, 30 * PX), (40 * PX, 30 * PX), 1.05, 31))
    img.alpha_composite(planet(t, 32 * PX, 34 * PX, 13 * PX, 9))
    sparkle(img, t, [(32, 12, 2.4), (10, 54, 1.4), (55, 55, 1.4)])
    return img


def t_heart_wings(t):
    img = blank()
    img.alpha_composite(wings(t, (25 * PX, 26 * PX), (39 * PX, 26 * PX), 1.05, 41))
    m = heart_mask(32 * PX, 33 * PX, 34 * PX)
    img.alpha_composite(body(m, t, 12, 1.1))
    sparkle(img, t, [(24, 24, 1.8), (50, 54, 1.4)])
    return img


DESIGNS = {
    "1 Schild mit Fluegeln": t_shield_wings,
    "2 Fluegel + Kristall": t_wings_crystal,
    "3 Galaxie-Cape mit Planet": t_cape_planet,
    "4 Kristall-Cluster": t_crystal_cluster,
    "5 Planet mit Fluegeln": t_planet_wings,
    "6 Herz mit Fluegeln": t_heart_wings,
}


def finalize(img):
    """512 -> 64, kleine Restalpha entfernen, Farben leicht reduzieren (Pixel-Look)."""
    small = img.resize((N, N), Image.LANCZOS)
    a = small.split()[3].point(lambda v: 0 if v < 40 else v)
    rgb = small.convert("RGB").quantize(96, method=Image.Quantize.MEDIANCUT).convert("RGB")
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def preview_bg(w, h, t):
    bg = neb({**t, "icon_light": t["icon"]}, 77, 0.55, stars=False)
    bg = bg.resize((w, h))
    dark = Image.new("RGBA", (w, h), (8, 4, 18, 120))
    bg.alpha_composite(dark)
    return bg


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    scale, pad = 5, 24
    themes = sys.argv[1:] or ["lila", "schwarz-weiss"]
    tiles = []
    for th in themes:
        t = THEMES[th]
        for i, (name, fn) in enumerate(DESIGNS.items()):
            tex = finalize(fn(t))
            tex.save(OUT / f"totem2_{i + 1}_{th}.png")
            tile = preview_bg(N * scale + pad, N * scale + pad + 18, t)
            tile.alpha_composite(tex.resize((N * scale, N * scale), Image.NEAREST), (pad // 2, 18 + pad // 2))
            ImageDraw.Draw(tile).text((6, 4), f"{name} ({th})", fill=(255, 255, 255, 255))
            tiles.append(tile)
    cols = 3
    w, h = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (w + 6) + 6, rows * (h + 6) + 6), hexc("#0C0A10"))
    for i, tl in enumerate(tiles):
        sheet.alpha_composite(tl, (6 + (i % cols) * (w + 6), 6 + (i // cols) * (h + 6)))
    sheet.convert("RGB").save(OUT / "totem_entwurf_v2.png")
    print("ok")
