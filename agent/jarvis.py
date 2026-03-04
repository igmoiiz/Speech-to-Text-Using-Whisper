# agent/jarvis.py — Agent Brain: Tool Calling + Streaming Response

import ollama
import asyncio
import re
import json
from config import (
    OLLAMA_MODEL, AGENT_SYSTEM_PROMPT,
    MAX_TOOL_CALLS, CONVERSATION_TURNS
)
from core.tts import generate_tts, play_audio
from agent.memory import (
    build_memory_context, remember, save_episode, recall
)
from agent.tools import TOOL_DESCRIPTIONS, execute_tool

# Short term conversation history
_conversation: list = []

def _build_system_prompt() -> str:
    """Build dynamic system prompt with memory context."""
    memory_ctx = build_memory_context()
    prompt     = AGENT_SYSTEM_PROMPT + "\n\n" + TOOL_DESCRIPTIONS
    if memory_ctx:
        prompt += f"\n\n--- YOUR MEMORY ---\n{memory_ctx}\n---"
    return prompt

def _trim_conversation():
    """Keep conversation to last N turns."""
    global _conversation
    max_msgs = CONVERSATION_TURNS * 2
    if len(_conversation) > max_msgs:
        _conversation = _conversation[-max_msgs:]

# ── Fix malformed tool calls from LLM ─────────────────
def normalize_tool_call(text: str) -> str:
    """
    Auto-correct common LLM tool call formatting mistakes.
    Converts any variation into: TOOL: tool_name(arg="value")
    """
    # Pattern: OPEN_APP(WhatsApp) or open_app(WhatsApp) without TOOL: prefix
    def fix_match(m):
        func = m.group(1).lower()
        args = m.group(2).strip().strip('"\'')

        # Map common arg-less calls to correct format
        arg_map = {
            "open_app":          f'app_name="{args}"',
            "close_app":         f'app_name="{args}"',
            "search_web":        f'query="{args}"',
            "open_website":      f'url="{args}"',
            "run_command":       f'command="{args}"',
            "create_note":       f'title="{args}", content=""',
            "read_note":         f'title="{args}"',
            "delete_note":       f'title="{args}"',
            "kill_process":      f'name="{args}"',
            "install_package":   f'package="{args}"',
            "run_python":        f'code="{args}"',
            "remember_fact":     f'fact="{args}"',
            "recall_memory":     f'query="{args}"',
        }

        formatted_args = arg_map.get(func, f'"{args}"') if args else ""
        return f'TOOL: {func}({formatted_args})'

    # Fix UPPERCASE_FUNC(arg) or lowercase_func(arg) missing TOOL: prefix
    text = re.sub(
        r'(?<!TOOL:\s{0,10})\b([A-Z_]{3,}|[a-z_]{3,})\(([^)]*)\)',
        fix_match,
        text
    )

    return text

# ── Parse tool call from LLM output ───────────────────
def parse_tool_call(text: str):
    """
    Parse TOOL: tool_name(arg1="val1", arg2="val2") from text.
    Returns (tool_name, kwargs) or (None, None).
    """
    # First normalize any malformed tool calls
    text = normalize_tool_call(text)

    pattern = r'TOOL:\s*(\w+)\((.*?)\)'
    match   = re.search(pattern, text, re.DOTALL)
    if not match:
        return None, None

    tool_name = match.group(1).lower()
    args_str  = match.group(2).strip()
    kwargs    = {}

    if args_str:
        kv_pattern = r'(\w+)\s*=\s*(?:"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*) \'|([^,\)]+))'
        for kv in re.finditer(kv_pattern, args_str):
            key   = kv.group(1)
            value = kv.group(2) or kv.group(3) or kv.group(4)
            if value:
                kwargs[key] = value.strip().strip('"\'')

        # If no kwargs parsed but there are args, use positional fallback
        if not kwargs and args_str:
            # Map first positional arg to most common parameter name
            first_arg = args_str.strip().strip('"\'')
            param_defaults = {
                "open_app":      "app_name",
                "close_app":     "app_name",
                "search_web":    "query",
                "open_website":  "url",
                "run_command":   "command",
                "read_note":     "title",
                "delete_note":   "title",
                "kill_process":  "name",
                "remember_fact": "fact",
                "recall_memory": "query",
                "calculate":     "expression",
                "fetch_webpage": "url",
                "run_python":    "code",
            }
            param = param_defaults.get(tool_name, "query")
            kwargs[param] = first_arg

    return tool_name, kwargs

