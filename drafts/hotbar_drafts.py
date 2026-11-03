"""Hotbar-Entwuerfe in HD (4x) + Vorschau im Spiel-Look."""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
OUT = Path(__file__).parent
S = 4            # Ausgabe-Skalierung (4x = 728x88)
SS = 4           # Supersampling fuer glatte Kanten
K = S * SS

def canvas(w, h):
    return Image.new("RGBA", (w * K, h * K), (0, 0, 0, 0))

def down(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)

def rr(d, box, r, **kw):
    x0, y0, x1, y1 = [v * K for v in box]
    d.rounded_rectangle((x0, y0, x1 - 1, y1 - 1), radius=r * K, **kw)

def vgrad(w, h, top, bot):
    g = Image.new("RGBA", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(4)))
    return g.resize((w, h))

def masked(img, fill, mask):
    img.paste(fill, (0, 0), mask)

def slot_mask(box, r, size):
    m = Image.new("L", size, 0)
    rr(ImageDraw.Draw(m), box, r, fill=255)
    return m

def glow(img, color, blur):
    a = img.split()[3]
    g = Image.new("RGBA", img.size, color)
    ga = a.filter(ImageFilter.GaussianBlur(blur))
    # zum Rand hin ausblenden, damit kein harter Kasten entsteht
    w, h = img.size; e = int(0.9 * K)
    fade = Image.new("L", img.size, 0)
    ImageDraw.Draw(fade).rectangle((e, e, w - e, h - e), fill=255)
    fade = fade.filter(ImageFilter.GaussianBlur(e / 2))
    from PIL import ImageChops
    g.putalpha(ImageChops.multiply(ga, fade))
    return g

# ---------------- A: Clean Dark ----------------
def draft_a():
    bar = canvas(182, 22)
    d = ImageDraw.Draw(bar)
    rr(d, (0, 0, 182, 22), 3, fill=(10, 10, 14, 150))
    for i in range(9):
        x = 1 + i * 20
        rr(d, (x + 1, 2, x + 19, 20), 2.5, fill=(255, 255, 255, 18), outline=(255, 255, 255, 60), width=SS)
    rr(d, (0, 0, 182, 22), 3, outline=(255, 255, 255, 90), width=SS)
    sel = canvas(24, 23)
    s = Image.new("RGBA", sel.size)
    rr(ImageDraw.Draw(s), (1, 1, 23, 23), 3.5, outline=(255, 255, 255, 255), width=int(1.5 * K))
    sel.alpha_composite(glow(s, (180, 220, 255, 255), 1.5 * K))
    sel.alpha_composite(s)
    return down(bar), down(sel)

# ---------------- B: Kristall / Amethyst ----------------
def draft_b():
    w, h = 182 * K, 22 * K
    bar = canvas(182, 22)
    m = slot_mask((0, 0, 182, 22), 4, bar.size)
    masked(bar, vgrad(w, h, (70, 30, 120, 200), (25, 8, 50, 220)), m)
    d = ImageDraw.Draw(bar)
    for i in range(9):
        x = 1 + i * 20
        sm = slot_mask((x + 1, 2, x + 19, 20), 3, bar.size)
        masked(bar, vgrad(w, h, (20, 6, 40, 200), (50, 20, 90, 200)), sm)
        rr(d, (x + 1, 2, x + 19, 20), 3, outline=(190, 120, 255, 140), width=SS)
        # Glanzlicht oben
        rr(d, (x + 3, 3, x + 17, 4.2), 0.6, fill=(230, 200, 255, 22))
    # Edelstein-Trenner
    for i in range(1, 9):
        cx, cy = (1 + i * 20) * K, 11 * K
        r = 1.6 * K
        d.polygon([(cx, cy - r), (cx + r * .7, cy), (cx, cy + r), (cx - r * .7, cy)], fill=(230, 190, 255, 255))
    rr(d, (0, 0, 182, 22), 4, outline=(210, 150, 255, 220), width=SS * 2)
    rr(d, (1, 1, 181, 21), 3, outline=(40, 10, 70, 200), width=SS)
    sel = canvas(24, 23)
    s = Image.new("RGBA", sel.size)
    sd = ImageDraw.Draw(s)
    rr(sd, (1, 1, 23, 23), 4, outline=(255, 235, 255, 255), width=int(1.75 * K))
    rr(sd, (2.5, 2.5, 21.5, 21.5), 3, outline=(200, 120, 255, 255), width=SS * 2)
    for (cx, cy) in ((12, 1.2),):
        cx, cy, r = cx * K, cy * K, 2.2 * K
        sd.polygon([(cx, cy - r), (cx + r * .8, cy), (cx, cy + r), (cx - r * .8, cy)], fill=(255, 255, 255, 255))
    sel.alpha_composite(glow(s, (200, 110, 255, 255), 2.2 * K))
    sel.alpha_composite(s)
    return down(bar), down(sel)

# ---------------- C: Minimal (nur Slots) ----------------
def draft_c():
    bar = canvas(182, 22)
    d = ImageDraw.Draw(bar)
    for i in range(9):
        x = 1 + i * 20
        rr(d, (x + 1.5, 2.5, x + 18.5, 19.5), 4, fill=(0, 0, 0, 110), outline=(255, 255, 255, 120), width=SS)
    sel = canvas(24, 23)
    s = Image.new("RGBA", sel.size)
    sd = ImageDraw.Draw(s)
    rr(sd, (2, 2, 22, 22), 5, fill=(255, 255, 255, 40), outline=(255, 255, 255, 255), width=int(1.25 * K))
    sel.alpha_composite(glow(s, (255, 255, 255, 200), 1.2 * K))
    sel.alpha_composite(s)
    return down(bar), down(sel)

def mockup(bar, sel, title):
    W, H = 900, 200
    bg = vgrad(W, H, (120, 170, 235, 255), (95, 140, 70, 255)).copy()
    d = ImageDraw.Draw(bg)
    d.rectangle((0, 130, W, H), fill=(92, 128, 60, 255))
    d.text((12, 10), title, fill=(255, 255, 255, 255))
    sc = 4.5 / S   # Darstellung wie GUI-Scale ~4.5
    b = bar.resize((int(bar.width * sc), int(bar.height * sc)), Image.LANCZOS)
    s = sel.resize((int(sel.width * sc), int(sel.height * sc)), Image.LANCZOS)
    x0, y0 = (W - b.width) // 2, H - b.height - 12
    bg.alpha_composite(b, (x0, y0))
    bg.alpha_composite(s, (x0 + int((2 * 20 - 1) * S * sc), y0 - int(1 * S * sc)))
    return bg

drafts = [("A  Clean Dark", draft_a()), ("B  Kristall / Amethyst", draft_b()), ("C  Minimal", draft_c())]
sheet = Image.new("RGBA", (900, 200 * 3 + 20), (30, 30, 30, 255))
for i, (name, (bar, sel)) in enumerate(drafts):
    key = name[0]
    bar.save(OUT / f"hotbar_{key}.png"); sel.save(OUT / f"hotbar_selection_{key}.png")
    sheet.alpha_composite(mockup(bar, sel, name), (0, i * 210))
sheet.save(OUT / "hotbar_entwuerfe.png")
print("ok", drafts[0][1][0].size)
