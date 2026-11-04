"""Totem-Entwuerfe v3 (64x64): naeher am Galaxy-Cosmetic-Bild.
Neue Fluegel: Vogelfluegel mit Vorderkante, haengenden Federreihen, leuchtenden Spitzen."""
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, str(Path(__file__).parent))
from hud_galaxy import THEMES, hexc
from totems_hd import (S, N, PX, blank, neb, body, rim, outline, poly_mask, sc, planet, crystal,
                       sparkle, heater_shield, heart_mask, finalize, preview_bg, fill)

OUT = Path(__file__).parent / "hud"


def feather_poly(root, theta, length, width):
    """Feder: an der Wurzel schmal, breiter Koerper, runde Spitze."""
    a = math.radians(theta)
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    L, R_ = [], []
    for i in range(25):
        s = i / 24
        w = width * min(1, s * 3.5) * math.sqrt(max(0, 1 - max(0, (s - .55) / .45) ** 2))
        cx, cy = root[0] + dx * s * length, root[1] + dy * s * length
        L.append((cx + px * w / 2, cy + py * w / 2))
        R_.append((cx - px * w / 2, cy - py * w / 2))
    return L + R_[::-1]


def feather_img(t, pts, root, theta, length, seed, br):
    m = poly_mask(pts)
    out = blank()
    out.alpha_composite(outline(m, t, PX * .7))
    out.alpha_composite(fill(m, neb(t, seed, br, stars=False)))
    # Verlauf: Wurzel dunkel -> Spitze leuchtend
    g = blank("L")
    gd = ImageDraw.Draw(g)
    a = math.radians(theta)
    for k in range(20):
        s = k / 19
        r = length * (1 - s) + PX
        cx = root[0] + math.cos(a) * length
        cy = root[1] + math.sin(a) * length
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=int(255 * s ** 1.6))
    g = ImageChops.multiply(g.filter(ImageFilter.GaussianBlur(PX * 2)), m)
    tip = Image.new("RGBA", (S, S), hexc(t["icon"]))
    tip.putalpha(g.point(lambda v: v * 200 // 255))
    out.alpha_composite(tip)
    root_dark = Image.new("RGBA", (S, S), hexc(t["nebula"][0]))
    rg = ImageChops.multiply(ImageChops.invert(g), m).point(lambda v: v * 110 // 255)
    root_dark.putalpha(rg)
    out.alpha_composite(root_dark)
    # Kiel
    ImageDraw.Draw(out).line([root, (root[0] + math.cos(a) * length * .8, root[1] + math.sin(a) * length * .8)],
                             fill=hexc(t["icon_light"], 120), width=max(1, int(PX * .4)))
    return out


def bird_wing(t, root, span, side, seed, lift=.55):
    """root/span in Mal-Pixeln. side = +1 rechts, -1 links."""
    rng = np.random.default_rng(seed)

    def edge(s):  # Vorderkante: von der Schulter nach aussen-oben
        return (root[0] + side * span * s, root[1] - span * lift * math.sin(s * math.pi * .62))

    def ang(deg):  # Winkel fuer rechte Seite -> gespiegelt fuer links
        return deg if side > 0 else 180 - deg

    out = blank()
    rows = [
        # (Anzahl, s-Bereich, Winkel(s), Laenge(s), Breite, Helligkeit)
        (9, (.25, 1.0), lambda s: 105 - 70 * s, lambda s: span * (.50 + .62 * s), span * .15, 1.3),
        (8, (.05, .85), lambda s: 100 - 55 * s, lambda s: span * (.36 + .30 * s), span * .15, 1.1),
        (8, (.00, .92), lambda s: 90 - 40 * s, lambda s: span * .22, span * .17, .95),
    ]
    for n, (s0, s1), th, ln, w, br in rows:
        for i in range(n):
            s = s0 + (s1 - s0) * i / (n - 1)
            r = edge(s)
            theta = ang(th(s))
            L = ln(s)
            out.alpha_composite(feather_img(t, feather_poly(r, theta, L, w), r, theta, L,
                                            int(rng.integers(1e6)), br))
    # Vorderkante (Fluegel-Knochen)
    pts = [edge(i / 20) for i in range(21)]
    arm = blank("L")
    ImageDraw.Draw(arm).line(pts, fill=255, width=int(span * .09), joint="curve")
    out.alpha_composite(outline(arm, t, PX * .7))
    out.alpha_composite(fill(arm, neb(t, seed + 7, 1.3, stars=False)))
    out.alpha_composite(rim(arm, t, width=PX * .6, glow_r=PX * 1.2))
    # Sternfunken auf dem Fluegel
    sp = blank()
    d = ImageDraw.Draw(sp)
    for _ in range(14):
        s = rng.uniform(.1, 1)
        e = edge(s)
        dist = rng.uniform(.1, .7) * span
        a = math.radians(ang(rng.uniform(40, 100)))
        x, y = e[0] + math.cos(a) * dist, e[1] + math.sin(a) * dist
        rr = PX * rng.uniform(.45, .9)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(255, 235, 255, 255))
    out.alpha_composite(sp.filter(ImageFilter.GaussianBlur(PX * 1.2)))
    out.alpha_composite(sp)
    return out


def wing_pair(t, cx, cy, gap, span, seed, lift=.55):
    out = blank()
    out.alpha_composite(bird_wing(t, (cx - gap, cy), span, -1, seed, lift))
    out.alpha_composite(bird_wing(t, (cx + gap, cy), span, 1, seed + 1, lift))
    return out


def floating_crystals(img, t, spots):
    for (x, y, s, tilt) in spots:
        c = crystal({**t, "icon": "#FFFFFF", "icon_light": "#FFFFFF", "icon_dark": t["icon_light"]},
                    x * PX, y * PX, s * PX * .6, s * PX, tilt, int(x * 7 + y))
        img.alpha_composite(c)


# --------------------------------------------------------------------------- #
# Designs (Koordinaten in Endpixeln 0..64)
# --------------------------------------------------------------------------- #
def d_wings(t):
    img = blank()
    img.alpha_composite(wing_pair(t, 32 * PX, 32 * PX, 2 * PX, 27 * PX, 101, 1.0))
    m = blank("L")
    ImageDraw.Draw(m).ellipse(sc([(28, 26), (36, 34)])[0] + sc([(28, 26), (36, 34)])[1], fill=255)
    img.alpha_composite(body(m, t, 5, 1.6))
    sparkle(img, t, [(32, 30, 3.2), (10, 56, 1.4), (55, 58, 1.4)])
    floating_crystals(img, t, [(6, 8, 5, 20), (58, 10, 4, -25)])
    return img


def d_shield(t):
    img = blank()
    img.alpha_composite(wing_pair(t, 32 * PX, 24 * PX, 9 * PX, 21 * PX, 201, 1.0))
    m = poly_mask(sc(heater_shield(32, 9, 30, 48)))
    img.alpha_composite(body(m, t, 3, 1.05))
    inner = poly_mask(sc(heater_shield(32, 13, 23, 39)))
    img.alpha_composite(rim(inner, t, width=PX * .55, glow_r=PX * 1.4, col=t["icon"]))
    sparkle(img, t, [(26, 20, 1.6), (54, 50, 1.6)])
    floating_crystals(img, t, [(8, 52, 4, 25), (57, 40, 3.5, -20)])
    return img


def d_cape(t):
    img = blank()
    pts = sc([(14, 5), (49, 3), (53, 58), (11, 61)])
    m = poly_mask(pts)
    img.alpha_composite(body(m, t, 7, 0.9))
    inner = poly_mask(sc([(17, 8), (46, 6.5), (49.5, 55), (14.5, 57.5)]))
    img.alpha_composite(rim(inner, t, width=PX * .45, glow_r=PX * 1, col=t["icon"]))
    pl = blank()
    pl.alpha_composite(planet(t, 31 * PX, 34 * PX, 12 * PX, 8))
    # Sichel oben rechts
    cr = blank("L")
    ImageDraw.Draw(cr).ellipse(sc([(38, 9), (48, 19)])[0] + sc([(38, 9), (48, 19)])[1], fill=255)
    ImageDraw.Draw(cr).ellipse(sc([(40.5, 8), (50.5, 18)])[0] + sc([(40.5, 8), (50.5, 18)])[1], fill=0)
    moon = Image.new("RGBA", (S, S), hexc(t["icon_light"]))
    moon.putalpha(cr)
    g = Image.new("RGBA", (S, S), hexc(t["border_glow"]))
    g.putalpha(cr.filter(ImageFilter.GaussianBlur(PX * 1.5)))
    pl.alpha_composite(g)
    pl.alpha_composite(moon)
    pl.putalpha(ImageChops.multiply(pl.split()[3], m))
    img.alpha_composite(pl)
    sparkle(img, t, [(20, 50, 1.6), (45, 52, 1.2), (21, 15, 1.2)])
    return img


def d_figure(t):
    img = blank()
    img.alpha_composite(wing_pair(t, 32 * PX, 28 * PX, 7 * PX, 23 * PX, 401, 1.0))
    parts = [
        poly_mask(sc([(23, 5), (41, 5), (42, 7), (42, 21), (22, 21), (22, 7)])),   # Kopf
        poly_mask(sc([(25, 22), (39, 22), (40, 47), (24, 47)])),                     # Koerper
        poly_mask(sc([(19, 49), (45, 49), (42, 57), (22, 57)])),                     # Sockel
    ]
    for i, m in enumerate(parts):
        img.alpha_composite(body(m, t, 20 + i, 1.15 if i == 0 else 1.0))
    d = ImageDraw.Draw(img)
    for x0 in (26, 34):                                                               # Augen
        e = sc([(x0, 11), (x0 + 4, 14)])
        d.rectangle(e[0] + e[1], fill=hexc("#FFFFFF"))
    gl = blank("L")
    for x0 in (26, 34):
        e = sc([(x0, 11), (x0 + 4, 14)])
        ImageDraw.Draw(gl).rectangle(e[0] + e[1], fill=255)
    g = Image.new("RGBA", (S, S), hexc(t["icon_light"]))
    g.putalpha(gl.filter(ImageFilter.GaussianBlur(PX * 1.5)))
    img.alpha_composite(g)
    m = sc([(28, 17), (36, 18.5)])
    d.rectangle(m[0] + m[1], fill=hexc(t["icon_line"]))
    # Edelstein auf der Brust
    img.alpha_composite(crystal(t, 32 * PX, 33 * PX, 6 * PX, 10 * PX, 0, 9))
    sparkle(img, t, [(32, 33, 2), (8, 8, 1.4)])
    return img


def d_heart(t):
    img = blank()
    img.alpha_composite(wing_pair(t, 32 * PX, 28 * PX, 8 * PX, 22 * PX, 501, 1.0))
    m = heart_mask(32 * PX, 34 * PX, 36 * PX)
    img.alpha_composite(body(m, t, 12, 1.2))
    inner = heart_mask(32 * PX, 34 * PX, 28 * PX)
    img.alpha_composite(rim(inner, t, width=PX * .5, glow_r=PX * 1.2, col=t["icon"]))
    sparkle(img, t, [(24, 26, 1.8), (52, 56, 1.4)])
    floating_crystals(img, t, [(9, 54, 4, 20)])
    return img


def d_crystal(t):
    img = blank()
    img.alpha_composite(wing_pair(t, 32 * PX, 30 * PX, 4 * PX, 25 * PX, 601, 1.0))
    img.alpha_composite(crystal(t, 32 * PX, 33 * PX, 14 * PX, 44 * PX, 0, 5))
    sparkle(img, t, [(32, 11, 3), (12, 55, 1.6), (53, 55, 1.6)])
    floating_crystals(img, t, [(8, 10, 4, 25), (56, 8, 4, -20)])
    return img


DESIGNS = {
    "1 Fluegel-Paar": d_wings,
    "2 Schild mit Fluegeln": d_shield,
    "3 Galaxie-Cape": d_cape,
    "4 Totem-Figur": d_figure,
    "5 Herz mit Fluegeln": d_heart,
    "6 Kristall mit Fluegeln": d_crystal,
}

if __name__ == "__main__":
    scale, pad = 5, 24
    themes = sys.argv[1:] or ["lila"]
    tiles = []
    for th in themes:
        t = THEMES[th]
        for i, (name, fn) in enumerate(DESIGNS.items()):
            tex = finalize(fn(t))
            tex.save(OUT / f"totem3_{i + 1}_{th}.png")
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
    sheet.convert("RGB").save(OUT / "totem_entwurf_v3.png")
    print("ok")
