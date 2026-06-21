import os
import logging
from langchain.tools import tool

AVAILABLE_MODELS = {
    "fast": "ollama/qwen2.5:0.5b",
    "smart": "ollama/qwen3:8b",
    "code": "ollama/qwen3.5:9b",
    "cloud": "groq/llama3-70b-8192"
}

CURRENT_MODEL_MODE = "smart"

def switch_model(mode: str) -> str:
    global CURRENT_MODEL_MODE
    clean_mode = mode.lower().strip()
    if clean_mode not in AVAILABLE_MODELS:
        return f"Error: Mode '{clean_mode}' is not available. Available modes: {list(AVAILABLE_MODELS.keys())}"
        
    model_uri = AVAILABLE_MODELS[clean_mode]
    try:
        from friday.core.llm_agent import rebuild_agent
        rebuild_agent(model_uri=model_uri)
        CURRENT_MODEL_MODE = clean_mode
        logging.info(f"Switched model mode to '{clean_mode}' ({model_uri})")
        return f"Successfully switched to model mode: {clean_mode} ({model_uri})."
    except Exception as e:
        logging.error(f"Failed to switch to model mode '{clean_mode}': {e}")
        return f"Failed to switch to mode {clean_mode}: {e}"

@tool("switch_model_mode")
def switch_model_mode(mode: str) -> str:
    """
    Switches Friday's active brain/LLM reasoning model to a different mode at runtime.
    Modes available:
    - 'fast': Quick replies and simple chitchat (Qwen 0.5B).
    - 'smart': High reasoning quality for general tool utilization (Qwen 8B).
    - 'code': Specialized coding intelligence, best for writing software (Qwen 9B).
    - 'cloud': Cloud-hosted high-capacity LLaMA 70B model via Groq (requires internet and Groq API key).
    Input: the target mode string ('fast', 'smart', 'code', or 'cloud').
    """
    return switch_model(mode)
