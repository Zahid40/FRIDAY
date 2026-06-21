import os
import logging
import time
import tempfile
import re
from dotenv import load_dotenv
import speech_recognition as sr
from langchain_ollama import ChatOllama, OllamaLLM
from kokoro import KPipeline
import sounddevice as sd
from faster_whisper import WhisperModel

# from langchain_openai import ChatOpenAI # if you want to use openai
from langchain_core.messages import HumanMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferWindowMemory

from system_control import handle_system_command
from friday.character.loader import build_system_prompt
from friday.tool_manager import load_all_tools, register_reload_callback

load_dotenv()

MIC_INDEX = None
TRIGGER_WORD = "friday"
CONVERSATION_TIMEOUT = 30  # seconds of inactivity before exiting conversation mode

logging.basicConfig(level=logging.DEBUG)  # logging

# api_key = os.getenv("OPENAI_API_KEY") removed because it's not needed for ollama
# org_id = os.getenv("OPENAI_ORG_ID") removed because it's not needed for ollama

recognizer = sr.Recognizer()
mic = sr.Microphone(device_index=MIC_INDEX)

# Initialize TTS and STT models
try:
    logging.info("⏳ Loading Kokoro TTS pipeline...")
    kokoro_pipeline = KPipeline(lang_code='a')
except Exception as e:
    logging.error(f"❌ Failed to load Kokoro Pipeline: {e}")
    kokoro_pipeline = None

try:
    logging.info("⏳ Loading Whisper STT model...")
    whisper_model = WhisperModel("small.en", device="cpu", compute_type="int8")
except Exception as e:
    logging.error(f"❌ Failed to load Whisper Model: {e}")
    whisper_model = None

def strip_markdown(text: str) -> str:
    # Remove markdown headers
    text = re.sub(r'#+\s+', '', text)
    # Remove bold/italic asterisks and underscores
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'_+', '', text)
    # Remove code blocks and backticks
    text = re.sub(r'`+', '', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Remove list bullet symbols at the start of lines
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    # Remove numbering like "1. ", "2. "
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    return text.strip()

def transcribe_audio(audio_data) -> str:
    if whisper_model is None:
        logging.error("❌ Whisper model is not loaded. Cannot transcribe.")
        return ""
    
    try:
        # Convert AudioData to WAV format bytes
        wav_bytes = audio_data.get_wav_data()
        
        # Write to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(wav_bytes)
            temp_path = f.name
        
        try:
            # Transcribe using faster-whisper with VAD activity filtering
            segments, _ = whisper_model.transcribe(
                temp_path,
                beam_size=5,
                language="en",
                vad_filter=True,
                vad_parameters=dict(
                    threshold=0.3,
                    min_silence_duration_ms=300,
                    speech_pad_ms=400,
                )
            )
            transcript = " ".join([s.text for s in segments])
            return transcript.strip()
        finally:
            # Ensure the temporary file is deleted
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except Exception as e:
        logging.error(f"❌ Transcription failed: {e}")
        return ""

# Initialize LLM
llm = ChatOllama(model="qwen3:8b", reasoning=False)

# llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, organization=org_id) for openai

# Tool list — auto-discovered from tools/
tools = load_all_tools()

# Tool-calling prompt
prompt = ChatPromptTemplate.from_messages(
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

# Conversation memory (last 6 turns)
memory = ConversationBufferWindowMemory(
    k=6, memory_key="chat_history", return_messages=True
)

# Agent + executor
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=6,
    early_stopping_method="generate",
    memory=memory,
)


def rebuild_agent(new_tools):
    global agent, executor, tools
    tools = new_tools
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=6,
        early_stopping_method="generate",
        memory=memory,
    )
    logging.info(f"Agent rebuilt with {len(tools)} tools.")


register_reload_callback(rebuild_agent)

FAILURE_PHRASES = [
    "i can't", "i cannot", "i'm unable", "unable to",
    "don't have the ability", "not able to", "no tool",
    "i don't have access", "i have no way", "i'm not able",
    "can't do that", "cannot do that",
]

def looks_like_failure(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in FAILURE_PHRASES)


# TTS setup using Kokoro
def speak_text(text: str):
    try:
        if kokoro_pipeline is None:
            logging.error("❌ Kokoro TTS pipeline not initialized.")
            return
        
        # Clean any markdown tags before speaking
        cleaned_text = strip_markdown(text)
        if not cleaned_text:
            return
            
        generator = kokoro_pipeline(cleaned_text, voice='af_heart', speed=1.0)
        for _, _, audio in generator:
            sd.play(audio, samplerate=24000)
            sd.wait()
        time.sleep(0.4)  # Small pause to clear room echo before next microphone listen
    except Exception as e:
        logging.error(f"❌ TTS failed: {e}")


# Main interaction loop
def write():
    conversation_mode = False
    last_interaction_time = None

    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            while True:
                try:
                    if not conversation_mode:
                        logging.info("🎤 Listening for wake word...")
                        audio = recognizer.listen(source, timeout=10)
                        transcript = transcribe_audio(audio)
                        logging.info(f"🗣 Heard: {transcript}")

                        if transcript and TRIGGER_WORD.lower() in transcript.lower():
                            logging.info(f"🗣 Triggered by: {transcript}")
                            speak_text("Yes sir?")
                            conversation_mode = True
                            last_interaction_time = time.time()
                        else:
                            logging.debug("Wake word not detected, continuing...")
                    else:
                        logging.info("🎤 Listening for next command...")
                        audio = recognizer.listen(source, timeout=10)
                        command = transcribe_audio(audio)
                        logging.info(f"📥 Command: {command}")

                        if not command or not command.strip():
                            logging.warning("⚠️ Command is empty, skipping.")
                            continue

                        # Intercept and handle system commands offline
                        is_system_cmd = handle_system_command(command, speak_fn=speak_text)
                        if not is_system_cmd:
                            logging.info("🤖 Sending command to agent...")
                            response = executor.invoke({"input": command})
                            content = response["output"]

                            # If FRIDAY failed, auto-build a tool and retry
                            if looks_like_failure(content):
                                logging.info("🔧 Failure detected — triggering auto-build...")
                                speak_text("Let me build that.")
                                executor.invoke({
                                    "input": (
                                        f"Use auto_build_tool to research and build "
                                        f"the capability needed for this task: {command}"
                                    )
                                })
                                # Retry original command on the rebuilt executor
                                response = executor.invoke({"input": command})
                                content = response["output"]

                            logging.info(f"✅ Agent responded: {content}")
                            print("Friday:", content)
                            speak_text(content)
                        last_interaction_time = time.time()

                        if time.time() - last_interaction_time > CONVERSATION_TIMEOUT:
                            logging.info("⌛ Timeout: Returning to wake word mode.")
                            conversation_mode = False

                except sr.WaitTimeoutError:
                    logging.warning("⚠️ Timeout waiting for audio.")
                    if (
                        conversation_mode
                        and time.time() - last_interaction_time > CONVERSATION_TIMEOUT
                    ):
                        logging.info(
                            "⌛ No input in conversation mode. Returning to wake word mode."
                        )
                        conversation_mode = False
                except sr.UnknownValueError:
                    logging.warning("⚠️ Could not understand audio.")
                except Exception as e:
                    logging.error(f"❌ Error during recognition or tool call: {e}")
                    time.sleep(1)

    except Exception as e:
        logging.critical(f"❌ Critical error in main loop: {e}")


if __name__ == "__main__":
    write()
