import webbrowser
from langchain.tools import tool
from friday.core.command_executor import open_application, URL_MAP

@tool("smart_launcher")
def smart_launcher(app_or_url: str) -> str:
    """
    Launch applications locally or open website URLs by voice.
    Use this tool when the user says:
    - "Open VS Code", "Launch Chrome", "Start Spotify"
    - "Open YouTube", "Go to github.com", "Search google.com"
    Input: the name of the app (e.g. 'chrome', 'spotify', 'vscode') or website URL.
    """
    clean_input = app_or_url.strip().lower()
    
    # 1. Check if it's a known URL map keyword
    if clean_input in URL_MAP:
        url = URL_MAP[clean_input]
        webbrowser.open(url)
        return f"Opened website: {url}"
        
    # 2. Check if it looks like a URL
    if clean_input.startswith("http://") or clean_input.startswith("https://") or "www." in clean_input or clean_input.endswith(".com") or clean_input.endswith(".org") or clean_input.endswith(".net"):
        url = clean_input
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened website: {url}"
        
    # 3. Otherwise try to launch as application name
    if open_application(app_or_url):
        return f"Successfully launched application: {app_or_url}"
    else:
        return f"Could not launch application: {app_or_url}. Make sure it is installed and on system path."
