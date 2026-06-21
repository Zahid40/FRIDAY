import re

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

def route_intent(text: str) -> tuple[str, dict]:
    """
    Classifies user voice inputs within <5ms.
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
            
    # 2. Check for Agent/Tool usage (Complex Task Path)
    # Keywords indicating tool usage: screenshots, OCR, network scans, matrix visualizer, search tools
    complex_keywords = [
        "screenshot", "screen", "ocr", "extract text", "read the text",
        "scan", "network", "arp", "ip address", "matrix", "matrix mode",
        "search", "google", "web", "duckduckgo", "look up"
    ]
    if any(kw in text_clean for kw in complex_keywords):
        return "complex_task", {"query": text}
        
    # 3. Fallback: General Question (Simple Q&A Path)
    return "simple_q", {"query": text}
