"""Python code interpreter tool.

SECURITY: this runs model-written code on the API server. It is disabled unless
ENABLE_CODE_INTERPRETER=true. When enabled, the child process gets no secrets in its
environment, an isolated interpreter (-I), a throw-away working directory, and CPU,
memory, file-size and process limits. That reduces the blast radius but it is NOT a
real sandbox (no network or filesystem isolation) - see docs/SECURITY.md.
"""
import os
import subprocess
import sys
import tempfile

from langchain_core.tools import tool

from app.core import config

MAX_OUTPUT_CHARS = 4000
_SAFE_ENV = {"PATH": "/usr/bin:/bin", "PYTHONIOENCODING": "utf-8", "HOME": "/tmp", "LANG": "C.UTF-8"}


def _limit_resources():  # runs in the child before exec (POSIX only)
    import resource
    cpu = config.CODE_TIMEOUT_SECONDS
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
    os.setsid()


def run_python(code: str) -> str:
    if not config.ENABLE_CODE_INTERPRETER:
        return ("The code interpreter is disabled on this server (ENABLE_CODE_INTERPRETER is off). "
                "Explain the solution or compute it step by step instead.")
    with tempfile.TemporaryDirectory(prefix="agentos_code_") as workdir:
        script = os.path.join(workdir, "main.py")
        with open(script, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            result = subprocess.run(
                [sys.executable, "-I", script],
                capture_output=True,
                text=True,
                timeout=config.CODE_TIMEOUT_SECONDS,
                cwd=workdir,
                env=_SAFE_ENV,
                stdin=subprocess.DEVNULL,
                preexec_fn=_limit_resources if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out after {config.CODE_TIMEOUT_SECONDS} seconds."
        except Exception as e:
            return f"Error executing code: {e}"

    output = ""
    if result.stdout:
        output += f"Output:\n{result.stdout}\n"
    if result.stderr:
        output += f"Error:\n{result.stderr}\n"
    output = output or "Code executed successfully with no output."
    return output[:MAX_OUTPUT_CHARS]


@tool
def python_code_interpreter(code: str) -> str:
    """Executes the given Python code snippet and returns its output (stdout/stderr).
    Useful for math, data processing, and logical reasoning. Print the values you need."""
    return run_python(code)
