"""Entwuerfe: verschiedene Hotbar-Hintergruende (mit Herzen 5, Aepfeln 4, Schild 1)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, str(Path(__file__).parent))
from hud_galaxy import THEMES, hexc, nebula
from selection_styles import hud_mock, s_gefuellt, SHIELDS, grid
from galaxy import fbm

OUT = Path(__file__).parent / "hud"


def rgb(c):
    return np.array(hexc(c)[:3], np.float32)


def to_img(arr, alpha):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    al = Image.fromarray(np.clip(alpha, 0, 255).astype(np.uint8), "L")
    return im, al


def bg_dunkler_nebel(W, H, t):
    rng = np.random.default_rng(8)
    n = fbm(W, H, rng, base=W // 5)
    s = fbm(W, H, rng, base=W // 12)
    v = np.clip((n * .6 + s * .4 - .35) * 2.2, 0, 1) ** 1.5
    a, b, c = rgb(t["nebula"][0]), rgb(t["nebula"][2]), rgb(t["icon"])
    col = a[None, None] * (1 - v[..., None]) + b[None, None] * v[..., None]
    streak = np.clip((s - .62) * 6, 0, 1)[..., None]
    col = col * (1 - streak * .6) + c[None, None] * streak * .6
    return to_img(col, 175 + v * 50)


def bg_glas(W, H, t):
    y = np.linspace(0, 1, H)[:, None, None]
    base = rgb(t["nebula"][1])[None, None]
    col = np.repeat(base * (1.3 - .5 * y), W, axis=1)
    col[: H // 3] += 25
    alpha = np.full((H, W), 115.0)
    alpha[: H // 3] = 140
    return to_img(col, alpha)


def bg_verlauf(W, H, t):
    x = np.linspace(0, 1, W)[None, :, None]
    y = np.linspace(0, 1, H)[:, None, None]
    a, b = rgb(t["nebula"][1]), rgb(t["icon_dark"])
    m = np.abs(np.sin(np.pi * x))
    col = a * (1 - m) + b * m
    col = col * (1.15 - .4 * y)
    return to_img(np.broadcast_to(col, (H, W, 3)).copy(), np.full((H, W), 165.0))


def bg_sterne(W, H, t):
    rng = np.random.default_rng(3)
    col = np.broadcast_to(rgb(t["nebula"][0]), (H, W, 3)).copy()
    alpha = np.full((H, W), 150.0)
    for _ in range(int(W * H / 90)):
        x, y = rng.integers(0, W), rng.integers(0, H)
        c = rgb("#FFFFFF") if rng.random() < .6 else rgb(t["icon_light"])
        col[y, x] = c
        alpha[y, x] = 255
        if rng.random() < .12 and x + 1 < W and y + 1 < H:
            col[y:y + 2, x:x + 2] = c
            alpha[y:y + 2, x:x + 2] = 255
    return to_img(col, alpha)


def bg_wellen(W, H, t):
    x = np.linspace(0, 6 * np.pi, W)[None, :]
    y = np.linspace(0, 1, H)[:, None]
    w1 = np.exp(-((y - .45 - .18 * np.sin(x * .7)) ** 2) / .012)
    w2 = np.exp(-((y - .7 - .12 * np.sin(x * 1.1 + 2)) ** 2) / .008)
    base = rgb(t["nebula"][0])
    col = base + (rgb(t["icon_dark"]) - base) * w1[..., None] + (rgb(t["icon"]) - base) * (w2[..., None] * .7)
    return to_img(col, 140 + 80 * np.maximum(w1, w2))


def bg_kristall(W, H, t):
    yy, xx = np.mgrid[0:H, 0:W]
    k = 12
    lat = (((xx + yy) % k) < 1) | (((xx - yy) % k) < 1)
    base = rgb(t["nebula"][1])
    col = np.broadcast_to(base, (H, W, 3)).copy()
    # Facetten: jede Raute leicht unterschiedlich hell
    cell = ((xx + yy) // k + (xx - yy) // k) % 3
    col *= (0.85 + 0.15 * cell)[..., None]
    col[lat] = rgb(t["icon_dark"])
    alpha = np.where(lat, 210, 150).astype(np.float32)
    return to_img(col, alpha)


def bg_unsichtbar(W, H, t):
    return to_img(np.broadcast_to(rgb(t["nebula"][0]), (H, W, 3)).copy(), np.full((H, W), 55.0))


BGS = {
    "1 Nebel (bisher)": None,
    "2 Dunkler Nebel": bg_dunkler_nebel,
    "3 Glas": bg_glas,
    "4 Verlauf": bg_verlauf,
    "5 Sternenhimmel": bg_sterne,
    "6 Wellen": bg_wellen,
    "7 Kristall-Muster": bg_kristall,
    "8 Fast unsichtbar": bg_unsichtbar,
}

if __name__ == "__main__":
    t = THEMES[sys.argv[1] if len(sys.argv) > 1 else "lila"]
    imgs = [hud_mock(t, s_gefuellt(t), SHIELDS["1 Schild (bisher)"], title=n, bg=fn) for n, fn in BGS.items()]
    grid(imgs, 2).convert("RGB").save(OUT / "hotbar_hintergruende.png")
    print("ok")
