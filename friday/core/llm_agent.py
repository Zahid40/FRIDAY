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

from friday.skills.time import get_time
from friday.skills.OCR import read_text_from_latest_image
from friday.skills.arp_scan import arp_scan_terminal
from friday.skills.duckduckgo import duckduckgo_search_tool
from friday.skills.matrix import matrix_mode
from friday.skills.screenshot import take_screenshot
from friday.character.loader import build_system_prompt

# Import upgraded skills/tools
from friday.skills.memory_tools import remember_user_fact, recall_user_facts
from friday.skills.file_manager import file_system_manager
from friday.skills.smart_launcher import smart_launcher
from friday.skills.communicator import send_email, send_whatsapp_message
from friday.skills.clipboard import clipboard_tool
from friday.skills.code_runner import run_python_code
from friday.skills.stock_checker import stock_market_checker
from friday.skills.weather_checker import get_tool as get_weather_tool
weather_checker = get_weather_tool()

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

def load_persistent_history_to_memory():
    try:
        from friday.memory.long_term_memory import get_chat_history
        history = get_chat_history()
        memory.clear()
        for turn in history:
            role = turn.get("role")
            content = turn.get("content")
            if role == "human":
                memory.chat_memory.add_user_message(content)
            elif role == "ai":
                memory.chat_memory.add_ai_message(content)
        logging.info(f"Loaded {len(history)} persistent chat turns into memory.")
    except Exception as e:
        logging.error(f"Failed to load persistent history to memory: {e}")

# Load persistent history on startup
load_persistent_history_to_memory()

# Available tools
from friday.tool_manager import load_all_tools

# Load all tools dynamically
tools = load_all_tools()

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
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# Rebuild agent executor dynamically at runtime
def rebuild_agent(model_uri: str = None):
    global smart_llm, smart_prompt, executor, tools
    
    if model_uri:
        logging.info(f"Rebuilding agent with model: {model_uri}")
        if model_uri.startswith("ollama/"):
            model_name = model_uri.split("/", 1)[1]
            smart_llm = ChatOllama(model=model_name, reasoning=False)
        elif model_uri.startswith("groq/"):
            model_name = model_uri.split("/", 1)[1]
            api_key = os.environ.get("GROQ_API_KEY")
            from langchain_openai import ChatOpenAI
            smart_llm = ChatOpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
                model=model_name
            )
        else:
            raise ValueError(f"Unknown model URI prefix: {model_uri}")
            
    # Reload prompt from updated config files
    smart_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                build_system_prompt(),
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    
    # Reload tools dynamically
    tools = load_all_tools()
    
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
        logging.info("Agent executor successfully rebuilt.")
    else:
        executor = None

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

# Register tool reloading callback
from friday.tool_manager import register_reload_callback
register_reload_callback(lambda updated_tools: rebuild_agent(model_uri=None))

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
        # Dynamically refresh model name if qwen2.5:7b was installed in the background (only in smart mode)
        from friday.core.model_manager import CURRENT_MODEL_MODE
        if CURRENT_MODEL_MODE == "smart":
            current_smart = get_smart_model_name()
            if hasattr(executor.agent.runnable.first, "model") and current_smart != executor.agent.runnable.first.model:
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

