@echo off
chcp 65001 > nul
title Installation TTS API

echo.
echo ========================================
echo   TTS API - Installation Automatique
echo ========================================
echo.
echo Ce script va installer automatiquement :
echo   - Python (si nécessaire)
echo   - Environnement virtuel
echo   - Toutes les dépendances
echo.
pause

REM Obtenir le répertoire du projet (dossier parent de scripts/)
set "PROJECT_DIR=%~dp0.."
cd /d "%PROJECT_DIR%"

echo.
echo [INFO] Répertoire du projet : %CD%
echo.

REM ================================
REM ETAPE 1 : Vérifier Python
REM ================================
echo [ETAPE 1/5] Vérification de Python...

where python >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python est installé
    python --version
    goto :python_ok
)

echo [ATTENTION] Python n'est pas installé
echo.
echo Veuillez installer Python 3.10 ou supérieur :
echo   1. Téléchargez depuis : https://www.python.org/downloads/
echo   2. IMPORTANT : Cochez "Add Python to PATH" lors de l'installation
echo   3. Relancez ce script après l'installation
echo.
pause
exit /b 1

:python_ok

REM ================================
REM ETAPE 2 : Créer environnement virtuel
REM ================================
echo.
echo [ETAPE 2/5] Création de l'environnement virtuel...

if exist "venv" (
    echo [INFO] Environnement virtuel déjà existant
) else (
    echo [INFO] Création d'un nouvel environnement virtuel...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERREUR] Impossible de créer l'environnement virtuel
        pause
        exit /b 1
    )
    echo [OK] Environnement virtuel créé
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM ================================
REM ETAPE 3 : Mettre à jour pip
REM ================================
echo.
echo [ETAPE 3/5] Mise à jour de pip...
python -m pip install --upgrade pip

REM ================================
REM ETAPE 4 : Installer les dépendances
REM ================================
echo.
echo [ETAPE 4/5] Installation des dépendances...
echo [INFO] Cela peut prendre plusieurs minutes...
echo.

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] L'installation des dépendances a échoué
    echo [INFO] Vérifiez votre connexion internet et réessayez
    pause
    exit /b 1
)

REM ================================
REM ETAPE 5 : Vérifier l'installation
REM ================================
echo.
echo [ETAPE 5/5] Vérification de l'installation...

python -c "import flask; import TTS; import gradio; print('[OK] Toutes les dépendances sont installées')"
if %errorlevel% neq 0 (
    echo [ERREUR] Certaines dépendances sont manquantes
    pause
    exit /b 1
)

REM ================================
REM Information sur les échantillons de voix
REM ================================
echo.
echo ========================================
echo   Installation terminée avec succès !
echo ========================================
echo.
echo IMPORTANT - Configuration des voix :
echo.
echo   Pour utiliser l'API avec des voix prédéfinies, placez vos
echo   échantillons de voix dans le dossier :
echo   %CD%\data\voices\
echo.
echo   Fichiers attendus :
echo     - bob.wav      (voix "bob")
echo     - pascal.wav   (voix "pascal")
echo.
echo   Format recommandé : WAV, 15-30 secondes, audio clair
echo.
echo ========================================
echo   Prochaines étapes :
echo ========================================
echo.
echo   Pour lancer l'API :
echo     - Double-cliquez sur : launch_api.bat
echo.
echo   Pour lancer l'interface web :
echo     - Double-cliquez sur : launch_ui.bat
echo.
echo   Consultez le README.md pour plus d'informations
echo.
pause
