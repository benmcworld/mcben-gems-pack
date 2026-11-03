"""Galaxie-/Nebel-Stil: Textur-Generator + Entwuerfe (Hotbar, Schild, Fluegel)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from pathlib import Path
OUT = Path(__file__).parent

PALETTE = [  # (Position, RGB)
    (0.00, (6, 2, 14)), (0.30, (28, 8, 58)), (0.52, (78, 20, 140)),
    (0.70, (150, 40, 220)), (0.85, (215, 90, 255)), (1.00, (255, 210, 255)),
]

def value_noise(w, h, cell, rng):
    gw, gh = w // cell + 2, h // cell + 2
    g = rng.random((gh, gw))
    img = Image.fromarray((g * 255).astype(np.uint8)).resize((gw * cell, gh * cell), Image.BICUBIC)
    return np.asarray(img, dtype=np.float32)[:h, :w] / 255

def fbm(w, h, rng, base=None, octaves=6):
    base = base or max(w, h) // 2
    out, amp, tot = np.zeros((h, w), np.float32), 1.0, 0
    cell = base
    for _ in range(octaves):
        out += value_noise(w, h, max(2, cell), rng) * amp
        tot += amp; amp *= 0.5; cell //= 2
    return out / tot

def colorize(v):
    xs = [p for p, _ in PALETTE]
    rgb = np.stack([np.interp(v, xs, [c[i] for _, c in PALETTE]) for i in range(3)], -1)
    return rgb

def galaxy(w, h, seed=1, stars=True):
    rng = np.random.default_rng(seed)
    n = fbm(w, h, rng)
    warp = fbm(w, h, rng)
    n2 = fbm(w, h, rng)
    v = np.clip((n * 0.6 + warp * 0.4 - 0.25) * 1.9, 0, 1)
    v = v ** 1.6
    v = np.clip(v + (np.abs(n2 - 0.5) < 0.03) * 0.25 * v, 0, 1)   # feine Nebel-Adern
    rgb = colorize(v)
    img = Image.fromarray(rgb.astype(np.uint8)).convert("RGBA")
    if stars:
        add_stars(img, rng, density=w * h / 900)
    return img

def add_stars(img, rng, density):
    w, h = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(int(density)):
        x, y = rng.random() * w, rng.random() * h
        r = rng.choice([0.6, 0.8, 1.0, 1.4, 2.2], p=[.4, .3, .17, .1, .03]) * max(1, w / 256)
        col = (255, 235, 255, 255) if rng.random() < .7 else (230, 140, 255, 255)
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    glow = layer.filter(ImageFilter.GaussianBlur(max(1.5, w / 160)))
    img.alpha_composite(glow); img.alpha_composite(glow); img.alpha_composite(layer)

def glow_of(img, color, blur, strength=2):
    a = img.split()[3].filter(ImageFilter.GaussianBlur(blur))
    g = Image.new("RGBA", img.size, color); g.putalpha(a)
    out = Image.new("RGBA", img.size)
    for _ in range(strength):
        out.alpha_composite(g)
    return out

def bg_scene(w, h):
    bg = galaxy(w, h, seed=99)
    dark = Image.new("RGBA", (w, h), (10, 6, 25, 150))
    bg.alpha_composite(dark)
    return bg

# ------------------------- Hotbar -------------------------
def hotbar(S=4):
    K = S * 4
    W, H = 182 * K, 22 * K
    big = Image.new("RGBA", (W, H))
    m = Image.new("L", (W, H)); md = ImageDraw.Draw(m)
    md.rounded_rectangle((0, 0, W - 1, H - 1), radius=4 * K, fill=255)
    tex = galaxy(W // 4, H // 4, seed=7).resize((W, H), Image.BICUBIC)
    tex.putalpha(ImageChops.multiply(m, Image.new("L", (W, H), 225)))
    big.alpha_composite(tex)
    d = ImageDraw.Draw(big)
    for i in range(9):
        x = (1 + i * 20) * K
        d.rounded_rectangle((x + K, 2 * K, x + 19 * K - 1, 20 * K - 1), radius=3 * K,
                            fill=(8, 2, 20, 150), outline=(190, 110, 255, 170), width=4)
    rim = Image.new("RGBA", (W, H)); ImageDraw.Draw(rim).rounded_rectangle(
        (2, 2, W - 3, H - 3), radius=4 * K, outline=(230, 160, 255, 255), width=int(0.6 * K))
    big.alpha_composite(rim)
    bar = big.resize((182 * S, 22 * S), Image.LANCZOS)
    # Auswahl
    sw, sh = 24 * K, 23 * K
    s = Image.new("RGBA", (sw, sh)); sd = ImageDraw.Draw(s)
    sd.rounded_rectangle((K, K, 23 * K, 23 * K), radius=4 * K, outline=(255, 240, 255, 255), width=int(1.4 * K))
    sd.rounded_rectangle((2.6 * K, 2.6 * K, 21.4 * K, 21.4 * K), radius=3 * K, outline=(200, 90, 255, 255), width=int(0.6 * K))
    sel = Image.new("RGBA", (sw, sh))
    g = glow_of(s, (210, 100, 255, 255), 0.7 * K, 2)
    sel.alpha_composite(g); sel.alpha_composite(s)
    # Stern-Funkeln an den Ecken
    for (cx, cy) in ((K * 1.6, K * 1.6), (sw - K * 1.6, K * 1.6)):
        r = 1.8 * K
        sd2 = ImageDraw.Draw(sel)
        sd2.polygon([(cx, cy - r), (cx + r * .25, cy - r * .25), (cx + r, cy), (cx + r * .25, cy + r * .25),
                     (cx, cy + r), (cx - r * .25, cy + r * .25), (cx - r, cy), (cx - r * .25, cy - r * .25)],
                    fill=(255, 255, 255, 255))
    sel = sel.resize((24 * S, 23 * S), Image.LANCZOS)
    return bar, sel

# ------------------------- Fluegel -------------------------
def feather(length, width):
    f = Image.new("L", (int(width * 2), int(length)))
    d = ImageDraw.Draw(f)
    d.ellipse((0, 0, width * 2 - 1, length - 1), fill=255)
    return f

def wing(size, seed=3, flip=False):
    W = H = size
    mask = Image.new("L", (W, H)); edge = Image.new("L", (W, H))
    shoulder = (W * 0.12, H * 0.28)
    rows = [  # (Anzahl, Laenge, Breite, Startwinkel, Endwinkel, Abstand)
        (9, H * 0.62, W * 0.045, -20, 75, 0.20),
        (8, H * 0.42, W * 0.05, -15, 70, 0.14),
        (7, H * 0.26, W * 0.055, -10, 60, 0.07),
    ]
    for n, L, bw, a0, a1, off in rows:
        for i in range(n):
            t = i / (n - 1)
            ang = math.radians(a0 + (a1 - a0) * t)
            l = L * (1 - 0.35 * t)
            f = feather(l, bw).rotate(math.degrees(-ang) + 90 - 90, expand=True, resample=Image.BICUBIC)
            f = feather(l, bw)
            f = f.rotate(-math.degrees(ang) - 90 + 90, expand=True, resample=Image.BICUBIC)
            cx = shoulder[0] + math.cos(ang) * (W * off + l * 0.5)
            cy = shoulder[1] + math.sin(ang) * (H * off + l * 0.5)
            fr = feather(l, bw).rotate(-90 - math.degrees(ang), expand=True, resample=Image.BICUBIC)
            pos = (int(cx - fr.width / 2), int(cy - fr.height / 2))
            mask.paste(255, pos, fr)
            e = fr.filter(ImageFilter.FIND_EDGES)
            edge.paste(255, pos, e)
    # Schulterbogen
    ImageDraw.Draw(mask).ellipse((0, H * 0.12, W * 0.55, H * 0.45), fill=255)
    tex = galaxy(W, H, seed=seed)
    w_img = Image.new("RGBA", (W, H))
    w_img.paste(tex, (0, 0), mask)
    dark = Image.new("RGBA", (W, H), (10, 0, 25, 200))
    w_img.paste(dark, (0, 0), edge.filter(ImageFilter.MaxFilter(3)))
    out = Image.new("RGBA", (W, H))
    out.alpha_composite(glow_of(w_img, (190, 70, 255, 255), size / 40, 1))
    out.alpha_composite(w_img)
    return out.transpose(Image.FLIP_LEFT_RIGHT) if flip else out

# ------------------------- Schild -------------------------
def shield_shape(w, h):
    pts = []
    for i in range(41):
        t = i / 40
        x = w * 0.5 + (w * 0.5) * math.sin(math.pi * (t - 0.5)) * 1.0
    m = Image.new("L", (w, h)); d = ImageDraw.Draw(m)
    poly = [(0, h * .08), (w * .5, 0), (w, h * .08)]
    for i in range(1, 30):
        t = i / 30
        poly.append((w - (w * .5) * (t ** 1.8), h * .08 + (h * .92) * t))
    poly.append((w * .5, h))
    for i in range(29, 0, -1):
        t = i / 30
        poly.append(((w * .5) * (t ** 1.8), h * .08 + (h * .92) * t))
    d.polygon(poly, fill=255)
    return m, poly

def shield(size=512):
    W, H = int(size * 0.62), int(size * 0.75)
    m, poly = shield_shape(W, H)
    tex = galaxy(W, H, seed=11)
    s = Image.new("RGBA", (W, H)); s.paste(tex, (0, 0), m)
    inner = m.filter(ImageFilter.MinFilter(int(size / 40) | 1))
    rim = ImageChops.subtract(m, inner)
    rim_img = Image.new("RGBA", (W, H), (235, 170, 255, 255)); rim_img.putalpha(rim)
    canvas = Image.new("RGBA", (size, size))
    ox, oy = (size - W) // 2, (size - H) // 2
    lw = wing(int(size * 0.45), seed=5, flip=True)
    rw = wing(int(size * 0.45), seed=6)
    canvas.alpha_composite(lw, (ox - int(size * 0.28), oy - int(size * 0.04)))
    canvas.alpha_composite(rw, (ox + W - int(size * 0.17), oy - int(size * 0.04)))
    body = Image.new("RGBA", (size, size)); body.alpha_composite(s, (ox, oy))
    rl = Image.new("RGBA", (size, size)); rl.alpha_composite(rim_img, (ox, oy))
    canvas.alpha_composite(glow_of(body, (170, 60, 255, 255), size / 30, 2))
    canvas.alpha_composite(body)
    canvas.alpha_composite(glow_of(rl, (230, 150, 255, 255), size / 120, 2))
    canvas.alpha_composite(rl)
    return canvas

if __name__ == "__main__":
    W, H = 1400, 900
    sheet = bg_scene(W, H)
    d = ImageDraw.Draw(sheet)
    # Fluegel-Paar
    lw, rw = wing(380, seed=3, flip=True), wing(380, seed=4)
    sheet.alpha_composite(lw, (30, 40)); sheet.alpha_composite(rw, (300, 40))
    # Schild
    sh = shield(460)
    sheet.alpha_composite(sh, (820, 10))
    # Hotbar
    bar, sel = hotbar(4)
    bar.save(OUT / "galaxy_hotbar.png"); sel.save(OUT / "galaxy_hotbar_selection.png")
    sc = 1.6
    b = bar.resize((int(bar.width * sc), int(bar.height * sc)), Image.LANCZOS)
    s = sel.resize((int(sel.width * sc), int(sel.height * sc)), Image.LANCZOS)
    x0, y0 = (W - b.width) // 2, H - b.height - 60
    sheet.alpha_composite(b, (x0, y0))
    sheet.alpha_composite(s, (x0 + int(39 * 4 * sc), y0 - int(4 * sc)))
    for (x, y, t) in ((40, 20, "Fluegel"), (860, 20, "Schild mit Fluegeln"), (x0, y0 - 40, "Hotbar")):
        d.text((x, y), t, fill=(255, 255, 255, 255))
    sheet.convert("RGB").save(OUT / "galaxy_entwurf.png")
    print("ok")
