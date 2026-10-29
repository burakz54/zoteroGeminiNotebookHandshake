#!/bin/bash
clear

# Ermittelt das Verzeichnis, in dem dieses .command-Skript liegt
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=================================================="
echo "   ZOTERO AUTO-HIGHLIGHTER (Zwischenablage)       "
echo "=================================================="
echo ""

# Führt das Skript relativ zum aktuellen Ordner aus
python3 "$DIR/1_clipboard_highlighter.py"

echo ""
echo "--------------------------------------------------"
read -p "Drücke ENTER zum Schließen dieses Fensters..."

