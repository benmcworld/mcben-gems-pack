"""Cape- und Fluegel(Elytra)-Entwuerfe im Galaxy-Stil.

Ausgabe-Format = offizielles Cape-Format 64x32 (hier 4x = 256x128):
  Cape-Box   UV (0,0)  10x16x1  -> Aussenseite (1,1)-(11,17), Innenseite (12,1)-(22,17)
  Elytra-Box UV (22,0) 10x20x2  -> Vorderseite (24,2)-(34,22), Rueckseite (36,2)-(46,22)
Dieselbe Datei funktioniert als Elytra-Textur im Resource Pack und als Cape fuer Cape-Mods.
"""
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, str(Path(__file__).parent))
from hud_galaxy import THEMES, hexc
from galaxy import fbm

OUT = Path(__file__).parent / "hud"
TX = 16          # Mal-Pixel pro Textur-Pixel
SCALE = 4        # Ausgabe: 4x (256x128)


def box(x0, y0, x1, y1):
    return (x0 * TX, y0 * TX, x1 * TX, y1 * TX)


def nebula_img(w, h, t, seed, bright=1.0, stars=22):
    rng = np.random.default_rng(seed)
    v = fbm(w, h, rng, base=max(16, max(w, h) // 3), octaves=7)
    u = fbm(w, h, rng, base=max(16, max(w, h) // 6), octaves=5)
    v = np.clip((v * .65 + u * .35 - .28) * 2.0, 0, 1) ** 1.3 * bright
    cols = [hexc(c) for c in (t["nebula"][0], t["nebula"][1], t["nebula"][2], t["icon_dark"], t["icon"], t["icon_light"])]
    stops = np.linspace(0, 1, len(cols))
    rgb = np.stack([np.interp(np.clip(v, 0, 1), stops, [c[i] for c in cols]) for i in range(3)], -1)
    img = Image.fromarray(rgb.astype(np.uint8)).convert("RGBA")
    st = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(st)
    for _ in range(stars):
        x, y = rng.random() * w, rng.random() * h
        r = rng.choice([TX * .14, TX * .22, TX * .38], p=[.6, .3, .1])
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 245, 255, 255))
    img.alpha_composite(st.filter(ImageFilter.GaussianBlur(TX * .3)))
    img.alpha_composite(st)
    return img


def glow_stroke(img, draw_fn, col, width, blur):
    m = Image.new("L", img.size)
    draw_fn(ImageDraw.Draw(m), width)
    g = Image.new("RGBA", img.size, col)
    g.putalpha(m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: min(255, v * 2)))
    img.alpha_composite(g)
    w = Image.new("RGBA", img.size, (255, 240, 255, 255))
    w.putalpha(m)
    img.alpha_composite(w)


def star4(d, x, y, r, col=(255, 255, 255, 255)):
    d.polygon([(x, y - r), (x + r * .2, y - r * .2), (x + r, y), (x + r * .2, y + r * .2),
               (x, y + r), (x - r * .2, y + r * .2), (x - r, y), (x - r * .2, y - r * .2)], fill=col)


# --------------------------------------------------------------------------- #
# Cape-Motive (zeichnen auf eine Flaeche w x h)
# --------------------------------------------------------------------------- #
def m_planet(w, h, t, seed):
    img = nebula_img(w, h, t, seed, .9)
    cx, cy, r = w * .5, h * .5, w * .3
    p = Image.new("L", (w, h))
    ImageDraw.Draw(p).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    pl = nebula_img(w, h, t, seed + 1, 2.3, stars=0)
    hl = Image.new("L", (w, h))
    ImageDraw.Draw(hl).ellipse((cx - r * .8, cy - r * .85, cx + r * .1, cy - r * .05), fill=150)
    pl.alpha_composite(Image.new("RGBA", (w, h), (255, 230, 255, 0)))
    glow = Image.new("RGBA", (w, h), hexc(t["border_glow"]))
    glow.putalpha(p.filter(ImageFilter.GaussianBlur(r * .25)))
    img.alpha_composite(glow)
    img.paste(pl, (0, 0), p)
    lt = Image.new("RGBA", (w, h), (255, 230, 255, 255))
    lt.putalpha(ImageChops.multiply(hl.filter(ImageFilter.GaussianBlur(r * .25)), p))
    img.alpha_composite(lt)
    glow_stroke(img, lambda d, wd: d.ellipse((cx - r * 1.7, cy - r * .4, cx + r * 1.7, cy + r * .4), outline=255, width=wd),
                hexc(t["icon"]), int(TX * .6), TX)
    # Mondsichel
    m = Image.new("L", (w, h))
    md = ImageDraw.Draw(m)
    mr = w * .1
    md.ellipse((w * .75 - mr, h * .14 - mr, w * .75 + mr, h * .14 + mr), fill=255)
    md.ellipse((w * .79 - mr, h * .12 - mr, w * .79 + mr, h * .12 + mr), fill=0)
    mo = Image.new("RGBA", (w, h), hexc(t["icon_light"]))
    mo.putalpha(m)
    img.alpha_composite(mo)
    return img


def m_nebel(w, h, t, seed):
    img = nebula_img(w, h, t, seed, 1.25, stars=45)
    d = ImageDraw.Draw(img)
    for (x, y, r) in ((.3, .25, .09), (.7, .6, .07), (.45, .8, .05)):
        star4(d, w * x, h * y, w * r)
    return img


def m_kristall(w, h, t, seed):
    img = nebula_img(w, h, t, seed, .8)
    for (cx, cy, cw, ch, tilt) in ((.5, .48, .22, .6, 0), (.28, .58, .12, .34, -25), (.72, .58, .12, .34, 25)):
        cx, cy, cw, ch = w * cx, h * cy, w * cw, h * ch
        pts = [(0, -ch / 2), (cw / 2, -ch / 2 + cw * .5), (cw / 2, ch / 2 - cw * .5), (0, ch / 2),
               (-cw / 2, ch / 2 - cw * .5), (-cw / 2, -ch / 2 + cw * .5)]
        a = math.radians(tilt)
        pts = [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in pts]
        m = Image.new("L", (w, h))
        ImageDraw.Draw(m).polygon(pts, fill=255)
        g = Image.new("RGBA", (w, h), hexc(t["border_glow"]))
        g.putalpha(m.filter(ImageFilter.GaussianBlur(TX * 1.5)))
        img.alpha_composite(g)
        img.paste(nebula_img(w, h, {**t, "nebula": [t["icon_dark"], t["icon"], t["icon_light"], "#FFFFFF"]}, seed + 3, 1.9, 0), (0, 0), m)
        half = Image.new("L", (w, h))
        ImageDraw.Draw(half).polygon(pts[0:4], fill=90)
        dk = Image.new("RGBA", (w, h), hexc(t["nebula"][0]))
        dk.putalpha(ImageChops.multiply(half, m))
        img.alpha_composite(dk)
        glow_stroke(img, lambda d, wd, p=pts: d.line(p + [p[0]], fill=255, width=wd), hexc(t["icon"]), int(TX * .4), TX * .6)
    return img


def m_fluegel(w, h, t, seed):
    img = nebula_img(w, h, t, seed, .85)
    cx, cy = w * .5, h * .42
    for side in (-1, 1):
        for i in range(6):
            ang = math.radians(-50 + i * 22)
            L = w * (.36 - i * .03)
            pts = []
            for k in range(13):
                s = k / 12
                wd = w * .05 * math.sin(math.pi * min(1, s * 1.1)) ** .6
                x = cx + side * (w * .05 + math.cos(ang) * s * L)
                y = cy + math.sin(ang) * s * L
                pts.append((x - wd * math.sin(ang) * side, y + wd * math.cos(ang)))
            for k in range(12, -1, -1):
                s = k / 12
                wd = w * .05 * math.sin(math.pi * min(1, s * 1.1)) ** .6
                x = cx + side * (w * .05 + math.cos(ang) * s * L)
                y = cy + math.sin(ang) * s * L
                pts.append((x + wd * math.sin(ang) * side, y - wd * math.cos(ang)))
            glow_stroke(img, lambda d, wd, p=pts: d.polygon(p, outline=255, width=wd), hexc(t["icon"]), int(TX * .35), TX * .7)
    m = Image.new("L", (w, h))
    ImageDraw.Draw(m).ellipse((cx - w * .09, cy - w * .09, cx + w * .09, cy + w * .09), fill=255)
    g = Image.new("RGBA", (w, h), hexc(t["border_glow"]))
    g.putalpha(m.filter(ImageFilter.GaussianBlur(TX * 2)))
    img.alpha_composite(g)
    c = Image.new("RGBA", (w, h), hexc(t["icon_light"]))
    c.putalpha(m)
    img.alpha_composite(c)
    star4(ImageDraw.Draw(img), cx, cy, w * .07)
    return img


def m_neon(w, h, t, seed):
    img = nebula_img(w, h, {**t, "icon": t["nebula"][2], "icon_light": t["icon_dark"]}, seed, .7, 40)
    for k in range(-h, w + h, int(TX * 3)):
        glow_stroke(img, lambda d, wd, k=k: d.line((k, 0, k - h * .6, h), fill=255, width=wd),
                    hexc(t["icon"], 160), max(1, int(TX * .18)), TX * .5)
    return img


def m_verlauf(w, h, t, seed):
    y = np.linspace(0, 1, h)[:, None, None]
    a, b = np.array(hexc(t["nebula"][0])[:3], float), np.array(hexc(t["icon"])[:3], float)
    col = a * (1 - y) + b * y
    img = Image.fromarray(np.broadcast_to(col, (h, w, 3)).astype(np.uint8)).convert("RGBA")
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(img)
    for _ in range(30):
        x, yy = rng.random() * w, rng.random() * h * .75
        r = TX * rng.choice([.14, .22, .34])
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=(255, 240, 255, 255))
    for (x, yy, r) in ((.25, .2, .07), (.7, .35, .05)):
        star4(d, w * x, h * yy, w * r)
    return img


