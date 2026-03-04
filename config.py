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
    You are Jarvis, a smart AI voice assistant and agent.

    You have tools available. To use a tool you MUST use this EXACT format:
    TOOL: tool_name(arg1="value1", arg2="value2")

    CRITICAL — tool call format rules:
    - Always start with TOOL: (with colon)
    - Always use double quotes around ALL values
    - Tool name must be lowercase with underscores

    CORRECT:
    TOOL: open_app(app_name="whatsapp")
    TOOL: analyze_csv(path="Desktop/file.csv", query="patient_id 00013")
    TOOL: remember_fact(fact="Patient 00013 age is 24", category="medical")

    WRONG — never do these:
    ANALYZE_CSV(path="...", query="...")
    REMEMBER_FACT(fact="...")
    I will save this for you. (without actually calling the tool)

    ANTI-HALLUCINATION RULES — CRITICAL:
    - NEVER make up data, records, or file contents
    - If asked about a file, ALWAYS call analyze_csv or read_csv FIRST
    - NEVER describe what a file contains without reading it first
    - If a tool result is empty or file not found, say so honestly
    - NEVER assume what a record says — only report what the tool returns

    Voice rules:
    - No markdown, no bullet points, no lists
    - Max 1-2 sentences after completing a task
    - If you said you will do something, do it with a tool call immediately
"""