# ── Auto extract and remember facts ───────────────────
def auto_remember(user_text: str, assistant_reply: str):
    """
    Use LLM to intelligently extract and categorize
    memorable facts from the conversation.
    """
    words = user_text.split()

    # Too short
    if len(words) < 6:
        return

    # Skip obvious commands
    skip_starters = [
        "open ", "close ", "play ", "stop ", "pause ",
        "search for", "look up", "find me", "show me",
        "what time", "what date", "take a screenshot",
        "turn off", "turn on", "set a timer", "set a reminder",
        "run ", "execute ", "calculate ", "convert ",
        "read my", "list my", "delete ", "rename ",
        "can you open", "please open", "could you open",
    ]
    if any(user_text.lower().startswith(p) for p in skip_starters):
        return
    if any(user_text.lower().startswith(p) for p in ["can you", "could you", "please", "would you"]):
        # Still skip if it's a simple action command
        action_words = ["open", "close", "search", "find", "show", "play", "run", "delete"]
        second_word  = user_text.lower().split()[1] if len(user_text.split()) > 1 else ""
        third_word   = user_text.lower().split()[2] if len(user_text.split()) > 2 else ""
        if second_word in action_words or third_word in action_words:
            return

    # Only run if message likely contains personal info
    memory_signals = [
        "my name", "i am", "i'm", "i live", "i work",
        "i study", "i like", "i love", "i hate", "i prefer",
        "i need", "i want", "i have", "my ", "remember",
        "don't forget", "keep in mind", "note that",
        "birthday", "age", "years old", "i was born",
    ]
    if not any(signal in user_text.lower() for signal in memory_signals):
        return

    extraction_prompt = f"""
Analyze this message and extract ONLY genuinely useful facts worth remembering long-term.

Message: "{user_text}"

Rules:
- Extract specific, concrete facts only (names, dates, places, preferences, goals, skills)
- Ignore filler words, greetings, and commands like "remember this"
- Each fact must be a clean, standalone sentence
- Assign a category: name / age / location / education / work / preference / goal / skill / birthday / relationship / other
- If nothing is worth remembering, return empty JSON array

Respond ONLY with a JSON array like:
[
  {{"fact": "User's name is Abdul Moiz", "category": "name"}},
  {{"fact": "User is 19 years old, turning 20 on October 31st", "category": "birthday"}}
]

No explanation, no markdown, just the JSON array.
"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": extraction_prompt}],
            options={"num_predict": 200, "temperature": 0}
        )

        raw = response["message"]["content"].strip()
        raw = re.sub(r"```json|```", "", raw).strip()

        json_match = re.search(r'\[.*\]', raw, re.DOTALL)
        if json_match:
            raw = json_match.group(0)

        facts = json.loads(raw)

        for item in facts:
            fact     = item.get("fact", "").strip()
            category = item.get("category", "general").strip()
            if fact:
                remember(fact, category)
                print(f"  🧠 Remembered [{category}]: {fact}")

    except json.JSONDecodeError:
        if len(words) > 8:
            remember(f"User said: {user_text.strip()}", "general")
    except Exception as e:
        print(f"  Memory extraction failed: {e}")

# ── Streaming response with tool calling ──────────────
async def respond_streaming(user_text: str):
    global _conversation

    _conversation.append({"role": "user", "content": user_text})
    _trim_conversation()

    # Run auto_remember in background — don't block response
    asyncio.get_event_loop().run_in_executor(
        None, auto_remember, user_text, ""
    )

    messages = [
        {"role": "system", "content": _build_system_prompt()}
    ] + _conversation

    tts_queue  = asyncio.Queue()
    done_event = asyncio.Event()
    tokens     = []
    loop       = asyncio.get_event_loop()

    def split_sentences(text: str) -> list:
        parts = re.split(r'(?<=[.!?])\s+', text.strip())
        return [p.strip() for p in parts if p.strip()]

    # ── Tool execution loop ────────────────────────────
    async def run_with_tools() -> str:
        nonlocal messages
        full_response = ""
        tool_calls    = 0

        while tool_calls < MAX_TOOL_CALLS:
            buffer   = ""
            response = ""

            print("  Jarvis: ", end="", flush=True)

            stream = ollama.chat(
                model=OLLAMA_MODEL,
                messages=messages,
                stream=True,
                options={
                    # Shorter after tool calls — just need confirmation
                    "num_predict":    60 if tool_calls > 0 else 150,
                    "temperature":    0.7,
                    "top_p":          0.9,
                    "repeat_penalty": 1.1,
                }
            )

            for chunk in stream:
                token     = chunk["message"]["content"]
                response += token
                tokens.append(token)
                buffer   += token
                print(token, end="", flush=True)

                # Only stream TTS if no tool call is forming
                if "TOOL:" not in response and not re.search(
                    r'\b[A-Z_]{3,}\(', response
                ):
                    sentences = split_sentences(buffer)
                    if len(sentences) > 1:
                        to_speak = " ".join(sentences[:-1])
                        buffer   = sentences[-1]
                        path     = await generate_tts(to_speak)
                        await tts_queue.put(path)

            print()
            full_response += response

            # Normalize + parse tool call
            normalized         = normalize_tool_call(response)
            tool_name, kwargs  = parse_tool_call(normalized)

            if tool_name:
                # Flush any spoken buffer before executing tool
                if buffer.strip() and "TOOL:" not in buffer:
                    path = await generate_tts(buffer.strip())
                    await tts_queue.put(path)
                    buffer = ""

                print(f"  🔧 Tool: {tool_name}({kwargs})")
                tool_result = execute_tool(tool_name, kwargs or {})
                print(f"  ✅ Result: {tool_result[:150]}")

                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role":    "user",
                    "content": (
                        f"Tool result: {tool_result}\n\n"
                        f"Reply in ONE short sentence confirming what was done. "
                        f"No markdown. Spoken aloud."
                    )
                })
                tool_calls += 1
                tokens.clear()
                buffer = ""
            else:
                # No tool call — speak remaining buffer and finish
                if buffer.strip():
                    path = await generate_tts(buffer.strip())
                    await tts_queue.put(path)
                break

        done_event.set()
        return full_response

    # ── Audio consumer ─────────────────────────────────
    async def consumer():
        while True:
            try:
                path = tts_queue.get_nowait()
            except asyncio.QueueEmpty:
                if done_event.is_set() and tts_queue.empty():
                    break
                await asyncio.sleep(0.02)
                continue
            await loop.run_in_executor(None, play_audio, path)

    # Run producer + consumer concurrently
    final_reply, _ = await asyncio.gather(
        run_with_tools(),
        consumer()
    )

    print("\n")

    # Save clean reply to history (strip tool calls)
    clean_reply = re.sub(r'TOOL:\s*\w+\([^)]*\)', '', final_reply).strip()
    _conversation.append({"role": "assistant", "content": clean_reply})
    _trim_conversation()

    # Save episode summary every 10 turns
    if len(_conversation) % 10 == 0:
        save_episode(f"User asked: {user_text[:100]}")

def get_response(user_text: str):
    """Entry point — run the async agent."""
    asyncio.run(respond_streaming(user_text))

def reset_conversation():
    """Clear short term memory."""
    global _conversation
    _conversation = []