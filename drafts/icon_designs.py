"""Design-Katalog: verschiedene Herzen, Ruestung, Hunger (9x9 Pixel-Art) + durchsichtige Hotbar."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent))
from hud_galaxy import THEMES, hexc, hotbar, xp, R

OUT = Path(__file__).parent / "hud"

# Zeichen: O Umriss | F Farbe | L hell | D dunkel | W Glanz | N tief-dunkel | S Stern
#          G Gold | g Gold hell | d Gold dunkel | T Stiel | V Blatt | E Funkeln (Theme hell)
HEARTS = {
    "1 Klassisch": [
        ".OOO.OOO.",
        "OWLFOFFDO",
        "OLFFFFFDO",
        "OFFFFFFDO",
        ".OFFFFDO.",
        "..OFFDO..",
        "...ODO...",
        "....O....",
        "........."],
    "2 Kristall": [
        ".OOO.OOO.",
        "OWLLOLFDO",
        "OLLFLFDDO",
        "OLFFFDDDO",
        ".OFFFDDO.",
        "..OFDDO..",
        "...ODO...",
        "....O....",
        "........."],
    "3 Galaxie": [
        ".LLL.LLL.",
        "LNDNLNNNL",
        "LNNNNNSNL",
        "LNSNNDNNL",
        ".LNNNNNL.",
        "..LNDNL..",
        "...LNL...",
        "....L....",
        "........."],
    "4 Neon": [
        ".WWW.WWW.",
        "WLLLWLLLW",
        "WLNNLNNLW",
        "WLNNNNNLW",
        ".WLNNNLW.",
        "..WLNLW..",
        "...WLW...",
        "....W....",
        "........."],
    "5 Rund": [
        "..OO.OO..",
        ".OWLOFFO.",
        "OWLFFFFDO",
        "OLFFFFFDO",
        "OFFFFFFDO",
        ".OFFFFDO.",
        "..OFFDO..",
        "...ODO...",
        "....O...."],
}
ARMOR = {
    "1 Brustplatte": [
        "OOO..OOO.",
        "OWLOOFDO.",
        "OLFFFFDO.",
        ".OLFFDO..",
        ".OFFFDO..",
        ".OFFFDO..",
        ".OOOOOO..",
        ".........",
        "........."],
    "2 Schild": [
        "OOOOOOO..",
        "OWLFFDO..",
        "OLFFFDO..",
        "OLFFFDO..",
        "OFFFFDO..",
        ".OFFDO...",
        "..ODO....",
        "...O.....",
        "........."],
    "3 Helm": [
        ".........",
        ".OOOOO...",
        "OWLFFDO..",
        "OLFFFDO..",
        "OFOOODO..",
        "OFO.ODO..",
        "OOO.OOO..",
        ".........",
        "........."],
    "4 Edelstein": [
        ".........",
        ".OOOOO...",
        "OWLFFDO..",
        "OOOOOOO..",
        "OLFFFDO..",
        ".OFFDO...",
        "..OFO....",
        "...O.....",
        "........."],
}
FOOD = {
    "1 Keule": [
        "....OOO..",
        "...OLLFO.",
        "..OLFFFDO",
        "..OFFFFDO",
        "..OFFFDDO",
        ".OBODDOO.",
        "OBBOOO...",
        ".OO......",
        "........."],
    "2 Goldener Apfel": [
        "....T.VV.",
        "....TVV..",
        ".OOOTOOO.",
        "OWggGGGdO",
        "OgGGGGGdO",
        "OGGGGGddO",
        "OGGGGddO.",
        ".OGGddO..",
        "..OO.OO.."],
    "3 OP-Gap": [
        "....T.VV.",
        "....TVV..",
        ".PPPTPPP.",
        "PWggGGGdP",
        "PgGGGEGdP",
        "PGEGGGddP",
        "PGGGGddP.",
        ".PGGddP..",
        "..PP.PP.."],
    "4 Apfel (Farbe)": [
        "....T.VV.",
        "....TVV..",
        ".OOOTOOO.",
        "OWLLFFFDO",
        "OLFFFFFDO",
        "OFFFFFDDO",
        "OFFFFDDO.",
        ".OFFDDO..",
        "..OO.OO.."],
}


def cmap(t):
    return {
        "O": t["icon_line"], "F": t["icon"], "L": t["icon_light"], "D": t["icon_dark"], "W": "#FFFFFF",
        "N": t["nebula"][2], "P": t["icon"], "S": "#FFFFFF", "B": t["bone"],
        "G": "#F5C518", "g": "#FFF08A", "d": "#B07A0A", "T": "#6B4A1E", "V": "#3FBF4A",
        "E": t["icon_light"],
    }


def is_edge(shape, x, y):
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if not (0 <= nx < 9 and 0 <= ny < 9) or shape[ny][nx] == ".":
            return True
    return False


def draw(shape, t, part="full", split=4):
    cm = cmap(t)
    img = Image.new("RGBA", (9, 9))
    for y, row in enumerate(shape):
        for x, c in enumerate(row):
            if c == "." or c in "TVE" and part in ("empty", "half_r"):
                continue
            col = cm[c]
            if part == "empty" or (part == "half_r" and x > split):
                col = t["icon_line"] if is_edge(shape, x, y) else t["empty"]
            if part == "half" and x > split:
                continue
            img.putpixel((x, y), hexc(col))
    return img


def world_bg(w, h, scale):
    """Spielwelt-aehnlicher Hintergrund (Stein, Holz, Wasser), damit man die Durchsicht sieht."""
    rng = np.random.default_rng(5)
    b = 16 * scale // 2
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    for by in range(0, h, b):
        for bx in range(0, w, b):
            if bx > w * 0.72:
                base = (140, 98, 55)
            elif bx > w * 0.55 and by > h * 0.3:
                base = (40, 70, 170)
            else:
                base = (110, 110, 112)
            for py in range(0, b, scale * 2):
                for px in range(0, b, scale * 2):
                    f = 0.75 + rng.random() * 0.4
                    d.rectangle((bx + px, by + py, bx + px + scale * 2 - 1, by + py + scale * 2 - 1),
                                fill=tuple(int(c * f) for c in base) + (255,))
    return img


def label(img, x, y, text):
    d = ImageDraw.Draw(img)
    for dx, dy in ((1, 1),):
        d.text((x + dx, y + dy), text, fill=(0, 0, 0, 255))
    d.text((x, y), text, fill=(255, 255, 255, 255))


def catalog(theme="lila", scale=6):
    t = THEMES[theme]
    col_w = 300
    rows = [("HERZEN", HEARTS, "heart"), ("RUESTUNG", ARMOR, "armor"), ("HUNGER", FOOD, "food")]
    W = col_w * 5 + 20
    H = 40 + len(rows) * (9 * scale * 2 + 70)
    img = Image.new("RGBA", (W, H), hexc("#2A2A30"))
    y = 10
    for title, designs, kind in rows:
        label(img, 10, y, title)
        y += 22
        for i, (name, shape) in enumerate(designs.items()):
            x = 10 + i * col_w
            label(img, x, y, name)
            yy = y + 18
            if kind == "heart":
                seq = [("c", "full")] * 3 + [("c", "half"), ("c", None)]
            elif kind == "armor":
                seq = [(None, "full")] * 3 + [(None, "half_r"), (None, "empty")]
            else:
                seq = [("c", None), ("c", "half")] + [("c", "full")] * 3
            for j, (cont, part) in enumerate(seq):
                px = x + j * 8 * scale
                if cont:
                    e = draw(shape, t, "empty").resize((9 * scale, 9 * scale), Image.NEAREST)
                    img.alpha_composite(e, (px, yy))
                if part:
                    s = draw(shape, t, part, split=3 if kind == "armor" else 4)
                    img.alpha_composite(s.resize((9 * scale, 9 * scale), Image.NEAREST), (px, yy))
        y += 9 * scale * 2 + 30
    return img


def hotbar_preview(theme="lila", scale=4):
    t = THEMES[theme]
    bar, sel = hotbar(t)
    xb, xprog = xp(t)
    W, H = 182 * scale + 80, 40 * scale
    bg = world_bg(W, H, scale)
    ox, oy = 40, H - 24 * scale

    def put(im, x, y, s):
        bg.alpha_composite(im.resize((int(im.width * s), int(im.height * s)), Image.NEAREST), (int(x), int(y)))
    put(bar, ox, oy + scale, scale / R)
    put(sel, ox + 59 * scale, oy, scale / R)
    put(xb, ox, oy - 6 * scale, scale)
    put(xprog.crop((0, 0, 75, 5)), ox, oy - 6 * scale, scale)
    label(bg, 8, 6, f"Hotbar durchsichtig ({theme})")
    return bg


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    previews = [hotbar_preview("lila"), hotbar_preview("schwarz-weiss")]
    cat = catalog("lila")
    W = max(cat.width, previews[0].width)
    sheet = Image.new("RGBA", (W, sum(p.height for p in previews) + cat.height + 20), hexc("#1A1A1F"))
    y = 0
    for p in previews:
        sheet.alpha_composite(p, (0, y))
        y += p.height + 10
    sheet.alpha_composite(cat, (0, y))
    sheet.convert("RGB").save(OUT / "design_auswahl.png")
    print("ok")
