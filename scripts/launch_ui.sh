#!/bin/bash
# TTS Voice Cloning - Interface Web

echo ""
echo "====================================="
echo "  TTS Voice Cloning - Interface Web"
echo "====================================="
echo ""
echo "Lancement de l'interface Ultra Pro"
echo "(Dialogues multi-voix et paramètres avancés)"
echo ""

# Obtenir le répertoire du projet (dossier parent de scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "[INFO] Répertoire du projet : $PWD"
echo ""

# Chercher Python dans l'ordre : venv local, système
echo "[ETAPE 1/3] Recherche de Python..."

# 1. Essayer l'environnement virtuel local
if [ -f "venv/bin/python" ]; then
    echo "[OK] Environnement virtuel détecté"
    source venv/bin/activate
elif command -v python3 &> /dev/null; then
    echo "[OK] Python système détecté"
else
    echo "[ERREUR] Python introuvable. Veuillez lancer setup.sh d'abord."
    exit 1
fi

echo ""
echo "[ETAPE 2/3] Vérification de l'installation..."
python --version

# Vérifier si les dépendances sont installées
python -c "import gradio, TTS" &> /dev/null
if [ $? -ne 0 ]; then
    echo "[ATTENTION] Dépendances manquantes. Lancez setup.sh pour installer."
    echo "            Tentative de lancement quand même..."
fi

echo ""
echo "[ETAPE 3/3] Démarrage de l'interface..."
echo ""
echo "================================"
echo "  Interface en cours d'exécution"
echo "  URL: http://localhost:7860"
echo "  Arrêt: Ctrl+C"
echo "================================"
echo ""

python src/webui_ultra_pro.py

echo ""
echo "[INFO] Interface arrêtée"
