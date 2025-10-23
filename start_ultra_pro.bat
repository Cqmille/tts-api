@echo off
echo ========================================
echo   TTS Ultra Pro - Lancement
echo ========================================
echo.

REM Activer l'environnement virtuel si disponible
if exist "venv\Scripts\activate.bat" (
    echo Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
) else (
    echo ATTENTION: Environnement virtuel non trouve
    echo Executez setup.bat d'abord
    echo.
    pause
    exit /b 1
)

echo Lancement de l'interface Ultra Pro...
echo.
python src\webui_ultra_pro.py

pause
