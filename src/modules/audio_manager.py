"""Audio and TTS management - Multi-engine support (XTTS v2 + Fish Speech)"""
import torch
import sys
import os

# Add parent path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import TTS_CONFIG


class AudioManager:
    """Manages TTS engines and audio generation with multi-engine support"""

    def __init__(self):
        # Check if CUDA is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️ Using device: {self.device}")

        # Current engine name
        self._current_engine = "xtts_v2"

        # Lazy-loaded engines
        self._xtts_model = None
        self._fish_speech_available = None

        # Initialize XTTS v2 model by default
        self._init_xtts()

    def _init_xtts(self):
        """Initialize XTTS v2 model (lazy loading)"""
        if self._xtts_model is None:
            from TTS.api import TTS
            print("Loading XTTS v2 model...")
            self._xtts_model = TTS(TTS_CONFIG["model"]).to(self.device)
            print("✅ XTTS v2 model loaded successfully")

    def _check_fish_speech(self) -> bool:
        """Check if Fish Speech server is available"""
        if self._fish_speech_available is None:
            try:
                import requests
                r = requests.get("http://127.0.0.1:7870/", timeout=2)
                self._fish_speech_available = r.status_code in [200, 307]
            except:
                self._fish_speech_available = False
        return self._fish_speech_available

    def get_current_engine(self) -> str:
        """Get current engine name"""
        return self._current_engine

    def set_engine(self, engine_name: str) -> bool:
        """Set current TTS engine"""
        if engine_name == "xtts_v2":
            self._current_engine = "xtts_v2"
            return True
        elif engine_name == "fish_speech":
            # Reset cache to recheck availability
            self._fish_speech_available = None
            if self._check_fish_speech():
                self._current_engine = "fish_speech"
                return True
            else:
                print("⚠️ Fish Speech server not available on http://127.0.0.1:7870")
                return False
        return False

    def get_available_engines(self) -> list:
        """Get list of available engines"""
        engines = [
            {
                "name": "xtts_v2",
                "label": "XTTS v2 (Coqui)",
                "available": True,
                "parameters": ["temperature", "speed"]
            }
        ]

        # Reset cache and check Fish Speech
        self._fish_speech_available = None
        fish_available = self._check_fish_speech()
        engines.append({
            "name": "fish_speech",
            "label": "Fish Speech (OpenAudio S1-mini)",
            "available": fish_available,
            "parameters": ["temperature", "top_p", "repetition_penalty"]
        })

        return engines

    def generate_audio(self, text, speaker_wav, language, output_path,
                      temperature=0.75, speed=1.0, top_p=0.7, repetition_penalty=1.2):
        """Generate audio from text using current TTS engine"""

        if self._current_engine == "xtts_v2":
            return self._generate_xtts(text, speaker_wav, language, output_path,
                                       temperature, speed)
        elif self._current_engine == "fish_speech":
            return self._generate_fish_speech(text, speaker_wav, language, output_path,
                                              temperature, top_p, repetition_penalty)
        else:
            raise ValueError(f"Unknown engine: {self._current_engine}")

    def _generate_xtts(self, text, speaker_wav, language, output_path,
                       temperature=0.75, speed=1.0):
        """Generate audio using XTTS v2"""
        self._init_xtts()
        self._xtts_model.tts_to_file(
            text=text,
            speaker_wav=speaker_wav,
            language=language,
            file_path=output_path,
            temperature=temperature,
            speed=speed
        )
        return output_path

    def _generate_fish_speech(self, text, speaker_wav, language, output_path,
                              temperature=0.7, top_p=0.7, repetition_penalty=1.2):
        """Generate audio using Fish Speech API"""
        import requests

        if not self._check_fish_speech():
            raise RuntimeError("Fish Speech server not available on http://127.0.0.1:7870")

        # Read reference audio
        with open(speaker_wav, "rb") as f:
            reference_audio = f.read()

        # Call Fish Speech API
        files = {
            "reference_audio": ("reference.wav", reference_audio, "audio/wav")
        }
        data = {
            "text": text,
            "chunk_length": 200,
            "format": "wav",
            "top_p": top_p,
            "temperature": temperature,
            "repetition_penalty": repetition_penalty,
        }

        response = requests.post(
            "http://127.0.0.1:7870/v1/tts",
            files=files,
            data=data,
            timeout=180
        )

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return output_path
        else:
            raise RuntimeError(f"Fish Speech API error: {response.status_code} - {response.text}")
