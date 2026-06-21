import os
import logging
import time
import tempfile
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

# importing tools
from tools.time import get_time
from tools.OCR import read_text_from_latest_image
from tools.arp_scan import arp_scan_terminal
from tools.duckduckgo import duckduckgo_search_tool
from tools.matrix import matrix_mode
from tools.screenshot import take_screenshot

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
            # Transcribe using faster-whisper
            segments, _ = whisper_model.transcribe(temp_path)
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
llm = ChatOllama(model="qwen3:1.7b", reasoning=False)

# llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, organization=org_id) for openai

# Tool list
tools = [get_time, arp_scan_terminal, read_text_from_latest_image, duckduckgo_search_tool, matrix_mode, take_screenshot]

# Tool-calling prompt
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Friday, an intelligent, conversational AI assistant. Your goal is to be helpful, friendly, and informative. You can respond in natural, human-like language and use tools when needed to answer questions more accurately. Always explain your reasoning simply when appropriate, and keep your responses conversational and concise.",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

# Agent + executor
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# TTS setup using Kokoro
def speak_text(text: str):
    try:
        if kokoro_pipeline is None:
            logging.error("❌ Kokoro TTS pipeline not initialized.")
            return
        
        generator = kokoro_pipeline(text, voice='af_heart', speed=1.0)
        for _, _, audio in generator:
            sd.play(audio, samplerate=24000)
            sd.wait()
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

                        logging.info("🤖 Sending command to agent...")
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
