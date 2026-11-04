"""3D-Vorschau fuers Plushie-Totem: kleiner Software-Renderer fuer Minecraft-Item-Modelle."""
import io
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plushie"))
from plush_totem import plush_model

OUT = Path(__file__).parent / "hud"


def placeholder_skin():
    """Eigener Platzhalter-Skin (lila Hoodie, Galaxy-Stil) - kein Mojang-Skin."""
    s = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    skin, hair, hood, hood_d, pants, shoe = (233, 190, 160), (60, 38, 30), (120, 50, 200), (70, 25, 130), (40, 30, 70), (25, 20, 35)
    d.rectangle((0, 0, 31, 15), fill=hair)                 # Kopf ringsum Haare
    d.rectangle((8, 8, 15, 15), fill=skin)                 # Gesicht
    d.rectangle((8, 8, 15, 9), fill=hair)                  # Pony
    for x in (9, 13):
        d.rectangle((x, 11, x + 1, 12), fill=(255, 255, 255))
        d.point((x + 1, 12), fill=(150, 60, 255))
    d.rectangle((11, 14, 12, 14), fill=(170, 100, 90))
    d.rectangle((0, 10, 7, 15), fill=skin)
    d.rectangle((16, 10, 23, 15), fill=skin)
    d.rectangle((0, 8, 7, 9), fill=hair)
    d.rectangle((16, 8, 23, 9), fill=hair)
    d.rectangle((16, 16, 39, 31), fill=hood)               # Koerper
    d.rectangle((20, 20, 27, 22), fill=hood_d)
    d.rectangle((23, 23, 24, 26), fill=(240, 200, 255))    # Stern-Logo
    d.rectangle((21, 24, 26, 25), fill=(240, 200, 255))
    d.rectangle((40, 16, 55, 31), fill=hood)               # rechter Arm
    d.rectangle((40, 29, 55, 31), fill=skin)
    d.rectangle((32, 48, 47, 63), fill=hood)               # linker Arm
    d.rectangle((32, 61, 47, 63), fill=skin)
    d.rectangle((0, 16, 15, 31), fill=pants)               # Beine
    d.rectangle((0, 29, 15, 31), fill=shoe)
    d.rectangle((16, 48, 31, 63), fill=pants)
    d.rectangle((16, 61, 31, 63), fill=shoe)
    return s


FACE_CORNERS = {  # (oben-links, oben-rechts, unten-links) wie Minecraft die UV legt
    "south": lambda a, b: ((a[0], b[1], b[2]), (b[0], b[1], b[2]), (a[0], a[1], b[2])),
    "north": lambda a, b: ((b[0], b[1], a[2]), (a[0], b[1], a[2]), (b[0], a[1], a[2])),
    "west":  lambda a, b: ((a[0], b[1], a[2]), (a[0], b[1], b[2]), (a[0], a[1], a[2])),
    "east":  lambda a, b: ((b[0], b[1], b[2]), (b[0], b[1], a[2]), (b[0], a[1], b[2])),
    "up":    lambda a, b: ((a[0], b[1], a[2]), (b[0], b[1], a[2]), (a[0], b[1], b[2])),
    "down":  lambda a, b: ((a[0], a[1], b[2]), (b[0], a[1], b[2]), (a[0], a[1], a[2])),
}
SHADE = {"up": 1.0, "down": .5, "north": .8, "south": .8, "east": .6, "west": .6}


def rot_matrix(axis, deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return {"x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]),
            "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
            "z": np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])}[axis]


def render(model, skin, yaw, pitch=15, size=360, unit=17):
    tex = np.array(skin.convert("RGBA"))
    TW, TH = tex.shape[1], tex.shape[0]
    view = rot_matrix("x", pitch) @ rot_matrix("y", yaw)
    polys = []
    for e in model["elements"]:
        a, b = np.array(e["from"], float), np.array(e["to"], float)
        er = e.get("rotation")
        for fname, f in e["faces"].items():
            pts = [np.array(p, float) for p in FACE_CORNERS[fname](a, b)]
            if er:
                o = np.array(er["origin"], float)
                R = rot_matrix(er["axis"], er["angle"])
                pts = [R @ (p - o) + o for p in pts]
            pts = [view @ (p - 8) for p in pts]
            ex, ey = pts[1] - pts[0], pts[2] - pts[0]
            n = np.cross(ey, ex)            # Normale (nach aussen)
            if n[2] <= 0:
                continue
            depth = (pts[0][2] + pts[1][2] + pts[2][2] + (pts[1] + ey)[2]) / 4
            polys.append((depth, pts, f["uv"], SHADE[fname]))
    img = np.zeros((size, size, 4), np.uint8)
    c = size / 2
    for depth, pts, uv, sh in sorted(polys, key=lambda p: p[0]):
        P = [(c + p[0] * unit, c - p[1] * unit) for p in pts]
        p0, ex, ey = np.array(P[0]), np.array(P[1]) - P[0], np.array(P[2]) - P[0]
        M = np.array([ex, ey]).T
        if abs(np.linalg.det(M)) < 1e-6:
            continue
        Mi = np.linalg.inv(M)
        allp = np.array(P + [tuple(np.array(P[1]) + ey)])
        x0, y0 = np.floor(allp.min(0)).astype(int)
        x1, y1 = np.ceil(allp.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size), min(y1, size)
        if x1 <= x0 or y1 <= y0:
            continue
        ys, xs = np.mgrid[y0:y1, x0:x1]
        q = np.stack([xs + .5 - p0[0], ys + .5 - p0[1]], -1) @ Mi.T
        inside = (q[..., 0] >= 0) & (q[..., 0] < 1) & (q[..., 1] >= 0) & (q[..., 1] < 1)
        u = uv[0] + q[..., 0] * (uv[2] - uv[0])
        v = uv[1] + q[..., 1] * (uv[3] - uv[1])
        tu = np.clip((u / 16 * TW).astype(int), 0, TW - 1)
        tv = np.clip((v / 16 * TH).astype(int), 0, TH - 1)
        col = tex[tv, tu]
        ok = inside & (col[..., 3] > 0)
        rgb = (col[..., :3] * sh).astype(np.uint8)
        region = img[y0:y1, x0:x1]
        region[ok, :3] = rgb[ok]
        region[ok, 3] = 255
    return Image.fromarray(img)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    skin = Image.open(sys.argv[1]).convert("RGBA") if len(sys.argv) > 1 else placeholder_skin()
    slim = len(sys.argv) > 2 and sys.argv[2] == "slim"
    model = plush_model(slim)
    views = [(-25, "vorne"), (-90, "links"), (155, "hinten"), (35, "schraeg")]
    tiles = []
    for yaw, name in views:
        r = render(model, skin, yaw)
        tile = Image.new("RGBA", r.size, (24, 14, 40, 255))
        tile.alpha_composite(r)
        ImageDraw.Draw(tile).text((8, 6), name, fill=(255, 255, 255, 255))
        tiles.append(tile)
    sk = skin.resize((256, 256), Image.NEAREST)
    st = Image.new("RGBA", (300, tiles[0].height), (24, 14, 40, 255))
    st.alpha_composite(sk, (22, 40))
    ImageDraw.Draw(st).text((8, 6), "Skin", fill=(255, 255, 255, 255))
    sheet = Image.new("RGBA", (sum(t.width for t in tiles) + st.width + 6 * 6, tiles[0].height + 12), (10, 8, 14, 255))
    x = 6
    for t in tiles + [st]:
        sheet.alpha_composite(t, (x, 6))
        x += t.width + 6
    sheet.convert("RGB").save(OUT / "plushie_vorschau.png")
    print("ok")
