"""Totem-Entwuerfe (32x32 Pixel-Art) im Galaxy-Stil."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter
sys.path.insert(0, str(Path(__file__).parent))
from hud_galaxy import THEMES, hexc
from galaxy import fbm

OUT = Path(__file__).parent / "hud"
N = 32


def fill_tex(t, seed, bright=1.0):
    """Nebel-Fuellung in Theme-Farben + Pixel-Sterne."""
    rng = np.random.default_rng(seed)
    v = fbm(N, N, rng, base=12)
    v = np.clip((v - .25) * 1.8, 0, 1) * bright
    stops = np.linspace(0, 1, 5)
    cols = [hexc(c) for c in (t["nebula"][1], t["nebula"][2], t["icon_dark"], t["icon"], t["icon_light"])]
    rgb = np.stack([np.interp(v, stops, [c[i] for c in cols]) for i in range(3)], -1)
    img = Image.fromarray(rgb.astype(np.uint8)).convert("RGBA")
    for _ in range(9):
        x, y = rng.integers(2, N - 2, 2)
        img.putpixel((int(x), int(y)), hexc("#FFFFFF"))
    return img


def shade(mask, t, seed, bright=1.0, rim=True):
    """Maske -> Pixel-Art mit Fuellung, hellem Rand oben-links, dunklem Rand unten-rechts, Umriss."""
    m = np.array(mask) > 127
    out = Image.new("RGBA", (N, N))
    tex = fill_tex(t, seed, bright)
    light, dark, line = hexc(t["icon_light"]), hexc(t["icon_dark"]), hexc(t["icon_line"])
    for y in range(N):
        for x in range(N):
            if not m[y, x]:
                continue
            c = tex.getpixel((x, y))
            if rim:
                if (y > 0 and not m[y - 1, x]) or (x > 0 and not m[y, x - 1]):
                    c = light
                elif (y < N - 1 and not m[y + 1, x]) or (x < N - 1 and not m[y, x + 1]):
                    c = dark
            out.putpixel((x, y), c)
    # Umriss aussen
    for y in range(N):
        for x in range(N):
            if m[y, x]:
                continue
            if any(0 <= x + dx < N and 0 <= y + dy < N and m[y + dy, x + dx]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), line)
    return out


def mask():
    m = Image.new("L", (N, N))
    return m, ImageDraw.Draw(m)


def compose(parts, t):
    """Teile von hinten nach vorne einzeln schattieren -> jede Feder hat eigenen Umriss."""
    out = Image.new("RGBA", (N, N))
    for i, (m, bright) in enumerate(parts):
        out.alpha_composite(shade(m, t, 10 + i, bright))
    return out


def feather_masks(cx, cy, lengths, angles, width=3.6):
    import math
    res = []
    for side in (-1, 1):
        for L, a in zip(lengths, angles):
            m, d = mask()
            ang = math.radians(a)
            dx, dy = math.cos(ang) * side, math.sin(ang)
            px, py = -dy, dx
            x0, y0 = cx + side * 2, cy
            pts = [
                (x0 + px * width / 2, y0 + py * width / 2),
                (x0 + dx * L * .6 + px * width * .7, y0 + dy * L * .6 + py * width * .7),
                (x0 + dx * L, y0 + dy * L),
                (x0 + dx * L * .6 - px * width * .7, y0 + dy * L * .6 - py * width * .7),
                (x0 - px * width / 2, y0 - py * width / 2),
            ]
            d.polygon(pts, fill=255)
            res.append((m, 0.85))
    return res


WING_L = (14, 13, 11, 8)
WING_A = (-38, -16, 6, 28)


def totem_figure(t):
    parts = feather_masks(16, 14, WING_L, WING_A)
    m, d = mask()
    d.rounded_rectangle((11, 3, 20, 12), radius=2, fill=255)
    parts.append((m, 1.1))
    m, d = mask()
    d.rectangle((12, 13, 19, 24), fill=255)
    parts.append((m, 1.0))
    m, d = mask()
    d.polygon([(9, 26), (22, 26), (20, 29), (11, 29)], fill=255)
    parts.append((m, 0.9))
    img = compose(parts, t)
    for (x, y) in ((13, 7), (14, 7), (17, 7), (18, 7)):
        img.putpixel((x, y), hexc("#FFFFFF"))
    for x in range(14, 18):
        img.putpixel((x, 10), hexc(t["icon_line"]))
    for x in range(13, 19):
        img.putpixel((x, 18), hexc(t["icon_light"]))
    return img


def totem_crystal(t):
    parts = feather_masks(16, 13, WING_L, WING_A)
    m, d = mask()
    d.polygon([(16, 1), (21, 7), (21, 22), (16, 30), (11, 22), (11, 7)], fill=255)
    parts.append((m, 1.2))
    img = compose(parts, t)
    for y in range(3, 29):
        img.putpixel((16, y), hexc(t["icon_light"]) if y % 2 else hexc(t["icon"]))
    for x in range(12, 21):
        img.putpixel((x, 7), hexc(t["icon_light"]))
    return img


def totem_heart(t):
    parts = feather_masks(16, 12, WING_L, WING_A)
    m, d = mask()
    d.ellipse((7, 6, 17, 16), fill=255)
    d.ellipse((15, 6, 25, 16), fill=255)
    d.polygon([(7.5, 12), (24.5, 12), (16, 26)], fill=255)
    parts.append((m, 1.15))
    img = compose(parts, t)
    for (x, y) in ((10, 9), (11, 8), (10, 10), (12, 8)):
        img.putpixel((x, y), hexc("#FFFFFF"))
    return img


def totem_star(t):
    m, d = mask()
    d.polygon([(16, 1), (19, 13), (31, 16), (19, 19), (16, 31), (13, 19), (1, 16), (13, 13)], fill=255)
    m2, d2 = mask()
    d2.ellipse((10, 10, 22, 22), fill=255)
    img = compose([(m, 1.0), (m2, 1.25)], t)
    ring = Image.new("L", (N, N))
    ImageDraw.Draw(ring).ellipse((3, 11, 28, 21), outline=255, width=1)
    for y in range(N):
        for x in range(N):
            if ring.getpixel((x, y)) and (y > 16 or img.getpixel((x, y))[3] == 0):
                img.putpixel((x, y), hexc(t["icon_light"]))
    img.putpixel((16, 16), hexc("#FFFFFF"))
    return img


DESIGNS = {
    "1 Totem-Figur": totem_figure,
    "2 Kristall": totem_crystal,
    "3 Herz mit Fluegeln": totem_heart,
    "4 Galaxie-Stern": totem_star,
}


def glow_behind(img, col, scale):
    big = img.resize((N * scale, N * scale), Image.NEAREST)
    a = big.split()[3].filter(ImageFilter.GaussianBlur(scale * 1.5))
    g = Image.new("RGBA", big.size, col)
    g.putalpha(a.point(lambda v: v * 0.7))
    out = Image.new("RGBA", big.size)
    out.alpha_composite(g)
    out.alpha_composite(big)
    return out


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    scale, pad = 8, 30
    themes = ["lila", "schwarz-weiss", "blau"]
    W = len(DESIGNS) * (N * scale + pad) + pad
    H = len(themes) * (N * scale + pad + 20) + pad
    sheet = Image.new("RGBA", (W, H), hexc("#15121C"))
    dr = ImageDraw.Draw(sheet)
    for r, th in enumerate(themes):
        for c, (name, fn) in enumerate(DESIGNS.items()):
            img = fn(THEMES[th])
            img.save(OUT / f"totem_{c + 1}_{th}.png")
            x = pad + c * (N * scale + pad)
            y = pad + r * (N * scale + pad + 20)
            dr.text((x, y - 16), f"{name}  ({th})", fill=(255, 255, 255, 255))
            sheet.alpha_composite(glow_behind(img, hexc(THEMES[th]["border_glow"]), scale), (x, y))
    sheet.convert("RGB").save(OUT / "totem_entwurf.png")
    print("ok")
