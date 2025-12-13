"""FastAPI Backend for TTS Timeline Studio"""
import os
import sys
import uuid
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.new_ui.tts_engine import (
    create_engine_manager, TTSEngineManager, VoiceManager,
    XTTSEngine, FishSpeechEngine
)
from src.new_ui.audio_processor import (
    get_wav_info, trim_audio, concat_samples, export_zip,
    export_per_track, generate_edl, get_waveform_data
)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VOICES_DIR = DATA_DIR / "voices"
TEMP_DIR = DATA_DIR / "temp" / "timeline"
EXPORTS_DIR = DATA_DIR / "exports"
PRESETS_FILE = DATA_DIR / "voice_presets.json"
STATIC_DIR = Path(__file__).parent / "static"

# Ensure directories exist
for d in [VOICES_DIR, TEMP_DIR, EXPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Global instances
engine_manager: Optional[TTSEngineManager] = None
voice_manager: Optional[VoiceManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize TTS engines on startup"""
    global engine_manager, voice_manager
    print("[App] Starting TTS Timeline Studio...")
    engine_manager = create_engine_manager()
    voice_manager = VoiceManager(VOICES_DIR, PRESETS_FILE)

    # Log available engines
    engines = engine_manager.get_available_engines()
    for eng in engines:
        status = "available" if eng["available"] else "not installed"
        print(f"[App] Engine {eng['name']}: {status}")

    print("[App] Ready!")
    yield
    print("[App] Shutting down...")


app = FastAPI(title="TTS Timeline Studio", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# =============================================================================
# Pydantic Models
# =============================================================================

class GenerateRequest(BaseModel):
    text: str
    voice: str
    engine: str = "xtts_v2"
    language: str = "fr"
    # Common parameters
    temperature: float = 0.75
    # XTTS specific
    speed: float = 1.0
    # Fish Speech specific
    top_p: float = 0.7
    repetition_penalty: float = 1.2


class TrimRequest(BaseModel):
    sample_id: str
    start_time: float
    end_time: float


class ExportRequest(BaseModel):
    samples: list  # List of sample dicts with timing info
    format: str = "wav"  # wav, zip, per_track, edl


class PresetRequest(BaseModel):
    voice: str
    engine: str = "xtts_v2"
    temperature: float = 0.75
    speed: float = 1.0
    top_p: float = 0.7
    repetition_penalty: float = 1.2


class EngineRequest(BaseModel):
    engine: str


# Fish Speech presets directory
FISH_PRESETS_DIR = DATA_DIR / "fish_presets"
FISH_PRESETS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Routes - Pages
# =============================================================================

@app.get("/")
async def index():
    """Serve main page"""
    return FileResponse(STATIC_DIR / "index.html")


# =============================================================================
# Routes - Engines
# =============================================================================

@app.get("/api/engines")
async def get_engines():
    """Get list of available TTS engines"""
    engines = engine_manager.get_available_engines()
    current = engine_manager._current_engine
    return {
        "engines": engines,
        "current": current
    }


@app.post("/api/engines/select")
async def select_engine(req: EngineRequest):
    """Select active TTS engine"""
    if engine_manager.set_current_engine(req.engine):
        return {"success": True, "engine": req.engine}
    raise HTTPException(status_code=400, detail=f"Engine '{req.engine}' not available")


@app.get("/api/engines/{engine_name}/status")
async def get_engine_status(engine_name: str):
    """Get detailed status of a specific engine"""
    engine = engine_manager.get_engine(engine_name)
    if not engine:
        raise HTTPException(status_code=404, detail="Engine not found")

    status = {
        "name": engine_name,
        "available": engine.is_available(),
        "device": engine.get_device(),
        "languages": engine.get_supported_languages(),
        "parameters": engine.get_parameters()
    }

    # Add Fish Speech specific info
    if engine_name == "fish_speech" and hasattr(engine, 'get_installation_status'):
        status["installation"] = engine.get_installation_status()

    return status


# =============================================================================
# Routes - Voices
# =============================================================================

@app.get("/api/voices")
async def get_voices():
    """Get list of available voices with their presets"""
    voices = voice_manager.get_voices()
    # Get languages from current engine
    current_engine = engine_manager.get_current_engine()
    languages = current_engine.get_supported_languages() if current_engine else ["fr", "en"]
    return {"voices": voices, "languages": languages}


@app.get("/api/voices/{voice_name}/preview")
async def preview_voice(voice_name: str):
    """Get voice sample for preview"""
    voice_path = voice_manager.get_voice_path(voice_name)
    if not voice_path or not os.path.exists(voice_path):
        raise HTTPException(status_code=404, detail="Voice not found")
    return FileResponse(voice_path, media_type="audio/wav")


@app.post("/api/voices/upload")
async def upload_voice(file: UploadFile = File(...), name: str = Form(...)):
    """Upload a new voice sample"""
    if not file.filename.lower().endswith('.wav'):
        raise HTTPException(status_code=400, detail="Only WAV files are supported")

    # Clean name
    clean_name = "".join(c for c in name if c.isalnum() or c in "_-").lower()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Invalid voice name")

    # Check if exists
    existing_path = voice_manager.get_voice_path(clean_name)
    if existing_path:
        raise HTTPException(status_code=400, detail="Voice already exists")

    # Save
    audio_data = await file.read()
    voice_manager.add_voice(clean_name, audio_data)

    return {"success": True, "name": clean_name}


@app.delete("/api/voices/{voice_name}")
async def delete_voice(voice_name: str):
    """Delete a voice sample"""
    if voice_name.lower() == "pasqual":
        raise HTTPException(status_code=400, detail="Cannot delete default voice")

    if not voice_manager.delete_voice(voice_name):
        raise HTTPException(status_code=404, detail="Voice not found")

    return {"success": True}


@app.post("/api/voices/preset")
async def save_preset(req: PresetRequest):
    """Save voice preset"""
    voice_manager.save_preset(
        req.voice,
        req.temperature,
        req.speed,
        top_p=req.top_p,
        repetition_penalty=req.repetition_penalty,
        engine=req.engine
    )
    return {"success": True}


# =============================================================================
# Routes - Fish Speech References
# =============================================================================

@app.get("/api/fish_speech/references")
async def get_fish_speech_references():
    """Get list of Fish Speech voice references"""
    fish_engine = engine_manager.get_engine("fish_speech")
    if not fish_engine or not fish_engine.is_available():
        return {"references": [], "available": False}

    try:
        import requests as req
        response = req.get(f"{fish_engine.api_url}/v1/references/list", timeout=10)
        if response.status_code == 200:
            refs = response.json()
            # Get transcription info from preset files
            references_with_info = []
            for ref_id in refs:
                preset_file = FISH_PRESETS_DIR / f"{ref_id}.txt"
                transcription = ""
                if preset_file.exists():
                    with open(preset_file, "r", encoding="utf-8") as f:
                        transcription = f.read().strip()
                references_with_info.append({
                    "id": ref_id,
                    "transcription": transcription[:100] + "..." if len(transcription) > 100 else transcription
                })
            return {"references": references_with_info, "available": True}
        return {"references": [], "available": True}
    except Exception as e:
        return {"references": [], "available": True, "error": str(e)}


@app.post("/api/fish_speech/references")
async def add_fish_speech_reference(
    audio: UploadFile = File(...),
    reference_id: str = Form(...),
    transcription: str = Form(...)
):
    """Add a new Fish Speech voice reference"""
    fish_engine = engine_manager.get_engine("fish_speech")
    if not fish_engine or not fish_engine.is_available():
        raise HTTPException(status_code=503, detail="Fish Speech server not available")

    # Validate inputs
    clean_id = "".join(c for c in reference_id if c.isalnum() or c in "_-").lower()
    if not clean_id:
        raise HTTPException(status_code=400, detail="Invalid reference ID")

    if not transcription.strip():
        raise HTTPException(status_code=400, detail="Transcription cannot be empty")

    try:
        import requests as req

        # Read audio data
        audio_data = await audio.read()

        # Add reference to Fish Speech API
        files = {
            "audio": (audio.filename or f"{clean_id}.wav", audio_data, "audio/wav")
        }
        data = {
            "id": clean_id,
            "text": transcription.strip()
        }

        response = req.post(
            f"{fish_engine.api_url}/v1/references/add",
            files=files,
            data=data,
            timeout=60
        )

        if response.status_code not in [200, 201]:
            error_msg = response.text
            raise HTTPException(status_code=400, detail=f"Fish Speech error: {error_msg}")

        # Save transcription to preset file for future use
        preset_file = FISH_PRESETS_DIR / f"{clean_id}.txt"
        with open(preset_file, "w", encoding="utf-8") as f:
            f.write(transcription.strip())

        # Also save the audio file to voices directory for consistency
        voice_file = VOICES_DIR / f"{clean_id}.wav"
        with open(voice_file, "wb") as f:
            f.write(audio_data)

        return {"success": True, "reference_id": clean_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/fish_speech/references/{reference_id}")
async def delete_fish_speech_reference(reference_id: str):
    """Delete a Fish Speech voice reference"""
    fish_engine = engine_manager.get_engine("fish_speech")
    if not fish_engine or not fish_engine.is_available():
        raise HTTPException(status_code=503, detail="Fish Speech server not available")

    try:
        import requests as req

        # Delete from Fish Speech API
        response = req.delete(
            f"{fish_engine.api_url}/v1/references/{reference_id}",
            timeout=30
        )

        # Also remove local preset file if exists
        preset_file = FISH_PRESETS_DIR / f"{reference_id}.txt"
        if preset_file.exists():
            preset_file.unlink()

        if response.status_code in [200, 204, 404]:
            return {"success": True}
        else:
            raise HTTPException(status_code=400, detail=f"Fish Speech error: {response.text}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/fish_speech/presets")
async def get_fish_speech_presets():
    """Get available presets (transcription files)"""
    presets = []
    for preset_file in FISH_PRESETS_DIR.glob("*.txt"):
        preset_id = preset_file.stem
        with open(preset_file, "r", encoding="utf-8") as f:
            transcription = f.read().strip()

        # Check if voice file exists
        voice_file = VOICES_DIR / f"{preset_id}.wav"
        has_audio = voice_file.exists()

        presets.append({
            "id": preset_id,
            "transcription": transcription,  # Full transcription for modal
            "has_audio": has_audio
        })

    return {"presets": presets}


# =============================================================================
# Routes - TTS Generation
# =============================================================================

@app.post("/api/generate")
async def generate_sample(req: GenerateRequest):
    """Generate a new audio sample"""
    # Select engine if specified
    if req.engine:
        engine_manager.set_current_engine(req.engine)

    current_engine = engine_manager.get_current_engine()
    if not current_engine:
        raise HTTPException(status_code=500, detail="No TTS engine available")

    # Validate voice
    voice_path = voice_manager.get_voice_path(req.voice)
    if not voice_path:
        raise HTTPException(status_code=404, detail=f"Voice '{req.voice}' not found")

    # Generate unique filename
    sample_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%H%M%S")
    text_preview = "".join(c for c in req.text[:20] if c.isalnum() or c in " _-").replace(" ", "_")
    filename = f"{timestamp}_{req.voice}_{text_preview}_{sample_id}.wav"
    output_path = TEMP_DIR / filename

    try:
        # Build kwargs based on engine
        kwargs = {
            "text": req.text,
            "voice_path": voice_path,
            "output_path": str(output_path),
            "language": req.language,
            "temperature": req.temperature
        }

        # Add engine-specific parameters
        if req.engine == "xtts_v2":
            kwargs["speed"] = req.speed
        elif req.engine == "fish_speech":
            kwargs["top_p"] = req.top_p
            kwargs["repetition_penalty"] = req.repetition_penalty

        # Generate audio
        current_engine.generate(**kwargs)

        # Get info
        info = get_wav_info(str(output_path))
        waveform = get_waveform_data(str(output_path), num_points=100)

        # Save preset for this voice
        voice_manager.save_preset(
            req.voice, req.temperature, req.speed,
            top_p=req.top_p, repetition_penalty=req.repetition_penalty,
            engine=req.engine
        )

        return {
            "success": True,
            "sample": {
                "id": sample_id,
                "filename": filename,
                "text": req.text,
                "voice": req.voice,
                "engine": req.engine,
                "duration": info["duration"],
                "waveform": waveform,
                "path": f"/api/samples/{filename}"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Routes - Samples
# =============================================================================

@app.get("/api/samples/{filename}")
async def get_sample(filename: str):
    """Get audio sample file"""
    file_path = TEMP_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample not found")
    return FileResponse(file_path, media_type="audio/wav")


@app.delete("/api/samples/{filename}")
async def delete_sample(filename: str):
    """Delete an audio sample"""
    file_path = TEMP_DIR / filename
    if file_path.exists():
        file_path.unlink()
    return {"success": True}


@app.post("/api/samples/{filename}/trim")
async def trim_sample(filename: str, start: float = Form(...), end: float = Form(...)):
    """Trim a sample and return new version"""
    file_path = TEMP_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample not found")

    # Create trimmed version with new name
    new_id = str(uuid.uuid4())[:8]
    new_filename = filename.replace(".wav", f"_trimmed_{new_id}.wav")
    output_path = TEMP_DIR / new_filename

    trim_audio(str(file_path), start, end, str(output_path))

    info = get_wav_info(str(output_path))
    waveform = get_waveform_data(str(output_path), num_points=100)

    return {
        "success": True,
        "filename": new_filename,
        "duration": info["duration"],
        "waveform": waveform,
        "path": f"/api/samples/{new_filename}"
    }


@app.get("/api/samples/{filename}/waveform")
async def get_sample_waveform(filename: str, points: int = 100):
    """Get waveform data for visualization"""
    file_path = TEMP_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample not found")

    waveform = get_waveform_data(str(file_path), num_points=points)
    info = get_wav_info(str(file_path))

    return {"waveform": waveform, "duration": info["duration"]}


# =============================================================================
# Routes - Export
# =============================================================================

@app.post("/api/export")
async def export_timeline(req: ExportRequest):
    """Export timeline in various formats"""
    if not req.samples:
        raise HTTPException(status_code=400, detail="No samples to export")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Convert sample paths to full paths
    samples_with_paths = []
    for s in req.samples:
        filename = s.get("filename") or s.get("path", "").split("/")[-1]
        full_path = TEMP_DIR / filename
        if full_path.exists():
            samples_with_paths.append({
                **s,
                "path": str(full_path)
            })

    if not samples_with_paths:
        raise HTTPException(status_code=400, detail="No valid samples found")

    try:
        if req.format == "wav":
            # Single mixed WAV
            output_path = EXPORTS_DIR / f"mix_{timestamp}.wav"
            concat_samples(samples_with_paths, str(output_path))
            return FileResponse(output_path, filename=f"mix_{timestamp}.wav",
                                media_type="audio/wav")

        elif req.format == "zip":
            # ZIP of all samples
            output_path = EXPORTS_DIR / f"samples_{timestamp}.zip"
            export_zip(samples_with_paths, str(output_path))
            return FileResponse(output_path, filename=f"samples_{timestamp}.zip",
                                media_type="application/zip")

        elif req.format == "per_track":
            # One WAV per track/voice
            outputs = export_per_track(samples_with_paths, EXPORTS_DIR)
            # Return as ZIP
            zip_path = EXPORTS_DIR / f"tracks_{timestamp}.zip"
            with zipfile.ZipFile(str(zip_path), 'w') as zf:
                for voice, path in outputs.items():
                    zf.write(path, os.path.basename(path))
            return FileResponse(zip_path, filename=f"tracks_{timestamp}.zip",
                                media_type="application/zip")

        elif req.format == "edl":
            # EDL file for Vegas
            output_path = EXPORTS_DIR / f"timeline_{timestamp}.edl"
            generate_edl(samples_with_paths, str(output_path))
            return FileResponse(output_path, filename=f"timeline_{timestamp}.edl",
                                media_type="text/plain")

        else:
            raise HTTPException(status_code=400, detail=f"Unknown format: {req.format}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Routes - Status
# =============================================================================

@app.get("/api/status")
async def get_status():
    """Get system status"""
    current_engine = engine_manager.get_current_engine() if engine_manager else None
    return {
        "status": "ok",
        "device": current_engine.get_device() if current_engine else "not loaded",
        "engine": engine_manager._current_engine if engine_manager else None,
        "voices": len(voice_manager.get_voices()) if voice_manager else 0
    }


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  TTS Timeline Studio")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=7860)
