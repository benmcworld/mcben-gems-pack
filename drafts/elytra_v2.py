"""Elytra v2: Galaxy-Vogelfluegel (wie Totem v3) als ausgeschnittene Elytra-Textur."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent))
from hud_galaxy import THEMES, hexc
from totems_v3 import bird_wing, S, PX
from capes_wings import assemble, m_nebel, bg, label, SCALE

OUT = Path(__file__).parent / "hud"


def wing_face(t, seed, span_px=330, lift=.9):
    """Rechter Fluegel, um 90 Grad gedreht (haengt nach unten) -> 10x20-Flaeche (4x = 40x80)."""
    big = Image.new("RGBA", (S, S))
    big.alpha_composite(bird_wing(t, (40, S * .45), span_px, 1, seed, lift))
    big = big.rotate(-90, expand=True)                 # Spannweite zeigt jetzt nach unten
    bbox = big.getbbox()
    big = big.crop(bbox)
    face = big.resize((10 * SCALE, 20 * SCALE), Image.LANCZOS)
    a = face.split()[3].point(lambda v: 0 if v < 90 else 255)
    face.putalpha(a)
    return face


def build(t, seed):
    tex = assemble(t, m_nebel, "galaxie", seed)       # Cape-Teil + Grundgeruest
    s = SCALE
    face = wing_face(t, seed)
    tex.paste(Image.new("RGBA", (10 * s, 20 * s)), (24 * s, 2 * s))
    tex.paste(Image.new("RGBA", (10 * s, 20 * s)), (36 * s, 2 * s))
    tex.alpha_composite(face, (24 * s, 2 * s))
    tex.alpha_composite(face.transpose(Image.FLIP_LEFT_RIGHT), (36 * s, 2 * s))
    return tex


def pair_view(tex, big=4, spread=28):
    s = SCALE
    f = tex.crop((24 * s, 2 * s, 34 * s, 22 * s)).resize((10 * s * big, 20 * s * big), Image.NEAREST)
    left = f.transpose(Image.FLIP_LEFT_RIGHT).rotate(-spread, expand=True, resample=Image.NEAREST)
    right = f.rotate(spread, expand=True, resample=Image.NEAREST)
    out = Image.new("RGBA", (left.width + right.width - 40, max(left.height, right.height)))
    out.alpha_composite(left, (0, 0))
    out.alpha_composite(right, (left.width - 40, 0))
    return out


if __name__ == "__main__":
    tiles = []
    for i, th in enumerate(["lila", "schwarz-weiss", "blau"]):
        t = THEMES[th]
        tex = build(t, 700 + i)
        tex.save(OUT / f"elytra2_{th}.png")
        v = pair_view(tex)
        tile = bg(v.width + 40, v.height + 50, t)
        tile.alpha_composite(v, (20, 36))
        label(tile, 8, 8, f"Galaxie-Federfluegel ({th})")
        tiles.append(tile)
    w = sum(t.width for t in tiles) + 6 * (len(tiles) + 1)
    h = max(t.height for t in tiles) + 12
    sheet = Image.new("RGBA", (w, h), hexc("#0C0A10"))
    x = 6
    for tl in tiles:
        sheet.alpha_composite(tl, (x, 6))
        x += tl.width + 6
    sheet.convert("RGB").save(OUT / "fluegel_entwurf_v2.png")
    print("ok")
