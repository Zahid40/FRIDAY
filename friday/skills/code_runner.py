import sys
import subprocess
from pathlib import Path
from langchain.tools import tool
from pydantic import BaseModel, Field

class CodeExecutionInput(BaseModel):
    script_name: str = Field(description="Filename for the python script (e.g. 'test_script.py')")
    code_body: str = Field(description="The complete Python source code block to execute")

@tool("run_python_code", args_schema=CodeExecutionInput)
def run_python_code(script_name: str, code_body: str) -> str:
    """
    Generates and runs a Python script locally on the system.
    Use this when the user asks to write and run a script, perform calculations, or run automation.
    The script is saved in the project's scratch directory and executed with Python.
    """
    workspace_root = Path(r"c:\Users\Zahid\Documents\Personal\FRIDAY")
    scratch_dir = workspace_root / "scratch"
    scratch_dir.mkdir(exist_ok=True)
    
    # Ensure file ends with .py
    if not script_name.endswith(".py"):
        script_name += ".py"
        
    script_path = scratch_dir / script_name
    
    try:
        # Write script
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code_body)
            
        # Execute script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        output = f"Execution Status: {'Success' if result.returncode == 0 else 'Failed (Exit Code ' + str(result.returncode) + ')'}\n"
        if result.stdout:
            output += f"Stdout:\n{result.stdout.strip()}\n"
        if result.stderr:
            output += f"Stderr:\n{result.stderr.strip()}\n"
            
        if not result.stdout and not result.stderr:
            output += "Script ran successfully with no output."
            
        return output
        
    except subprocess.TimeoutExpired:
        return f"Execution failed: Timeout expired (15 seconds)."
    except Exception as e:
        return f"Execution failed: {e}"
