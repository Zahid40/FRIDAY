from langchain.tools import tool
from pydantic import BaseModel, Field

class ClipboardAction(BaseModel):
    action: str = Field(description="Action to perform: 'read' (get clipboard text) or 'write' (set clipboard text)")
    content: str = Field(default="", description="The text content to copy to the clipboard (required only for 'write' action)")

@tool("clipboard_tool", args_schema=ClipboardAction)
def clipboard_tool(action: str, content: str = "") -> str:
    """
    Manages the system clipboard. Supports reading the current clipboard contents or
    copying new text to the clipboard.
    """
    try:
        # We use PyQt6 which is already installed and highly reliable
        from PyQt6.QtWidgets import QApplication
        
        # Ensure a QApplication instance exists to access the clipboard
        app = QApplication.instance()
        if not app:
            app = QApplication([])
            
        clipboard = app.clipboard()
        
        if action == "read":
            text = clipboard.text()
            if not text:
                return "Clipboard is currently empty."
            return f"Clipboard Content:\n{text}"
            
        elif action == "write":
            if not content:
                return "Error: Content is required for write action."
            clipboard.setText(content)
            return "Successfully copied text to clipboard."
            
        else:
            return f"Error: Unknown clipboard action '{action}'."
            
    except Exception as e:
        return f"Clipboard operation failed: {e}"
