"""Entwuerfe: Auswahl-Rahmen (Hotbar) + Schild-Ruestung, mit Herzen 5 und Hunger 4."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
sys.path.insert(0, str(Path(__file__).parent))
from hud_galaxy import THEMES, hexc, hotbar, xp, R, rmask, ring, solid, glow, nebula
from icon_designs import HEARTS, FOOD, draw, world_bg, label

OUT = Path(__file__).parent / "hud"
SW, SH = 24 * R, 23 * R
BH = SH + R  # unten abgeschnitten wie Vanilla


def crop(m):
    return m.crop((0, 0, SW, SH))


def frame_layers(sel, t, r, thick, inset=0):
    rm = crop(ring(SW, BH, r, inset, thick))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel"]), rm))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel_light"]),
                              crop(ring(SW, BH, r, inset + max(1, thick // 4), max(1, thick // 2)))))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel_dark"]), crop(ring(SW, BH, r, inset, 1))))
    return rm


def s_eckig(t):
    sel = Image.new("RGBA", (SW, SH))
    rm = crop(ring(SW, BH, R, 0, 2 * R))
    sel.alpha_composite(glow(rm, hexc(t["sel_glow"], 220), 2.5 * R, crop(rmask(SW, BH, R, 2 * R))))
    frame_layers(sel, t, R, 2 * R)
    return sel


def s_gefuellt(t):
    sel = Image.new("RGBA", (SW, SH))
    inner = crop(rmask(SW, BH, R, 2 * R))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel_glow"], 55), inner))
    rm = crop(ring(SW, BH, R, 0, 2 * R))
    sel.alpha_composite(glow(rm, hexc(t["sel_glow"], 255), 4 * R, inner))
    frame_layers(sel, t, R, 2 * R)
    return sel


def s_doppel(t):
    sel = Image.new("RGBA", (SW, SH))
    outer = crop(ring(SW, BH, R, 0, R))
    inner = crop(ring(SW, BH, R, 2 * R, R))
    sel.alpha_composite(glow(inner, hexc(t["sel_glow"], 200), 2 * R, crop(rmask(SW, BH, R, 3 * R))))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel_light"]), outer))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel"]), inner))
    return sel


def s_ecken(t):
    m = Image.new("L", (SW, BH))
    d = ImageDraw.Draw(m)
    L, T = 8 * R, 2 * R
    for (x, y, sx, sy) in ((0, 0, 1, 1), (SW - 1, 0, -1, 1), (0, BH - 1, 1, -1), (SW - 1, BH - 1, -1, -1)):
        d.rectangle(sorted((x, x + sx * L))[:1] + sorted((y, y + sy * T))[:1] +
                    sorted((x, x + sx * L))[1:] + sorted((y, y + sy * T))[1:], fill=255)
        d.rectangle(sorted((x, x + sx * T))[:1] + sorted((y, y + sy * L))[:1] +
                    sorted((x, x + sx * T))[1:] + sorted((y, y + sy * L))[1:], fill=255)
    m = crop(m)
    sel = Image.new("RGBA", (SW, SH))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel_glow"], 40), crop(rmask(SW, BH, R, 2 * R))))
    sel.alpha_composite(glow(m, hexc(t["sel_glow"], 255), 2 * R))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel"]), m))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel_light"]), m.filter(__import__("PIL.ImageFilter").ImageFilter.MinFilter(3))))
    return sel


def s_galaxie(t):
    sel = Image.new("RGBA", (SW, SH))
    inner = crop(rmask(SW, BH, R, 2 * R))
    neb = nebula(SW, SH, {**t, "nebula": [t["nebula"][2], t["icon_dark"], t["icon"], t["icon_light"]]}, 4)
    neb.putalpha(inner.point(lambda v: v * 120 // 255))
    sel.alpha_composite(neb)
    rm = crop(ring(SW, BH, R, 0, 2 * R))
    sel.alpha_composite(glow(rm, hexc(t["sel_glow"], 230), 2.5 * R, inner))
    frame_layers(sel, t, R, 2 * R)
    return sel


def diamond(d, cx, cy, r, col):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=col)


def s_kristall(t):
    sel = s_gefuellt(t)
    d = ImageDraw.Draw(sel)
    for (x, y) in ((2 * R, 2 * R), (SW - 2 * R - 1, 2 * R), (2 * R, SH - 2 * R), (SW - 2 * R - 1, SH - 2 * R)):
        diamond(d, x, y, 2.5 * R, hexc("#FFFFFF"))
        diamond(d, x, y, 1.2 * R, hexc(t["sel_light"]))
    return sel


def s_neon(t):
    sel = Image.new("RGBA", (SW, SH))
    rm = crop(ring(SW, BH, 2 * R, R, R))
    sel.alpha_composite(glow(rm, hexc(t["sel_glow"], 255), 2 * R))
    sel.alpha_composite(glow(rm, hexc(t["sel_glow"], 255), 1 * R))
    sel.alpha_composite(solid((SW, SH), hexc("#FFFFFF"), rm))
    return sel


def s_bevel(t):
    """Kantiger 3D-Rahmen: oben hell, unten dunkel, Pixel-Ecken."""
    sel = Image.new("RGBA", (SW, SH))
    inner = crop(rmask(SW, BH, 0, 3 * R))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel_glow"], 45), inner))
    rm = crop(ring(SW, BH, 0, 0, 3 * R))
    top = Image.new("L", (SW, SH))
    ImageDraw.Draw(top).polygon([(0, 0), (SW, 0), (0, SH)], fill=255)
    sel.alpha_composite(solid((SW, SH), hexc(t["sel"]), rm))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel_light"]), ImageChops.multiply(rm, top)))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel_dark"]), crop(ring(SW, BH, 0, 0, 1))))
    sel.alpha_composite(solid((SW, SH), hexc(t["sel_dark"]), crop(ring(SW, BH, 0, 3 * R - 1, 1))))
    for (x, y) in ((0, 0), (SW - R, 0)):  # Pixel-Ecken ausschneiden
        ImageDraw.Draw(sel).rectangle((x, y, x + R - 1, y + R - 1), fill=(0, 0, 0, 0))
    return sel


STYLES = {
    "1 Eckig (bisher)": s_eckig,
    "2 Gefuellt + Glow": s_gefuellt,
    "3 Doppelrahmen": s_doppel,
    "4 Nur Ecken": s_ecken,
    "5 Galaxie innen": s_galaxie,
    "6 Kristall-Ecken": s_kristall,
    "7 Neon": s_neon,
    "8 Kantig 3D": s_bevel,
}

SHIELDS = {
    "1 Schild (bisher)": ["OOOOOOO..", "OWLFFDO..", "OLFFFDO..", "OLFFFDO..", "OFFFFDO..", ".OFFDO...", "..ODO....", "...O.....", "........."],
    "2 Edelstein-Schild": ["OOOOOOO..", "OLFFFDO..", "OFFWFDO..", "OFWLWDO..", "OFFWFDO..", ".OFFDO...", "..ODO....", "...O.....", "........."],
    "3 Schild mit Fluegeln": ["Y.......Y", "YOOOOOOOY", "YOWLFFDOY", ".OLFFFDO.", ".OFFFFDO.", "..OFFDO..", "...ODO...", "....O....", "........."],
    "4 Neon-Schild": ["WWWWWWW..", "WLLLLLW..", "WLNNNLW..", "WLNNNLW..", "WLNNNLW..", ".WLNLW...", "..WLW....", "...W.....", "........."],
    "5 Galaxie-Schild": ["LLLLLLL..", "LNNSNNL..", "LNDNNNL..", "LNNNSNL..", "LSNDNNL..", ".LNNNL...", "..LSL....", "...L.....", "........."],
    "6 Rundschild": ["..OOO....", ".OWLFO...", "OLFWFDO..", "OFWLWDO..", "OFFWFDO..", ".OFFDO...", "..OOO....", ".........", "........."],
}


def hud_mock(t, sel, shield, scale=3, title=""):
    bar, _ = hotbar(t)
    xb, xprog = xp(t)
    W, H = 182 * scale + 40, 60 * scale
    bg = world_bg(W, H, scale)

    def put(im, x, y, s=scale):
        bg.alpha_composite(im.resize((int(im.width * s), int(im.height * s)), Image.NEAREST), (int(x), int(y)))
    ox, oy = 20, H - 24 * scale
    put(bar, ox, oy + scale, scale / R)
    put(sel, ox + 59 * scale, oy, scale / R)
    xpy = oy - 6 * scale
    put(xb, ox, xpy)
    put(xprog.crop((0, 0, 75, 5)), ox, xpy)
    hy = xpy - 10 * scale
    heart, food = HEARTS["5 Rund"], FOOD["4 Apfel (Farbe)"]
    for i in range(10):
        x = ox + i * 8 * scale
        put(draw(heart, t, "empty"), x, hy)
        put(draw(heart, t, "full" if i < 9 else "half"), x, hy)
        if shield:
            part = "full" if i < 7 else "half_r" if i == 7 else "empty"
            put(draw(shield, t, part, split=3), x, hy - 10 * scale)
        fx = ox + (182 - 9 - i * 8) * scale
        put(draw(food, t, "empty"), fx, hy)
        if i < 9:
            put(draw(food, t, "full" if i < 8 else "half"), fx, hy)
    label(bg, 6, 4, title)
    return bg


def grid(images, cols, pad=8, bg="#141218"):
    w, h = images[0].width, images[0].height
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (w + pad) + pad, rows * (h + pad) + pad), hexc(bg))
    for i, im in enumerate(images):
        sheet.alpha_composite(im, (pad + (i % cols) * (w + pad), pad + (i // cols) * (h + pad)))
    return sheet


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    t = THEMES["lila"]
    shield = SHIELDS["3 Schild mit Fluegeln"]
    sel_imgs = [hud_mock(t, fn(t), shield, title=n) for n, fn in STYLES.items()]
    grid(sel_imgs, 2).convert("RGB").save(OUT / "auswahl_designs.png")
    sh_imgs = [hud_mock(t, s_gefuellt(t), sh, title=n) for n, sh in SHIELDS.items()]
    grid(sh_imgs, 2).convert("RGB").save(OUT / "schild_designs.png")
    print("ok")


def shield_closeup(t, scale=10):
    pad = 30
    names = list(SHIELDS)
    W = len(names) * (9 * scale * 2 + pad) + pad
    img = Image.new("RGBA", (W, 9 * scale + 50), hexc("#1E1A26"))
    for i, n in enumerate(names):
        x = pad + i * (9 * scale * 2 + pad)
        label(img, x, 6, n)
        img.alpha_composite(draw(SHIELDS[n], t, "full", split=3).resize((9 * scale, 9 * scale), Image.NEAREST), (x, 30))
        img.alpha_composite(draw(SHIELDS[n], t, "half_r", split=3).resize((9 * scale, 9 * scale), Image.NEAREST), (x + 9 * scale, 30))
    return img


if __name__ == "__main__":
    t = THEMES["lila"]
    close = shield_closeup(t)
    grid_img = Image.open(OUT / "schild_designs.png").convert("RGBA")
    W = max(close.width, grid_img.width)
    out = Image.new("RGBA", (W, close.height + grid_img.height), hexc("#141218"))
    out.alpha_composite(close, (0, 0))
    out.alpha_composite(grid_img, (0, close.height))
    out.convert("RGB").save(OUT / "schild_designs.png")