CAPES = {
    "1 Planet": m_planet,
    "2 Sternennebel": m_nebel,
    "3 Kristalle": m_kristall,
    "4 Fluegel-Emblem": m_fluegel,
    "5 Neon-Streifen": m_neon,
    "6 Verlauf": m_verlauf,
}


# --------------------------------------------------------------------------- #
# Fluegel (Elytra) - Federmuster auf 10x20 Flaeche
# --------------------------------------------------------------------------- #
def wing_mask(w, h):
    """Fluegel-Silhouette: oben voll, Aussenkante (links) laeuft nach unten schraeg zu, Federspitzen unten."""
    m = Image.new("L", (w, h))
    d = ImageDraw.Draw(m)
    pts = [(0, 0), (w, 0), (w, h * .97)]
    n = 5
    for i in range(1, n + 1):
        x = w - w * i / n
        y = h * (.97 - .38 * (i / n) ** 1.3)
        pts += [(x + w / n * .5, y + h * .035), (x, y)]
    d.polygon(pts, fill=255)
    return m


def feather_rows(w, h, t, seed, style):
    base_t = t
    neb = nebula_img(w, h, base_t, seed, 1.0 if style != "neon" else .5, stars=10)
    img = neb.copy()
    rows, cols = 6, 5
    line = hexc(t["icon_line"]) if style != "engel" else hexc("#6A4A9A")
    for r in range(rows - 1, -1, -1):              # untere Reihen zuerst -> obere ueberlappen
        y0 = h * (.02 + r * .155)
        fh = h * (.20 + .035 * r)
        fw = w / cols * 1.25
        for c in range(cols + 1):
            x = w * (c + .5 * (r % 2)) / cols
            m = Image.new("L", (w, h))
            md = ImageDraw.Draw(m)
            if style == "kristall":
                md.polygon([(x - fw / 2, y0), (x + fw / 2, y0), (x + fw / 2, y0 + fh * .6), (x, y0 + fh),
                            (x - fw / 2, y0 + fh * .6)], fill=255)
            else:
                md.rectangle((x - fw / 2, y0, x + fw / 2, y0 + fh * .5), fill=255)
                md.ellipse((x - fw / 2, y0 + fh * .1, x + fw / 2, y0 + fh), fill=255)
            k = r / (rows - 1)
            if style == "neon":
                fill_ = Image.new("RGBA", (w, h), hexc(t["nebula"][1]))
            elif style == "engel":
                fill_ = Image.new("RGBA", (w, h), hexc("#F2EAFF" if k < .5 else "#D9C6FF"))
            else:
                fill_ = neb.copy()
                tint = Image.new("RGBA", (w, h), hexc(t["icon"], int(40 + 120 * k)))
                fill_.alpha_composite(tint)
            img.paste(fill_, (0, 0), m)
            edge = ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(int(TX * .5) | 1)))
            if style == "neon":
                g = Image.new("RGBA", (w, h), hexc(t["icon"]))
                g.putalpha(edge.filter(ImageFilter.GaussianBlur(TX * .5)).point(lambda v: min(255, v * 2)))
                img.alpha_composite(g)
                e = Image.new("RGBA", (w, h), hexc(t["icon_light"]))
            else:
                e = Image.new("RGBA", (w, h), line)
            e.putalpha(edge)
            img.alpha_composite(e)
            # Glanz oben links + Kiel
            hd = ImageDraw.Draw(img)
            hl = hexc("#FFFFFF", 150) if style != "neon" else hexc(t["icon_light"], 120)
            hd.line((x, y0 + fh * .15, x, y0 + fh * .8), fill=hexc(t["icon_light"] if style != "engel" else "#B9A0E6", 140),
                    width=max(1, int(TX * .2)))
            hd.arc((x - fw / 2 + TX * .6, y0 + fh * .15, x + fw / 2 - TX * .6, y0 + fh - TX * .6), 140, 200, fill=hl,
                   width=max(1, int(TX * .2)))
    # Sterne obendrauf
    rng = np.random.default_rng(seed + 5)
    d = ImageDraw.Draw(img)
    for _ in range(8):
        star4(d, rng.random() * w, rng.random() * h * .9, TX * rng.uniform(.3, .55))
    return img


