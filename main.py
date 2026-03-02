import whisper
import sounddevice as sd
import numpy as np
import torch
import time
import collections
import webrtcvad

# ── Config ─────────────────────────────────────────────
MODEL_SIZE         = "medium"
SAMPLE_RATE        = 16000      # webrtcvad requires 16kHz
CHANNELS           = 1
VAD_AGGRESSIVENESS = 2          # 0=least aggressive, 3=most aggressive
FRAME_DURATION_MS  = 30         # 10, 20, or 30ms (webrtcvad requirement)
PADDING_DURATION_MS = 1200      # how long to wait after speech stops (ms)
MIN_SPEECH_DURATION = 0.5       # ignore sounds shorter than this (seconds)
LANGUAGE           = None

# ── Load Model ─────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")
print(f"Loading Whisper {MODEL_SIZE} model....")
model = whisper.load_model(MODEL_SIZE, device=device)
print("Model Loaded! Listening...\n")
print("=" * 50)
print("  JARVIS MODE — Speak freely, I'm listening...")
print("=" * 50 + "\n")

# ── Setup VAD ──────────────────────────────────────────
vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

# Frame size in samples
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)

# How many frames fit in the padding window
NUM_PADDING_FRAMES = int(PADDING_DURATION_MS / FRAME_DURATION_MS)

# ── Transcribe ─────────────────────────────────────────
def transcribe(audio: np.ndarray) -> str:
    audio_tensor = torch.from_numpy(audio).float()
    result = model.transcribe(
        audio_tensor,
        language=LANGUAGE,
        fp16=(device == "cuda"),
    )
    return result["text"].strip()

# ── VAD Stream ─────────────────────────────────────────
def is_speech(frame: np.ndarray) -> bool:
    # Convert float32 → int16 PCM bytes for webrtcvad
    pcm = (frame * 32767).astype(np.int16).tobytes()
    try:
        return vad.is_speech(pcm, SAMPLE_RATE)
    except:
        return False

# ── Main Loop ──────────────────────────────────────────
print("Waiting for you to speak...\n")

try:
    while True:
        # Ring buffer holds recent frames to catch speech start
        ring_buffer = collections.deque(maxlen=NUM_PADDING_FRAMES)
        triggered = False       # are we currently recording speech?
        voiced_frames = []      # all frames of the current utterance

        # Open audio stream
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32") as stream:
            while True:
                # Read one frame
                frame, _ = stream.read(FRAME_SIZE)
                frame_flat = frame.flatten()
                speech = is_speech(frame_flat)

                if not triggered:
                    # Not recording yet — watch ring buffer for speech
                    ring_buffer.append((frame_flat, speech))
                    num_voiced = len([f for f, s in ring_buffer if s])

                    # If >60% of ring buffer is speech → start recording
                    if num_voiced > 0.6 * ring_buffer.maxlen:
                        triggered = True
                        print("🎤 Listening...", end="\r")
                        # Include buffered frames so we don't miss the start
                        voiced_frames.extend([f for f, _ in ring_buffer])
                        ring_buffer.clear()
                else:
                    # Currently recording — collect frames
                    voiced_frames.append(frame_flat)
                    ring_buffer.append((frame_flat, speech))
                    num_unvoiced = len([f for f, s in ring_buffer if not s])

                    # If >90% of ring buffer is silence → stop recording
                    if num_unvoiced > 0.90 * ring_buffer.maxlen:
                        print("                    ", end="\r")  # clear indicator
                        triggered = False

                        # Build full audio array
                        audio = np.concatenate(voiced_frames)

                        # Ignore very short sounds (coughs, clicks etc)
                        duration = len(audio) / SAMPLE_RATE
                        if duration < MIN_SPEECH_DURATION:
                            voiced_frames = []
                            ring_buffer.clear()
                            continue

                        # Transcribe
                        text = transcribe(audio)
                        if text:
                            timestamp = time.strftime("%H:%M:%S")
                            print(f"[{timestamp}] {text}\n")

                        # Reset for next utterance
                        voiced_frames = []
                        ring_buffer.clear()
                        break  # restart outer loop for fresh stream

except KeyboardInterrupt:
    print("\n\nJarvis offline. Bye!")