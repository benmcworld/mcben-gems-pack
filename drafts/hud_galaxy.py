"""Galaxy-HUD (Pixel-Art): Hotbar 2x, Herzen, Ruestung, XP-Leiste + Mockup."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, str(Path(__file__).parent))
from galaxy import fbm, colorize

OUT = Path(__file__).parent / "hud"
OUT.mkdir(exist_ok=True)
R = 2  # Hotbar-Aufloesung (2x = 364x44)

def hexc(h, a=255):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (a,)

def nebula(w, h, seed):
    rng = np.random.default_rng(seed)
    n = fbm(w, h, rng, base=max(8, w // 6)); m = fbm(w, h, rng, base=max(8, w // 10))
    v = np.clip((n * .65 + m * .35 - .3) * 1.7, 0, 1) ** 1.2 * .9 + .1
    img = Image.fromarray(colorize(v).astype(np.uint8)).convert("RGBA")
    for _ in range(int(w * h / 260)):        # kleine Pixel-Sterne
        x, y = rng.integers(0, w), rng.integers(0, h)
        img.putpixel((int(x), int(y)), hexc("#F3D9FF") if rng.random() < .6 else hexc("#C77DFF"))
    return img

def rounded_mask(w, h, r, inset=0):
    m = Image.new("L", (w, h)); ImageDraw.Draw(m).rounded_rectangle(
        (inset, inset, w - 1 - inset, h - 1 - inset), radius=r, fill=255)
    return m

def ring(w, h, r, inset, thick):
    return ImageChops.subtract(rounded_mask(w, h, r, inset), rounded_mask(w, h, max(0, r - thick), inset + thick))

def solid(size, col, mask):
    i = Image.new("RGBA", size, col); i.putalpha(mask); return i

def glow(mask, col, blur, clip=None):
    g = mask.filter(ImageFilter.GaussianBlur(blur))
    if clip is not None: g = ImageChops.multiply(g, clip)
    return solid(mask.size, col, g)

# ---------------- Hotbar ----------------
def hotbar():
    W, H = 182 * R, 22 * R
    full = rounded_mask(W, H, 4 * R)
    bar = Image.new("RGBA", (W, H))
    neb = nebula(W, H, 21); neb.putalpha(ImageChops.multiply(full, Image.new("L", (W, H), 235)))
    bar.alpha_composite(neb)
    border = ring(W, H, 4 * R, 0, 2 * R)
    bar.alpha_composite(glow(border, hexc("#B23CFF"), 3 * R, full))      # Leuchten nach innen
    bar.alpha_composite(solid((W, H), hexc("#8A2BE2"), border))
    bar.alpha_composite(solid((W, H), hexc("#D07BFF"), ring(W, H, 4 * R, R // 2, R)))  # heller Mittelstreifen
    bar.alpha_composite(solid((W, H), hexc("#3A0A66"), ring(W, H, 4 * R, 0, 1)))       # dunkle Aussenlinie
    bar = bar.quantize(64, method=Image.Quantize.FASTOCTREE).convert("RGBA")         # Pixel-Art-Look
    bar.putalpha(full)
    # Auswahl (24x23)
    sw, sh = 24 * R, 23 * R
    sel = Image.new("RGBA", (sw, sh))
    rm = ring(sw, sh + R, 4 * R, 0, 2 * R).crop((0, 0, sw, sh))
    inner = rounded_mask(sw, sh + R, 4 * R, 2 * R).crop((0, 0, sw, sh))
    sel.alpha_composite(glow(rm, hexc("#FF4DF0", 230), 3 * R, inner))
    sel.alpha_composite(solid((sw, sh), hexc("#E83CE8"), rm))
    sel.alpha_composite(solid((sw, sh), hexc("#FFB3FA"), ring(sw, sh + R, 4 * R, R // 2, R).crop((0, 0, sw, sh))))
    sel.alpha_composite(solid((sw, sh), hexc("#7A0E7A"), ring(sw, sh + R, 4 * R, 0, 1).crop((0, 0, sw, sh))))
    return bar, sel

# ---------------- Herzen / Ruestung (9x9 Pixel-Art) ----------------
HEART = ["..##.##..",
         ".#######.",
         ".#######.",
         ".#######.",
         "..#####..",
         "...###...",
         "....#....",
         ".........",
         "........."]
CHEST = [".##...##.",
         ".###.###.",
         ".#######.",
         "..#####..",
         "..#####..",
         "..#####..",
         "..##.##..",
         ".........",
         "........."]

def sprite(shape, base, light, dark, outline, half=False, shift=1):
    img = Image.new("RGBA", (9, 9))
    pts = {(x, y + shift) for y, row in enumerate(shape) for x, c in enumerate(row) if c == "#"}
    ys = [y for _, y in pts] or [0]
    for (x, y) in pts:
        col = base
        if (x - 1, y) not in pts or (x, y - 1) not in pts: col = light
        if (x + 1, y + 1) not in pts and (x, y + 1) not in pts: col = dark
        img.putpixel((x, y), col)
    for (x, y) in pts:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n not in pts and 0 <= n[0] < 9 and 0 <= n[1] < 9 and img.getpixel(n)[3] == 0 \
                        and not (half and n[0] > 4 and n[1] >= 0 and abs(dx) + abs(dy) and (n[0]-1, n[1]) in pts and dx == 1):
                    img.putpixel(n, outline)
    # Glanzpunkt
    hx = min(x for x, _ in pts) + 1; hy = min(ys) + 1
    if (hx, hy) in pts: img.putpixel((hx, hy), hexc("#FFFFFF"))
    if half:  # rechte Haelfte leer lassen -> dort zeigt Minecraft den leeren Container
        for x in range(5, 9):
            for y in range(9): img.putpixel((x, y), (0, 0, 0, 0))
    return img

def hearts():
    args = (hexc("#E23BD8"), hexc("#FF9BF5"), hexc("#97188F"), hexc("#2A0428"))
    return sprite(HEART, *args, shift=0), sprite(HEART, *args, half=True, shift=0)

def armor():
    args = (hexc("#E85AD8"), hexc("#FFB8F6"), hexc("#9C2591"), hexc("#2A0428"))
    return sprite(CHEST, *args, shift=1), sprite(CHEST, *args, half=True, shift=1)

# ---------------- XP-Leiste (182x5) ----------------
def xp():
    W, H = 182, 5
    prog = Image.new("RGBA", (W, H))
    top, mid, bot = hexc("#FF9BF5"), hexc("#E23BD8"), hexc("#8E1486")
    for x in range(W):
        notch = x % 20 in (0, 19) and 0 < x < W - 1
        for y in range(H):
            c = [hexc("#2A0428"), top, mid, bot, hexc("#2A0428")][y]
            if notch and 0 < y < H - 1: c = hexc("#B0209F")
            prog.putpixel((x, y), c)
    back = Image.new("RGBA", (W, H))
    for x in range(W):
        for y in range(H):
            c = hexc("#0E0418") if y in (0, H - 1) else hexc("#21123A")
            if x % 20 in (0, 19) and 0 < y < H - 1: c = hexc("#160A28")
            back.putpixel((x, y), c)
    return back, prog

# ---------------- Mockup ----------------
def mockup(bar, sel, hf, hh, af, ah, xb, xprog, scale=4):
    W, H = 182 * scale + 120, 70 * scale
    rng = np.random.default_rng(3)
    stone = (rng.random((H // (scale * 4) + 1, W // (scale * 4) + 1)) * 40 + 70).astype(np.uint8)
    bg = Image.fromarray(stone).resize((W, H), Image.NEAREST).convert("RGBA")
    def put(img, x, y, s=scale / 1):
        bg.alpha_composite(img.resize((int(img.width * s), int(img.height * s)), Image.NEAREST), (int(x), int(y)))
    ox = 60; oy = H - 26 * scale
    put(bar, ox, oy + scale, scale / R)
    put(sel, ox + 59 * scale, oy, scale / R)
    xpy = oy - 6 * scale
    put(xb, ox, xpy); put(xprog.crop((0, 0, 70, 5)), ox, xpy)
    for i in range(10):
        put(hf if i < 9 else hh, ox + i * 8 * scale, xpy - 10 * scale)
        put(af if i < 8 else ah, ox + i * 8 * scale, xpy - 20 * scale)
    return bg

if __name__ == "__main__":
    bar, sel = hotbar(); hf, hh = hearts(); af, ah = armor(); xb, xprog = xp()
    for n, i in dict(hotbar=bar, hotbar_selection=sel, heart_full=hf, heart_half=hh,
                     armor_full=af, armor_half=ah, experience_bar_background=xb,
                     experience_bar_progress=xprog).items():
        i.save(OUT / f"{n}.png")
    mockup(bar, sel, hf, hh, af, ah, xb, xprog).convert("RGB").save(OUT / "hud_entwurf.png")
    print("ok")
