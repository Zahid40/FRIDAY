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

# Smart Startup Greeting
def get_smart_greeting() -> str:
    import datetime
    
    now = datetime.datetime.now()
    hour = now.hour
    if hour < 12:
        tod = "morning"
    elif hour < 17:
        tod = "afternoon"
    else:
        tod = "evening"
        
    greeting = f"Good {tod}, Zahid. Friday is online."
    
    try:
        from friday.skills.weather_checker import get_tool
        weather_tool = get_tool()
        weather_info = weather_tool("Delhi")
        parts = weather_info.split(",")
        if len(parts) >= 2:
            weather_desc = parts[0].split(":")[-1].strip()
            temp = parts[1].strip()
            greeting += f" Currently in Delhi, it is {weather_desc} at {temp}."
    except Exception:
        pass
        
    return greeting

# Main interaction loop
def write():
    conversation_mode = False
    last_interaction_time = None

    try:
        with mic as source:
            logging.info("🎤 Calibrating microphone for ambient noise...")
            recognizer.adjust_for_ambient_noise(source)
            
            # Smart Greeting on startup
            greeting = get_smart_greeting()
            print("Friday:", greeting)
            speak_text(greeting)
            
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
                                res = ""
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
                                    
                                if intent != "idle" and res:
                                    try:
                                        from friday.memory.long_term_memory import add_chat_turn
                                        add_chat_turn("human", cmd_after_wake)
                                        add_chat_turn("ai", res)
                                    except Exception:
                                        pass
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
                        
                        res = ""
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
                            
                        if intent != "idle" and res:
                            try:
                                from friday.memory.long_term_memory import add_chat_turn
                                add_chat_turn("human", command)
                                add_chat_turn("ai", res)
                            except Exception:
                                pass
                            
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

def run_gui():
    import sys
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer
    
    # Import Friday UI elements
    from friday.ui.pill_widget import PillWidget
    from friday.ui.voice_thread import VoiceThread
    from friday.ui.tray import SystemTrayIcon

    class HotkeySignaler(QObject):
        """
        Listens for a global hotkey event in a background thread 
        and signals the main thread to toggle widget visibility safely.
        """
        hotkey_pressed = pyqtSignal()
        
        def __init__(self):
            super().__init__()
            try:
                import keyboard
                keyboard.add_hotkey("ctrl+space", self.trigger_signal)
                logging.info("Registered global toggle hotkey: Ctrl + Space")
            except Exception as e:
                logging.error(f"Failed to register keyboard hotkey: {e}")
            
        def trigger_signal(self):
            self.hotkey_pressed.emit()

    app = QApplication(sys.argv)
    
    # Prevent application from closing when the window is hidden/minimized
    app.setQuitOnLastWindowClosed(False)
    
    # Create the floating pill widget
    pill = PillWidget()
    pill.show()
    
    # Initialize the Voice Pipeline QThread
    voice_thread = VoiceThread()
    
    # Connect signals from the voice processing thread to UI slots
    voice_thread.state_changed.connect(pill.update_state)
    voice_thread.text_updated.connect(pill.update_text)
    voice_thread.time_elapsed.connect(pill.update_time)
    
    # Start the Voice Thread loop
    voice_thread.start()
    
    # Define Tray callbacks
    def show_friday():
        # Ensure UI modification runs on Qt main loop thread
        QTimer.singleShot(0, lambda: (
            pill.show(),
            pill.activateWindow(),
            pill.raise_(),
            pill.update_state("idle")
        ))
        
    def quit_friday():
        logging.info("Shutting down Friday assistant...")
        tray.stop()
        voice_thread.stop_thread()
        app.quit()
        sys.exit(0)
        
    # Start System Tray icon
    tray = SystemTrayIcon(on_show_callback=show_friday, on_quit_callback=quit_friday)
    tray.run()
    
    # Setup global hotkey handler
    hotkey_signaler = HotkeySignaler()
    
    def toggle_visibility():
        if pill.isVisible():
            pill.hide()
        else:
            pill.show()
            pill.activateWindow()
            pill.raise_()
            pill.update_state("idle")
            
    hotkey_signaler.hotkey_pressed.connect(toggle_visibility)
    
    # Start Qt event loop
    sys.exit(app.exec())

def main():
    import argparse
    parser = argparse.ArgumentParser(description="FRIDAY - Voice-Controlled AI Assistant")
    parser.add_argument("--cli", action="store_true", help="Run in CLI (console) mode without GUI")
    args = parser.parse_args()

    if args.cli:
        write()
    else:
        run_gui()

if __name__ == "__main__":
    main()
