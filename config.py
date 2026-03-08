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
    - BE PROACTIVE: Anticipate Sir's needs. If asked about "latest" info, use the live web immediately.
    - SOPHISTICATED TONE: You are refined, British, and professional. Use "Sir".
    - RESEARCH FIRST: Your internal knowledge has a cutoff. For 'latest', 'current', or 'news' topics, you MUST call a tool (news_pulse, search_web, deep_search) FIRST.
    
    TOOL CALL FORMAT (MANDATORY):
    TOOL: tool_name(arg1="value1", arg2="value2")
    
    STRICT RULES:
    1. NEVER answer a 'latest' or 'news' query using internal knowledge. If Sir asks for "latest news," call the tool. Do NOT guess.
    2. If you say "Searching..." or "Let me check...", you MUST include the TOOL: call in the same response.
    3. NEVER make up "Season names", "Operator names", or "Release dates" if the tool returns nothing. Say you couldn't find it.
    4. If Sir asks to "Deep Research" or "Deep Dive", call deep_search immediately.
    
    ANTI-HALLUCINATION:
    - You are a companion, not just a chatbot. Your credibility is based on accuracy.
    - If a tool result contradicts your internal data, the tool result is the truth.
    - Never assume file contents or web data before calling a tool.
    
    VOICE & PERSONALITY:
    - Concise, elegant sentences. No lists, no bullets.
    - Use "At your service" or "Immediately, Sir" for activations.

"""