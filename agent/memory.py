# agent/memory.py — Persistent Long Term Memory

import json
import os
import time
from datetime import datetime
from config import MEMORY_FILE, MAX_MEMORY_ENTRIES, CONVERSATION_TURNS

# ── Ensure data dir exists ─────────────────────────────
os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)

# ── Load / Save ────────────────────────────────────────
def _load() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {"facts": [], "episodes": [], "preferences": {}}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def _save(data: dict):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Remember a fact ────────────────────────────────────
def remember(fact: str, category: str = "general") -> str:
    """Store a fact in long term memory."""
    data = _load()
    entry = {
        "fact":      fact,
        "category":  category,
        "timestamp": datetime.now().isoformat(),
    }
    data["facts"].append(entry)

    # Trim if over limit
    if len(data["facts"]) > MAX_MEMORY_ENTRIES:
        data["facts"] = data["facts"][-MAX_MEMORY_ENTRIES:]

    _save(data)
    return f"Remembered: {fact}"

# ── Recall facts ───────────────────────────────────────
def recall(query: str = "", category: str = "") -> str:
    """Retrieve facts from memory. Filter by query or category."""
    data  = _load()
    facts = data.get("facts", [])

    if category:
        facts = [f for f in facts if f.get("category") == category]

    if query:
        query_lower = query.lower()
        facts = [f for f in facts if query_lower in f["fact"].lower()]

    if not facts:
        return "Nothing found in memory."

    # Return last 10 matching facts
    recent = facts[-10:]
    return "\n".join(f"- {f['fact']} ({f['category']})" for f in recent)

# ── Forget a fact ──────────────────────────────────────
def forget(query: str) -> str:
    """Remove facts matching query from memory."""
    data        = _load()
    before      = len(data["facts"])
    data["facts"] = [
        f for f in data["facts"]
        if query.lower() not in f["fact"].lower()
    ]
    removed = before - len(data["facts"])
    _save(data)
    return f"Removed {removed} memory entries matching '{query}'."

# ── Save episode (conversation summary) ───────────────
def save_episode(summary: str):
    """Save a summary of a conversation episode."""
    data = _load()
    data["episodes"].append({
        "summary":   summary,
        "timestamp": datetime.now().isoformat(),
    })
    # Keep last 100 episodes
    data["episodes"] = data["episodes"][-100:]
    _save(data)

# ── Get recent episodes ────────────────────────────────
def get_recent_episodes(n: int = 5) -> str:
    data     = _load()
    episodes = data.get("episodes", [])[-n:]
    if not episodes:
        return "No past conversations found."
    return "\n".join(
        f"[{e['timestamp'][:10]}] {e['summary']}" for e in episodes
    )

# ── Set preference ─────────────────────────────────────
def set_preference(key: str, value: str) -> str:
    data = _load()
    data["preferences"][key] = value
    _save(data)
    return f"Preference saved: {key} = {value}"

# ── Get preference ─────────────────────────────────────
def get_preference(key: str) -> str:
    data = _load()
    return data["preferences"].get(key, "Not set.")

# ── Build memory context for LLM ──────────────────────
def build_memory_context() -> str:
    """Return a summary of memory to inject into LLM context."""
    data        = _load()
    facts       = data.get("facts", [])[-20:]   # last 20 facts
    preferences = data.get("preferences", {})
    episodes    = data.get("episodes", [])[-3:]  # last 3 episodes

    parts = []

    if facts:
        fact_lines = "\n".join(f"- {f['fact']}" for f in facts)
        parts.append(f"Known facts about the user:\n{fact_lines}")

    if preferences:
        pref_lines = "\n".join(f"- {k}: {v}" for k, v in preferences.items())
        parts.append(f"User preferences:\n{pref_lines}")

    if episodes:
        ep_lines = "\n".join(
            f"- [{e['timestamp'][:10]}] {e['summary']}" for e in episodes
        )
        parts.append(f"Recent conversation history:\n{ep_lines}")

    return "\n\n".join(parts) if parts else ""