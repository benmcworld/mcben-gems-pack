"""Baut die fertigen HUD-Texturen (alle Sprites, die Minecraft 1.20.2+ fuer das HUD benutzt).

Auswahl (vom User bestaetigt):
  Hotbar-Hintergrund 4 "Verlauf" | Auswahl-Rahmen 2 "Gefuellt + Glow"
  Herzen 5 "Rund" | Ruestung "1 Schild" | Hunger 4 "Apfel (Farbe)"
"""
import sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from hud_galaxy import THEMES, hotbar, xp
from icon_designs import HEARTS, FOOD, draw
from selection_styles import s_gefuellt, SHIELDS
from hotbar_backgrounds import bg_verlauf

CHOICE = {
    "background": bg_verlauf,
    "selection": s_gefuellt,
    "heart": HEARTS["5 Rund"],
    "armor": SHIELDS["1 Schild (bisher)"],
    "food": FOOD["4 Apfel (Farbe)"],
}

# Sonder-Farben fuer Herz-Zustaende (gelten fuer alle Themes)
STATUS = {
    "poisoned": dict(icon="#7BC23A", icon_light="#C6F28A", icon_dark="#3E6E16", icon_line="#122406"),
    "withered": dict(icon="#3A3A3A", icon_light="#7A7A7A", icon_dark="#1C1C1C", icon_line="#050505"),
    "absorbing": dict(icon="#F5C518", icon_light="#FFF08A", icon_dark="#B07A0A", icon_line="#2E1E02"),
    "frozen": dict(icon="#7FD4FF", icon_light="#E0F6FF", icon_dark="#3A86B8", icon_line="#0A2233"),
}
HUNGER = dict(icon="#7BA33A", icon_light="#B9D97A", icon_dark="#4A6620", icon_line="#122406")


def blink(t):
    """Blinkende Variante (beim Schaden): heller."""
    def lighten(c):
        c = c.lstrip("#")
        rgb = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
        return "#" + "".join(f"{int(v + (255 - v) * .45):02X}" for v in rgb)
    return {**t, **{k: lighten(t[k]) for k in ("icon", "icon_light", "icon_dark")}}


def hud_sprites(theme):
    """-> dict {Pfad relativ zu textures/gui/sprites/hud: Image}"""
    t = THEMES[theme]
    out = {}
    bar, _ = hotbar(t, CHOICE["background"])
    out["hotbar.png"] = bar
    out["hotbar_selection.png"] = CHOICE["selection"](t)
    xb, xprog = xp(t)
    out["experience_bar_background.png"] = xb
    out["experience_bar_progress.png"] = xprog

    heart = CHOICE["heart"]
    # Container
    for suffix, tt in (("", t), ("_blinking", blink(t))):
        out[f"heart/container{suffix}.png"] = draw(heart, tt, "empty")
        out[f"heart/container_hardcore{suffix}.png"] = draw(heart, tt, "empty")
        out[f"heart/vehicle_container{suffix}.png" if suffix == "" else "_skip"] = draw(heart, tt, "empty")
    out.pop("_skip", None)
    # Herzen fuer alle Zustaende
    kinds = {"": t, **{k: {**t, **v} for k, v in STATUS.items()}}
    for kind, tt in kinds.items():
        pre = f"{kind}_" if kind else ""
        for blink_sfx, tb in (("", tt), ("_blinking", blink(tt))):
            for hc in ("", "hardcore_"):
                out[f"heart/{pre}{hc}full{blink_sfx}.png"] = draw(heart, tb, "full")
                out[f"heart/{pre}{hc}half{blink_sfx}.png"] = draw(heart, tb, "half")
    out["heart/vehicle_full.png"] = draw(heart, t, "full")
    out["heart/vehicle_half.png"] = draw(heart, t, "half")

    # Ruestung
    armor = CHOICE["armor"]
    out["armor_full.png"] = draw(armor, t, "full", split=3)
    out["armor_half.png"] = draw(armor, t, "half_r", split=3)
    out["armor_empty.png"] = draw(armor, t, "empty", split=3)

    # Hunger (+ gruene Variante bei Hunger-Effekt)
    food = CHOICE["food"]
    th = {**t, **HUNGER}
    out["food_full.png"] = draw(food, t, "full")
    out["food_half.png"] = draw(food, t, "half")
    out["food_empty.png"] = draw(food, t, "empty")
    out["food_full_hunger.png"] = draw(food, th, "full")
    out["food_half_hunger.png"] = draw(food, th, "half")
    out["food_empty_hunger.png"] = draw(food, th, "empty")
    return out


def pack_icon(theme):
    """64x64 pack.png: Herz, Schild, Apfel auf Hotbar-Ausschnitt."""
    t = THEMES[theme]
    sp = hud_sprites(theme)
    icon = Image.new("RGBA", (64, 64), (12, 8, 20, 255))
    bar = sp["hotbar.png"].crop((0, 0, 64, 44))
    icon.alpha_composite(bar.resize((64, 44)), (0, 20))
    icon.alpha_composite(sp["hotbar_selection.png"].resize((24, 23)), (2, 31))
    for i, key in enumerate(("heart/full.png", "armor_full.png", "food_full.png")):
        icon.alpha_composite(sp[key].resize((18, 18), Image.NEAREST), (2 + i * 21, 1))
    return icon
