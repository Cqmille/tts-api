@echo off
echo Lancement de TTS Voice Cloning...
call C:\Users\camil\miniconda3\Scripts\activate.bat tts
cd C:\tts
python webui3.py
pause