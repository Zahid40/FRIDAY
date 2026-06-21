import sys
import os
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr
from langchain_core.callbacks import BaseCallbackHandler

class FridayCallbackHandler(BaseCallbackHandler):
    def __init__(self, voice_thread):
        self.voice_thread = voice_thread

    def on_llm_start(self, serialized, prompts, **kwargs):
        # Only set to thinking if not already in a more specific active state
        if self.voice_thread.current_state not in ["planning", "typing", "searching", "reading"]:
            self.voice_thread.change_state("thinking")
            self.voice_thread.text_updated.emit("Thinking...")

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get('name', '')
        action_text = self._format_tool_name(tool_name, input_str)
        
        # Map tool to specific UI state
        state = "executing"
        if tool_name == "duckduckgo_search":
            state = "searching"
        elif tool_name in ["read_latest_screenshot", "read_text_from_latest_image"]:
            state = "reading"
            
        self.voice_thread.change_state(state)
        self.voice_thread.text_updated.emit(f"Tool: {action_text}")

    def _format_tool_name(self, name, input_str):
        if name == "take_screenshot":
            return "Taking screenshot"
        elif name == "read_latest_screenshot":
            return "Reading screenshot"
        elif name == "duckduckgo_search":
            return "Searching the web"
        elif name == "get_time":
            return "Checking time"
        elif name == "arp_scan_terminal":
            return "Scanning network"
        elif name == "matrix_mode":
            return "Entering Matrix mode"
        return name.replace('_', ' ').strip().capitalize()

# Add the parent directory to python path to import main components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    recognizer,
    mic,
    transcribe_audio,
    speak_text,
    executor,
    handle_system_command,
    TRIGGER_WORD,
    CONVERSATION_TIMEOUT
)

class VoiceThread(QThread):
    # Signals to communicate with GUI main thread
    state_changed = pyqtSignal(str)     # E.g. "idle", "listening", "speaking"
    text_updated = pyqtSignal(str)      # Subtitle/status text
    time_elapsed = pyqtSignal(int)      # Seconds elapsed during speaking/active state

    def __init__(self):
        super().__init__()
        self.running = True
        self.conversation_mode = False
        self.last_interaction_time = None
        self.active_timer = 0
        self.timer_running = False
        self.current_state = "idle"

    def change_state(self, state: str):
        self.current_state = state
        self.state_changed.emit(state)

    def run(self):
        logging.info("Friday Voice Pipeline Thread started.")
        self.change_state("idle")
        self.text_updated.emit("Say Friday...")

        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                while self.running:
                    if not self.conversation_mode:
                        self.change_state("idle")
                        self.text_updated.emit("Say Friday...")
                        self.stop_timer()

                        try:
                            # Listen for wake word
                            audio = recognizer.listen(source, timeout=2, phrase_time_limit=4)
                            self.change_state("listening")
                            self.text_updated.emit("Hearing...")

                            transcript = transcribe_audio(audio)
                            if transcript:
                                logging.info(f"Idle heard: {transcript}")
                                if TRIGGER_WORD.lower() in transcript.lower():
                                    self.start_timer()
                                    self.change_state("wake")
                                    self.text_updated.emit("Yes?")
                                    speak_text("Yes?")
                                    
                                    self.conversation_mode = True
                                    self.last_interaction_time = time.time()
                        except sr.WaitTimeoutError:
                            continue
                        except Exception as e:
                            logging.error(f"Error in idle listen: {e}")
                            
                    else:
                        # In active conversation loop
                        self.change_state("listening")
                        self.text_updated.emit("Listening...")

                        try:
                            audio = recognizer.listen(source, timeout=3, phrase_time_limit=10)
                            command = transcribe_audio(audio)

                            if not command or not command.strip():
                                if time.time() - self.last_interaction_time > CONVERSATION_TIMEOUT:
                                    logging.info("Timeout reached. Exiting conversation mode.")
                                    self.conversation_mode = False
                                continue

                            self.text_updated.emit(f"Heard: {command}")
                            self.last_interaction_time = time.time()

                            # Custom speak wrapper to handle speaking states
                            def speak_wrapper(text_to_speak):
                                self.change_state("speaking")
                                self.text_updated.emit(text_to_speak)
                                speak_text(text_to_speak)

                            # Intercept and run system controls
                            is_system_cmd = handle_system_command(command, speak_fn=speak_wrapper)
                            
                            if is_system_cmd:
                                # Command executed successfully. Show SUCCESS state!
                                self.change_state("success")
                                self.text_updated.emit("Success")
                                time.sleep(1.0)
                            else:
                                # Determine initial state based on keywords
                                lower_cmd = command.lower()
                                initial_state = "thinking"
                                if any(x in lower_cmd for x in ["plan", "schedule", "calendar"]):
                                    initial_state = "planning"
                                elif any(x in lower_cmd for x in ["write", "type", "draft", "email"]):
                                    initial_state = "typing"
                                
                                self.change_state(initial_state)
                                self.text_updated.emit("Thinking...")
                                
                                try:
                                    handler = FridayCallbackHandler(self)
                                    response = executor.invoke(
                                        {"input": command},
                                        {"callbacks": [handler]}
                                    )
                                    content = response["output"]
                                    
                                    # Show success flash
                                    self.change_state("success")
                                    self.text_updated.emit("Success")
                                    time.sleep(1.0)
                                    
                                    speak_wrapper(content)
                                except Exception as agent_err:
                                    logging.error(f"Local agent query failed: {agent_err}")
                                    self.change_state("error")
                                    self.text_updated.emit("Error")
                                    time.sleep(1.0)
                                    speak_wrapper("Offline. Please check if Ollama is running.")

                            self.last_interaction_time = time.time()

                        except sr.WaitTimeoutError:
                            if time.time() - self.last_interaction_time > CONVERSATION_TIMEOUT:
                                logging.info("Timeout reached. Exiting conversation mode.")
                                self.conversation_mode = False
                        except Exception as e:
                            logging.error(f"Error in conversation loop: {e}")
                            time.sleep(0.5)

        except Exception as e:
            logging.critical(f"Critical error in VoiceThread pipeline: {e}")
            self.text_updated.emit("Voice thread failed.")
            self.change_state("idle")

    def start_timer(self):
        self.active_timer = 0
        self.timer_running = True
        self.time_elapsed.emit(self.active_timer)
        # We handle seconds counter inside a simple sleep loop in this thread
        self.start_timer_thread()

    def stop_timer(self):
        self.timer_running = False
        self.active_timer = 0

    def start_timer_thread(self):
        # Starts a simple loop running every second to count active session length
        def run_timer():
            while self.timer_running and self.running:
                time.sleep(1)
                if self.timer_running:
                    self.active_timer += 1
                    self.time_elapsed.emit(self.active_timer)
        
        import threading
        t = threading.Thread(target=run_timer, daemon=True)
        t.start()

    def stop_thread(self):
        self.running = False
        self.stop_timer()
        self.wait()
