@echo off
cd /d "%~dp0"
findstr /c:"eula=true" eula.txt >nul 2>&1
if not errorlevel 1 goto start
echo Bitte lies die Minecraft-EULA: https://aka.ms/MinecraftEULA
set /p ANTWORT=Akzeptierst du die EULA? (ja/nein) 
if /i not "%ANTWORT%"=="ja" goto end
echo eula=true> eula.txt
:start
java -Xms2G -Xmx6G -jar fabric-server-launch.jar nogui
:end
pause
