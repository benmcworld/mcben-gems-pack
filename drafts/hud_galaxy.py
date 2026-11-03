"""Galaxy-HUD (Pixel-Art) in mehreren Farb-Themes:
Hotbar (2x), Auswahl, Herzen, Ruestung, Hunger, XP-Leiste + Mockup."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, str(Path(__file__).parent))
from galaxy import fbm

OUT = Path(__file__).parent / "hud"
R = 2  # Hotbar-Aufloesung (2x = 364x44)


def hexc(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


# --------------------------------------------------------------------------- #
# Themes
# --------------------------------------------------------------------------- #
THEMES = {
    "lila": dict(
        nebula=["#07020F", "#1C0838", "#3A1270", "#6A2AB0", "#A45CE6", "#E3C2FF"],
        stars=["#F3D9FF", "#C77DFF"],
        border="#8A2BE2", border_light="#D07BFF", border_dark="#2A0650", border_glow="#B23CFF",
        sel="#E83CE8", sel_light="#FFB3FA", sel_dark="#5E0A5E", sel_glow="#FF4DF0",
        icon="#E23BD8", icon_light="#FF9BF5", icon_dark="#97188F", icon_line="#2A0428",
        empty="#3A1A45", bone="#F6E6FF",
        xp_bg="#1E1230", xp_bg_dark="#0C0618",
    ),
    "schwarz-weiss": dict(
        nebula=["#020203", "#0D0D12", "#24242C", "#4A4A55", "#8C8C99", "#F2F2F7"],
        stars=["#FFFFFF", "#B9B9C6"],
        border="#BFBFC8", border_light="#FFFFFF", border_dark="#101014", border_glow="#FFFFFF",
        sel="#FFFFFF", sel_light="#FFFFFF", sel_dark="#3A3A44", sel_glow="#FFFFFF",
        icon="#E9E9EF", icon_light="#FFFFFF", icon_dark="#8C8C99", icon_line="#0A0A0E",
        empty="#2A2A32", bone="#FFFFFF",
        xp_bg="#1A1A20", xp_bg_dark="#08080A",
    ),
    "blau": dict(
        nebula=["#02040F", "#071A38", "#0F3470", "#1E5FC0", "#4FA3FF", "#CBE6FF"],
        stars=["#E6F3FF", "#7FC1FF"],
        border="#1E7BFF", border_light="#8CC8FF", border_dark="#06204A", border_glow="#3D9BFF",
        sel="#38C8FF", sel_light="#C8F1FF", sel_dark="#073A5E", sel_glow="#4DE1FF",
        icon="#3DA9FF", icon_light="#BFE6FF", icon_dark="#1452A8", icon_line="#04122A",
        empty="#14283F", bone="#EAF6FF",
        xp_bg="#0F1A2E", xp_bg_dark="#050A16",
    ),
    "rot": dict(
        nebula=["#0F0204", "#380810", "#701222", "#B02A3A", "#E65C6C", "#FFC9D0"],
        stars=["#FFE0E4", "#FF7F8F"],
        border="#E22B45", border_light="#FF8C9C", border_dark="#4A0610", border_glow="#FF3D58",
        sel="#FF4D63", sel_light="#FFC8D0", sel_dark="#5E0A16", sel_glow="#FF5A70",
        icon="#FF3B55", icon_light="#FFB3BE", icon_dark="#A0142A", icon_line="#2A040A",
        empty="#3F141B", bone="#FFF0F2",
        xp_bg="#2E0F14", xp_bg_dark="#16050A",
    ),
    "gruen": dict(
        nebula=["#020F06", "#083818", "#127034", "#2AB05A", "#5CE68C", "#C9FFDA"],
        stars=["#E0FFE9", "#7FFFA8"],
        border="#22C55E", border_light="#8CF5B0", border_dark="#064A1E", border_glow="#3DFF7F",
        sel="#4DFF8A", sel_light="#C8FFD9", sel_dark="#0A5E28", sel_glow="#5AFF95",
        icon="#3BE070", icon_light="#B3FFCB", icon_dark="#14903E", icon_line="#042A10",
        empty="#143F22", bone="#F0FFF4",
        xp_bg="#0F2E18", xp_bg_dark="#05160A",
    ),
}


# --------------------------------------------------------------------------- #
# Helfer
# --------------------------------------------------------------------------- #
def nebula(w, h, t, seed):
    rng = np.random.default_rng(seed)
    n = fbm(w, h, rng, base=max(8, w // 6))
    m = fbm(w, h, rng, base=max(8, w // 10))
    v = np.clip((n * .65 + m * .35 - .3) * 1.7, 0, 1) ** 1.45 * .8 + .03
    stops = np.linspace(0, 1, len(t["nebula"]))
    cols = [hexc(c) for c in t["nebula"]]
    rgb = np.stack([np.interp(v, stops, [c[i] for c in cols]) for i in range(3)], -1)
    img = Image.fromarray(rgb.astype(np.uint8)).convert("RGBA")
    for _ in range(int(w * h / 260)):
        x, y = rng.integers(0, w), rng.integers(0, h)
        img.putpixel((int(x), int(y)), hexc(t["stars"][0] if rng.random() < .6 else t["stars"][1]))
    return img


def rmask(w, h, r, inset=0):
    m = Image.new("L", (w, h))
    ImageDraw.Draw(m).rounded_rectangle((inset, inset, w - 1 - inset, h - 1 - inset), radius=r, fill=255)
    return m


def ring(w, h, r, inset, thick):
    return ImageChops.subtract(rmask(w, h, r, inset), rmask(w, h, max(0, r - thick), inset + thick))


def solid(size, col, mask):
    i = Image.new("RGBA", size, col)
    i.putalpha(mask)
    return i


def glow(mask, col, blur, clip=None):
    g = mask.filter(ImageFilter.GaussianBlur(blur))
    if clip is not None:
        g = ImageChops.multiply(g, clip)
    return solid(mask.size, col, g)


# --------------------------------------------------------------------------- #
# Hotbar + Auswahl
# --------------------------------------------------------------------------- #
def hotbar(t):
    W, H = 182 * R, 22 * R
    rad = 3 * R
    full = rmask(W, H, rad)
    bar = Image.new("RGBA", (W, H))
    neb = nebula(W, H, t, 21)
    neb.putalpha(ImageChops.multiply(full, Image.new("L", (W, H), 235)))
    bar.alpha_composite(neb)
    border = ring(W, H, rad, 0, 2 * R)
    bar.alpha_composite(glow(border, hexc(t["border_glow"], 150), 2 * R, full))
    bar.alpha_composite(solid((W, H), hexc(t["border"]), border))
    bar.alpha_composite(solid((W, H), hexc(t["border_light"]), ring(W, H, rad, R // 2, R)))
    bar.alpha_composite(solid((W, H), hexc(t["border_dark"]), ring(W, H, rad, 0, 1)))
    bar = bar.quantize(64, method=Image.Quantize.FASTOCTREE).convert("RGBA")
    bar.putalpha(full)

    # Auswahl: eckig (nur 1px abgeschraegte Ecken), dicker Rahmen, Leuchten nach innen
    sw, sh = 24 * R, 23 * R
    big_h = sh + R
    r2 = R
    rm = ring(sw, big_h, r2, 0, 2 * R).crop((0, 0, sw, sh))
    inner = rmask(sw, big_h, r2, 2 * R).crop((0, 0, sw, sh))
    sel = Image.new("RGBA", (sw, sh))
    sel.alpha_composite(glow(rm, hexc(t["sel_glow"], 220), 2.5 * R, inner))
    sel.alpha_composite(solid((sw, sh), hexc(t["sel"]), rm))
    sel.alpha_composite(solid((sw, sh), hexc(t["sel_light"]), ring(sw, big_h, r2, R // 2, R).crop((0, 0, sw, sh))))
    sel.alpha_composite(solid((sw, sh), hexc(t["sel_dark"]), ring(sw, big_h, r2, 0, 1).crop((0, 0, sw, sh))))
    return bar, sel


# --------------------------------------------------------------------------- #
# Icons (9x9 Pixel-Art, handgezeichnet)
#   O = Umrandung, F = Farbe, L = hell, D = dunkel, W = Glanz/Knochen, E = leer
# --------------------------------------------------------------------------- #
HEART = [
    ".OOO.OOO.",
    "OWLFOFFDO",
    "OLFFFFFDO",
    "OFFFFFFDO",
    ".OFFFFDO.",
    "..OFFDO..",
    "...ODO...",
    "....O....",
    ".........",
]
CHEST = [
    "OOO..OOO.",
    "OWLOOFDO.",
    "OLFFFFDO.",
    ".OLFFDO..",
    ".OFFFDO..",
    ".OFFFDO..",
    ".OOOOOO..",
    ".........",
    ".........",
]
FOOD = [
    "....OOO..",
    "...OLLFO.",
    "..OLFFFDO",
    "..OFFFFDO",
    "..OFFFDDO",
    ".OBODDOO.",
    "OBBOOO...",
    ".OO......",
    ".........",
]


def draw_icon(shape, t, part="full", split=4):
    cmap = {"O": t["icon_line"], "F": t["icon"], "L": t["icon_light"], "D": t["icon_dark"],
            "W": "#FFFFFF", "B": t["bone"]}
    img = Image.new("RGBA", (9, 9))
    for y, row in enumerate(shape):
        for x, c in enumerate(row):
            if c == ".":
                continue
            col = cmap[c]
            if part == "empty" or (part == "half" and x > split):
                col = t["icon_line"] if c == "O" else (t["bone"] if c == "B" and False else t["empty"])
            if part == "half_only" and x > split:
                continue
            img.putpixel((x, y), hexc(col))
    return img


def icons(t):
    return {
        # Herzen: Minecraft zeichnet den (Vanilla-)Container immer darunter -> half nur links
        "heart/full": draw_icon(HEART, t),
        "heart/half": draw_icon(HEART, t, "half_only"),
        "heart/container": draw_icon(HEART, t, "empty"),
        # Ruestung: half muss die leere Haelfte selbst enthalten
        "armor_full": draw_icon(CHEST, t),
        "armor_half": draw_icon(CHEST, t, "half", split=3),
        "armor_empty": draw_icon(CHEST, t, "empty"),
        # Hunger: Container wird immer darunter gezeichnet
        "food_full": draw_icon(FOOD, t),
        "food_half": draw_icon(FOOD, t, "half_only"),
        "food_empty": draw_icon(FOOD, t, "empty"),
    }


# --------------------------------------------------------------------------- #
# XP-Leiste (182x5)
# --------------------------------------------------------------------------- #
def xp(t):
    W, H = 182, 5
    prog, back = Image.new("RGBA", (W, H)), Image.new("RGBA", (W, H))
    rows = [t["icon_line"], t["icon_light"], t["icon"], t["icon_dark"], t["icon_line"]]
    for x in range(W):
        seg = x % 20
        notch = seg in (0, 19) and 0 < x < W - 1
        for y in range(H):
            c = rows[y]
            if notch and 0 < y < H - 1:
                c = t["icon_dark"]
            elif y == 2 and 3 <= seg <= 16:
                c = t["icon_light"] if seg % 4 else t["icon"]   # heller Mittelstrich
            prog.putpixel((x, y), hexc(c))
            b = t["xp_bg_dark"] if y in (0, H - 1) or (notch and 0 < y < H - 1) else t["xp_bg"]
            back.putpixel((x, y), hexc(b))
    return back, prog


# --------------------------------------------------------------------------- #
# Mockup
# --------------------------------------------------------------------------- #
def mockup(name, t, bar, sel, ic, xb, xprog, scale=4):
    W, H = 182 * scale + 80, 60 * scale
    rng = np.random.default_rng(3)
    stone = (rng.random((H // (scale * 4) + 1, W // (scale * 4) + 1)) * 40 + 70).astype(np.uint8)
    bg = Image.fromarray(stone).resize((W, H), Image.NEAREST).convert("RGBA")
    bg.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 60)))

    def put(img, x, y, s=scale):
        bg.alpha_composite(img.resize((int(img.width * s), int(img.height * s)), Image.NEAREST), (int(x), int(y)))

    ox = 40
    oy = H - 24 * scale
    put(bar, ox, oy + scale, scale / R)
    put(sel, ox + 59 * scale, oy, scale / R)
    xpy = oy - 6 * scale
    put(xb, ox, xpy)
    put(xprog.crop((0, 0, 75, 5)), ox, xpy)
    hy = xpy - 10 * scale
    # Herzen (19 HP: 9 voll + 1 halb), Ruestung (15: 7 voll + 1 halb + 2 leer), Hunger (17)
    for i in range(10):
        x = ox + i * 8 * scale
        put(ic["heart/container"], x, hy)
        put(ic["heart/full"] if i < 9 else ic["heart/half"], x, hy)
        a = ic["armor_full"] if i < 7 else ic["armor_half"] if i == 7 else ic["armor_empty"]
        put(a, x, hy - 10 * scale)
        fx = ox + (182 - 9 - i * 8) * scale       # Hunger von rechts nach links
        put(ic["food_empty"], fx, hy)
        if i < 8:
            put(ic["food_full"], fx, hy)
        elif i == 8:
            put(ic["food_half"], fx, hy)
    ImageDraw.Draw(bg).text((8, 6), name, fill=(255, 255, 255, 255))
    return bg


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    shots = []
    for name, t in THEMES.items():
        bar, sel = hotbar(t)
        ic = icons(t)
        xb, xprog = xp(t)
        d = OUT / name
        d.mkdir(exist_ok=True)
        bar.save(d / "hotbar.png")
        sel.save(d / "hotbar_selection.png")
        xb.save(d / "experience_bar_background.png")
        xprog.save(d / "experience_bar_progress.png")
        for k, im in ic.items():
            p = d / f"{k}.png"
            p.parent.mkdir(parents=True, exist_ok=True)
            im.save(p)
        shots.append(mockup(name, t, bar, sel, ic, xb, xprog))
    sheet = Image.new("RGBA", (shots[0].width, sum(s.height + 6 for s in shots)), (20, 20, 20, 255))
    y = 0
    for s in shots:
        sheet.alpha_composite(s, (0, y))
        y += s.height + 6
    sheet.convert("RGB").save(OUT / "hud_entwurf.png")
    print("ok")
