"""Audio Processing - Trim, concat, mix, export"""
import wave
import struct
import os
from pathlib import Path
from typing import List, Tuple
import json
import zipfile
from datetime import datetime


def get_wav_info(file_path: str) -> dict:
    """Get WAV file information"""
    with wave.open(file_path, 'rb') as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
        duration = frames / float(rate)
        return {
            "duration": duration,
            "sample_rate": rate,
            "channels": wav.getnchannels(),
            "sample_width": wav.getsampwidth()
        }


def read_wav(file_path: str) -> Tuple[bytes, dict]:
    """Read WAV file and return raw audio data and params"""
    with wave.open(file_path, 'rb') as wav:
        params = {
            "channels": wav.getnchannels(),
            "sample_width": wav.getsampwidth(),
            "framerate": wav.getframerate(),
            "nframes": wav.getnframes()
        }
        data = wav.readframes(wav.getnframes())
    return data, params


def write_wav(file_path: str, data: bytes, params: dict):
    """Write audio data to WAV file"""
    with wave.open(file_path, 'wb') as wav:
        wav.setnchannels(params["channels"])
        wav.setsampwidth(params["sample_width"])
        wav.setframerate(params["framerate"])
        wav.writeframes(data)


def generate_silence(duration_seconds: float, sample_rate: int = 44100,
                     channels: int = 1, sample_width: int = 2) -> bytes:
    """Generate silence audio data"""
    num_frames = int(duration_seconds * sample_rate)
    silence = b'\x00' * (num_frames * channels * sample_width)
    return silence


def trim_audio(file_path: str, start_time: float, end_time: float, output_path: str) -> str:
    """Trim audio file between start and end times (in seconds)"""
    data, params = read_wav(file_path)

    bytes_per_frame = params["channels"] * params["sample_width"]
    start_frame = int(start_time * params["framerate"])
    end_frame = int(end_time * params["framerate"])

    start_byte = start_frame * bytes_per_frame
    end_byte = end_frame * bytes_per_frame

    trimmed_data = data[start_byte:end_byte]
    write_wav(output_path, trimmed_data, params)

    return output_path


def adjust_volume(data: bytes, volume: float, sample_width: int = 2) -> bytes:
    """Adjust volume of audio data (volume: 0.0 - 2.0)"""
    if sample_width != 2:
        return data  # Only support 16-bit for now

    # Unpack samples
    num_samples = len(data) // 2
    samples = struct.unpack(f'{num_samples}h', data)

    # Adjust volume with clipping
    adjusted = []
    for sample in samples:
        new_val = int(sample * volume)
        new_val = max(-32768, min(32767, new_val))  # Clip to 16-bit range
        adjusted.append(new_val)

    # Repack
    return struct.pack(f'{num_samples}h', *adjusted)


def mix_tracks(tracks_data: List[Tuple[bytes, float, float]],
               total_duration: float,
               sample_rate: int = 44100,
               channels: int = 1,
               sample_width: int = 2) -> bytes:
    """Mix multiple audio tracks with timing offsets

    Args:
        tracks_data: List of (audio_bytes, start_time, volume)
        total_duration: Total output duration in seconds
        sample_rate: Sample rate
        channels: Number of channels
        sample_width: Bytes per sample

    Returns:
        Mixed audio data
    """
    total_frames = int(total_duration * sample_rate)
    bytes_per_frame = channels * sample_width

    # Initialize output buffer with zeros (32-bit for mixing headroom)
    output = [0] * (total_frames * channels)

    for audio_data, start_time, volume in tracks_data:
        start_frame = int(start_time * sample_rate)
        num_samples = len(audio_data) // sample_width

        if sample_width == 2:
            samples = struct.unpack(f'{num_samples}h', audio_data)
        else:
            continue  # Skip unsupported formats

        # Mix into output
        for i, sample in enumerate(samples):
            output_idx = (start_frame * channels) + i
            if output_idx < len(output):
                output[output_idx] += int(sample * volume)

    # Normalize and clip to 16-bit
    max_val = max(abs(min(output)), abs(max(output))) if output else 1
    if max_val > 32767:
        scale = 32767 / max_val
        output = [int(s * scale) for s in output]
    else:
        output = [max(-32768, min(32767, s)) for s in output]

    return struct.pack(f'{len(output)}h', *output)


