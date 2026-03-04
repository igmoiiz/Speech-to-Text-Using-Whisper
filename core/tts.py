# core/tts.py — Edge TTS + Pygame Playback

import edge_tts
import asyncio
import pygame
import tempfile
import os
import time
from config import TTS_VOICE, TTS_RATE

pygame.mixer.init()

async def generate_tts(text: str) -> str:
    """Generate TTS audio file and return path."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
    await communicate.save(tmp_path)
    return tmp_path

def play_audio(path: str):
    """Play an audio file and delete it after."""
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.05)
    pygame.mixer.music.unload()
    try:
        os.unlink(path)
    except:
        pass

def speak(text: str):
    """Synchronous speak — generate and play."""
    asyncio.run(_speak_async(text))

async def _speak_async(text: str):
    path = await generate_tts(text)
    play_audio(path)

def quit_mixer():
    pygame.mixer.quit()