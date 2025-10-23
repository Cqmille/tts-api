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

# Configuration TTS par défaut
TTS_CONFIG = {
    "model": "tts_models/multilingual/multi-dataset/xtts_v2",
    "default_language": "fr",
    "default_temperature": 0.75,
    "default_speed": 1.0
}

# Langues supportées
SUPPORTED_LANGUAGES = [
    "fr", "en", "es", "de", "it", "pt", "pl", "tr",
    "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"
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
    "server_port": GRADIO_PORT,
    "max_threads": 10
}

# Configuration alternative si le port est occupé
GRADIO_CONFIG_AUTO_PORT = {
    "share": False,
    "max_threads": 10
    # On ne spécifie pas server_port pour que Gradio trouve automatiquement un port libre
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
