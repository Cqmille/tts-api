"""Utility functions for TTS Ultra Pro"""
import re
import os


def sanitize_filename(text, max_length=50):
    """Creates a valid filename from text"""
    text = text.strip().split('\n')[0]
    text = text[:max_length]
    text = re.sub(r'[\\/*?:"<>|]', '', text)
    text = re.sub(r'\s+', '_', text)
    text = text.strip('._')
    return text if text else "output"


def get_voice_name(speaker_wav_path):
    """Extracts a voice name from the file path"""
    if not speaker_wav_path:
        return "Unknown_Voice"
    return os.path.splitext(os.path.basename(speaker_wav_path))[0]
