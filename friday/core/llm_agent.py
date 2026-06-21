import os
import sys
import logging
import subprocess
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import AgentExecutor, create_tool_calling_agent

# Add the workspace root directory to python path to import tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.time import get_time
from tools.OCR import read_text_from_latest_image
from tools.arp_scan import arp_scan_terminal
from tools.duckduckgo import duckduckgo_search_tool
from tools.matrix import matrix_mode
from tools.screenshot import take_screenshot
from friday.character.loader import build_system_prompt

# Define model names
FAST_MODEL = "qwen2.5:0.5b"

def get_smart_model_name() -> str:
    """Checks the list of installed Ollama models and selects the best available smart model."""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            output = result.stdout.lower()
            if "qwen2.5:7b" in output:
                return "qwen2.5:7b"
            elif "qwen3:8b" in output:
                return "qwen3:8b"
    except Exception:
        pass
    return "qwen3:8b"  # Default fallback

SMART_MODEL = get_smart_model_name()
logging.info(f"⏳ Dynamic Model Selection: Fast={FAST_MODEL}, Smart={SMART_MODEL}")

# Initialize LLMs
try:
    fast_llm = ChatOllama(model=FAST_MODEL, temperature=0.1)
except Exception as e:
    logging.error(f"❌ Failed to load Fast model: {e}")
    fast_llm = None

try:
    smart_llm = ChatOllama(model=SMART_MODEL, reasoning=False)
except Exception as e:
    logging.error(f"❌ Failed to load Smart model: {e}")
    smart_llm = None

# Shared memory for context preservation (6 turns window)
memory = ConversationBufferWindowMemory(
    k=6, memory_key="chat_history", return_messages=True
)

# Available tools
tools = [get_time, arp_scan_terminal, read_text_from_latest_image, duckduckgo_search_tool, matrix_mode, take_screenshot]

# Prompt Templates
fast_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are FRIDAY. You must be calm, minimal, and direct. Keep voice answers under 2 short sentences. Do not use emojis, exclamation marks, or polite phrases like 'Certainly!', 'Great question!', or 'Sure!'."
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}")
    ]
)

smart_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(),
        ),
        (
            "system",
            "IMPORTANT personality override: You are FRIDAY. You must be calm, minimal, and direct. Keep voice answers under 2 short sentences. Do not use emojis, exclamation marks, or polite phrases like 'Certainly!', 'Great question!', or 'Sure!'."
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# Initialize LangChain Agent
if smart_llm:
    agent = create_tool_calling_agent(llm=smart_llm, tools=tools, prompt=smart_prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=3,
        early_stopping_method="generate",
        memory=memory,
    )
else:
    executor = None

def get_simple_response(text: str) -> str:
    """Uses the fast 0.5B model for instant answers (<400ms)."""
    if not fast_llm:
        return "Fast model offline."
    try:
        chat_history = memory.load_memory_variables({})["chat_history"]
        messages = fast_prompt.format_messages(input=text, chat_history=chat_history)
        response = fast_llm.invoke(messages)
        content = response.content
        memory.save_context({"input": text}, {"output": content})
        return content.strip()
    except Exception as e:
        logging.error(f"❌ Error getting response from fast model: {e}")
        return "Error getting response from fast model."

def run_complex_agent(text: str, callbacks=None) -> str:
    """Uses the smart 8B/7B model with the LangChain agent for complex queries."""
    if not executor:
        return "Smart agent executor offline."
    try:
        # Dynamically refresh model name if qwen2.5:7b was installed in the background
        current_smart = get_smart_model_name()
        if current_smart != executor.agent.runnable.first.model:
            logging.info(f"🔄 Switching executor smart model: {executor.agent.runnable.first.model} -> {current_smart}")
            executor.agent.runnable.first.model = current_smart
            
        response = executor.invoke(
            {"input": text},
            {"callbacks": callbacks} if callbacks else {}
        )
        return response["output"].strip()
    except Exception as e:
        logging.error(f"❌ Error running agent executor: {e}")
        raise e
