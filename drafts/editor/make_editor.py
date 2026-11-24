"""Baut den McBen Pack-Editor (eine HTML-Seite mit eingebetteten Pack-Bildern)."""
import base64, io, json, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "drafts/editor/editor.html"
THEMES = {"Lila": "McBen-HUD-Lila", "Schwarz-Weiß": "McBen-HUD-Schwarz-Weiss", "Blau": "McBen-HUD-Blau",
          "Rot": "McBen-HUD-Rot", "Grün": "McBen-HUD-Gruen"}
SPRITES = ["hotbar", "hotbar_selection", "experience_bar_background", "experience_bar_progress",
           "armor_full", "armor_half", "armor_empty", "food_full", "food_half", "food_empty",
           "food_full_hunger", "food_half_hunger", "food_empty_hunger",
           "heart/container", "heart/full", "heart/half", "heart/poisoned_full", "heart/poisoned_half",
           "heart/withered_full", "heart/withered_half", "heart/frozen_full", "heart/frozen_half",
           "heart/absorbing_full", "heart/absorbing_half", "heart/hardcore_full", "heart/hardcore_half"]

def uri(img_or_path, fmt="PNG", quality=None):
    im = Image.open(img_or_path) if not isinstance(img_or_path, Image.Image) else img_or_path
    b = io.BytesIO()
    if fmt == "JPEG":
        im.convert("RGB").save(b, "JPEG", quality=quality or 82)
        return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()

packs = {}
for name, folder in THEMES.items():
    base = ROOT / "build" / folder / "assets/minecraft/textures/gui/sprites/hud"
    packs[name] = {s: uri(base / f"{s}.png") for s in SPRITES}

shots = ROOT / "mod/build/run/clientGameTest/screenshots"
# Hintergrund: Ich-Perspektive (Himmel + Gras), untere HUD-Zone mit Gras aufgefuellt
bg = Image.open(sorted(shots.glob("*6_plushie_ich*.png"))[0]).convert("RGB")
w, h = bg.size
top = bg.crop((0, 0, w, int(h * .62)))
grass = bg.crop((0, int(h * .42), int(w * .45), int(h * .62))).resize((w, h - top.height))
canvas = Image.new("RGB", (w, h)); canvas.paste(top, (0, 0)); canvas.paste(grass, (0, top.height))
background = uri(canvas, "JPEG", 85)

gallery = []
for pat, cap in [("*1_galaxie_lila_hinten*", "Galaxie-Flügel Lila, von hinten"), ("*1_galaxie_lila_vorne*", "Galaxie-Flügel Lila, von vorne"),
                 ("*2_engel_heiligenschein_vorne*", "Engel-Flügel + Heiligenschein"), ("*3_galaxie_gruen_hinten*", "Galaxie Grün + Heiligenschein"),
                 ("*4_galaxie_dark_vorne*", "Dark Edition"), ("*7_plushie_inventar*", "Plushie-Totem im Inventar"),
                 ("*6_plushie_ich*", "Plushie in der Hand"), ("*8_plushie_ausloesen*", "Plushie beim Auslösen"), ("*9_menue*", "Menü mit Taste K")]:
    f = sorted(shots.glob(pat + ".png"))
    if f:
        gallery.append({"src": uri(Image.open(f[0]).convert("RGB").resize((640, 360)), "JPEG", 80), "cap": cap})

tpl = (Path(__file__).parent / "editor_template.html").read_text(encoding="utf-8")
html = tpl.replace("/*__DATA__*/", "const PACKS = " + json.dumps(packs) + ";\nconst BG = " + json.dumps(background) +
                   ";\nconst GALLERY = " + json.dumps(gallery) + ";")
OUT.write_text(html, encoding="utf-8")
print("ok", OUT, round(len(html) / 1e6, 2), "MB")
