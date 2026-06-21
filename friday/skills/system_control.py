import os
import re
import platform
import subprocess
import webbrowser
import pyautogui
import keyboard

# Mappings for common applications on Windows/Mac
WINDOWS_APPS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "chrome.exe"
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        "firefox.exe"
    ],
    "spotify": [
        os.path.join(os.path.expanduser("~"), r"AppData\Roaming\Spotify\Spotify.exe"),
        "spotify.exe"
    ],
    "discord": [
        os.path.join(os.path.expanduser("~"), r"AppData\Local\Discord\Update.exe"),
        "discord.exe"
    ],
    "vscode": [
        os.path.join(os.path.expanduser("~"), r"AppData\Local\Programs\Microsoft VS Code\Code.exe"),
        "code.exe"
    ],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "file explorer": ["explorer.exe"],
    "terminal": ["cmd.exe", "powershell.exe"],
    "whatsapp": [
        os.path.join(os.path.expanduser("~"), r"AppData\Local\WhatsApp\WhatsApp.exe")
    ]
}

# Site mappings for Open URL
URL_MAP = {
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com"
}

def open_application(app_name: str) -> bool:
    """Launch application by name."""
    system = platform.system()
    app_name_clean = app_name.lower().strip()
    
    # Standardize names
    if "vs code" in app_name_clean or "vscode" in app_name_clean:
        key = "vscode"
    elif "explorer" in app_name_clean:
        key = "file explorer"
    else:
        key = app_name_clean

    protocols = {
        "spotify": "spotify:",
        "whatsapp": "whatsapp://",
        "discord": "discord://",
        "vscode": "vscode://"
    }

    if system == "Windows":
        if key in WINDOWS_APPS:
            for path in WINDOWS_APPS[key]:
                try:
                    # Discord special handling via Update.exe wrapper
                    if "discord" in path.lower() and "update.exe" in path.lower():
                        subprocess.Popen([path, "--processStart", "Discord.exe"])
                        return True
                    
                    if os.path.exists(path) or path.endswith(".exe"):
                        if os.path.exists(path):
                            os.startfile(path)
                        else:
                            subprocess.Popen(path)
                        return True
                except Exception:
                    continue
            
            # Protocol fallback
            if key in protocols:
                try:
                    webbrowser.open(protocols[key])
                    return True
                except Exception:
                    pass

        # Try to run directly via shell/cmd if not in dict or if paths failed
        try:
            # cmd.exe /c start command to launch system programs
            subprocess.Popen(app_name_clean, shell=True)
            return True
        except Exception:
            pass

    elif system == "Darwin":  # macOS
        mac_apps = {
            "chrome": "Google Chrome",
            "firefox": "Firefox",
            "spotify": "Spotify",
            "discord": "Discord",
            "vscode": "Visual Studio Code",
            "notepad": "TextEdit",
            "calculator": "Calculator",
            "file explorer": "Finder",
            "terminal": "Terminal",
            "whatsapp": "WhatsApp"
        }
        app_to_open = mac_apps.get(key, app_name)
        try:
            subprocess.Popen(["open", "-a", app_to_open])
            return True
        except Exception:
            pass
            
    else:  # Linux
        try:
            subprocess.Popen([app_name_clean])
            return True
        except Exception:
            pass

    return False

