#!/bin/bash
# TTS API - Installation Automatique (Linux/macOS)

echo ""
echo "========================================"
echo "  TTS API - Installation Automatique"
echo "========================================"
echo ""
echo "Ce script va installer automatiquement :"
echo "  - Environnement virtuel Python"
echo "  - Toutes les dépendances"
echo ""
read -p "Appuyez sur Entrée pour continuer..."

# Obtenir le répertoire du script
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo "[INFO] Répertoire du projet : $PWD"
echo ""

# ================================
# ETAPE 1 : Vérifier Python
# ================================
echo "[ETAPE 1/5] Vérification de Python..."

if command -v python3 &> /dev/null; then
    echo "[OK] Python est installé"
    python3 --version
else
    echo "[ERREUR] Python 3 n'est pas installé"
    echo ""
    echo "Veuillez installer Python 3.10 ou supérieur :"
    echo "  - Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  - macOS: brew install python3"
    echo "  - Fedora: sudo dnf install python3 python3-pip"
    echo ""
    exit 1
fi

# ================================
# ETAPE 2 : Créer environnement virtuel
# ================================
echo ""
echo "[ETAPE 2/5] Création de l'environnement virtuel..."

if [ -d "venv" ]; then
    echo "[INFO] Environnement virtuel déjà existant"
else
    echo "[INFO] Création d'un nouvel environnement virtuel..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERREUR] Impossible de créer l'environnement virtuel"
        echo "[INFO] Installez python3-venv : sudo apt install python3-venv"
        exit 1
    fi
    echo "[OK] Environnement virtuel créé"
fi

# Activer l'environnement virtuel
source venv/bin/activate

# ================================
# ETAPE 3 : Mettre à jour pip
# ================================
echo ""
echo "[ETAPE 3/5] Mise à jour de pip..."
python -m pip install --upgrade pip

# ================================
# ETAPE 4 : Installer les dépendances
# ================================
echo ""
echo "[ETAPE 4/5] Installation des dépendances..."
echo "[INFO] Cela peut prendre plusieurs minutes..."
echo ""

pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERREUR] L'installation des dépendances a échoué"
    echo "[INFO] Vérifiez votre connexion internet et réessayez"
    exit 1
fi

# ================================
# ETAPE 5 : Vérifier l'installation
# ================================
echo ""
echo "[ETAPE 5/5] Vérification de l'installation..."

python -c "import flask; import TTS; import gradio; print('[OK] Toutes les dépendances sont installées')"
if [ $? -ne 0 ]; then
    echo "[ERREUR] Certaines dépendances sont manquantes"
    exit 1
fi

# ================================
# Information sur les échantillons de voix
# ================================
echo ""
echo "========================================"
echo "  Installation terminée avec succès !"
echo "========================================"
echo ""
echo "IMPORTANT - Configuration des voix :"
echo ""
echo "  Pour utiliser l'API avec des voix prédéfinies, placez vos"
echo "  échantillons de voix dans le dossier :"
echo "  $PWD/data/voices/"
echo ""
echo "  Fichiers attendus :"
echo "    - bob.wav      (voix \"bob\")"
echo "    - pascal.wav   (voix \"pascal\")"
echo ""
echo "  Format recommandé : WAV, 15-30 secondes, audio clair"
echo ""
echo "========================================"
echo "  Prochaines étapes :"
echo "========================================"
echo ""
echo "  Pour lancer l'API :"
echo "    bash scripts/launch_api.sh"
echo ""
echo "  Pour lancer l'interface web :"
echo "    bash scripts/launch_ui.sh"
echo ""
echo "  Consultez le README.md pour plus d'informations"
echo ""