def concat_samples(samples: List[dict], output_path: str,
                   sample_rate: int = 44100) -> str:
    """Concatenate samples in order with their gaps

    Args:
        samples: List of {"path": str, "start_time": float, "duration": float, "volume": float}
        output_path: Output file path
        sample_rate: Output sample rate
    """
    if not samples:
        return None

    # Sort by start time
    sorted_samples = sorted(samples, key=lambda x: x["start_time"])

    # Calculate total duration
    total_duration = max(s["start_time"] + s["duration"] for s in sorted_samples)

    # Collect all audio with timing
    tracks = []
    for sample in sorted_samples:
        data, params = read_wav(sample["path"])
        volume = sample.get("volume", 1.0)
        tracks.append((data, sample["start_time"], volume))

    # Mix all tracks
    mixed = mix_tracks(tracks, total_duration, sample_rate)

    # Write output
    params = {
        "channels": 1,
        "sample_width": 2,
        "framerate": sample_rate
    }
    write_wav(output_path, mixed, params)

    return output_path


def export_zip(samples: List[dict], output_path: str) -> str:
    """Export all samples as a ZIP file"""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for sample in samples:
            if os.path.exists(sample["path"]):
                filename = os.path.basename(sample["path"])
                zf.write(sample["path"], filename)
    return output_path


def export_per_track(samples: List[dict], output_dir: Path,
                     sample_rate: int = 44100) -> dict:
    """Export one WAV file per track (voice)

    Returns:
        Dict of {voice_name: output_path}
    """
    # Group samples by voice/track
    tracks = {}
    for sample in samples:
        voice = sample.get("voice", "unknown")
        if voice not in tracks:
            tracks[voice] = []
        tracks[voice].append(sample)

    outputs = {}
    for voice, voice_samples in tracks.items():
        output_path = output_dir / f"track_{voice}.wav"
        concat_samples(voice_samples, str(output_path), sample_rate)
        outputs[voice] = str(output_path)

    return outputs


def generate_edl(samples: List[dict], output_path: str, fps: float = 30.0) -> str:
    """Generate EDL (Edit Decision List) file for Vegas/Premiere

    Simple CMX 3600 EDL format
    """
    lines = [
        "TITLE: TTS Export",
        f"FCM: NON-DROP FRAME",
        ""
    ]

    def frames_to_tc(seconds: float) -> str:
        """Convert seconds to timecode HH:MM:SS:FF"""
        total_frames = int(seconds * fps)
        hours = total_frames // (3600 * int(fps))
        minutes = (total_frames % (3600 * int(fps))) // (60 * int(fps))
        secs = (total_frames % (60 * int(fps))) // int(fps)
        frames = total_frames % int(fps)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"

    sorted_samples = sorted(samples, key=lambda x: x["start_time"])

    for i, sample in enumerate(sorted_samples, 1):
        start = sample["start_time"]
        duration = sample["duration"]
        end = start + duration
        filename = os.path.basename(sample["path"])

        lines.append(f"{i:03d}  AX       AA     C        {frames_to_tc(0)} {frames_to_tc(duration)} {frames_to_tc(start)} {frames_to_tc(end)}")
        lines.append(f"* FROM CLIP NAME: {filename}")
        lines.append("")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    return output_path


def get_waveform_data(file_path: str, num_points: int = 200) -> List[float]:
    """Get simplified waveform data for visualization

    Returns list of amplitude values (0.0 - 1.0) for drawing
    """
    data, params = read_wav(file_path)

    if params["sample_width"] != 2:
        return [0.5] * num_points

    num_samples = len(data) // 2
    samples = struct.unpack(f'{num_samples}h', data)

    # Downsample to num_points
    chunk_size = max(1, num_samples // num_points)
    waveform = []

    for i in range(0, num_samples, chunk_size):
        chunk = samples[i:i + chunk_size]
        if chunk:
            # RMS amplitude normalized to 0-1
            rms = (sum(s * s for s in chunk) / len(chunk)) ** 0.5
            normalized = min(1.0, rms / 16384)  # Normalize to ~0-1 range
            waveform.append(normalized)

    # Ensure exactly num_points
    while len(waveform) < num_points:
        waveform.append(0)

    return waveform[:num_points]
