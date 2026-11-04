# MCBen Gems Resource Pack

Resource Packs für Minecraft **Java Edition 1.20.2 und neuer** (läuft auch im NoRisk Client).

![Vorschau](preview.png)

## Download

Die fertigen Packs liegen in [`dist/`](dist/).

| Pack | Was es macht |
|------|--------------|
| `McBen-HUD-Lila.zip` / `-Schwarz-Weiss` / `-Blau` / `-Rot` / `-Gruen` | Galaxy-HUD: Hotbar (Verlauf, halb durchsichtig), leuchtende Auswahl, runde Herzen, Schild-Rüstung, Äpfel als Hunger, XP-Leiste. **Nur eine Farbe gleichzeitig aktivieren.** |
| `McBen-LowFire.zip` | Feuer nur noch ~6/16 hoch |
| `McBen-LowShield.zip` | Schild sitzt in der 1st-Person tiefer |

Das HUD-Pack ändert auch die Herzen für Gift, Wither, Frost, Absorption, Hardcore und Reittiere, und die grünen Äpfel beim Hunger-Effekt.

## Installation

1. Minecraft → **Optionen → Ressourcenpakete → „Pack-Ordner öffnen“**.
2. Die `.zip`-Dateien **ungeöffnet** in den Ordner ziehen.
3. Im Spiel nach rechts schieben → Fertig. Farbe wechseln = anderes HUD-Pack aktivieren.

## Selbst anpassen

- Farben der Themes: `drafts/hud_galaxy.py` → `THEMES`
- Welche Designs benutzt werden: `drafts/hud_pack.py` → `CHOICE`
- Low Fire / Low Shield: `config.json`

Danach `pip install pillow numpy` und `python3 build.py` – die Zips landen in `dist/`.
Die Entwurfs-Bilder (alle Design-Varianten) liegen in `drafts/hud/`.
