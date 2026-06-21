from langchain.tools import tool
from friday.core.model_manager import switch_model

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
