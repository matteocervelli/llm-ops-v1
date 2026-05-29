from pathlib import Path


def test_webhook_demo_script_exists_and_mentions_endpoint() -> None:
    script = Path("demos/webhook_demo.sh")

    text = script.read_text()

    assert script.exists()
    assert "/webhook/ticket" in text
    assert "LLM_OPS_WEBHOOK_TOKEN" in text
    assert "BACKEND" in text
    assert "export BACKEND BODY SUBJECT" in text
