from langchain.tools import tool
import os
import mss
import mss.tools

@tool("capture_screenshot")
def take_screenshot() -> str:
    """
    Captures the current screen and saves it to '~/path/to/example.png' using the 'mss' library.
    
    Use this tool when the user says:
    - "Take a screenshot"
    - "Capture the screen"
    - "Save a screenshot"
    """
    try:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(desktop_path, exist_ok=True)
        image_path = os.path.join(desktop_path, "screenshot.png")

        with mss.mss() as sct:
            monitor = sct.monitors[1]  # [1] = main monitor; [0] = all monitors
            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=image_path)

        return f"Screenshot captured and saved to Desktop."
    except Exception as e:
        return f"Failed to capture screenshot: {str(e)}"
