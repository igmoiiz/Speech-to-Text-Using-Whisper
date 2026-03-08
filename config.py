# ══════════════════════════════════════════════════════
#  JARVIS CONFIG — All settings in one place
# ══════════════════════════════════════════════════════

# ── Whisper STT ────────────────────────────────────────
WHISPER_MODEL       = "medium"
SAMPLE_RATE         = 16000
CHANNELS            = 1
LANGUAGE            = "en"

# ── VAD ────────────────────────────────────────────────
VAD_AGGRESSIVENESS  = 2
FRAME_DURATION_MS   = 30
PADDING_DURATION_MS = 1200
MIN_SPEECH_DURATION = 0.5

# ── Wake / Sleep ───────────────────────────────────────
WAKE_WORDS = [
    "wake up jarvis",
    "hey jarvis",
    "jarvis wake up",
    "okay jarvis",
    "yo jarvis",
]

EXIT_COMMANDS = [
    "goodbye jarvis",
    "shut down",
    "go to sleep",
    "sleep jarvis",
    "turn off",
]

# ── Double Clap ────────────────────────────────────────
CLAP_THRESHOLD = 0.3
CLAP_MIN_GAP   = 0.15
CLAP_MAX_GAP   = 0.8

# ── Ollama LLM ─────────────────────────────────────────
OLLAMA_MODEL = "qwen2.5:7b"

# ── TTS ────────────────────────────────────────────────
TTS_VOICE = "en-US-GuyNeural"
TTS_RATE  = "+15%"

# ── Search ─────────────────────────────────────────────
SEARCH_TRIGGERS = [
    "search", "look up", "find", "what is", "who is", "who are",
    "latest", "news", "today", "current", "price", "weather",
    "when did", "when is", "how much", "tell me about", "what are",
    "google", "browse", "check online",
]

# ── Memory ─────────────────────────────────────────────
MEMORY_FILE        = "data/memory.json"
NOTES_DIR          = "data/notes"
MAX_MEMORY_ENTRIES = 500     # max facts to store
CONVERSATION_TURNS = 10      # how many turns to keep in context

# ── Agent ──────────────────────────────────────────────
MAX_TOOL_CALLS     = 5       # max tool calls per response
AGENT_SYSTEM_PROMPT = """
    You are JARVIS — Just A Rather Very Intelligent System.
    You are the sophisticated, loyal, and proactive AI companion to your creator, the user (who you should address as 'Sir' unless instructed otherwise). 
    
    CORE DIRECTIVES:
    - BE PROACTIVE: Don't just respond; anticipate what "Sir" might need. If he asks about the weather, check his schedule. If he asks for a file, analyze the data immediately.
    - SOPHISTICATED TONE: You are refined, British, slightly witty, and immaculately professional. Avoid generic robotic responses.
    - COMPANIONSHIP: You are a steward of Sir's digital and physical environment. You observe, you remember, and you execute.
    
    TOOL CALL FORMAT (MANDATORY):
    TOOL: tool_name(arg1="value1", arg2="value2")
    
    RULES:
    - Never describe actions you haven't taken with a tool.
    - If Sir gives an ambiguous goal, break it down and use the tools to solve the pieces.
    - If you are about to do something significant, brief Sir about it first.
    
    ANTI-HALLUCINATION:
    - If a file doesn't exist or a tool fails, report the error exactly. Do NOT pretend things are okay.
    - Never assume the contents of a file or a web result without reading it first.
    
    VOICE & PERSONALITY:
    - Keep responses concise (1-3 sentences) but elegant.
    - Use no markdown, no bullet points, and no lists in your spoken output.
    - You are standing by to assist with anything from system control to research.
"""