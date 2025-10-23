from flask import Flask, request, send_file
from flask_cors import CORS
import torch
from TTS.api import TTS
import os
import io

app = Flask(__name__)
CORS(app)  # Important pour Unity

# Initialisation (comme dans ton webui)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️ Utilisation du device: {device}")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# Chemins vers tes samples
VOICE_SAMPLES = {
    "bob": "C:/tts/bob.wav",      # Ton sample Bob
    "pascal": "C:/tts/pp1.wav"  # Ton sample Pascal
}

@app.route('/api/tts', methods=['POST'])
def generate_speech():
    try:
        data = request.get_json()
        text = data.get('text')
        speaker = data.get('speaker', 'bob')  # 'bob' ou 'pascal'
        
        if not text:
            return {"error": "No text provided"}, 400
        
        speaker_wav = VOICE_SAMPLES.get(speaker.lower())
        if not speaker_wav:
            return {"error": f"Unknown speaker: {speaker}"}, 400
        
        # Génération temporaire
        temp_path = f"C:/tts/temp_{speaker}.wav"
        
        tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav,
            language="fr",
            file_path=temp_path,
            temperature=0.75,
            speed=1.0
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
    print("🚀 API TTS lancée sur http://localhost:5002")
    app.run(host='0.0.0.0', port=5002, debug=False)