WINGS = {
    "1 Galaxie-Federn": "galaxie",
    "2 Kristall-Fluegel": "kristall",
    "3 Neon-Federn": "neon",
    "4 Engel (hell)": "engel",
}


# --------------------------------------------------------------------------- #
# Zusammenbauen im Cape-Format
# --------------------------------------------------------------------------- #
def assemble(t, cape_fn, wing_style, seed=1):
    W, H = 64 * TX, 32 * TX
    tex = Image.new("RGBA", (W, H))
    # Cape
    fw, fh = 10 * TX, 16 * TX
    front = cape_fn(fw, fh, t, seed)
    edge = Image.new("L", (fw, fh))
    ImageDraw.Draw(edge).rectangle((0, 0, fw - 1, fh - 1), outline=255, width=int(TX * .6))
    rim = Image.new("RGBA", (fw, fh), hexc(t["icon_light"]))
    rim.putalpha(edge)
    front.alpha_composite(rim)
    tex.paste(front, (1 * TX, 1 * TX))
    back = nebula_img(fw, fh, t, seed + 50, .6, 20)
    tex.paste(back, (12 * TX, 1 * TX))
    side = Image.new("RGBA", (TX, fh), hexc(t["icon_dark"]))
    tex.paste(side, (0, TX))
    tex.paste(side, (11 * TX, TX))
    tex.paste(Image.new("RGBA", (10 * TX, TX), hexc(t["icon_dark"])), (TX, 0))
    tex.paste(Image.new("RGBA", (10 * TX, TX), hexc(t["icon_dark"])), (11 * TX, 0))
    # Elytra
    ew, eh = 10 * TX, 20 * TX
    style_t = t if wing_style != "engel" else {**t, "nebula": ["#3A2A55", "#7A5AA8", "#B99AE0", "#E8DAFF", "#FFFFFF", "#FFFFFF"]}
    wing = feather_rows(ew, eh, style_t, seed + 9, wing_style)
    wm = wing_mask(ew, eh)
    out = Image.new("RGBA", (ew, eh))
    out.paste(wing, (0, 0), wm)
    rimm = ImageChops.subtract(wm, wm.filter(ImageFilter.MinFilter(int(TX * .5) | 1)))
    rr = Image.new("RGBA", (ew, eh), hexc(t["icon_light"]))
    rr.putalpha(rimm)
    out.alpha_composite(rr)
    tex.paste(out, (24 * TX, 2 * TX))
    dark = out.copy()
    dark.alpha_composite(Image.new("RGBA", (ew, eh), (0, 0, 0, 0)))
    shade = Image.new("RGBA", (ew, eh), (0, 0, 0, 90))
    shade.putalpha(ImageChops.multiply(wm, Image.new("L", (ew, eh), 90)))
    dark.alpha_composite(shade)
    tex.paste(dark.transpose(Image.FLIP_LEFT_RIGHT), (36 * TX, 2 * TX))
    tex.paste(Image.new("RGBA", (2 * TX, eh), hexc(t["icon_dark"])), (22 * TX, 2 * TX))
    tex.paste(Image.new("RGBA", (2 * TX, eh), hexc(t["icon_dark"])), (34 * TX, 2 * TX))
    tex.paste(Image.new("RGBA", (10 * TX, 2 * TX), hexc(t["icon_dark"])), (24 * TX, 0))
    tex.paste(Image.new("RGBA", (10 * TX, 2 * TX), hexc(t["icon_dark"])), (34 * TX, 0))
    final = tex.resize((64 * SCALE, 32 * SCALE), Image.LANCZOS)
    a = final.split()[3].point(lambda v: 0 if v < 60 else 255)   # harte Kanten (Minecraft-Cutout)
    final.putalpha(a)
    return final


