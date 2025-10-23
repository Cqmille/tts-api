from flask import Flask, request, send_file
from flask_cors import CORS
import torch
from TTS.api import TTS
import os
import sys

# Ajouter le dossier parent au path pour importer config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import *

app = Flask(__name__)
CORS(app)  # Important pour Unity

# Initialisation
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️ Utilisation du device: {device}")
tts = TTS(TTS_CONFIG["model"]).to(device)

@app.route('/api/tts', methods=['POST'])
def generate_speech():
    try:
        data = request.get_json()
        text = data.get('text')
        speaker = data.get('speaker', 'bob')  # 'bob' ou 'pascal'
        
        if not text:
            return {"error": "No text provided"}, 400
        
        speaker_wav = get_voice_sample_path(speaker)
        if not speaker_wav:
            return {"error": f"Unknown speaker: {speaker}"}, 400

        # Génération temporaire
        temp_path = get_temp_path(f"temp_{speaker}.wav")

        tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav,
            language=TTS_CONFIG["default_language"],
            file_path=temp_path,
            temperature=TTS_CONFIG["default_temperature"],
            speed=TTS_CONFIG["default_speed"]
        )
        
        # Envoyer le fichier
        return send_file(temp_path, mimetype='audio/wav')
        
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok", "device": device}

if __name__ == '__main__':
    print(f"🚀 API TTS lancée sur http://localhost:{FLASK_CONFIG['port']}")
    app.run(**FLASK_CONFIG)