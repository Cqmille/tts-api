@echo off
echo Lancement de l'API TTS...
call C:\Users\camil\miniconda3\Scripts\activate.bat tts
cd C:\tts
python tts_api.py
pause