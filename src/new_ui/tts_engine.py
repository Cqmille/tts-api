"""TTS Engine - Wrapper for XTTS v2"""
import torch
from TTS.api import TTS
from pathlib import Path
import json

# Configuration
MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
SUPPORTED_LANGUAGES = ["fr", "en", "es", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"]

class TTSEngine:
    """XTTS v2 TTS Engine"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[TTS] Device: {self.device}")

        print("[TTS] Loading XTTS v2 model...")
        self.tts = TTS(MODEL_NAME).to(self.device)
        print("[TTS] Model loaded successfully")

        self._initialized = True

    def generate(self, text: str, voice_path: str, output_path: str,
                 language: str = "fr", temperature: float = 0.75, speed: float = 1.0) -> str:
        """Generate audio from text

        Args:
            text: Text to synthesize
            voice_path: Path to reference voice WAV file
            output_path: Path for output WAV file
            language: Language code (default: fr)
            temperature: Generation temperature (0.1-1.0)
            speed: Speech speed (0.5-2.0)

        Returns:
            Path to generated audio file
        """
        self.tts.tts_to_file(
            text=text,
            speaker_wav=voice_path,
            language=language,
            file_path=output_path,
            temperature=temperature,
            speed=speed
        )
        return output_path

    def get_device(self) -> str:
        return self.device


class VoiceManager:
    """Manages voice samples and presets"""

    def __init__(self, voices_dir: Path, presets_file: Path):
        self.voices_dir = voices_dir
        self.presets_file = presets_file
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        self._load_presets()

    def _load_presets(self):
        """Load voice presets from file"""
        if self.presets_file.exists():
            with open(self.presets_file, 'r') as f:
                self.presets = json.load(f)
        else:
            self.presets = {}

    def _save_presets(self):
        """Save voice presets to file"""
        with open(self.presets_file, 'w') as f:
            json.dump(self.presets, f, indent=2)

    def get_voices(self) -> list:
        """Get list of available voices"""
        voices = []
        for wav_file in self.voices_dir.glob("*.wav"):
            voice_name = wav_file.stem
            preset = self.presets.get(voice_name, {"temperature": 0.75, "speed": 1.0})
            voices.append({
                "name": voice_name,
                "path": str(wav_file),
                "temperature": preset.get("temperature", 0.75),
                "speed": preset.get("speed", 1.0)
            })
        # Sort with pasqual first
        voices.sort(key=lambda v: (0 if v["name"].lower() == "pasqual" else 1, v["name"]))
        return voices

    def get_voice_path(self, voice_name: str) -> str | None:
        """Get path to voice sample"""
        voice_file = self.voices_dir / f"{voice_name}.wav"
        if voice_file.exists():
            return str(voice_file)
        return None

    def save_preset(self, voice_name: str, temperature: float, speed: float):
        """Save preset for a voice"""
        self.presets[voice_name] = {"temperature": temperature, "speed": speed}
        self._save_presets()

    def add_voice(self, name: str, audio_data: bytes) -> bool:
        """Add a new voice sample"""
        voice_file = self.voices_dir / f"{name}.wav"
        with open(voice_file, 'wb') as f:
            f.write(audio_data)
        return True

    def delete_voice(self, name: str) -> bool:
        """Delete a voice sample"""
        voice_file = self.voices_dir / f"{name}.wav"
        if voice_file.exists() and name.lower() != "pasqual":  # Protect default voice
            voice_file.unlink()
            if name in self.presets:
                del self.presets[name]
                self._save_presets()
            return True
        return False
