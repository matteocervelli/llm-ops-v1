#!/usr/bin/env python3
"""PreToolUse hook: block dangerous bash commands.

Claude Code calls this script before every Bash tool use, passing a JSON
payload on stdin. Exit 2 blocks the command and feeds stderr back to Claude.
Exit 0 allows it. Exit 1 signals a non-blocking script error.

Usage in settings.json:
  "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command",
                  "command": "python .claude/hooks/pre-bash.py"}]}]

Students: copy this to .claude/hooks/pre-bash.py in your project.
"""

import json
import re
import sys

# Each entry: (compiled pattern, human-readable reason).
# re.search() is used, so patterns match anywhere in the command string.
BLOCKED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"rm\s+-rf?\s+[/~.]"),
        "Blocked: destructive rm -rf detected. Use 'rm' without -rf on specific paths.",
    ),
    (
        re.compile(r"\b(DROP\s+TABLE|DROP\s+DATABASE|TRUNCATE)\b", re.IGNORECASE),
        "Blocked: destructive SQL statement. Run schema changes manually after review.",
    ),
    (
        re.compile(r"git\s+push\s+--force"),
        "Blocked: force push. Use --force-with-lease or push to a feature branch.",
    ),
    (
        re.compile(r"--no-verify"),
        "Blocked: --no-verify skips git hooks, which defeats this safety layer.",
    ),
    (
        re.compile(r"(curl|wget)\s+.+\|\s*(ba)?sh"),
        "Blocked: pipe-to-shell pattern. Download the script first, review it, then run it.",
    ),
    (
        re.compile(r"chmod\s+777"),
        "Blocked: chmod 777 grants world-write access. Use the minimum required permissions.",
    ),
    (
        re.compile(r">\s*/dev/sd"),
        "Blocked: raw device write detected. This would overwrite disk data.",
    ),
]


def main() -> None:
    # --- 1. Read the hook payload from stdin ---
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"pre-bash.py: invalid JSON input: {exc}", file=sys.stderr)
        sys.exit(1)

    # --- 2. Only inspect Bash tool calls ---
    # The matcher in settings.json already filters, but guard defensively.
    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command: str = payload.get("tool_input", {}).get("command", "")

    # --- 3. Check command against blocked patterns ---
    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(command):
            print(reason, file=sys.stderr)
            sys.exit(2)  # exit 2 = block; Claude sees stderr as feedback

    # --- 4. All checks passed — allow the command ---
    sys.exit(0)


if __name__ == "__main__":
    main()
