import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HeadlessRunResult:
    command: list[str]
    stdout: str
    stderr: str
    exit_code: int


def run_claude_headless(prompt: str, cwd: Path | None = None) -> HeadlessRunResult:
    binary = shutil.which("claude")
    if not binary:
        raise RuntimeError("Claude CLI is not installed or not available on PATH.")

    command = [binary, "-p", prompt, "--output-format", "json"]
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = completed.stdout.strip()
    if stdout:
        stdout = json.dumps(json.loads(stdout), indent=2)
    return HeadlessRunResult(command, stdout, completed.stderr.strip(), completed.returncode)
