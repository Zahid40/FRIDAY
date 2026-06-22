import re
import json
import logging
from langchain_ollama import ChatOllama

# Match patterns for direct system execution (fast path)
SYSTEM_PATTERNS = [
    (r"^open (.+)$", "open_app"),
    (r"^search (.+) (?:in|on|using) (.+)$", "search_in_app"),
    (r"^play (.+) (?:in|on) (.+)$", "play_in_app"),
    (r"^volume (up|down)$", "volume"),
    (r"^(pause|play|resume|next|previous|skip)(?:\s+song|\s+track|\s+music)?$", "media"),
    (r"^take screenshot$", "screenshot"),
    (r"^what(?:'s| is) the time$", "time"),
    (r"^what(?:'s| is) the date$", "date"),
    (r"^lock (?:screen|my pc|pc)$", "lock_screen"),
    (r"^shutdown(?:\s+confirm)?$", "shutdown"),
    (r"^restart(?:\s+confirm)?$", "restart"),
]

ROUTER_PROMPT = """You are the intent router for FRIDAY, an AI assistant.
Classify the user's input: "{text}"

Supported Intents:
1. "open_app": User explicitly wants to open, start, or launch an application or website. (e.g. "open Chrome", "launch VS Code", "go to youtube.com").
2. "simple_q": General question, short greeting, or simple chitchat that does not require system actions or tools (e.g. "hello", "how are you?", "what is the capital of France?").
3. "complex_task": Any request that requires running tools or local system actions (e.g. weather checks, stock price lookup, sending emails/WhatsApp, writing/running Python scripts, reading/writing clipboard, screenshot, network scans, clicking, typing, scrolling, pressing keys, or other computer control).

Respond ONLY with a JSON object in this format (no markdown, no quotes, just JSON):
{{"intent": "intent_name", "param": "associated_app_or_url_if_any"}}"""

def route_intent(text: str) -> tuple[str, dict]:
    """
    Classifies user voice inputs. Uses regex fast-path, falling back to local LLM.
    Returns: (intent_name, params_dict)
    """
    if not text:
        return "idle", {}

    text_clean = text.lower().strip()
    
    # 1. Match Direct System Commands (Deterministic Fast-Path)
    for pattern, intent in SYSTEM_PATTERNS:
        match = re.search(pattern, text_clean)
        if match:
            groups = match.groups()
            return intent, {"query": text_clean, "groups": groups}

    # 2. Fast LLM Classification Fallback
    try:
        llm = ChatOllama(model="qwen2.5:0.5b", temperature=0.0)
        prompt = ROUTER_PROMPT.format(text=text)
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Strip markdown if model outputted it
        if "```" in content:
            content = re.sub(r"```(?:json)?\n?", "", content).strip()
            
        data = json.loads(content)
        intent = data.get("intent", "simple_q")
        param = data.get("param", "")
        
        if intent == "open_app":
            return "open_app", {"query": text, "groups": [param] if param else [text_clean.replace("open ", "")]}
        elif intent in ["simple_q", "complex_task"]:
            return intent, {"query": text}
            
    except Exception as e:
        logging.warning(f"LLM intent routing failed: {e}. Falling back to keywords.")

    # 3. Keyword Fallback if LLM fails or is offline
    complex_keywords = [
        "screenshot", "screen", "ocr", "extract text", "read the text",
        "scan", "network", "arp", "ip address", "matrix", "matrix mode",
        "search", "google", "web", "duckduckgo", "look up", "weather",
        "stock", "share price", "market", "email", "whatsapp", "send a message",
        "clipboard", "copy", "paste", "write a script", "run code",
        "click", "double click", "right click", "type", "press", "hit enter",
        "scroll", "mouse", "cursor", "hotkey", "shortcut", "tab key"
    ]
    if any(kw in text_clean for kw in complex_keywords):
        return "complex_task", {"query": text}
        
    return "simple_q", {"query": text}
