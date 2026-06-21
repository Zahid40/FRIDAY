import sys
import os
import time
import logging
import re
from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr
from langchain_core.callbacks import BaseCallbackHandler

# Add parent directory to path to import core files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from friday.core.intent_router import route_intent
from friday.core.command_executor import execute_system_command
from friday.core.llm_agent import get_simple_response, run_complex_agent

from main import (
    recognizer,
    mic,
    transcribe_audio,
    speak_text,
    TRIGGER_WORD,
    CONVERSATION_TIMEOUT
)

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

class VoiceThread(QThread):
    state_changed = pyqtSignal(str)     # "idle", "listening", "speaking", etc.
    text_updated = pyqtSignal(str)      # Subtitle/status text
    time_elapsed = pyqtSignal(int)      # Running active session timer

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

    def process_command(self, command: str):
        """Processes voice command using the Two-Brain local routing architecture."""
        if not command or not command.strip():
            return

        self.text_updated.emit(f"Heard: {command}")
        self.last_interaction_time = time.time()

        # Speak wrapper updating state and displaying text in the UI
        def speak_wrapper(text_to_speak):
            self.change_state("speaking")
            self.text_updated.emit(text_to_speak)
            speak_text(text_to_speak)

        try:
            # 1. Fast Pattern Matching (Intent Router)
            intent, params = route_intent(command)
            logging.info(f"Routed command '{command}' -> Intent: {intent}")

            # Direct execution for system commands
            if intent not in ["simple_q", "complex_task", "idle"]:
                self.change_state("executing")
                self.text_updated.emit("Executing...")
                
                response = execute_system_command(intent, params)
                
                self.change_state("success")
                self.text_updated.emit("Success")
                time.sleep(1.0)
                
                speak_wrapper(response)

            # Direct Q&A via fast local model (Qwen 0.5B)
            elif intent == "simple_q":
                self.change_state("thinking")
                self.text_updated.emit("Thinking...")
                
                response = get_simple_response(command)
                
                self.change_state("success")
                self.text_updated.emit("Success")
                time.sleep(1.0)
                
                speak_wrapper(response)

            # Complex tasks using agent executor (Qwen 8B)
            elif intent == "complex_task":
                lower_cmd = command.lower()
                initial_state = "thinking"
                if any(x in lower_cmd for x in ["plan", "schedule", "calendar"]):
                    initial_state = "planning"
                elif any(x in lower_cmd for x in ["write", "type", "draft", "email"]):
                    initial_state = "typing"

                self.change_state(initial_state)
                self.text_updated.emit("Thinking...")

                handler = FridayCallbackHandler(self)
                response = run_complex_agent(command, callbacks=[handler])

                self.change_state("success")
                self.text_updated.emit("Success")
                time.sleep(1.0)

                speak_wrapper(response)

        except Exception as e:
            logging.error(f"Error processing command '{command}': {e}")
            self.change_state("error")
            self.text_updated.emit("Error")
            time.sleep(1.0)
            speak_wrapper("Error executing command.")

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
                                    
                                    # Extract direct command spoken with/after wake word
                                    wake_idx = transcript.lower().find(TRIGGER_WORD.lower())
                                    cmd_after_wake = transcript[wake_idx + len(TRIGGER_WORD):].strip()
                                    cmd_after_wake = re.sub(r"^[,\s\-\.]+", "", cmd_after_wake).strip()
                                    
                                    self.conversation_mode = True
                                    self.last_interaction_time = time.time()
                                    
                                    if cmd_after_wake:
                                        logging.info(f"Direct command after wake word: {cmd_after_wake}")
                                        self.process_command(cmd_after_wake)
                                    else:
                                        # Standard wake response
                                        self.change_state("wake")
                                        self.text_updated.emit("Yes?")
                                        speak_text("Yes?")
                        except sr.WaitTimeoutError:
                            continue
                        except Exception as e:
                            logging.error(f"Error in idle listen: {e}")
                            
                    else:
                        # In active conversation loop
                        self.change_state("listening")
                        self.text_updated.emit("Listening...")
                        
                        # Wait 300ms buffer after previous voice output to prevent echo / overlap
                        time.sleep(0.3)

                        try:
                            audio = recognizer.listen(source, timeout=3, phrase_time_limit=10)
                            command = transcribe_audio(audio)

                            if not command or not command.strip():
                                if time.time() - self.last_interaction_time > CONVERSATION_TIMEOUT:
                                    logging.info("Timeout reached. Exiting conversation mode.")
                                    self.conversation_mode = False
                                continue

                            self.process_command(command)
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
        self.start_timer_thread()

    def stop_timer(self):
        self.timer_running = False
        self.active_timer = 0

    def start_timer_thread(self):
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
