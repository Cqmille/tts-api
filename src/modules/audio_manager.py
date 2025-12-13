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

        base_url = "http://127.0.0.1:7870"

        # Get reference ID from the voice file name
        voice_id = os.path.splitext(os.path.basename(speaker_wav))[0]

        # Check if reference exists - it must be created first via the UI
        existing_refs = self.fish_speech_list_references()

        if voice_id not in existing_refs:
            raise RuntimeError(
                f"Référence Fish Speech '{voice_id}' non trouvée.\n"
                f"Créez d'abord le profil vocal dans la section 'Gestion des Profils Fish Speech'.\n"
                f"Profils disponibles: {', '.join(existing_refs) if existing_refs else 'aucun'}"
            )

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
            f"{base_url}/v1/tts",
            json=tts_payload,
            timeout=180
        )

        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return output_path
        else:
            raise RuntimeError(f"Fish Speech API error: {response.status_code} - {response.text}")

    # =========================================================================
    # Fish Speech Reference Management
    # =========================================================================

    def fish_speech_list_references(self) -> list:
        """List all Fish Speech voice references"""
        import requests

        if not self._check_fish_speech():
            return []

        try:
            response = requests.get("http://127.0.0.1:7870/v1/references/list", timeout=10)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def fish_speech_add_reference(self, reference_id: str, audio_path: str, text: str) -> tuple:
        """
        Add a new Fish Speech voice reference.

        Args:
            reference_id: Unique ID for the voice reference
            audio_path: Path to the audio file
            text: Transcription of what is said in the audio (required!)

        Returns:
            (success: bool, message: str)
        """
        import requests

        if not self._check_fish_speech():
            return False, "Fish Speech server not available"

        if not text or not text.strip():
            return False, "Le texte de transcription est obligatoire pour Fish Speech"

        # Check if reference already exists
        existing = self.fish_speech_list_references()
        if reference_id in existing:
            return False, f"La référence '{reference_id}' existe déjà"

        try:
            with open(audio_path, "rb") as f:
                audio_data = f.read()

            files = {
                "audio": (os.path.basename(audio_path), audio_data, "audio/wav")
            }
            data = {
                "id": reference_id,
                "text": text.strip()
            }

            response = requests.post(
                "http://127.0.0.1:7870/v1/references/add",
                files=files,
                data=data,
                timeout=60
            )

            if response.status_code in [200, 201]:
                return True, f"Référence '{reference_id}' ajoutée avec succès"
            else:
                return False, f"Erreur: {response.text}"

        except FileNotFoundError:
            return False, f"Fichier audio non trouvé: {audio_path}"
        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def fish_speech_delete_reference(self, reference_id: str) -> tuple:
        """
        Delete a Fish Speech voice reference.

        Returns:
            (success: bool, message: str)
        """
        import requests

        if not self._check_fish_speech():
            return False, "Fish Speech server not available"

        try:
            response = requests.delete(
                "http://127.0.0.1:7870/v1/references/delete",
                json={"reference_id": reference_id},
                timeout=10
            )

            if response.status_code in [200, 204]:
                return True, f"Référence '{reference_id}' supprimée"
            else:
                return False, f"Erreur: {response.text}"

        except Exception as e:
            return False, f"Erreur: {str(e)}"

    def fish_speech_reference_exists(self, reference_id: str) -> bool:
        """Check if a reference exists"""
        return reference_id in self.fish_speech_list_references()

