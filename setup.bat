@echo off
chcp 65001 > nul
title Installation TTS API

echo.
echo ========================================
echo   TTS API - Installation Automatique
echo ========================================
echo.
echo Ce script va installer automatiquement :
echo   - Environnement virtuel (Python 3.10)
echo   - Toutes les dépendances
echo.
echo IMPORTANT: TTS (Coqui) nécessite Python 3.10 ou 3.11
echo            Python 3.12+ n'est PAS supporté !
echo.
pause

REM Obtenir le répertoire du projet
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo.
echo [INFO] Répertoire du projet : %CD%
echo.

REM ================================
REM ETAPE 1 : Trouver Python 3.10/3.11
REM ================================
echo [ETAPE 1/5] Recherche de Python 3.10 ou 3.11...

REM Chercher Python 3.10 dans les emplacements courants
set "PYTHON_EXE="

REM Essayer py launcher d'abord (méthode recommandée)
where py >nul 2>&1
if %errorlevel% equ 0 (
    REM Vérifier si Python 3.10 est disponible
    py -3.10 --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=py -3.10"
        echo [OK] Python 3.10 trouvé via py launcher
        goto :python_found
    )
    REM Vérifier si Python 3.11 est disponible
    py -3.11 --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=py -3.11"
        echo [OK] Python 3.11 trouvé via py launcher
        goto :python_found
    )
)

REM Chercher dans les chemins standards
if exist "C:\Python310\python.exe" (
    set "PYTHON_EXE=C:\Python310\python.exe"
    echo [OK] Python 3.10 trouvé: C:\Python310
    goto :python_found
)

if exist "C:\Python311\python.exe" (
    set "PYTHON_EXE=C:\Python311\python.exe"
    echo [OK] Python 3.11 trouvé: C:\Python311
    goto :python_found
)

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    echo [OK] Python 3.10 trouvé: %LOCALAPPDATA%\Programs\Python\Python310
    goto :python_found
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    echo [OK] Python 3.11 trouvé: %LOCALAPPDATA%\Programs\Python\Python311
    goto :python_found
)

REM Python compatible non trouvé
echo.
echo [ERREUR] Python 3.10 ou 3.11 non trouvé !
echo.
echo TTS (Coqui) nécessite Python 3.10 ou 3.11.
echo Python 3.12, 3.13, 3.14 ne sont PAS supportés.
echo.
echo Installez Python 3.10 depuis :
echo   https://www.python.org/downloads/release/python-31011/
echo.
echo Cochez "Add Python to PATH" lors de l'installation.
echo.
pause
exit /b 1

:python_found
%PYTHON_EXE% --version

REM ================================
REM ETAPE 2 : Créer environnement virtuel
REM ================================
echo.
echo [ETAPE 2/5] Création de l'environnement virtuel...

REM Supprimer l'ancien venv s'il existe avec mauvaise version
if exist "venv" (
    echo [INFO] Vérification de la version Python du venv existant...
    venv\Scripts\python.exe --version 2>nul | findstr /C:"3.10" >nul
    if %errorlevel% neq 0 (
        venv\Scripts\python.exe --version 2>nul | findstr /C:"3.11" >nul
        if %errorlevel% neq 0 (
            echo [INFO] Ancien venv avec mauvaise version Python détecté
            echo [INFO] Suppression et recréation...
            rmdir /s /q venv
        )
    )
)

if exist "venv" (
    echo [INFO] Environnement virtuel compatible existant
) else (
    echo [INFO] Création d'un nouvel environnement virtuel avec Python 3.10/3.11...
    %PYTHON_EXE% -m venv venv
    if %errorlevel% neq 0 (
        echo [ERREUR] Impossible de créer l'environnement virtuel
        pause
        exit /b 1
    )
    echo [OK] Environnement virtuel créé
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Vérifier la version
python --version

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

python -c "import flask; import TTS; import fastapi; print('[OK] Toutes les dépendances sont installées')"
if %errorlevel% neq 0 (
    echo [ERREUR] Certaines dépendances sont manquantes
    pause
    exit /b 1
)

REM ================================
REM Information finale
REM ================================
echo.
echo ========================================
echo   Installation terminée avec succès !
echo ========================================
echo.
echo Pour lancer la NOUVELLE interface Timeline Studio :
echo   - Double-cliquez sur : launch_studio.bat
echo   - Ouvrez : http://localhost:7860
echo.
echo Pour l'ancienne interface Gradio :
echo   - Double-cliquez sur : scripts\launch_ui.bat
echo.
pause
