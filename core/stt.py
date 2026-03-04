# core/stt.py — Whisper Speech to Text

import whisper
import numpy as np
import torch
from config import WHISPER_MODEL, LANGUAGE

_model  = None
_device = None

def load_model():
    global _model, _device
    _device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {_device}")
    print(f"Loading Whisper {WHISPER_MODEL}...")
    _model = whisper.load_model(WHISPER_MODEL, device=_device)
    print("Whisper ready!")

def transcribe(audio: np.ndarray) -> str:
    if _model is None:
        raise RuntimeError("STT model not loaded. Call load_model() first.")
    audio_tensor = torch.from_numpy(audio).float()
    result = _model.transcribe(
        audio_tensor,
        language=LANGUAGE,
        fp16=(_device == "cuda"),
        temperature=0,
        beam_size=1,
        best_of=1,
    )
    return result["text"].strip()

def get_device() -> str:
    return _device