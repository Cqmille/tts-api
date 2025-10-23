@echo off
chcp 65001 > nul
title TTS Voice Cloning UI

echo.
echo =====================================
echo   TTS Voice Cloning - Interface Web
echo =====================================
echo.
echo Lancement de l'interface Ultra Pro
echo (Dialogues multi-voix et paramètres avancés)
echo.

REM Obtenir le répertoire du projet (dossier parent de scripts/)
set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

echo [INFO] Répertoire du projet : %CD%
echo.

REM Chercher Python dans l'ordre : venv local, conda, système
echo [ETAPE 1/3] Recherche de Python...

REM 1. Essayer l'environnement virtuel local
if exist "venv\Scripts\python.exe" (
    echo [OK] Environnement virtuel détecté
    call venv\Scripts\activate.bat
    goto :python_found
)

REM 2. Essayer Conda
where conda >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Conda détecté, activation de l'environnement "tts"
    call conda activate tts 2>nul
    if %errorlevel% equ 0 goto :python_found
)

REM 3. Essayer Python système
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python système détecté
    goto :python_found
)

echo [ERREUR] Python introuvable. Veuillez lancer setup.bat d'abord.
pause
exit /b 1

:python_found
echo.
echo [ETAPE 2/3] Vérification de l'installation...
python --version

REM Vérifier si les dépendances sont installées
python -c "import gradio, TTS" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ATTENTION] Dépendances manquantes. Lancez setup.bat pour installer.
    echo             Tentative de lancement quand même...
)

echo.
echo [ETAPE 3/3] Démarrage de l'interface...
echo.
echo ================================
echo   Interface en cours d'exécution
echo   URL: http://localhost:7860
echo   Arrêt: Ctrl+C
echo ================================
echo.

python src\webui_ultra_pro.py

echo.
echo [INFO] Interface arrêtée
pause
