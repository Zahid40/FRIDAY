# 🤖 FRIDAY — Your Personal On-Device AI Assistant

> *"Just say **Friday**... and it's done."*

**FRIDAY** is a fully local, voice-activated AI assistant inspired by Iron Man's J.A.R.V.I.S. — built to run entirely on your laptop without sending your data to any cloud. Talk to it naturally, and it actually *does* things: launches apps, writes & runs code, sends emails, manages files, checks weather/stocks, and more.

No subscriptions. No API keys. No internet required. 100% yours.

---

## ✨ What Makes FRIDAY Special

| Feature | Details |
|---|---|
| 🎙 **Wake Word** | Just say **"Friday"** — always listening |
| 🧠 **Local LLMs** | Powered by Ollama (`qwen2.5`, `qwen3`) — runs offline |
| 🔊 **Natural Voice** | Kokoro TTS — sounds like a real assistant |
| 💾 **Persistent Memory** | Remembers facts about you across restarts |
| 🖥 **Floating GUI** | Beautiful PyQt6 notch-style island with audio waveform |
| 🛠 **Real Actions** | Not just chat — it actually *does* tasks for you |

---

## 🔧 What FRIDAY Can Do

- 🚀 **Launch Apps** — "Friday, open VS Code / Chrome / Spotify"
- ⌨️ **Computer Control** — type text, press keys, click, scroll via voice
- 📁 **File Manager** — create, read, move, delete files by voice
- 📧 **Send Emails** — via Gmail SMTP with natural language
- 💬 **WhatsApp Messages** — open chats with pre-filled text
- 📋 **Clipboard** — read, write, and summarize clipboard content
- 🐍 **Run Python Scripts** — write and execute code on the fly
- 📈 **Stock Prices** — real-time from Yahoo Finance
- 🌤 **Weather** — live data from wttr.in
- 🧠 **Learns from failures** — remembers what went wrong and fixes it

---

## 💻 System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| RAM | 8 GB | 16 GB+ |
| Storage | 10 GB free | 20 GB+ free |
| Python | 3.10+ | 3.11+ |
| GPU | Not required | NVIDIA GPU (for faster LLM) |
| Microphone | Required | USB/headset mic preferred |

---

## 🚀 Quick Start (5 Steps)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Zahid40/FRIDAY.git
cd FRIDAY
```

### Step 2 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

> 💡 Recommended: use a virtual environment
> ```bash
> python -m venv venv
> source venv/bin/activate   # Linux/Mac
> venv\Scripts\activate      # Windows
> pip install -r requirements.txt
> ```

### Step 3 — Install Ollama & Download Models

1. Download & install **Ollama** from [ollama.com](https://ollama.com)
2. Pull the required models:

```bash
ollama pull qwen2.5:0.5b    # Fast router / simple Q&A
ollama pull qwen2.5:7b      # Smart agent (complex tasks)
```

> ⚡ Optionally use `qwen3:8b` instead of `qwen2.5:7b` for better quality.

### Step 4 — Configure Environment (Optional but Recommended)

Create a `.env` file in the project root:

```env
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

> 🔐 For Gmail: enable 2FA and generate an **App Password** from your Google account settings.

### Step 5 — Run FRIDAY

**GUI Mode** (floating island on screen):
```bash
python main.py
```

**CLI Mode** (terminal only):
```bash
python main.py --cli
```

---

## 🗣 How to Use FRIDAY

1. Run `python main.py` — FRIDAY greets you with local weather
2. Say **"Friday"** — the assistant wakes up and listens
3. Give your command naturally:
   - *"Friday, open Chrome"*
   - *"Friday, what's the weather today?"*
   - *"Friday, create a folder called Projects on my desktop"*
   - *"Friday, send an email to John saying I'll be late"*
   - *"Friday, what's the stock price of Tesla?"*
   - *"Friday, write a Python script to rename all files in a folder"*
4. FRIDAY speaks back and takes action immediately

---

## 🗂 Project Structure

```
FRIDAY/
├── main.py              # Entry point — GUI & CLI launcher
├── requirements.txt     # Python dependencies
├── .env                 # Your credentials (not committed)
├── config/              # Configuration files
└── friday/
    ├── memory/          # Persistent memory (chat history, facts)
    └── ...              # Core modules (tools, LLM, TTS, GUI)
```

---

## 🛣 Roadmap

- [ ] 📱 Android / iOS companion app
- [ ] 🌐 Multi-language support (Hindi, Urdu, etc.)
- [ ] 🔌 Plugin system for custom tools
- [ ] 🖼 Screen vision (see what's on your screen)
- [ ] 🤝 Multi-device sync (laptop ↔ phone)
- [ ] 🧩 Better wake word model (custom trained)

---

## 🤝 Help Wanted — Join the Build!

> **I'm building FRIDAY solo and looking for contributors, testers, and builders.**

This project needs help with:
- 🐛 **Bug reports** — test it and open issues
- 📱 **Mobile version** — React Native / Flutter developers
- 🧠 **LLM fine-tuning** — making the agent smarter
- 🎨 **UI/UX** — improving the PyQt6 GUI
- 📝 **Documentation** — tutorials, video demos
- 🔧 **New tools** — calendar, browser automation, etc.

### How to Contribute

```bash
# Fork the repo, make your changes, then:
git checkout -b feature/your-feature-name
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
# Open a Pull Request 🚀
```

---

## 📣 Follow & Support on X (Twitter)

If you find this cool, **please share it** — it helps a solo developer keep building!

> 🐦 Tweet about it: [**#FridayAI #OpenSource #LocalAI #BuildInPublic**](https://twitter.com/intent/tweet?text=I%20just%20found%20FRIDAY%20%E2%80%94%20a%20local%2C%20voice-controlled%20AI%20assistant%20like%20Iron%20Man%27s%20JARVIS%2C%20runs%20100%25%20offline%20on%20your%20laptop!%20%F0%9F%A4%96%F0%9F%94%A5%0A%0Ahttps%3A%2F%2Fgithub.com%2FZahid40%2FFRIDAY%0A%0A%23FridayAI%20%23LocalAI%20%23OpenSource%20%23BuildInPublic)

**If you're a developer who wants to collaborate, DM me or open an Issue — all skill levels welcome!**

---

## 📄 License

MIT License — free to use, fork, and build upon.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/Zahid40">Zahid40</a> — from Delhi, India 🇮🇳
</p>
