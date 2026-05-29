import subprocess
from pathlib import Path

import pytest

from llm_ops_v1.agents import claude_headless, codex_headless


def test_claude_headless_builds_json_command(monkeypatch, tmp_path: Path) -> None:
    completed = subprocess.CompletedProcess(
        args=["claude"],
        returncode=0,
        stdout='{"result": "ok"}\n',
        stderr="",
    )
    calls: list[dict[str, object]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append({"command": command, **kwargs})
        return completed

    monkeypatch.setattr(claude_headless.shutil, "which", lambda _: "/usr/bin/claude")
    monkeypatch.setattr(claude_headless.subprocess, "run", fake_run)

    result = claude_headless.run_claude_headless("review this", cwd=tmp_path)

    assert result.command == ["/usr/bin/claude", "-p", "review this", "--output-format", "json"]
    assert '"result": "ok"' in result.stdout
    assert result.exit_code == 0
    assert calls[0]["cwd"] == str(tmp_path)


def test_claude_headless_requires_cli(monkeypatch) -> None:
    monkeypatch.setattr(claude_headless.shutil, "which", lambda _: None)

    with pytest.raises(RuntimeError, match="Claude CLI"):
        claude_headless.run_claude_headless("prompt")


def test_codex_headless_uses_configured_command(monkeypatch, tmp_path: Path) -> None:
    completed = subprocess.CompletedProcess(
        args=["codex"],
        returncode=0,
        stdout="done\n",
        stderr="",
    )
    calls: list[dict[str, object]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append({"command": command, **kwargs})
        return completed

    monkeypatch.setenv("CODEX_COMMAND", "codex exec --json")
    monkeypatch.setattr(codex_headless.shutil, "which", lambda _: "/usr/bin/codex")
    monkeypatch.setattr(codex_headless.subprocess, "run", fake_run)

    result = codex_headless.run_codex_headless("map repo", cwd=tmp_path)

    assert result.command == ["codex", "exec", "--json", "map repo"]
    assert result.stdout == "done"
    assert result.exit_code == 0
    assert calls[0]["cwd"] == str(tmp_path)


def test_codex_headless_requires_cli(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_COMMAND", "missing-codex exec")
    monkeypatch.setattr(codex_headless.shutil, "which", lambda _: None)

    with pytest.raises(RuntimeError, match="Codex CLI"):
        codex_headless.run_codex_headless("prompt")
