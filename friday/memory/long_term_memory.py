import os
import json
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "persistent_memory.json"

def _initialize_memory():
    if not MEMORY_FILE.exists():
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"chat_history": [], "user_facts": []}, f, indent=4)

def load_memory() -> dict:
    _initialize_memory()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"chat_history": [], "user_facts": []}

def save_memory(data: dict):
    _initialize_memory()
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        import logging
        logging.error(f"Failed to save memory file: {e}")

def add_chat_turn(role: str, content: str, max_turns: int = 20):
    data = load_memory()
    history = data.get("chat_history", [])
    history.append({"role": role, "content": content})
    # Keep only the last `max_turns`
    if len(history) > max_turns:
        history = history[-max_turns:]
    data["chat_history"] = history
    save_memory(data)

def get_chat_history() -> list:
    data = load_memory()
    return data.get("chat_history", [])

def add_user_fact(fact: str) -> str:
    data = load_memory()
    facts = data.get("user_facts", [])
    fact_clean = fact.strip()
    if fact_clean and fact_clean not in facts:
        facts.append(fact_clean)
        data["user_facts"] = facts
        save_memory(data)
        return f"I will remember that: {fact_clean}"
    return "I already know that or the fact was empty."

def search_user_facts(query: str) -> list:
    data = load_memory()
    facts = data.get("user_facts", [])
    if not query or query.strip() == "":
        return facts
    
    keywords = [kw.lower() for kw in query.split() if len(kw) > 2]
    if not keywords:
        return facts
        
    matched = []
    for fact in facts:
        fact_lower = fact.lower()
        if any(kw in fact_lower for kw in keywords):
            matched.append(fact)
    return matched
