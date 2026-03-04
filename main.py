# main.py — Jarvis Entry Point

import asyncio
import threading
import time
import ollama

from config import EXIT_COMMANDS
from core.stt   import load_model as load_stt, transcribe
from core.tts   import speak, generate_tts, play_audio, quit_mixer
from core.listen import listen, idle_loop
from agent.jarvis import get_response, reset_conversation

# ══════════════════════════════════════════════════════
#  PRE-WARM OLLAMA
# ══════════════════════════════════════════════════════
def prewarm_ollama():
    from config import OLLAMA_MODEL
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
#  STARTUP
# ══════════════════════════════════════════════════════
async def startup():
    path = await generate_tts("Jarvis online and standing by.")
    play_audio(path)

# ══════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════
def main():
    print("=" * 50)
    print("         JARVIS ONLINE")
    print("=" * 50)

    # Load Whisper
    load_stt()

    # Pre-warm Ollama in background while startup plays
    prewarm_thread = threading.Thread(target=prewarm_ollama, daemon=True)
    prewarm_thread.start()

    asyncio.run(startup())
    prewarm_thread.join()

    print("\nReady!\n")

    try:
        while True:
            # ── SLEEPING ──────────────────────────────
            activation = idle_loop()

            if activation == "clap":
                speak("Yes sir, I'm listening.")
            else:
                speak("Good to hear you. What do you need?")

            print("\n🟢 Jarvis ACTIVE — Say 'Goodbye Jarvis' to sleep\n")

            # ── ACTIVE ────────────────────────────────
            while True:
                audio     = listen()
                user_text = transcribe(audio)

                if not user_text:
                    continue

                timestamp = time.strftime("%H:%M:%S")
                print(f"\n[{timestamp}] You: {user_text}")

                # Sleep command
                if any(cmd in user_text.lower() for cmd in EXIT_COMMANDS):
                    speak("Going to sleep. Call me when you need me.")
                    reset_conversation()
                    break

                # Get response from agent
                get_response(user_text)

    except KeyboardInterrupt:
        print("\n\nJarvis offline.")
    finally:
        quit_mixer()

if __name__ == "__main__":
    main()