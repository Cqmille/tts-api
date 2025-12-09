"""FastAPI Backend for TTS Timeline Studio"""
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.new_ui.tts_engine import TTSEngine, VoiceManager, SUPPORTED_LANGUAGES
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
tts_engine: Optional[TTSEngine] = None
voice_manager: Optional[VoiceManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize TTS engine on startup"""
    global tts_engine, voice_manager
    print("[App] Starting TTS Timeline Studio...")
    tts_engine = TTSEngine()
    voice_manager = VoiceManager(VOICES_DIR, PRESETS_FILE)
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
    language: str = "fr"
    temperature: float = 0.75
    speed: float = 1.0


class TrimRequest(BaseModel):
    sample_id: str
    start_time: float
    end_time: float


class ExportRequest(BaseModel):
    samples: list  # List of sample dicts with timing info
    format: str = "wav"  # wav, zip, per_track, edl


class PresetRequest(BaseModel):
    voice: str
    temperature: float
    speed: float


# =============================================================================
# Routes - Pages
# =============================================================================

@app.get("/")
async def index():
    """Serve main page"""
    return FileResponse(STATIC_DIR / "index.html")


# =============================================================================
# Routes - Voices
# =============================================================================

@app.get("/api/voices")
async def get_voices():
    """Get list of available voices with their presets"""
    voices = voice_manager.get_voices()
    return {"voices": voices, "languages": SUPPORTED_LANGUAGES}


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
    """Save voice preset (temperature, speed)"""
    voice_manager.save_preset(req.voice, req.temperature, req.speed)
    return {"success": True}


# =============================================================================
# Routes - TTS Generation
# =============================================================================

@app.post("/api/generate")
async def generate_sample(req: GenerateRequest):
    """Generate a new audio sample"""
    # Validate voice
    voice_path = voice_manager.get_voice_path(req.voice)
    if not voice_path:
        raise HTTPException(status_code=404, detail=f"Voice '{req.voice}' not found")

    # Generate unique filename
    sample_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%H%M%S")
    text_preview = req.text[:20].replace(" ", "_").replace("/", "_")
    filename = f"{timestamp}_{req.voice}_{text_preview}_{sample_id}.wav"
    output_path = TEMP_DIR / filename

    try:
        # Generate audio
        tts_engine.generate(
            text=req.text,
            voice_path=voice_path,
            output_path=str(output_path),
            language=req.language,
            temperature=req.temperature,
            speed=req.speed
        )

        # Get info
        info = get_wav_info(str(output_path))
        waveform = get_waveform_data(str(output_path), num_points=100)

        # Save preset for this voice
        voice_manager.save_preset(req.voice, req.temperature, req.speed)

        return {
            "success": True,
            "sample": {
                "id": sample_id,
                "filename": filename,
                "text": req.text,
                "voice": req.voice,
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
    return {
        "status": "ok",
        "device": tts_engine.get_device() if tts_engine else "not loaded",
        "voices": len(voice_manager.get_voices()) if voice_manager else 0
    }


# =============================================================================
# Missing import for zipfile in export
# =============================================================================
import zipfile


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  TTS Timeline Studio")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=7860)
