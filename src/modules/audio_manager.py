"""Audio and TTS management"""
import torch
from TTS.api import TTS
from config.settings import TTS_CONFIG


class AudioManager:
    """Manages TTS model and audio generation"""

    def __init__(self):
        # Check if CUDA is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️ Using device: {self.device}")

        # Initialize XTTS v2 model
        print("Loading XTTS v2 model...")
        self.tts = TTS(TTS_CONFIG["model"]).to(self.device)
        print("✅ Model loaded successfully")

    def generate_audio(self, text, speaker_wav, language, output_path, temperature=0.75, speed=1.0):
        """Generate audio from text using TTS"""
        self.tts.tts_to_file(
            text=text,
            speaker_wav=speaker_wav,
            language=language,
            file_path=output_path,
            temperature=temperature,
            speed=speed
        )
        return output_path
