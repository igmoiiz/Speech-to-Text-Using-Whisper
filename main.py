import whisper
import sounddevice as sd
import numpy as np
import torch
import time
import collections
import webrtcvad
import ollama
import edge_tts
import asyncio
import pygame
import os
import tempfile
import re
from ddgs import DDGS

# ══════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════
WHISPER_MODEL       = "medium"
SAMPLE_RATE         = 16000
CHANNELS            = 1
VAD_AGGRESSIVENESS  = 2
FRAME_DURATION_MS   = 30
PADDING_DURATION_MS = 1200
MIN_SPEECH_DURATION = 0.5
LANGUAGE            = "en"

OLLAMA_MODEL        = "qwen2.5:7b"
TTS_VOICE           = "en-US-GuyNeural"
TTS_RATE            = "+15%"

SEARCH_TRIGGERS = [
    "search", "look up", "find", "what is", "who is", "who are",
    "latest", "news", "today", "current", "price", "weather",
    "when did", "when is", "how much", "tell me about", "what are"
]

EXIT_COMMANDS = ["goodbye jarvis", "shut down", "exit", "turn off"]

conversation_history = [
    {
        "role": "system",
        "content": (
            "You are Jarvis, a smart and efficient AI voice assistant. "
            "Keep responses concise and conversational — you are spoken aloud. "
            "No markdown, no bullet points, no lists. "
            "Natural speech only. Max 3-4 sentences unless asked for more."
        )
    }
]

# ══════════════════════════════════════════════════════
#  LOAD MODELS
# ══════════════════════════════════════════════════════
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
print(f"Loading Whisper {WHISPER_MODEL}...")
stt_model = whisper.load_model(WHISPER_MODEL, device=device)
print("Whisper ready!")

pygame.mixer.init()
vad                = webrtcvad.Vad(VAD_AGGRESSIVENESS)
FRAME_SIZE         = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
NUM_PADDING_FRAMES = int(PADDING_DURATION_MS / FRAME_DURATION_MS)

# ══════════════════════════════════════════════════════
#  PRE-WARM OLLAMA
# ══════════════════════════════════════════════════════
def prewarm_ollama():
    print("Pre-warming Ollama...")
    try:
        ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            options={"num_predict": 1}
        )
        print("Ollama ready!")
    except Exception as e:
        print(f"Pre-warm failed: {e}")

# ══════════════════════════════════════════════════════
#  SPEECH TO TEXT
# ══════════════════════════════════════════════════════
def transcribe(audio: np.ndarray) -> str:
    audio_tensor = torch.from_numpy(audio).float()
    result = stt_model.transcribe(
        audio_tensor,
        language=LANGUAGE,
        fp16=(device == "cuda"),
        temperature=0,
        beam_size=1,
        best_of=1,
    )
    return result["text"].strip()

def is_speech(frame: np.ndarray) -> bool:
    pcm = (frame * 32767).astype(np.int16).tobytes()
    try:
        return vad.is_speech(pcm, SAMPLE_RATE)
    except:
        return False

# ══════════════════════════════════════════════════════
#  WEB SEARCH
# ══════════════════════════════════════════════════════
def should_search(text: str) -> bool:
    return any(trigger in text.lower() for trigger in SEARCH_TRIGGERS)

def web_search(query: str) -> str:
    print(f"  🔍 Searching: {query}")
    for attempt in range(3):
        try:
            # Try past 24 hours first
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query, max_results=5,
                    backend="lite", timelimit="d"
                ))
            # Fallback to past week
            if not results:
                with DDGS() as ddgs:
                    results = list(ddgs.text(
                        query, max_results=5,
                        backend="lite", timelimit="w"
                    ))
            if results:
                return "\n".join(
                    f"{r['title']}: {r['body']}" for r in results
                ).strip()
        except Exception as e:
            print(f"  Search attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    return ""

# ══════════════════════════════════════════════════════
#  TTS
# ══════════════════════════════════════════════════════
async def generate_tts(text: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
    await communicate.save(tmp_path)
    return tmp_path

def play_audio(path: str):
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.05)
    pygame.mixer.music.unload()
    try:
        os.unlink(path)
    except:
        pass

# ══════════════════════════════════════════════════════
#  STREAMING RESPONSE
#  Producer: streams tokens + generates TTS per sentence
#  Consumer: plays audio files as soon as they're ready
#  Both run concurrently via asyncio.gather — no gaps!
# ══════════════════════════════════════════════════════
def split_sentences(text: str) -> list:
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]

