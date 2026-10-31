"""Gemini client behaviour, tested offline with a fake API client."""

import pytest
from google.genai import errors

from src.llm.gemini import GeminiClient, GeminiError


class Chunk:
    def __init__(self, text):
        self.text = text


def api_error(code, message="error"):
    return errors.ClientError(code, {"error": {"code": code, "message": message, "status": "X"}})


class FakeModels:
    """Behaviour per model: list of chunks to stream, or an exception to raise."""

    def __init__(self, behaviour):
        self.behaviour = behaviour
        self.calls = []

    def generate_content_stream(self, model, contents, config):
        self.calls.append((model, config.thinking_config))
        b = self.behaviour[model]
        if callable(b):
            b = b(config)
        if isinstance(b, Exception):
            raise b
        return (Chunk(t) for t in b)


def make_client(behaviour, thinking="low", models=("main", "backup")):
    client = GeminiClient(api_key="test", model=models[0], fallback_models=list(models[1:]), thinking=thinking)
    fake = FakeModels(behaviour)
    client._client = type("C", (), {"models": fake})()
    return client, fake


def test_streams_pieces_in_order():
    client, _ = make_client({"main": ["Fraud ", "must be reported ", "in 14 days [1]."]})
    assert list(client.generate_stream("sys", "q")) == ["Fraud ", "must be reported ", "in 14 days [1]."]
    assert client.last_model_used == "main"
    assert client.generate("sys", "q") == "Fraud must be reported in 14 days [1]."


def test_rate_limit_switches_model_immediately_and_cools_down():
    client, fake = make_client({"main": api_error(429), "backup": ["ok"]})
    assert client.generate("sys", "q") == "ok"
    assert client.last_model_used == "backup"
    fake.calls.clear()
    client.generate("sys", "q")
    assert [m for m, _ in fake.calls] == ["backup"]   # main skipped during cooldown


def test_thinking_setting_retried_without_when_rejected():
    def main(cfg):
        return api_error(400, "thinking_level is not supported") if cfg.thinking_config else ["ok"]

    client, fake = make_client({"main": main, "backup": ["unused"]})
    assert client.generate("sys", "q") == "ok"
    assert [m for m, _ in fake.calls] == ["main", "main"]
    assert fake.calls[1][1] is None


def test_thinking_config_per_model_family():
    client, _ = make_client({"main": ["x"]}, thinking="off")
    assert client._thinking_config("gemini-2.5-flash").thinking_budget == 0
    assert client._thinking_config("gemini-flash-latest").thinking_level is not None
    client.thinking = "default"
    assert client._thinking_config("gemini-flash-latest") is None


def test_all_models_failing_gives_readable_error():
    client, _ = make_client({"main": api_error(429), "backup": api_error(429)})
    with pytest.raises(GeminiError, match="Semantic Retrieval"):
        client.generate("sys", "q")


def test_bad_api_key_is_reported():
    client, _ = make_client({"main": api_error(403, "permission denied"), "backup": ["x"]})
    with pytest.raises(GeminiError, match="API key"):
        client.generate("sys", "q")


def test_missing_key_raises():
    with pytest.raises(GeminiError, match="GEMINI_API_KEY"):
        GeminiClient(api_key="your_gemini_api_key_here")
