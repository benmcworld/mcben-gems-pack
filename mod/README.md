# McBen Cosmetics (Fabric-Mod)

Eigene Cosmetics für **Minecraft Java 26.3** mit **Fabric**. Läuft nur bei dir (clientseitig), auf jedem Server.

| Cosmetic | Was es macht |
|---|---|
| **Flügel** | Runde 3D-Federflügel aus Blender: *Galaxie-Federn* (in 6 Farben) oder *Engel*. Leuchtende Spitzen, Flügelschlag. |
| **Heiligenschein** | Leuchtender Ring über dem Kopf, schwebt und dreht sich langsam. |
| **Mods** | Fullbright (G), Zoom (C halten, Stärke einstellbar), Auto-Sprint, Low Fire und Low Shield mit Höhen-Regler, Item-Zähler, Todespunkt merken. |
| **HUD (20 Anzeigen)** | FPS, Ping, Koordinaten, Richtung, Uhrzeit, MC-Zeit + Tag, letzter Tod, Keystrokes, Effekte, Rüstung, Totems + Pops, Gegner-HP, CPS, Reach, Combo, Tempo, Biom, Lichtlevel, Nether-XZ, RAM. Jede einzeln an/aus. |
| **HUD-Editor** | Jede Anzeige mit der Maus **verschieben**, mit dem Mausrad **größer/kleiner**, Rechtsklick = an/aus. Pro Anzeige: Größe, Hintergrund 0–100 % (0 % = nur die Zahlen), Textschatten, Beschriftung, eigene Farbe. |
| **Design** | Schriftart (Minecraft, Clean, Clean Bold, Mono, Uniform), Akzentfarbe, Kästchen-Stil (Streifen, Rahmen, Unterstrich, Schlicht). |
| **Totem-Minimods** | *Totem vorne halten* (Abstand und Größe einstellbar). *Pop-Umriss*: Beim Totem-Pop bleibt kurz ein flackernder, leuchtender Umriss stehen (bei dir und bei Gegnern, Farbe und Dauer einstellbar). *Pop-Nachricht* mit Pop-Zähler. |
| **Plushie-Totem** | Das Totem der Unsterblichkeit wird ein rundes 3D-Plushie mit **deinem eigenen Skin** (oder dem Skin eines Spielernamens, den du einträgst). Im Inventar, in der Hand und beim Auslösen. |

## Installation

1. [Fabric Loader](https://fabricmc.net/use/) für Minecraft **26.3** installieren (bzw. im NoRisk Client ein Fabric-Profil benutzen).
2. **Fabric API** für 26.3 herunterladen (Modrinth/CurseForge).
3. `mcben-cosmetics-x.y.z.jar` und die Fabric API in den `mods`-Ordner legen.
4. Spiel starten.

## Bedienen

- **Taste K** öffnet das McBen-Menü mit den Tabs **Cosmetics, Mods, HUD, Totem, Design** (Tasten änderbar unter *Optionen → Steuerung*).
- Im Tab **HUD** → *HUD-Editor öffnen*: Anzeigen ziehen, Mausrad für die Größe, anklicken für alle Einstellungen. Shift gedrückt halten = ohne Einrasten verschieben.
- Bei Auswahl-Feldern (‹ … ›) blättert Linksklick vor und Rechtsklick zurück.
- **G** schaltet Fullbright, **C** gedrückt halten zoomt.
- **F5** drücken, um dich selbst von außen zu sehen.
- Die Auswahl wird in `config/mcbencosmetics.json` gespeichert. Dort steht auch `plushieName`
  (leer = dein eigener Skin, sonst z. B. ein anderer Spielername).

## Wichtig zu wissen

- Andere Spieler sehen deine Cosmetics nur, wenn sie die Mod auch haben **und** es einen gemeinsamen Server-Dienst gibt (gibt es noch nicht). Im Moment siehst nur **du** sie.
- Leuchten wird ohne Shader nicht „verschwommen“ wie in den Renderbildern, die Teile leuchten aber im Dunkeln.

## Selbst bauen

```bash
# Java 25 + Gradle 9.8
gradle build              # Mod-Datei in build/libs/
gradle runClientGameTest  # startet Minecraft automatisch und macht Test-Screenshots
```

Die Schriften Clean/Mono sind DejaVu Sans (freie Lizenz, siehe `assets/mcbencosmetics/font/dejavu_license.txt`).

Die Modelle kommen aus Blender (`drafts/blender/export_wing.py`), die Texturen aus `drafts/blender/make_textures.py`.
