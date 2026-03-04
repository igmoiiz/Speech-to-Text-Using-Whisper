# core/listen.py — VAD, Wake Word, Double Clap Detection

import sounddevice as sd
import numpy as np
import webrtcvad
import collections
from config import (
    SAMPLE_RATE, CHANNELS, FRAME_DURATION_MS,
    PADDING_DURATION_MS, MIN_SPEECH_DURATION,
    VAD_AGGRESSIVENESS, WAKE_WORDS,
    CLAP_THRESHOLD, CLAP_MIN_GAP, CLAP_MAX_GAP
)
from core.stt import transcribe

vad                = webrtcvad.Vad(VAD_AGGRESSIVENESS)
FRAME_SIZE         = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
NUM_PADDING_FRAMES = int(PADDING_DURATION_MS / FRAME_DURATION_MS)

# ── VAD helpers ────────────────────────────────────────
def is_speech(frame: np.ndarray) -> bool:
    pcm = (frame * 32767).astype(np.int16).tobytes()
    try:
        return vad.is_speech(pcm, SAMPLE_RATE)
    except:
        return False

# ── Active listening (VAD based) ──────────────────────
def listen() -> np.ndarray:
    """Record audio until natural speech pause. Returns audio array."""
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

# ── Double clap detection ──────────────────────────────
def detect_double_clap(audio_chunk: np.ndarray) -> bool:
    """Detect two sharp energy spikes within time window."""
    window_size = int(SAMPLE_RATE * 0.05)
    energies    = []

    for i in range(0, len(audio_chunk) - window_size, window_size):
        window = audio_chunk[i:i + window_size]
        energy = np.sqrt(np.mean(window ** 2))
        energies.append((i / SAMPLE_RATE, energy))

    spikes = [t for t, e in energies if e > CLAP_THRESHOLD]

    if len(spikes) < 2:
        return False

    for i in range(len(spikes) - 1):
        gap = spikes[i + 1] - spikes[i]
        if CLAP_MIN_GAP <= gap <= CLAP_MAX_GAP:
            return True

    return False

# ── Wake word detection ────────────────────────────────
def check_wake_word(audio: np.ndarray) -> bool:
    """Transcribe audio and check for wake word."""
    text = transcribe(audio).lower().strip()
    if text:
        print(f"  [idle] Heard: {text}")
    return any(wake in text for wake in WAKE_WORDS)

# ── Idle loop ──────────────────────────────────────────
def idle_loop() -> str:
    """
    Passively listens in 2-second chunks.
    Returns 'clap' or 'wake_word' when activated.
    """
    print("\n😴 Jarvis sleeping... (double clap or say wake word)\n")
    IDLE_CHUNK = int(SAMPLE_RATE * 2)

    while True:
        audio = sd.rec(
            IDLE_CHUNK,
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32"
        )
        sd.wait()
        audio_flat = audio.flatten()

        if detect_double_clap(audio_flat):
            print("👏 Double clap detected!")
            return "clap"

        if np.abs(audio_flat).mean() > 0.01:
            if check_wake_word(audio_flat):
                return "wake_word"