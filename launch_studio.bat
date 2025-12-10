@echo off
chcp 65001 > nul
title TTS Timeline Studio
echo ============================================
echo   TTS Timeline Studio
echo ============================================
echo.

cd /d "%~dp0"

REM Vérifier si le venv existe
if not exist "venv\Scripts\activate.bat" (
    echo [ERREUR] Environnement virtuel non trouvé !
    echo.
    echo Lancez d'abord : setup.bat
    echo.
    pause
    exit /b 1
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

echo Démarrage du serveur...
echo.
echo ============================================
echo   Interface: http://localhost:7860
echo ============================================
echo.
echo Appuyez sur Ctrl+C pour arrêter
echo.

python -m uvicorn src.new_ui.app:app --host 0.0.0.0 --port 7860

pause
