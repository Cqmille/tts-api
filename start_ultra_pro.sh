#!/bin/bash
# TTS Ultra Pro - Script de lancement

echo "🎬 Démarrage de TTS Ultra Pro..."
echo "================================"

# Activer l'environnement virtuel si disponible
if [ -d "venv" ]; then
    echo "📦 Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

# Lancer l'interface
echo "🚀 Lancement de l'interface..."
python src/webui_ultra_pro.py
