import os
import logging
import time
import tempfile
import re
from dotenv import load_dotenv
import speech_recognition as sr
from kokoro import KPipeline
import sounddevice as sd
from faster_whisper import WhisperModel

load_dotenv()

MIC_INDEX = None
TRIGGER_WORD = "friday"
CONVERSATION_TIMEOUT = 30  # seconds of inactivity before exiting conversation mode

logging.basicConfig(level=logging.DEBUG)

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
    text = re.sub(r'#+\s+', '', text)
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'_+', '', text)
    text = re.sub(r'`+', '', text)
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    return text.strip()

def transcribe_audio(audio_data) -> str:
    if whisper_model is None:
        logging.error("❌ Whisper model is not loaded. Cannot transcribe.")
        return ""
    
    try:
        wav_bytes = audio_data.get_wav_data()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(wav_bytes)
            temp_path = f.name
        
        try:
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
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except Exception as e:
        logging.error(f"❌ Transcription failed: {e}")
        return ""

# TTS setup using Kokoro
def speak_text(text: str):
    try:
        if kokoro_pipeline is None:
            logging.error("❌ Kokoro TTS pipeline not initialized.")
            return
        
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

# Delay imports to avoid circular dependencies
from friday.core.intent_router import route_intent
from friday.core.command_executor import execute_system_command
from friday.core.llm_agent import get_simple_response, run_complex_agent

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
                            
                            # Extract direct command spoken with/after wake word
                            wake_idx = transcript.lower().find(TRIGGER_WORD.lower())
                            cmd_after_wake = transcript[wake_idx + len(TRIGGER_WORD):].strip()
                            cmd_after_wake = re.sub(r"^[,\s\-\.]+", "", cmd_after_wake).strip()
                            
                            conversation_mode = True
                            last_interaction_time = time.time()
                            
                            if cmd_after_wake:
                                logging.info(f"Direct command after wake word: {cmd_after_wake}")
                                intent, params = route_intent(cmd_after_wake)
                                if intent not in ["simple_q", "complex_task", "idle"]:
                                    res = execute_system_command(intent, params)
                                    print("Friday:", res)
                                    speak_text(res)
                                elif intent == "simple_q":
                                    res = get_simple_response(cmd_after_wake)
                                    print("Friday:", res)
                                    speak_text(res)
                                elif intent == "complex_task":
                                    res = run_complex_agent(cmd_after_wake)
                                    print("Friday:", res)
                                    speak_text(res)
                            else:
                                speak_text("Yes sir?")
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

                        # Intent routing
                        intent, params = route_intent(command)
                        logging.info(f"Routed command '{command}' to: {intent}")
                        
                        if intent not in ["simple_q", "complex_task", "idle"]:
                            res = execute_system_command(intent, params)
                            print("Friday:", res)
                            speak_text(res)
                        elif intent == "simple_q":
                            res = get_simple_response(command)
                            print("Friday:", res)
                            speak_text(res)
                        elif intent == "complex_task":
                            res = run_complex_agent(command)
                            print("Friday:", res)
                            speak_text(res)
                            
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
                    logging.error(f"❌ Error during recognition: {e}")
                    time.sleep(1)

    except Exception as e:
        logging.critical(f"❌ Critical error in main loop: {e}")

if __name__ == "__main__":
    write()
