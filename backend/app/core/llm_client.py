from typing import Optional

import httpx

from app.core.config import get_settings

settings = get_settings()


class LLMClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self._client = httpx.Client(timeout=20.0)

    def chat(self, model: str, messages: list[dict], temperature: float = 0.2, tools: Optional[list] = None) -> dict:
        if not self.api_key:
            return {"content": None, "tool_calls": None, "fallback": True}
        payload = {"model": model, "messages": messages, "temperature": temperature}
        if tools:
            payload["tools"] = tools
        try:
            resp = self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            msg = data["choices"][0]["message"]
            return {
                "content": msg.get("content"),
                "tool_calls": msg.get("tool_calls"),
                "usage": data.get("usage"),
                "model": data.get("model"),
            }
        except Exception as e:
            return {"content": None, "tool_calls": None, "error": str(e), "fallback": True}

    def embed(self, texts: list[str]) -> Optional[list[list[float]]]:
        if not self.api_key:
            return None
        try:
            resp = self._client.post(
                f"{self.base_url}/embeddings",
                json={"model": settings.embedding_model, "input": texts},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return [d["embedding"] for d in data["data"]]
        except Exception:
            return None


_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient(settings.llm_api_key, settings.llm_base_url)
    return _client
