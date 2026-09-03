from app.core.config import Settings
from app.rag.llms import ollama_client


class _Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def test_generation_request_metadata_records_explicit_settings_values() -> None:
    metadata = ollama_client.get_generation_request_metadata(Settings(_env_file=None))

    assert metadata == {
        "generation_stream": False,
        "generation_stream_source": "explicit",
        "generation_temperature": 0.0,
        "generation_temperature_source": "settings_explicit",
        "generation_seed": 42,
        "generation_seed_source": "settings_explicit",
        "generation_think": False,
        "generation_think_source": "settings_explicit",
        "generation_options": {"temperature": 0.0, "seed": 42},
        "generation_options_source": "settings_explicit",
        "generation_inherited_options": [
            "top_k",
            "top_p",
            "min_p",
            "repeat_penalty",
            "num_predict",
            "num_ctx",
        ],
        "generation_inherited_options_source": "ollama_model_or_service_defaults",
        "generation_timeout_seconds": 120,
        "generation_timeout_source": "explicit",
    }


def test_ollama_generate_sends_explicit_temperature_and_seed(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, *, json: dict[str, object], timeout: int) -> _Response:
        captured.update({"url": url, "payload": json, "timeout": timeout})
        return _Response({"response": "生成结果"})

    monkeypatch.setattr(ollama_client.requests, "post", fake_post)
    client = ollama_client.OllamaClient(Settings(_env_file=None))

    assert client.generate("测试提示") == "生成结果"
    assert captured["url"] == "http://127.0.0.1:11434/api/generate"
    assert captured["timeout"] == ollama_client.GENERATE_TIMEOUT_SECONDS
    assert captured["payload"] == {
        "model": "qwen3.5:9b",
        "prompt": "测试提示",
        "stream": False,
        "options": {"temperature": 0.0, "seed": 42},
        "think": False,
    }


def test_ollama_generate_only_sends_think_when_explicit(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, *, json: dict[str, object], timeout: int) -> _Response:
        captured["payload"] = json
        return _Response({"response": "生成结果"})

    monkeypatch.setattr(ollama_client.requests, "post", fake_post)
    client = ollama_client.OllamaClient(Settings(_env_file=None, OLLAMA_THINK=True))

    assert client.generate("测试提示") == "生成结果"
    assert captured["payload"] == {
        "model": "qwen3.5:9b",
        "prompt": "测试提示",
        "stream": False,
        "options": {"temperature": 0.0, "seed": 42},
        "think": True,
    }


def test_collect_ollama_runtime_metadata_reads_version_and_digest(monkeypatch) -> None:
    calls: list[str] = []

    def fake_get(url: str, *, timeout: int) -> _Response:
        calls.append(url)
        assert timeout == ollama_client.METADATA_TIMEOUT_SECONDS
        if url.endswith("/api/version"):
            return _Response({"version": "0.6.0"})
        return _Response(
            {
                "models": [
                    {
                        "name": "qwen3.5:9b",
                        "digest": "sha256:immutable-model-digest",
                    }
                ]
            }
        )

    monkeypatch.setattr(ollama_client.requests, "get", fake_get)

    metadata = ollama_client.collect_ollama_runtime_metadata(Settings(_env_file=None))

    assert calls == [
        "http://127.0.0.1:11434/api/version",
        "http://127.0.0.1:11434/api/tags",
    ]
    assert metadata["ollama_version"] == "0.6.0"
    assert metadata["ollama_version_source"] == "api_version"
    assert metadata["ollama_model_tag"] == "qwen3.5:9b"
    assert metadata["ollama_model_digest"] == "sha256:immutable-model-digest"
    assert metadata["ollama_model_digest_source"] == "api_tags"
    assert metadata["ollama_runtime_metadata_error"] is None


def test_collect_ollama_runtime_metadata_keeps_unknown_values_on_lookup_failure(
    monkeypatch,
) -> None:
    def fail_get(url: str, *, timeout: int) -> _Response:
        raise ollama_client.requests.ConnectionError("service unavailable")

    monkeypatch.setattr(ollama_client.requests, "get", fail_get)

    metadata = ollama_client.collect_ollama_runtime_metadata(Settings(_env_file=None))

    assert metadata["ollama_version"] is None
    assert metadata["ollama_version_source"] == "unknown"
    assert metadata["ollama_model_digest"] is None
    assert metadata["ollama_model_digest_source"] == "unknown"
    assert metadata["ollama_runtime_metadata_error"] == (
        "api_version_unavailable:ConnectionError;"
        "api_tags_unavailable:ConnectionError"
    )
