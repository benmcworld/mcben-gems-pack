"""Entwuerfe: coolere XP-Leisten (2x Aufloesung) + runde Ruestung (passend zu Herzen 5)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
sys.path.insert(0, str(Path(__file__).parent))
from hud_galaxy import THEMES, hexc, rmask, solid, glow, nebula
from icon_designs import HEARTS, draw, world_bg, label
from hud_pack import hud_sprites
from selection_styles import grid

OUT = Path(__file__).parent / "hud"
XR = 2                      # XP-Aufloesung (2x = 364x10)
XW, XH = 182 * XR, 5 * XR


# --------------------------------------------------------------------------- #
# XP-Leisten: jede Funktion -> (background, progress)
# --------------------------------------------------------------------------- #
def xp_bisher(t):
    from hud_galaxy import xp
    b, p = xp(t)
    return b.resize((XW, XH), Image.NEAREST), p.resize((XW, XH), Image.NEAREST)


def _pill(w, h):
    return rmask(w, h, h // 2)


def xp_glow(t):
    """Durchgehender Leuchtbalken: abgerundet, heller Kern, Glow-Kante."""
    back = Image.new("RGBA", (XW, XH))
    m = _pill(XW, XH)
    back.alpha_composite(solid((XW, XH), hexc(t["xp_bg_dark"], 200), m))
    back.alpha_composite(solid((XW, XH), hexc(t["xp_bg"], 220), rmask(XW, XH, XH // 2, 2)))
    prog = Image.new("RGBA", (XW, XH))
    prog.alpha_composite(solid((XW, XH), hexc(t["icon_dark"]), m))
    prog.alpha_composite(solid((XW, XH), hexc(t["icon"]), rmask(XW, XH, XH // 2, 1)))
    core = Image.new("L", (XW, XH))
    ImageDraw.Draw(core).rectangle((3, XH // 2 - 1, XW - 4, XH // 2), fill=255)
    prog.alpha_composite(glow(core, hexc(t["icon_light"]), 1.2, m))
    prog.alpha_composite(solid((XW, XH), hexc("#FFFFFF", 230), core))
    return back, prog


def xp_galaxie(t):
    """Galaxie-Nebel im Balken mit Sternen, heller Rand."""
    m = _pill(XW, XH)
    back = Image.new("RGBA", (XW, XH))
    back.alpha_composite(solid((XW, XH), hexc(t["xp_bg_dark"], 210), m))
    neb = nebula(XW, XH, {**t, "nebula": [t["icon_dark"], t["icon"], t["icon_light"], "#FFFFFF"]}, 9)
    prog = Image.new("RGBA", (XW, XH))
    prog.paste(neb, (0, 0), m)
    edge = ImageChops.subtract(m, rmask(XW, XH, XH // 2, 1))
    prog.alpha_composite(solid((XW, XH), hexc(t["icon_light"]), edge))
    return back, prog


def xp_perlen(t):
    """Einzelne Perlen/Pillen pro Abschnitt mit Luecken."""
    back, prog = Image.new("RGBA", (XW, XH)), Image.new("RGBA", (XW, XH))
    seg = 20 * XR
    for x0 in range(0, XW, seg):
        w = min(seg, XW - x0) - 2
        if w <= 4:
            continue
        m = Image.new("L", (XW, XH))
        ImageDraw.Draw(m).rounded_rectangle((x0 + 1, 0, x0 + w, XH - 1), radius=XH // 2, fill=255)
        back.alpha_composite(solid((XW, XH), hexc(t["xp_bg"], 230), m))
        back.alpha_composite(solid((XW, XH), hexc(t["xp_bg_dark"]), ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(3)))))
        prog.alpha_composite(solid((XW, XH), hexc(t["icon"]), m))
        prog.alpha_composite(solid((XW, XH), hexc(t["icon_line"]), ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(3)))))
        hl = Image.new("L", (XW, XH))
        ImageDraw.Draw(hl).rounded_rectangle((x0 + 4, 2, x0 + w - 3, 3), radius=1, fill=255)
        prog.alpha_composite(solid((XW, XH), hexc(t["icon_light"]), hl))
    return back, prog


def xp_verlauf(t):
    """Farbverlauf dunkel -> hell nach rechts, Glanzlinie oben, feine Abschnitte."""
    m = _pill(XW, XH)
    back = Image.new("RGBA", (XW, XH))
    back.alpha_composite(solid((XW, XH), hexc(t["xp_bg_dark"], 220), m))
    a, b = np.array(hexc(t["icon_dark"])[:3], float), np.array(hexc(t["icon_light"])[:3], float)
    x = np.linspace(0, 1, XW)[None, :, None]
    y = np.linspace(0, 1, XH)[:, None, None]
    col = a * (1 - x) + b * x
    col = col * (1.15 - .45 * y)
    img = Image.fromarray(np.clip(np.broadcast_to(col, (XH, XW, 3)), 0, 255).astype(np.uint8)).convert("RGBA")
    prog = Image.new("RGBA", (XW, XH))
    prog.paste(img, (0, 0), m)
    d = ImageDraw.Draw(prog)
    d.line((3, 2, XW - 4, 2), fill=hexc("#FFFFFF", 150))
    for xx in range(20 * XR, XW, 20 * XR):
        d.line((xx, 1, xx, XH - 2), fill=hexc(t["icon_line"], 160))
    return back, prog


def xp_kristall(t):
    """Chevron-/Kristall-Muster (>>>) mit Leuchtkante."""
    m = _pill(XW, XH)
    back = Image.new("RGBA", (XW, XH))
    back.alpha_composite(solid((XW, XH), hexc(t["xp_bg_dark"], 220), m))
    prog = Image.new("RGBA", (XW, XH))
    yy, xx = np.mgrid[0:XH, 0:XW]
    k = 8
    chev = ((xx - np.abs(yy - XH / 2 + .5) * 1.2) % k) < k / 2
    base = np.where(chev[..., None], np.array(hexc(t["icon"])[:3]), np.array(hexc(t["icon_dark"])[:3]))
    img = Image.fromarray(base.astype(np.uint8)).convert("RGBA")
    prog.paste(img, (0, 0), m)
    edge = ImageChops.subtract(m, rmask(XW, XH, XH // 2, 1))
    prog.alpha_composite(solid((XW, XH), hexc(t["icon_light"]), edge))
    return back, prog


XPS = {
    "1 Bisher": xp_bisher,
    "2 Leuchtbalken": xp_glow,
    "3 Galaxie": xp_galaxie,
    "4 Perlen": xp_perlen,
    "5 Verlauf": xp_verlauf,
    "6 Kristall-Pfeile": xp_kristall,
}

# --------------------------------------------------------------------------- #
# Runde Ruestung (9x9, Stil wie Herzen 5 "Rund")
# --------------------------------------------------------------------------- #
ARMOR_ROUND = {
    "1 Runde Brustplatte": [
        ".OO...OO.",
        "OWLO.OFDO",
        "OLFOOOFDO",
        "OLFFFFFDO",
        ".OLFFFDO.",
        ".OFFFFDO.",
        ".OFFFDDO.",
        "..OOOOO..",
        "........."],
    "2 Runder Schild": [
        "..OOOOO..",
        ".OWLFFDO.",
        "OWLFFFFDO",
        "OLFFFFFDO",
        "OFFFFFFDO",
        ".OFFFFDO.",
        "..OFFDO..",
        "...OOO...",
        "........."],
    "3 Runder Helm": [
        "..OOOOO..",
        ".OWLFFDO.",
        "OWLFFFFDO",
        "OLFFFFFDO",
        "OFNNNNNDO",
        "OFO...ODO",
        "OOO...OOO",
        ".........",
        "........."],
    "4 Rundschild mit Stein": [
        "..OOOOO..",
        ".OLLFFDO.",
        "OLFFWFFDO",
        "OLFWLWFDO",
        "OFFFWFFDO",
        "OFFFFFDDO",
        ".OFFFDDO.",
        "..OOOOO..",
        "........."],
    "5 Blase": [
        "..OOOOO..",
        ".OWWLFFO.",
        "OWWLFFFDO",
        "OLLFFFFDO",
        "OFFFFFFDO",
        "OFFFFFDDO",
        ".OFFDDDO.",
        "..OOOOO..",
        "........."],
}


def mock(t, back, prog, armor, title, frac=.45, S=3):
    sp = hud_sprites_cache(t)
    W, H = 182 * S + 40, 60 * S
    bg = world_bg(W, H, S)

    def put(im, x, y, w=None, h=None):
        bg.alpha_composite(im.resize((int(w or im.width * S), int(h or im.height * S)), Image.NEAREST), (int(x), int(y)))
    ox, oy = 20, H - 24 * S
    put(sp["hotbar.png"], ox, oy + S, 182 * S, 22 * S)
    put(sp["hotbar_selection.png"], ox + 59 * S, oy, 24 * S, 23 * S)
    xpy = oy - 6 * S
    put(back, ox, xpy, 182 * S, 5 * S)
    cut = int(XW * frac)
    put(prog.crop((0, 0, cut, XH)), ox, xpy, cut * S / XR, 5 * S)
    hy = xpy - 10 * S
    for i in range(10):
        x = ox + i * 8 * S
        put(sp["heart/container.png"], x, hy)
        put(sp["heart/full.png" if i < 9 else "heart/half.png"], x, hy)
        part = "full" if i < 7 else "half_r" if i == 7 else "empty"
        put(draw(armor, t, part, split=4), x, hy - 10 * S)
        fx = ox + (182 - 9 - i * 8) * S
        put(sp["food_empty.png"], fx, hy)
        if i < 9:
            put(sp["food_full.png" if i < 8 else "food_half.png"], fx, hy)
    label(bg, 6, 4, title)
    return bg


_cache = {}


def hud_sprites_cache(t):
    key = t["icon"]
    if key not in _cache:
        name = next(n for n, v in THEMES.items() if v is t)
        _cache[key] = hud_sprites(name)
    return _cache[key]


def closeup(t, scale=10):
    pad = 26
    names = list(ARMOR_ROUND)
    img = Image.new("RGBA", (len(names) * (9 * scale * 2 + pad) + pad, 9 * scale + 46), hexc("#1E1A26"))
    for i, n in enumerate(names):
        x = pad + i * (9 * scale * 2 + pad)
        label(img, x, 6, n)
        img.alpha_composite(draw(ARMOR_ROUND[n], t, "full").resize((9 * scale, 9 * scale), Image.NEAREST), (x, 28))
        img.alpha_composite(draw(ARMOR_ROUND[n], t, "half_r", split=4).resize((9 * scale, 9 * scale), Image.NEAREST), (x + 9 * scale, 28))
    return img


if __name__ == "__main__":
    t = THEMES["lila"]
    armor0 = ARMOR_ROUND["2 Runder Schild"]
    xp_imgs = [mock(t, *fn(t), armor0, n) for n, fn in XPS.items()]
    grid(xp_imgs, 2).convert("RGB").save(OUT / "xp_designs.png")

    ar_imgs = [mock(t, *xp_bisher(t), a, n) for n, a in ARMOR_ROUND.items()]
    g = grid(ar_imgs, 2)
    c = closeup(t)
    out = Image.new("RGBA", (max(g.width, c.width), g.height + c.height), hexc("#141218"))
    out.alpha_composite(c, (0, 0))
    out.alpha_composite(g, (0, c.height))
    out.convert("RGB").save(OUT / "runde_ruestung.png")
    print("ok")
