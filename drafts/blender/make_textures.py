"""Erzeugt die Mod-Texturen: Federn pro Farbe, Engel, Leucht-Maske, Weiss. python make_textures.py <outdir>"""
import sys, random, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
THEMES = {  # deep, mid, main, tip
    "lila":  ("#08030f", "#3a1270", "#a03cf0", "#ff6cf5"),
    "gruen": ("#020a05", "#0d4a24", "#22c55e", "#b0ff8a"),
    "blau":  ("#02060f", "#0f2f66", "#2f7cf0", "#8fe8ff"),
    "rot":   ("#0a0203", "#5a0d18", "#e0263c", "#ffa06c"),
    "dark":  ("#030304", "#2a2a33", "#9a9aa8", "#ffffff"),
    "gold":  ("#0a0702", "#5a3c0a", "#e0a020", "#fff0a0"),
}
W, H = 128, 512

def rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def gradient(stops):
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        for k in range(len(stops) - 1):
            p0, c0 = stops[k]; p1, c1 = stops[k + 1]
            if p0 <= t <= p1:
                c = lerp(c0, c1, (t - p0) / max(1e-6, p1 - p0)); break
        for x in range(W): px[x, y] = c
    return img

def blobs(img, cols, seed, n=36, alpha=110):
    r = random.Random(seed)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y, rad = r.random() * W, r.random() * H, 20 + r.random() * 60
        c = r.choice(cols)
        d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=(*c, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(22))
    base = img.convert("RGBA"); base.alpha_composite(layer); return base.convert("RGB")

def barbs(img, col, a1, a2):
    d = ImageDraw.Draw(img, "RGBA")
    d.line((64, 0, 64, 470), fill=(*col, a1), width=2)
    for y in range(20, 480, 9):
        d.line((64, y, 4, y + 26), fill=(*col, a2)); d.line((64, y, 124, y + 26), fill=(*col, a2))
    return img

def stars(img, seed, n=16):
    r = random.Random(seed); d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y, s = 10 + r.random() * 108, 60 + r.random() * 440, 3 if r.random() < .2 else 1.5
        d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 255, 255))
    return img

for name, (deep, mid, main, tip) in THEMES.items():
    deep, mid, main, tip = map(rgb, (deep, mid, main, tip))
    img = gradient([(0, deep), (.35, mid), (.75, main), (1, tip)])
    img = blobs(img, [main, deep], 7)
    img = barbs(img, lerp(main, (255, 255, 255), .6), 115, 46)
    stars(img, 3).save(OUT / f"feather_{name}.png")

angel = gradient([(0, (216, 208, 230)), (.6, (255, 255, 255)), (1, (255, 238, 255))])
angel = blobs(angel, [(200, 190, 230)], 9, alpha=60)
barbs(angel, (150, 140, 180), 150, 64).save(OUT / "feather_engel.png")

# Leucht-Maske (weiss, wird im Spiel mit der Farbe eingefaerbt): Spitzen + Sterne
glow = Image.new("RGB", (W, H), (0, 0, 0)); px = glow.load()
for y in range(H):
    t = max(0.0, (y / (H - 1) - .62) / .38) ** 1.4
    for x in range(W): px[x, y] = (int(255 * t),) * 3
stars(glow, 3).save(OUT / "feather_glow.png")
Image.new("RGB", (16, 16), (255, 255, 255)).save(OUT / "white.png")
print("ok")
