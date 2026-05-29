import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CodexRunResult:
    command: list[str]
    stdout: str
    stderr: str
    exit_code: int


def run_codex_headless(prompt: str, cwd: Path | None = None) -> CodexRunResult:
    command_text = os.getenv("CODEX_COMMAND", "codex exec")
    command = shlex.split(command_text) + [prompt]
    if not shutil.which(command[0]):
        raise RuntimeError(
            "Codex CLI is not installed. "
            "Set CODEX_COMMAND or install the CLI before using this wrapper."
        )

    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    return CodexRunResult(
        command,
        completed.stdout.strip(),
        completed.stderr.strip(),
        completed.returncode,
    )
