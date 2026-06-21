from langchain.tools import tool
from PIL import Image
import pytesseract
import os

@tool("read_latest_screenshot")
def read_text_from_latest_image() -> str:
    """
    Reads and extracts text from the most recent screenshot located at '~/path/to/example.png'.
    Use this tool when the user says something like:
    - "Read the screen"
    - "What does the screenshot say?"
    - "Extract text from the image"
    """
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    image_path = os.path.join(desktop_path, "screenshot.png")

    if not os.path.exists(image_path):
        return f"Screenshot not found at {image_path}."

    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip() if text else "No readable text found in the screenshot."
    except Exception as e:
        return f"Failed to extract text: {str(e)}"
