import edge_tts
import asyncio
import pygame
import tempfile
import os
import time
from config import TTS_VOICE, TTS_RATE

# Lazy init mixer
_mixer_initialized = False

def _init_mixer():
    global _mixer_initialized
    if not _mixer_initialized:
        try:
            pygame.mixer.init()
            _mixer_initialized = True
        except Exception as e:
            print(f"Mixer init failed: {e}")

async def generate_tts(text: str) -> str:
    """Generate TTS audio file and return path."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    
    try:
        communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
        await communicate.save(tmp_path)
    except Exception as e:
        print(f"TTS Generation failed: {e}")
        return ""
    return tmp_path

def play_audio(path: str):
    """Play an audio file and delete it after."""
    if not path or not os.path.exists(path):
        return
        
    _init_mixer()
    
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.01) # Faster poll for better fluidity
        pygame.mixer.music.unload()
    except Exception as e:
        print(f"Play audio failed: {e}")
    finally:
        try:
            os.unlink(path)
        except:
            pass

def speak(text: str):
    """Synchronous speak — generate and play."""
    # Check if we are already in an event loop
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            # If already running, we should task it or use a separate thread
            # but for simple activation phrases, a thread is safer to avoid blocking
            import threading
            threading.Thread(target=lambda: asyncio.run(_speak_async(text))).start()
            return
    except RuntimeError:
        pass
    
    asyncio.run(_speak_async(text))

async def _speak_async(text: str):
    path = await generate_tts(text)
    play_audio(path)

def quit_mixer():
    if _mixer_initialized:
        pygame.mixer.quit()
