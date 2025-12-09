@echo off
title TTS Timeline Studio
echo ============================================
echo   TTS Timeline Studio
echo ============================================
echo.

cd /d "%~dp0"

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Starting server...
echo.
echo Interface: http://localhost:7860
echo.

python -m uvicorn src.new_ui.app:app --host 0.0.0.0 --port 7860 --reload

pause
