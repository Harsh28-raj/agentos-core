import sys
import subprocess
import tempfile
import os
from langchain_core.tools import tool

@tool
def python_code_interpreter(code: str) -> str:
    """Executes the given Python code snippet and returns its output (stdout/stderr).
    Useful for math, data processing, and logical reasoning."""
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        result = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        os.remove(temp_file_path)

        output = ""
        if result.stdout:
            output += f"Output:\n{result.stdout}\n"
        if result.stderr:
            output += f"Error:\n{result.stderr}\n"

        if not output:
            output = "Code executed successfully with no output."
            
        return output
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out after 30 seconds."
    except Exception as e:
        return f"Error executing code: {str(e)}"
