import os
import platform
import subprocess
import webbrowser
import datetime
import pyautogui
import keyboard

# Mappings for common applications on Windows
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

# Site mappings for Open URL / Apps
URL_MAP = {
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com"
}

def open_application(app_name: str) -> bool:
    """Launch application by name locally."""
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

def execute_system_command(intent: str, params: dict) -> str:
    """
    Executes the matched system command.
    Returns the confirmation text to speak.
    """
    system = platform.system()
    query = params.get("query", "")
    groups = params.get("groups", [])
    
    # 1. TIME
    if intent == "time":
        now = datetime.datetime.now()
        return f"It is {now.strftime('%I:%M %p')}."
        
    # 2. DATE
    elif intent == "date":
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."
        
    # 3. OPEN APP
    elif intent == "open_app":
        app_name = groups[0] if groups else ""
        if app_name in URL_MAP:
            webbrowser.open(URL_MAP[app_name])
            return f"Opening {app_name}."
        elif open_application(app_name):
            return f"Opening {app_name}."
        else:
            return f"Failed to open {app_name}."
            
    # 4. SEARCH IN APP
    elif intent in ["search_in_app", "play_in_app"]:
        search_query = groups[0].strip() if len(groups) > 0 else ""
        target = groups[1].lower().strip() if len(groups) > 1 else "google"
        
        prefix = "Playing" if intent == "play_in_app" else "Searching for"
        
        if target == "spotify":
            webbrowser.open(f"spotify:search:{search_query}")
            return f"{prefix} {search_query} on Spotify."
        elif target == "youtube":
            chrome_opened = False
            url = f"https://www.youtube.com/results?search_query={search_query}"
            if system == "Windows":
                for path in WINDOWS_APPS["chrome"]:
                    if os.path.exists(path) or path == "chrome.exe":
                        try:
                            subprocess.Popen([path, url])
                            chrome_opened = True
                            break
                        except Exception:
                            continue
            elif system == "Darwin":
                try:
                    subprocess.Popen(["open", "-a", "Google Chrome", url])
                    chrome_opened = True
                except Exception:
                    pass
            if not chrome_opened:
                webbrowser.open(url)
            return f"{prefix} {search_query} on YouTube."
        else:
            webbrowser.open(f"https://www.google.com/search?q={search_query}")
            return f"Searching for {search_query} on Google."

    # 5. VOLUME
    elif intent == "volume":
        direction = groups[0] if groups else ""
        keyboard.send(f"volume {direction}")
        return f"Volume {direction}."
        
    # 6. MEDIA CONTROL
    elif intent == "media":
        cmd = groups[0] if groups else ""
        if cmd in ["play", "pause", "resume"]:
            keyboard.send("play/pause media")
            return "Done."
        elif cmd in ["next", "skip"]:
            keyboard.send("next track")
            return "Skipped song."
        elif cmd == "previous":
            keyboard.send("previous track")
            return "Previous song."
            
    # 7. SCREENSHOT
    elif intent == "screenshot":
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            os.makedirs(desktop, exist_ok=True)
            screenshot_file = os.path.join(desktop, "screenshot.png")
            pyautogui.screenshot(screenshot_file)
            return "Captured. Saved to desktop."
        except Exception as e:
            return f"Capture failed: {e}"
            
    # 8. LOCK SCREEN
    elif intent == "lock_screen":
        if system == "Windows":
            os.system("rundll32.exe user32.dll,LockWorkStation")
        elif system == "Darwin":
            os.system("pmset displaysleepnow")
        else:
            os.system("xdg-screensaver lock")
        return "Screen locked."
        
    # 9. SHUTDOWN
    elif intent == "shutdown":
        if "confirm" in query:
            if system == "Windows":
                os.system("shutdown /s /t 1")
            else:
                os.system("shutdown -h now")
            return "Shutting down."
        else:
            return "Please say shutdown confirm to proceed."
            
    # 10. RESTART
    elif intent == "restart":
        if "confirm" in query:
            if system == "Windows":
                os.system("shutdown /r /t 1")
            else:
                os.system("reboot")
            return "Restarting."
        else:
            return "Please say restart confirm to proceed."
            
    return "Done."
