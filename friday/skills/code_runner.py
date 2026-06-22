import sys
import tempfile
import subprocess
from pathlib import Path
from langchain.tools import tool
from pydantic import BaseModel, Field
from friday.skills.self_modify import is_safe_code

class CodeExecutionInput(BaseModel):
    script_name: str = Field(description="Filename for the python script (e.g. 'test_script.py')")
    code_body: str = Field(description="The complete Python source code block to execute")
    keep_script: bool = Field(
        default=False,
        description="Set to true only when the script should be kept for debugging or reuse. Default is false, which deletes the script after execution.",
    )

@tool("run_python_code", args_schema=CodeExecutionInput)
def run_python_code(script_name: str, code_body: str, keep_script: bool = False) -> str:
    """
    Generates and runs a Python script locally on the system.
    Use this when the user asks to write and run a script, perform calculations, or run automation.
    By default the script is treated as temporary, executed, and deleted after the run.
    Set keep_script=True only when the script should be preserved for debugging or reuse.
    """
    workspace_root = Path(r"c:\Users\Zahid\Documents\Personal\FRIDAY")
    scratch_dir = workspace_root / "scratch"
    scratch_dir.mkdir(exist_ok=True)

    is_safe, safety_message = is_safe_code(code_body)
    if not is_safe:
        return f"Execution blocked by safety sandbox: {safety_message}"

    if not script_name.endswith(".py"):
        script_name += ".py"

    script_path = scratch_dir / script_name if keep_script else None
    cleanup_required = False

    try:
        if keep_script:
            target_path = script_path
        else:
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                prefix="friday_task_",
                dir=scratch_dir,
                delete=False,
                encoding="utf-8",
            )
            target_path = Path(temp_file.name)
            temp_file.close()
            cleanup_required = True

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(code_body)

        result = subprocess.run(
            [sys.executable, str(target_path)],
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

        if keep_script:
            output += f"\nScript saved at: {target_path}"
        else:
            output += "\nTemporary script deleted after execution."

        return output

    except subprocess.TimeoutExpired:
        return f"Execution failed: Timeout expired (15 seconds)."
    except Exception as e:
        return f"Execution failed: {e}"
    finally:
        if cleanup_required:
            try:
                target_path.unlink(missing_ok=True)
            except Exception:
                pass
