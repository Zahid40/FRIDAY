# 🧠 Friday – Local Voice-Controlled AI Assistant

**Friday** is a voice-activated, conversational AI assistant powered by local LLMs (Qwen via Ollama). It listens for a wake word, processes spoken commands using a local language model with LangChain, and responds out loud via Kokoro TTS. It supports advanced tool-calling for system control, file management, scripts execution, clipboard control, communicator alerts, and real-time APIs.

---

## 🚀 Features

- 🗣 Voice-activated with wake word **"Friday"**
- 🧠 Local language models (`qwen2.5:0.5b` for fast routing/simple Q&A, and `qwen2.5:7b` / `qwen3:8b` for complex tasks)
- 🧠 **Persistent Memory**: Saves chat history and remembers facts about the user across restarts.
- 🔄 **Ollama Intent Routing**: Deterministic regex routing + fast local LLM fallback classification.
- 🔧 **Advanced Tools**:
  - `Smart Launcher`: Launch VS Code, Chrome, Spotify, etc., or open web URLs.
  - `File System Manager`: Create, read, move, list, or delete files/folders by voice.
  - `Communicator`: Send emails via SMTP and open WhatsApp messages with pre-filled text.
  - `Clipboard Manager`: Read, write, and summarize clipboard text.
  - `Code Runner`: Write and execute Python scripts locally in a scratch directory.
  - `Stock Market Checker`: Retrieve real-time prices from Yahoo Finance API.
  - `Weather Checker`: Fetch real-time weather from wttr.in.
- 🔊 Natural offline Text-to-Speech via **Kokoro TTS**.
- 🖥 Modern **PyQt6 Floating GUI** styled as a screen-notch/island with real-time waveform audio visualization.

---

## ▶️ How It Works (`main.py`)

1. **Startup & Local LLM Setup**
   - Loads the smart model and loads persistent chat history from `friday/memory/persistent_memory.json`.
   - Greets the user with a dynamic greeting (good morning/afternoon/evening) containing local weather details.

2. **Wake Word Listening**
   - Listens via microphone.
   - If it hears the word **"Friday"**, it enters "conversation mode" and shows a listening/hearing state.

3. **Voice Command Handling & Execution**
   - Transcribes voice using faster-whisper.
   - Determines intent (regex fast-path or local LLM fallback).
   - If intent requires tools, the LangChain agent executes them and saves the turns to persistent memory.
   - Speaks the result using Kokoro TTS.

---

## 🤖 How To Start Friday

1. **Install Dependencies**  
   Make sure you have installed all required dependencies listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up the Local Models**  
   Ensure you have Ollama running with:
   - `qwen2.5:0.5b` (fast classifier/QA)
   - `qwen2.5:7b` or `qwen3:8b` (smart agent executor)

3. **Configure Environment Variables**  
   Create a `.env` file in the root directory to specify credentials (optional):
   ```env
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_smtp_app_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

4. **Run Friday**  
   - **Launch GUI (Default)**:
     ```bash
     python main.py
     ```
   - **Launch CLI (Console Mode)**:
     ```bash
     python main.py --cli
     ```
---