async def respond_streaming(user_text: str):
    global conversation_history

    # Web search if needed
    user_message = user_text
    if should_search(user_text):
        results = web_search(user_text)
        if results:
            user_message = f"{user_text}\n\n[Web results:\n{results}]"

    conversation_history.append({"role": "user", "content": user_message})

    tts_queue  = asyncio.Queue()
    done_event = asyncio.Event()
    tokens     = []
    loop       = asyncio.get_event_loop()

    # ── Producer ──────────────────────────────────────
    # Streams tokens from Ollama + generates TTS per sentence
    async def producer():
        buffer = ""
        print("  Jarvis: ", end="", flush=True)

        stream = ollama.chat(
            model=OLLAMA_MODEL,
            messages=conversation_history,
            stream=True,
            options={
                "num_predict": 150,
                "temperature": 0.7,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            }
        )

        for chunk in stream:
            token   = chunk["message"]["content"]
            tokens.append(token)
            buffer += token
            print(token, end="", flush=True)

            sentences = split_sentences(buffer)
            if len(sentences) > 1:
                to_speak = " ".join(sentences[:-1])
                buffer   = sentences[-1]
                # Generate TTS and push to queue immediately
                path = await generate_tts(to_speak)
                await tts_queue.put(path)

        # Remaining buffer
        if buffer.strip():
            path = await generate_tts(buffer.strip())
            await tts_queue.put(path)

        print("\n")
        done_event.set()

    # ── Consumer ──────────────────────────────────────
    # Plays audio files as soon as they appear in queue
    async def consumer():
        while True:
            try:
                path = tts_queue.get_nowait()
            except asyncio.QueueEmpty:
                if done_event.is_set() and tts_queue.empty():
                    break
                await asyncio.sleep(0.02)
                continue
            # Play in executor so async loop stays unblocked
            await loop.run_in_executor(None, play_audio, path)

    # Run both concurrently
    await asyncio.gather(producer(), consumer())

    # Save full reply to history
    full_reply = "".join(tokens).strip()
    conversation_history.append({
        "role": "assistant",
        "content": full_reply
    })

    if len(conversation_history) > 21:
        conversation_history = (
            [conversation_history[0]] + conversation_history[-20:]
        )

def get_response(user_text: str):
    asyncio.run(respond_streaming(user_text))

# ══════════════════════════════════════════════════════
#  LISTEN
# ══════════════════════════════════════════════════════
def listen() -> np.ndarray:
    ring_buffer   = collections.deque(maxlen=NUM_PADDING_FRAMES)
    triggered     = False
    voiced_frames = []

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32"
    ) as stream:
        while True:
            frame, _   = stream.read(FRAME_SIZE)
            frame_flat = frame.flatten()
            speech     = is_speech(frame_flat)

            if not triggered:
                ring_buffer.append((frame_flat, speech))
                num_voiced = len([f for f, s in ring_buffer if s])
                if num_voiced > 0.6 * ring_buffer.maxlen:
                    triggered = True
                    print("🎤 Listening...", end="\r")
                    voiced_frames.extend([f for f, _ in ring_buffer])
                    ring_buffer.clear()
            else:
                voiced_frames.append(frame_flat)
                ring_buffer.append((frame_flat, speech))
                num_unvoiced = len([f for f, s in ring_buffer if not s])

                if num_unvoiced > 0.90 * ring_buffer.maxlen:
                    print("                    ", end="\r")
                    audio    = np.concatenate(voiced_frames)
                    duration = len(audio) / SAMPLE_RATE

                    if duration < MIN_SPEECH_DURATION:
                        triggered     = False
                        voiced_frames = []
                        ring_buffer.clear()
                        continue

                    return audio

# ══════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════
async def startup():
    path = await generate_tts("Jarvis online. How can I help?")
    play_audio(path)

print("=" * 50)
print("         JARVIS ONLINE")
print("=" * 50)

import threading
prewarm_thread = threading.Thread(target=prewarm_ollama, daemon=True)
prewarm_thread.start()

asyncio.run(startup())
prewarm_thread.join()

print("\nReady! Speak to Jarvis...\n")

try:
    while True:
        audio     = listen()
        user_text = transcribe(audio)

        if not user_text:
            continue

        timestamp = time.strftime("%H:%M:%S")
        print(f"\n[{timestamp}] You: {user_text}")

        if any(cmd in user_text.lower() for cmd in EXIT_COMMANDS):
            async def bye():
                path = await generate_tts("Goodbye. Jarvis offline.")
                play_audio(path)
            asyncio.run(bye())
            break

        get_response(user_text)

except KeyboardInterrupt:
    print("\n\nJarvis offline.")
finally:
    pygame.mixer.quit()