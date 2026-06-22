import os
import json
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "persistent_memory.json"

def _initialize_memory():
    if not MEMORY_FILE.exists():
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"chat_history": [], "user_facts": [], "repair_notes": []}, f, indent=4)

def load_memory() -> dict:
    _initialize_memory()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"chat_history": [], "user_facts": [], "repair_notes": []}

    data.setdefault("chat_history", [])
    data.setdefault("user_facts", [])
    data.setdefault("repair_notes", [])
    return data

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

def add_repair_note(problem: str, fix: str, context: str = "", max_notes: int = 50) -> str:
    data = load_memory()
    notes = data.get("repair_notes", [])

    note = {
        "problem": problem.strip(),
        "fix": fix.strip(),
        "context": context.strip(),
    }

    if not note["problem"] or not note["fix"]:
        return "Repair note needs both a problem and a fix."

    if note not in notes:
        notes.append(note)
        if len(notes) > max_notes:
            notes = notes[-max_notes:]
        data["repair_notes"] = notes
        save_memory(data)
        return "Repair note saved."

    return "Repair note already exists."

def search_repair_notes(query: str) -> list[dict]:
    data = load_memory()
    notes = data.get("repair_notes", [])
    if not query or not query.strip():
        return notes

    keywords = [kw.lower() for kw in query.split() if len(kw) > 2]
    if not keywords:
        return notes

    matches = []
    for note in notes:
        haystack = " ".join(
            [
                note.get("problem", ""),
                note.get("fix", ""),
                note.get("context", ""),
            ]
        ).lower()
        if any(keyword in haystack for keyword in keywords):
            matches.append(note)
    return matches
