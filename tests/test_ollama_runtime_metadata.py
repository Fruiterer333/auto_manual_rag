from app.core.config import Settings
from app.rag.llms import ollama_client


class _Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def test_generation_request_metadata_preserves_unset_ollama_defaults() -> None:
    metadata = ollama_client.get_generation_request_metadata()

    assert metadata == {
        "generation_stream": False,
        "generation_temperature": None,
        "generation_temperature_source": "unset_ollama_default",
        "generation_seed": None,
        "generation_seed_source": "unset_ollama_default",
        "generation_options": None,
        "generation_options_source": "not_sent",
        "generation_timeout_seconds": 120,
        "generation_timeout_source": "explicit",
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
                        "name": "qwen2.5:7b",
                        "digest": "sha256:immutable-model-digest",
                    }
                ]
            }
        )

    monkeypatch.setattr(ollama_client.requests, "get", fake_get)

    metadata = ollama_client.collect_ollama_runtime_metadata(Settings())

    assert calls == [
        "http://127.0.0.1:11434/api/version",
        "http://127.0.0.1:11434/api/tags",
    ]
    assert metadata["ollama_version"] == "0.6.0"
    assert metadata["ollama_version_source"] == "api_version"
    assert metadata["ollama_model_tag"] == "qwen2.5:7b"
    assert metadata["ollama_model_digest"] == "sha256:immutable-model-digest"
    assert metadata["ollama_model_digest_source"] == "api_tags"
    assert metadata["ollama_runtime_metadata_error"] is None


def test_collect_ollama_runtime_metadata_keeps_unknown_values_on_lookup_failure(
    monkeypatch,
) -> None:
    def fail_get(url: str, *, timeout: int) -> _Response:
        raise ollama_client.requests.ConnectionError("service unavailable")

    monkeypatch.setattr(ollama_client.requests, "get", fail_get)

    metadata = ollama_client.collect_ollama_runtime_metadata(Settings())

    assert metadata["ollama_version"] is None
    assert metadata["ollama_version_source"] == "unknown"
    assert metadata["ollama_model_digest"] is None
    assert metadata["ollama_model_digest_source"] == "unknown"
    assert metadata["ollama_runtime_metadata_error"] == (
        "api_version_unavailable:ConnectionError;"
        "api_tags_unavailable:ConnectionError"
    )
