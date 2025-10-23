#!/bin/bash
# TTS API Server

echo ""
echo "================================"
echo "  TTS API Server - Démarrage"
echo "================================"
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
python -c "import flask, TTS" &> /dev/null
if [ $? -ne 0 ]; then
    echo "[ATTENTION] Dépendances manquantes. Lancez setup.sh pour installer."
    echo "            Tentative de lancement quand même..."
fi

echo ""
echo "[ETAPE 3/3] Démarrage de l'API TTS..."
echo ""
echo "================================"
echo "  API en cours d'exécution"
echo "  URL: http://localhost:5002"
echo "  Arrêt: Ctrl+C"
echo "================================"
echo ""

python src/tts_api.py

echo ""
echo "[INFO] API arrêtée"