def handle_system_command(text: str, speak_fn=None) -> bool:
    """
    Parses natural language commands to execute local system controls.
    Returns True if the command was intercepted and handled, False otherwise.
    """
    if not text:
        return False

    clean_text = re.sub(r'[^\w\s]', '', text.lower()).strip()
    system = platform.system()

    def speak(msg):
        print(f"Friday (System): {msg}")
        if speak_fn:
            speak_fn(msg)

    # 1. SEARCH IN APP ("search [query] in [spotify/youtube/google]")
    search_match = re.search(r"search (.+?) in (spotify|youtube|google|chrome)", clean_text)
    if search_match:
        query = search_match.group(1).strip()
        target = search_match.group(2).lower()
        
        speak(f"Searching {query} on {target}.")

        if target == "spotify":
            webbrowser.open(f"spotify:search:{query}")
            return True
        elif target == "youtube":
            chrome_opened = False
            if system == "Windows":
                for path in WINDOWS_APPS["chrome"]:
                    if os.path.exists(path) or path == "chrome.exe":
                        try:
                            subprocess.Popen([path, f"https://www.youtube.com/results?search_query={query}"])
                            chrome_opened = True
                            break
                        except Exception:
                            continue
            elif system == "Darwin":
                try:
                    subprocess.Popen(["open", "-a", "Google Chrome", f"https://www.youtube.com/results?search_query={query}"])
                    chrome_opened = True
                except Exception:
                    pass

            if not chrome_opened:
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
            return True
        elif target in ["google", "chrome"]:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return True

    # 2. OPEN APP ("open [app_name]")
    open_app_match = re.search(r"open (chrome|firefox|spotify|discord|vscode|vs code|notepad|calculator|file explorer|terminal|whatsapp)", clean_text)
    if open_app_match:
        app_name = open_app_match.group(1)
        speak(f"Opening {app_name}.")
        if open_application(app_name):
            return True
        else:
            speak(f"Failed opening {app_name}.")
            return True

    # 3. OPEN URL ("open [youtube/github/gmail]")
    open_url_match = re.search(r"open (youtube|github|gmail)", clean_text)
    if open_url_match:
        site = open_url_match.group(1)
        url = URL_MAP.get(site)
        if url:
            speak(f"Opening {site}.")
            webbrowser.open(url)
            return True

    # 4. MEDIA CONTROL ("play", "pause", "next song", "volume up", "volume down")
    if clean_text in ["play", "pause", "resume", "play music", "pause music"]:
        keyboard.send("play/pause media")
        return True
    elif clean_text in ["next song", "next track", "skip song"]:
        keyboard.send("next track")
        return True
    elif clean_text in ["previous song", "previous track"]:
        keyboard.send("previous track")
        return True
    elif clean_text in ["volume up", "increase volume", "volume-up"]:
        keyboard.send("volume up")
        return True
    elif clean_text in ["volume down", "decrease volume", "volume-down"]:
        keyboard.send("volume down")
        return True

    # 5. SYSTEM ACTIONS ("take screenshot", "lock screen", "shutdown", "restart")
    if "screenshot" in clean_text or "take screenshot" in clean_text:
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            os.makedirs(desktop, exist_ok=True)
            screenshot_file = os.path.join(desktop, "screenshot.png")
            pyautogui.screenshot(screenshot_file)
            speak("Captured. Saved to desktop.")
        except Exception as e:
            speak(f"Capture failed: {e}")
        return True

    elif "lock screen" in clean_text or "lock my PC" in clean_text:
        speak("Locking screen.")
        if system == "Windows":
            os.system("rundll32.exe user32.dll,LockWorkStation")
        elif system == "Darwin":
            os.system("pmset displaysleepnow")
        else:
            os.system("xdg-screensaver lock")
        return True

    elif "shutdown" in clean_text:
        if "confirm" in clean_text:
            speak("Shutting down.")
            if system == "Windows":
                os.system("shutdown /s /t 1")
            else:
                os.system("shutdown -h now")
        else:
            speak("Say shutdown confirm to proceed.")
        return True

    elif "restart" in clean_text:
        if "confirm" in clean_text:
            speak("Restarting.")
            if system == "Windows":
                os.system("shutdown /r /t 1")
            else:
                os.system("reboot")
        else:
            speak("Say restart confirm to proceed.")
        return True

    return False

# ==========================================
# INTEGRATION INSTRUCTIONS (main.py):
# ==========================================
# 
# 1. Import handle_system_command:
#    from system_control import handle_system_command
# 
# 2. Modify the main conversation loop in main.py:
# 
#    Replace this block:
#        logging.info("🤖 Sending command to agent...")
#        response = executor.invoke({"input": command})
#        content = response["output"]
#        logging.info(f"✅ Agent responded: {content}")
#        print("Friday:", content)
#        speak_text(content)
# 
#    With this:
#        # Intercept and handle system commands offline
#        is_system_cmd = handle_system_command(command, speak_fn=speak_text)
#        if not is_system_cmd:
#            logging.info("🤖 Sending command to agent...")
#            response = executor.invoke({"input": command})
#            content = response["output"]
#            logging.info(f"✅ Agent responded: {content}")
#            print("Friday:", content)
#            speak_text(content)
#