# --------------------------------------------------------------------------- #
# Vorschau
# --------------------------------------------------------------------------- #
def label(img, x, y, txt):
    d = ImageDraw.Draw(img)
    d.text((x + 1, y + 1), txt, fill=(0, 0, 0, 255))
    d.text((x, y), txt, fill=(255, 255, 255, 255))


def cape_view(tex, big=3):
    s = SCALE
    face = tex.crop((1 * s, 1 * s, 11 * s, 17 * s))
    return face.resize((face.width * big, face.height * big), Image.NEAREST)


def wings_view(tex, big=3):
    s = SCALE
    f = tex.crop((24 * s, 2 * s, 34 * s, 22 * s))
    f = f.resize((f.width * big, f.height * big), Image.NEAREST)
    left = f.rotate(-18, expand=True, resample=Image.NEAREST)
    right = f.transpose(Image.FLIP_LEFT_RIGHT).rotate(18, expand=True, resample=Image.NEAREST)
    out = Image.new("RGBA", (left.width + right.width - 20, max(left.height, right.height)))
    out.alpha_composite(left, (0, 0))
    out.alpha_composite(right, (left.width - 20, 0))
    return out


def bg(w, h, t):
    b = nebula_img(w // 2, h // 2, {**t, "icon_light": t["nebula"][2], "icon": t["nebula"][2]}, 77, .5, 0).resize((w, h))
    b.alpha_composite(Image.new("RGBA", (w, h), (6, 4, 14, 140)))
    return b


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    theme = sys.argv[1] if len(sys.argv) > 1 else "lila"
    t = THEMES[theme]
    # Capes
    tiles = []
    for i, (name, fn) in enumerate(CAPES.items()):
        tex = assemble(t, fn, "galaxie", seed=10 + i)
        tex.save(OUT / f"cape_{i + 1}_{theme}.png")
        v = cape_view(tex)
        tile = bg(v.width + 40, v.height + 50, t)
        tile.alpha_composite(v, (20, 34))
        label(tile, 8, 8, name)
        tiles.append(tile)
    w, h = tiles[0].size
    sheet = Image.new("RGBA", (len(tiles) * (w + 6) + 6, h + 12), hexc("#0C0A10"))
    for i, tl in enumerate(tiles):
        sheet.alpha_composite(tl, (6 + i * (w + 6), 6))
    sheet.convert("RGB").save(OUT / "capes_entwurf.png")
    # Fluegel
    tiles = []
    for i, (name, style) in enumerate(WINGS.items()):
        tex = assemble(t, m_nebel, style, seed=40 + i)
        tex.save(OUT / f"wings_{i + 1}_{theme}.png")
        v = wings_view(tex)
        tile = bg(v.width + 40, v.height + 50, t)
        tile.alpha_composite(v, (20, 34))
        label(tile, 8, 8, name)
        tiles.append(tile)
    w, h = tiles[0].size
    sheet = Image.new("RGBA", (2 * (w + 6) + 6, 2 * (h + 6) + 6), hexc("#0C0A10"))
    for i, tl in enumerate(tiles):
        sheet.alpha_composite(tl, (6 + (i % 2) * (w + 6), 6 + (i // 2) * (h + 6)))
    sheet.convert("RGB").save(OUT / "fluegel_entwurf.png")
    print("ok")
