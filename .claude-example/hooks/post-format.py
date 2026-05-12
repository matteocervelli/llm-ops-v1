#!/usr/bin/env python3
"""PostToolUse hook: auto-format Python files with ruff after Write/Edit.

Claude Code calls this after every Write or Edit tool use. PostToolUse hooks
cannot block (the file is already written), so this always exits 0.

Runs: ruff format <file> then ruff check --fix <file>
Falls back gracefully if ruff is not installed.

Usage in settings.json:
  "PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command",
                   "command": "python .claude/hooks/post-format.py"}]}]

Students: copy this to .claude/hooks/post-format.py in your project.
"""

import json
import subprocess
import sys


def handle(payload: dict) -> None:
    """Format the file referenced in a Write or Edit payload.

    Exposed as a function so tests can call it directly without stdin.
    """
    file_path: str = payload.get("tool_input", {}).get("file_path", "")

    # Only format Python files — other types have no ruff support here
    if not file_path.endswith(".py"):
        return

    try:
        subprocess.run(["ruff", "format", file_path], check=False, capture_output=True)
        subprocess.run(["ruff", "check", "--fix", file_path], check=False, capture_output=True)
    except FileNotFoundError:
        # ruff is not installed in this environment — skip silently
        print(
            f"post-format.py: ruff not found, skipping auto-format for {file_path}",
            file=sys.stderr,
        )


def main() -> None:
    # --- 1. Read the hook payload from stdin ---
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"post-format.py: invalid JSON input: {exc}", file=sys.stderr)
        sys.exit(0)  # non-blocking: file already written

    handle(payload)
    sys.exit(0)


if __name__ == "__main__":
    main()
