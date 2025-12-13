"""TTS Engine - Multi-engine support (XTTS v2 + Fish Speech)"""
import torch
import json
import os
import subprocess
import requests
import tempfile
import shutil
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

# =============================================================================
# Configuration
# =============================================================================

XTTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
XTTS_LANGUAGES = ["fr", "en", "es", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"]

FISH_LANGUAGES = ["fr", "en", "es", "de", "zh", "ja", "ko", "ar", "pt", "ru"]
FISH_SPEECH_DIR = Path(__file__).parent.parent.parent / "fish-speech"
FISH_CHECKPOINTS_DIR = FISH_SPEECH_DIR / "checkpoints" / "openaudio-s1-mini"

# =============================================================================
# Base TTS Engine Interface
# =============================================================================

class BaseTTSEngine(ABC):
    """Abstract base class for TTS engines"""

    @abstractmethod
    def generate(self, text: str, voice_path: str, output_path: str, **kwargs) -> str:
        """Generate audio from text"""
        pass

    @abstractmethod
    def get_engine_name(self) -> str:
        """Get engine name"""
        pass

    @abstractmethod
    def get_supported_languages(self) -> list:
        """Get list of supported language codes"""
        pass

    @abstractmethod
    def get_parameters(self) -> list:
        """Get list of configurable parameters with their metadata"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available"""
        pass


# =============================================================================
# XTTS v2 Engine
# =============================================================================

class XTTSEngine(BaseTTSEngine):
    """XTTS v2 TTS Engine (Coqui)"""

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
        self.tts = None
        self._initialized = True

    def _load_model(self):
        """Lazy load model"""
        if self.tts is None:
            from TTS.api import TTS
            print(f"[XTTS] Loading model on {self.device}...")
            self.tts = TTS(XTTS_MODEL).to(self.device)
            print("[XTTS] Model loaded")

    def generate(self, text: str, voice_path: str, output_path: str,
                 language: str = "fr", temperature: float = 0.75, speed: float = 1.0, **kwargs) -> str:
        self._load_model()
        self.tts.tts_to_file(
            text=text,
            speaker_wav=voice_path,
            language=language,
            file_path=output_path,
            temperature=temperature,
            speed=speed
        )
        return output_path

    def get_engine_name(self) -> str:
        return "xtts_v2"

    def get_supported_languages(self) -> list:
        return XTTS_LANGUAGES

    def get_parameters(self) -> list:
        """Return parameter definitions for UI"""
        return [
            {
                "name": "temperature",
                "label": "Température",
                "type": "range",
                "min": 0.1,
                "max": 1.0,
                "step": 0.05,
                "default": 0.75,
                "description": "Créativité (plus haut = plus varié)"
            },
            {
                "name": "speed",
                "label": "Vitesse",
                "type": "range",
                "min": 0.5,
                "max": 2.0,
                "step": 0.1,
                "default": 1.0,
                "description": "Vitesse de parole"
            }
        ]

    def is_available(self) -> bool:
        try:
            import TTS
            return True
        except ImportError:
            return False

    def get_device(self) -> str:
        return self.device


# =============================================================================
# Fish Speech Engine
# =============================================================================

class FishSpeechEngine(BaseTTSEngine):
    """Fish Speech / OpenAudio TTS Engine"""

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
        self.api_url = "http://127.0.0.1:7870"  # Fish Speech API server (local)
        self.server_process = None
        self._models_loaded = False
        self._initialized = True

    def _check_installation(self) -> bool:
        """Check if Fish Speech is installed"""
        return FISH_SPEECH_DIR.exists() and (FISH_SPEECH_DIR / "tools").exists()

    def _check_models(self) -> bool:
        """Check if models are downloaded"""
        return FISH_CHECKPOINTS_DIR.exists() and (FISH_CHECKPOINTS_DIR / "codec.pth").exists()

    def _check_server(self) -> bool:
        """Check if API server is running"""
        try:
            # Fish Speech exposes OpenAPI docs at /docs or root
            r = requests.get(f"{self.api_url}/", timeout=2)
            return r.status_code in [200, 307]  # 307 redirect to /docs is OK
        except:
            return False

    def start_server(self) -> bool:
        """Start Fish Speech API server"""
        if self._check_server():
            return True

        if not self._check_installation():
            print("[FishSpeech] Not installed")
            return False

        if not self._check_models():
            print("[FishSpeech] Models not downloaded")
            return False

        print("[FishSpeech] Starting API server...")
        try:
            self.server_process = subprocess.Popen(
                [
                    "python", "-m", "tools.api_server",
                    "--listen", "127.0.0.1:8080",
                    "--llama-checkpoint-path", str(FISH_CHECKPOINTS_DIR),
                    "--decoder-checkpoint-path", str(FISH_CHECKPOINTS_DIR / "codec.pth"),
                    "--decoder-config-name", "modded_dac_vq"
                ],
                cwd=str(FISH_SPEECH_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Wait a bit for server to start
            import time
            for _ in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self._check_server():
                    print("[FishSpeech] Server started")
                    return True
            print("[FishSpeech] Server failed to start")
            return False
        except Exception as e:
            print(f"[FishSpeech] Error starting server: {e}")
            return False

    def stop_server(self):
        """Stop Fish Speech API server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None

    def generate(self, text: str, voice_path: str, output_path: str,
                 language: str = "fr",
                 top_p: float = 0.7,
                 temperature: float = 0.7,
                 repetition_penalty: float = 1.2,
                 **kwargs) -> str:
        """Generate audio using Fish Speech API"""

        if not self._check_server():
            raise RuntimeError("Fish Speech server not available on http://127.0.0.1:7870")

        # Create a unique reference ID based on the voice file path
        voice_id = os.path.splitext(os.path.basename(voice_path))[0]

        # Call API - Fish Speech v1 API format
        try:
            # Check if reference already exists
            try:
                list_response = requests.get(f"{self.api_url}/v1/references/list", timeout=10)
                existing_refs = list_response.json() if list_response.status_code == 200 else []
            except:
                existing_refs = []

            # Add reference if it doesn't exist
            if voice_id not in existing_refs:
                print(f"[Fish Speech] Adding reference voice: {voice_id}")
                with open(voice_path, "rb") as f:
                    audio_data = f.read()

                files = {
                    "audio": (os.path.basename(voice_path), audio_data, "audio/wav")
                }
                data = {
                    "id": voice_id,
                    "text": ""
                }

                add_response = requests.post(
                    f"{self.api_url}/v1/references/add",
                    files=files,
                    data=data,
                    timeout=60
                )

                if add_response.status_code not in [200, 201]:
                    print(f"[Fish Speech] Warning: Could not add reference: {add_response.text}")

            # Generate TTS using the reference_id
            tts_payload = {
                "text": text,
                "chunk_length": 200,
                "format": "wav",
                "reference_id": voice_id,
                "normalize": True,
                "streaming": False,
                "max_new_tokens": 1024,
                "top_p": float(top_p),
                "repetition_penalty": float(repetition_penalty),
                "temperature": float(temperature)
            }

            response = requests.post(
                f"{self.api_url}/v1/tts",
                json=tts_payload,
                timeout=180
            )

            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
            else:
                raise RuntimeError(f"Fish Speech API error: {response.status_code} - {response.text}")

        except requests.exceptions.ConnectionError:
            raise RuntimeError("Fish Speech server not running on http://127.0.0.1:7870")

    def get_engine_name(self) -> str:
        return "fish_speech"

    def get_supported_languages(self) -> list:
        return FISH_LANGUAGES

    def get_parameters(self) -> list:
        """Return Fish Speech specific parameters"""
        return [
            {
                "name": "temperature",
                "label": "Température",
                "type": "range",
                "min": 0.1,
                "max": 1.0,
                "step": 0.05,
                "default": 0.7,
                "description": "Créativité de génération"
            },
            {
                "name": "top_p",
                "label": "Top P",
                "type": "range",
                "min": 0.1,
                "max": 1.0,
                "step": 0.05,
                "default": 0.7,
                "description": "Nucleus sampling"
            },
            {
                "name": "repetition_penalty",
                "label": "Pénalité répétition",
                "type": "range",
                "min": 1.0,
                "max": 2.0,
                "step": 0.1,
                "default": 1.2,
                "description": "Évite les répétitions"
            }
        ]

    def is_available(self) -> bool:
        """Fish Speech is available if the server is running"""
        return self._check_server()

    def get_device(self) -> str:
        return self.device

    def get_installation_status(self) -> Dict[str, Any]:
        """Get detailed installation status"""
        return {
            "installed": self._check_installation(),
            "models_downloaded": self._check_models(),
            "server_running": self._check_server(),
            "fish_speech_dir": str(FISH_SPEECH_DIR),
            "checkpoints_dir": str(FISH_CHECKPOINTS_DIR)
        }


# =============================================================================
# Engine Manager
# =============================================================================

class TTSEngineManager:
    """Manages multiple TTS engines"""

    def __init__(self):
        self._engines: Dict[str, BaseTTSEngine] = {}
        self._current_engine: Optional[str] = None

    def register_engine(self, engine: BaseTTSEngine):
        """Register a TTS engine"""
        self._engines[engine.get_engine_name()] = engine

    def get_engine(self, name: str) -> Optional[BaseTTSEngine]:
        """Get engine by name"""
        return self._engines.get(name)

    def get_current_engine(self) -> Optional[BaseTTSEngine]:
        """Get current active engine"""
        if self._current_engine:
            return self._engines.get(self._current_engine)
        return None

    def set_current_engine(self, name: str) -> bool:
        """Set current active engine"""
        if name in self._engines:
            self._current_engine = name
            return True
        return False

    def get_available_engines(self) -> list:
        """Get list of available engines with their info"""
        result = []
        for name, engine in self._engines.items():
            result.append({
                "name": name,
                "available": engine.is_available(),
                "languages": engine.get_supported_languages(),
                "parameters": engine.get_parameters()
            })
        return result

    def generate(self, text: str, voice_path: str, output_path: str, **kwargs) -> str:
        """Generate using current engine"""
        engine = self.get_current_engine()
        if not engine:
            raise RuntimeError("No TTS engine selected")
        return engine.generate(text, voice_path, output_path, **kwargs)


# =============================================================================
# Voice Manager (unchanged)
# =============================================================================

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

    def save_preset(self, voice_name: str, temperature: float, speed: float, **extra):
        """Save preset for a voice"""
        self.presets[voice_name] = {"temperature": temperature, "speed": speed, **extra}
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


# =============================================================================
# Factory function for backward compatibility
# =============================================================================

def create_engine_manager() -> TTSEngineManager:
    """Create and configure engine manager with all available engines"""
    manager = TTSEngineManager()

    # Register XTTS v2 (always available if TTS is installed)
    try:
        xtts = XTTSEngine()
        manager.register_engine(xtts)
        manager.set_current_engine("xtts_v2")  # Default
    except Exception as e:
        print(f"[Warning] Could not initialize XTTS: {e}")

    # Register Fish Speech (if available)
    try:
        fish = FishSpeechEngine()
        manager.register_engine(fish)
    except Exception as e:
        print(f"[Warning] Could not initialize Fish Speech: {e}")

    return manager


# Legacy alias for backward compatibility
class TTSEngine(XTTSEngine):
    """Legacy alias for XTTSEngine"""
    pass
