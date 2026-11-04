#!/usr/bin/env python3
"""
McBen Plushie-Totem: macht aus deinem Minecraft-Skin ein 3D-Plushie, das das Totem ersetzt.

    python plush_totem.py                 -> laedt den Skin von "Ben1G" und baut das Pack
    python plush_totem.py --name Anderer  -> anderer Spielername
    python plush_totem.py --skin skin.png -> eigene Skin-Datei statt Download

Ergebnis: McBen-Plushie-Totem.zip (in den resourcepacks-Ordner legen).
Skin gewechselt? Einfach nochmal starten.  Benoetigt: Python 3 (keine Extra-Pakete).
Minecraft 1.21.4 oder neuer.
"""
import argparse
import base64
import io
import json
import struct
import urllib.request
import zipfile
import zlib
from pathlib import Path

DEFAULT_NAME = "Ben1G"
HERE = Path(__file__).resolve().parent

# --------------------------------------------------------------------------- #
# Skin laden (Mojang-API)
# --------------------------------------------------------------------------- #
def fetch_skin(name):
    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": "mcben-plushie-totem"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read()
    prof = json.loads(get(f"https://api.mojang.com/users/profiles/minecraft/{name}"))
    data = json.loads(get(f"https://sessionserver.mojang.com/session/minecraft/profile/{prof['id']}"))
    tex = next(p for p in data["properties"] if p["name"] == "textures")
    info = json.loads(base64.b64decode(tex["value"]))
    skin = info["textures"]["SKIN"]
    slim = skin.get("metadata", {}).get("model") == "slim"
    return get(skin["url"]), slim


def png_size(png):
    w, h = struct.unpack(">II", png[16:24])
    return w, h


# --------------------------------------------------------------------------- #
# Plushie-Modell (Koordinaten 0-16, Skin 64x64 -> UV-Faktor 0.25)
# --------------------------------------------------------------------------- #
K = 16 / 64


def faces(u, v, w, h, d):
    """Skin-Box (u,v, Breite w, Hoehe h, Tiefe d) -> UV pro Seite. Vorderseite = south."""
    r = lambda a, b, c, e: [a * K, b * K, c * K, e * K]
    return {
        "up":    {"uv": r(u + d, v, u + d + w, v + d)},
        "down":  {"uv": r(u + d + w, v + d, u + d + 2 * w, v)},
        "west":  {"uv": r(u, v + d, u + d, v + d + h)},
        "south": {"uv": r(u + d, v + d, u + d + w, v + d + h)},
        "east":  {"uv": r(u + d + w, v + d, u + 2 * d + w, v + d + h)},
        "north": {"uv": r(u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h)},
    }


def el(frm, to, skinbox, inflate=0.0, rot=None):
    f = {k: {**v, "texture": "#skin"} for k, v in faces(*skinbox).items()}
    e = {"from": [frm[0] - inflate, frm[1] - inflate, frm[2] - inflate],
         "to": [to[0] + inflate, to[1] + inflate, to[2] + inflate], "faces": f}
    if rot:
        e["rotation"] = rot
    return e


def plush_model(slim=False):
    aw = 3 if slim else 4          # Armbreite im Skin
    head = ((4, 7.5, 4), (12, 15.5, 12))
    body = ((5, 2.5, 6.5), (11, 7.5, 9.5))
    rarm = ((3, 3, 7), (5, 7.5, 9))
    larm = ((11, 3, 7), (13, 7.5, 9))
    rleg = ((5, 0, 6.5), (8, 2.5, 9.5))
    lleg = ((8, 0, 6.5), (11, 2.5, 9.5))
    rrot = {"angle": -22.5, "axis": "z", "origin": [5, 7.5, 8]}
    lrot = {"angle": 22.5, "axis": "z", "origin": [11, 7.5, 8]}
    els = [
        el(*head, (0, 0, 8, 8, 8)),
        el(*head, (32, 0, 8, 8, 8), .5),                  # Hut-Ebene
        el(*body, (16, 16, 8, 12, 4)),
        el(*body, (16, 32, 8, 12, 4), .25),               # Jacke
        el(*rarm, (40, 16, aw, 12, 4), rot=rrot),
        el(*rarm, (40, 32, aw, 12, 4), .25, rrot),        # Aermel
        el(*larm, (32, 48, aw, 12, 4), rot=lrot),
        el(*larm, (48, 48, aw, 12, 4), .25, lrot),
        el(*rleg, (0, 16, 4, 12, 4)),
        el(*rleg, (0, 32, 4, 12, 4), .25),                # Hose
        el(*lleg, (16, 48, 4, 12, 4)),
        el(*lleg, (0, 48, 4, 12, 4), .25),
    ]
    return {
        "textures": {"skin": "minecraft:item/mcben_plush_skin", "particle": "minecraft:item/mcben_plush_skin"},
        "elements": els,
        "display": {
            "gui": {"rotation": [12, -25, 0], "translation": [0, 0, 0], "scale": [0.95, 0.95, 0.95]},
            "fixed": {"rotation": [0, 180, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]},
            "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
            "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
            "thirdperson_righthand": {"rotation": [0, 180, 0], "translation": [0, 3, 1], "scale": [0.55, 0.55, 0.55]},
            "thirdperson_lefthand": {"rotation": [0, 180, 0], "translation": [0, 3, 1], "scale": [0.55, 0.55, 0.55]},
            "firstperson_righthand": {"rotation": [0, 160, 0], "translation": [1, 3, 1], "scale": [0.6, 0.6, 0.6]},
            "firstperson_lefthand": {"rotation": [0, 200, 0], "translation": [1, 3, 1], "scale": [0.6, 0.6, 0.6]},
        },
    }


# --------------------------------------------------------------------------- #
# Pack bauen
# --------------------------------------------------------------------------- #
def build_pack(skin_png, slim, out):
    if png_size(skin_png) != (64, 64):
        raise SystemExit("Der Skin muss 64x64 Pixel gross sein (alte 64x32-Skins gehen nicht).")
    mc = "assets/minecraft/"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pack.mcmeta", json.dumps({"pack": {
            "description": "§dMcBen §fPlushie-Totem §7- dein Skin als 3D-Totem",
            "pack_format": 46, "supported_formats": [46, 999], "min_format": 46, "max_format": 999}}, indent=2))
        z.writestr(mc + "items/totem_of_undying.json", json.dumps(
            {"model": {"type": "minecraft:model", "model": "minecraft:item/mcben_plush"}}, indent=2))
        z.writestr(mc + "models/item/mcben_plush.json", json.dumps(plush_model(slim), indent=2))
        z.writestr(mc + "textures/item/mcben_plush_skin.png", skin_png)
        z.writestr("pack.png", skin_png)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default=DEFAULT_NAME)
    ap.add_argument("--skin", help="lokale Skin-Datei (PNG 64x64) statt Download")
    ap.add_argument("--slim", action="store_true", help="duenne Arme (nur zusammen mit --skin noetig)")
    ap.add_argument("--out", default=str(HERE / "McBen-Plushie-Totem.zip"))
    a = ap.parse_args()
    if a.skin:
        skin, slim = Path(a.skin).read_bytes(), a.slim
    else:
        print(f"Lade Skin von {a.name} ...")
        skin, slim = fetch_skin(a.name)
    out = build_pack(skin, slim, a.out)
    print(f"Fertig: {out}  ({'duenne' if slim else 'normale'} Arme)")
    print("-> In den resourcepacks-Ordner legen und im Spiel aktivieren.")


if __name__ == "__main__":
    main()
