import pytest

from llm_ops_v1.economics import router


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.raised = False

    def raise_for_status(self) -> None:
        self.raised = True

    def json(self) -> dict[str, object]:
        return self._payload


class FakeAsyncClient:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.requests: list[dict[str, object]] = []

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def post(
        self,
        url: str,
        json: dict[str, object],
        headers: dict[str, str],
    ) -> FakeResponse:
        self.requests.append({"url": url, "json": json, "headers": headers})
        return self.response


def test_openrouter_client_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        router.OpenRouterClient()


async def test_openrouter_client_posts_chat_completion(monkeypatch) -> None:
    response = FakeResponse({"choices": [{"message": {"content": "ok"}}]})
    fake_client = FakeAsyncClient(response)
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-token")
    monkeypatch.setattr(router.httpx, "AsyncClient", lambda timeout: fake_client)
    client = router.OpenRouterClient(base_url="https://openrouter.test/api/v1")

    payload = await client.chat_completion(
        model="deepseek/deepseek-v4-flash",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=128,
        temperature=0.1,
    )

    assert payload == {"choices": [{"message": {"content": "ok"}}]}
    assert response.raised is True
    assert fake_client.requests == [
        {
            "url": "https://openrouter.test/api/v1/chat/completions",
            "json": {
                "model": "deepseek/deepseek-v4-flash",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 128,
                "temperature": 0.1,
            },
            "headers": {
                "Authorization": "Bearer env-token",
                "Content-Type": "application/json",
            },
        }
    ]
