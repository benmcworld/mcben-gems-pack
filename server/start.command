#!/bin/bash
# McBen Server starten (Mac): Doppelklick auf diese Datei.
cd "$(dirname "$0")"

# Java 25 pruefen
JAVA_BIN="java"
if [ -x "/Library/Java/JavaVirtualMachines/temurin-25.jdk/Contents/Home/bin/java" ]; then
  JAVA_BIN="/Library/Java/JavaVirtualMachines/temurin-25.jdk/Contents/Home/bin/java"
fi
JV=$("$JAVA_BIN" -version 2>&1 | head -1 | sed -E 's/.*version "([0-9]+).*/\1/')
if [ -z "$JV" ] || [ "$JV" -lt 25 ] 2>/dev/null; then
  echo "Du brauchst Java 25. Lade es hier herunter (macOS, .pkg): https://adoptium.net/temurin/releases/?version=25"
  echo "Danach diese Datei nochmal starten."
  read -n 1 -s -r -p "Taste druecken zum Schliessen ..."
  exit 1
fi

# Minecraft-EULA (muss der Server-Besitzer selbst bestaetigen)
if ! grep -q "eula=true" eula.txt 2>/dev/null; then
  echo "Bitte lies die Minecraft-EULA: https://aka.ms/MinecraftEULA"
  read -r -p "Akzeptierst du die EULA? (ja/nein) " ANTWORT
  if [ "$ANTWORT" = "ja" ]; then echo "eula=true" > eula.txt; else echo "Ohne EULA kann der Server nicht starten."; exit 1; fi
fi

echo "McBen Server startet ... (Stoppen: im Fenster 'stop' eingeben)"
"$JAVA_BIN" -Xms2G -Xmx6G -jar fabric-server-launch.jar nogui
