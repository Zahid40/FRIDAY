import os
import shutil
from pathlib import Path
from langchain.tools import tool
from pydantic import BaseModel, Field

class FileSystemAction(BaseModel):
    action: str = Field(description="Action to perform: 'create', 'move', 'delete', 'list', 'read'")
    path: str = Field(description="The target file or directory path (absolute or relative to project root)")
    destination: str = Field(default="", description="The destination path (required only for 'move' action)")
    content: str = Field(default="", description="Text content to write (required only for 'create' action)")

@tool("file_system_manager", args_schema=FileSystemAction)
def file_system_manager(action: str, path: str, destination: str = "", content: str = "") -> str:
    """
    Manages local files and folders by voice. Supports creating files, moving files/folders,
    deleting files/folders, listing directory contents, and reading text files.
    """
    workspace_root = Path(r"c:\Users\Zahid\Documents\Personal\FRIDAY")
    
    # Resolve target path safely
    target_path = Path(path)
    if not target_path.is_absolute():
        target_path = workspace_root / target_path
    
    try:
        if action == "create":
            # Ensure parent directories exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully created file at {target_path.name}"
            
        elif action == "read":
            if not target_path.exists():
                return f"Error: Path {target_path.name} does not exist."
            if not target_path.is_file():
                return f"Error: Path {target_path.name} is a directory, not a file."
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read(2000)  # limit output to first 2000 characters
                if len(text) >= 2000:
                    text += "\n...[truncated]..."
                return f"Content of {target_path.name}:\n{text}"
                
        elif action == "list":
            if not target_path.exists():
                return f"Error: Directory {target_path.name} does not exist."
            if not target_path.is_dir():
                return f"Error: Path {target_path.name} is a file, not a directory."
            items = os.listdir(target_path)
            if not items:
                return f"Directory {target_path.name} is empty."
            return f"Items in {target_path.name}:\n- " + "\n- ".join(items)
            
        elif action == "delete":
            if not target_path.exists():
                return f"Error: Path {target_path.name} does not exist."
            if target_path.is_file():
                os.remove(target_path)
                return f"Successfully deleted file {target_path.name}"
            elif target_path.is_dir():
                shutil.rmtree(target_path)
                return f"Successfully deleted directory {target_path.name}"
                
        elif action == "move":
            if not target_path.exists():
                return f"Error: Source path {target_path.name} does not exist."
            if not destination:
                return "Error: Destination path is required for move action."
            
            dest_path = Path(destination)
            if not dest_path.is_absolute():
                dest_path = workspace_root / dest_path
                
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target_path), str(dest_path))
            return f"Moved {target_path.name} to {dest_path.name}"
            
        else:
            return f"Error: Unknown action '{action}'."
            
    except Exception as e:
        return f"File system action failed: {e}"
