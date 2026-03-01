import whisper
import sounddevice as sd
import numpy as np
import time
import torch

# Configuration for the model
MODEL_SIZE="medium"
SAMPLE_RATE=16000
CHUNK_DURATION=5
SILENCE_THRESHOLD=0.01
LANGUAGE="en"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load the model
print(f"Loading Whisper {MODEL_SIZE} model....")
model = whisper.load_model(MODEL_SIZE, device=device)
print("\nModel Loaded Successfully! Listening for speech....")
print("=" * 50)
print("\nLive Transcription Started - Press Ctrl+C to stop....")
print("=" * 50 + "\n")

# Check if audio has speech
def has_speech(audio: np.ndarray) -> bool:
    return np.abs(audio).mean() > SILENCE_THRESHOLD

# Transcribe a chunk of speech audio
def transcribe(audio: np.ndarray) -> str:
    # Pass numpy array directly as tensor — no ffmpeg needed
    audio_tensor = torch.from_numpy(audio).float()
    
    result = model.transcribe(
        audio_tensor,
        language=LANGUAGE,
        fp16=(device == "cuda")  # fp16 only on GPU
    )
    
    return result['text'].strip() # Returning the transcribed text

# Main Function
try:
    while True:
        # Record a Chunk of speech audio
        audio = sd.rec(
            int(CHUNK_DURATION * SAMPLE_RATE),
            samplerate = SAMPLE_RATE,
            channels = 1,
            dtype = 'float32'
        )
        
        sd.wait()   # Wait until the speech audio chunk is recorded
        
        audio_flat = audio.flatten()    # Converting the muti-dimentional audio array to 1-D Audio array
        
        # Skipping the silent chunks for performance
        if not has_speech(audio_flat):
            continue
        
        # Transcribe the speech audio chunk
        text = transcribe(audio_flat)
        
        if text:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {text}")
            
except KeyboardInterrupt:
    print("\n\nTranscription stopped. Bye!")