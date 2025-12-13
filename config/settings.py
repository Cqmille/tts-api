import os
from pathlib import Path

# Répertoire racine du projet
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Ports
API_PORT = 5002
GRADIO_PORT = 7860

# Chemins des dossiers (relatifs au projet)
DATA_DIR = PROJECT_ROOT / "data"
VOICES_DIR = DATA_DIR / "voices"
OUTPUTS_DIR = DATA_DIR / "outputs"
TEMP_DIR = DATA_DIR / "temp"
TEMP_DIALOGUE_DIR = TEMP_DIR / "dialogue"

# Créer les dossiers s'ils n'existent pas
for directory in [DATA_DIR, VOICES_DIR, OUTPUTS_DIR, TEMP_DIR, TEMP_DIALOGUE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Échantillons de voix (noms de fichiers dans data/voices/)
VOICE_SAMPLES = {
    "bob": str(VOICES_DIR / "bob.wav"),
    "pascal": str(VOICES_DIR / "pascal.wav")  # Renommé de pp1.wav pour plus de clarté
}

# Configuration TTS par défaut (XTTS v2)
TTS_CONFIG = {
    "model": "tts_models/multilingual/multi-dataset/xtts_v2",
    "default_language": "fr",
    "default_temperature": 0.75,
    "default_speed": 1.0
}

# Configuration Fish Speech
FISH_SPEECH_CONFIG = {
    "api_url": "http://127.0.0.1:7870",
    "model": "openaudio-s1-mini",
    "default_temperature": 0.7,
    "default_top_p": 0.7,
    "default_repetition_penalty": 1.2
}

# Langues supportées par XTTS v2
SUPPORTED_LANGUAGES = [
    "fr", "en", "es", "de", "it", "pt", "pl", "tr",
    "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"
]

# Langues supportées par Fish Speech
FISH_SPEECH_LANGUAGES = [
    "fr", "en", "es", "de", "zh", "ja", "ko", "ar", "pt", "ru"
]

# Configuration Flask API
FLASK_CONFIG = {
    "host": "0.0.0.0",
    "port": API_PORT,
    "debug": False
}

# Configuration Gradio
GRADIO_CONFIG = {
    "share": False,
    "server_port": GRADIO_PORT
}

# Paramètres de génération de fichiers
FILE_CONFIG = {
    "max_filename_length": 50,
    "timestamp_format": "%Y%m%d_%H%M%S"
}

def get_voice_sample_path(voice_name):
    """Récupère le chemin d'un échantillon de voix"""
    return VOICE_SAMPLES.get(voice_name.lower())

def get_output_path(filename="output.wav"):
    """Génère un chemin de sortie complet"""
    return str(OUTPUTS_DIR / filename)

def get_temp_path(filename="temp.wav"):
    """Génère un chemin temporaire"""
    return str(TEMP_DIR / filename)
