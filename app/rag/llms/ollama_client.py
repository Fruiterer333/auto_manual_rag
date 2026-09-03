from typing import Any
from time import perf_counter

import requests

from app.core.config import Settings
from app.core.logger import get_logger
from app.rag.llms.base import BaseLLMClient


logger = get_logger(__name__)


GENERATE_TIMEOUT_SECONDS = 120
METADATA_TIMEOUT_SECONDS = 5
INHERITED_GENERATION_OPTIONS = (
    "top_k",
    "top_p",
    "min_p",
    "repeat_penalty",
    "num_predict",
    "num_ctx",
)


def get_generation_options(settings: Settings) -> dict[str, float | int]:
    """Return the complete set of generation options explicitly controlled here."""
    return {
        "temperature": settings.OLLAMA_TEMPERATURE,
        "seed": settings.OLLAMA_SEED,
    }


def build_generation_request_payload(settings: Settings, prompt: str) -> dict[str, Any]:
    """Build the single request shape shared by production and evaluation calls."""
    payload: dict[str, Any] = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": get_generation_options(settings),
    }
    if settings.OLLAMA_THINK is not None:
        payload["think"] = settings.OLLAMA_THINK
    return payload


def get_generation_request_metadata(settings: Settings) -> dict[str, Any]:
    """Describe the exact generation controls sent by the current client."""
    options = get_generation_options(settings)
    return {
        "generation_stream": False,
        "generation_stream_source": "explicit",
        "generation_temperature": options["temperature"],
        "generation_temperature_source": "settings_explicit",
        "generation_seed": options["seed"],
        "generation_seed_source": "settings_explicit",
        "generation_think": settings.OLLAMA_THINK,
        "generation_think_source": (
            "settings_explicit" if settings.OLLAMA_THINK is not None else "unset"
        ),
        "generation_options": options,
        "generation_options_source": "settings_explicit",
        "generation_inherited_options": list(INHERITED_GENERATION_OPTIONS),
        "generation_inherited_options_source": "ollama_model_or_service_defaults",
        "generation_timeout_seconds": GENERATE_TIMEOUT_SECONDS,
        "generation_timeout_source": "explicit",
    }


def collect_ollama_runtime_metadata(settings: Settings) -> dict[str, str | None]:
    """Best-effort runtime identity metadata without invoking generation.

    Version and digest are intentionally optional: a metadata lookup failure must
    not change generation behavior or prevent a baseline from recording the
    unknown value it actually ran with.
    """
    base_url = settings.OLLAMA_BASE_URL.rstrip("/")
    metadata: dict[str, str | None] = {
        "ollama_base_url": base_url,
        "ollama_version": None,
        "ollama_version_source": "unknown",
        "ollama_model_tag": settings.OLLAMA_MODEL,
        "ollama_model_digest": None,
        "ollama_model_digest_source": "unknown",
        "ollama_runtime_metadata_error": None,
    }
    errors: list[str] = []

    try:
        response = requests.get(
            f"{base_url}/api/version",
            timeout=METADATA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        version = response.json().get("version")
        if isinstance(version, str) and version:
            metadata["ollama_version"] = version
            metadata["ollama_version_source"] = "api_version"
        else:
            errors.append("api_version_missing_version")
    except (requests.RequestException, ValueError) as exc:
        errors.append(f"api_version_unavailable:{type(exc).__name__}")

    try:
        response = requests.get(
            f"{base_url}/api/tags",
            timeout=METADATA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        models = response.json().get("models")
        if isinstance(models, list):
            matching_model = next(
                (
                    model
                    for model in models
                    if isinstance(model, dict)
                    and settings.OLLAMA_MODEL in {
                        model.get("name"),
                        model.get("model"),
                    }
                ),
                None,
            )
            digest = matching_model.get("digest") if matching_model else None
            if isinstance(digest, str) and digest:
                metadata["ollama_model_digest"] = digest
                metadata["ollama_model_digest_source"] = "api_tags"
            else:
                errors.append("api_tags_model_digest_unavailable")
        else:
            errors.append("api_tags_missing_models")
    except (requests.RequestException, ValueError) as exc:
        errors.append(f"api_tags_unavailable:{type(exc).__name__}")

    if errors:
        metadata["ollama_runtime_metadata_error"] = ";".join(errors)
        logger.warning(
            "Ollama runtime metadata incomplete: model=%s errors=%s",
            settings.OLLAMA_MODEL,
            metadata["ollama_runtime_metadata_error"],
        )
    else:
        logger.info(
            "Ollama runtime metadata collected: model=%s version=%s digest=%s",
            settings.OLLAMA_MODEL,
            metadata["ollama_version"],
            metadata["ollama_model_digest"],
        )
    return metadata


class OllamaClient(BaseLLMClient):
    """Ollama LLM client."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        logger.info(
            "Initialized Ollama client: base_url=%s model=%s",
            self.settings.OLLAMA_BASE_URL,
            self.settings.OLLAMA_MODEL,
        )

    def generate(self, prompt: str) -> str:
        start_time = perf_counter()
        url = f"{self.settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        payload = build_generation_request_payload(self.settings, prompt)
        logger.info(
            "Calling Ollama: base_url=%s model=%s prompt_chars=%s temperature=%s seed=%s think=%s",
            self.settings.OLLAMA_BASE_URL,
            self.settings.OLLAMA_MODEL,
            len(prompt),
            self.settings.OLLAMA_TEMPERATURE,
            self.settings.OLLAMA_SEED,
            self.settings.OLLAMA_THINK,
        )

        try:
            response = requests.post(url, json=payload, timeout=GENERATE_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("Ollama request failed: model=%s", self.settings.OLLAMA_MODEL)
            raise RuntimeError(
                "Failed to call Ollama. Please make sure Ollama is running "
                f"at {self.settings.OLLAMA_BASE_URL} and model "
                f"{self.settings.OLLAMA_MODEL} is available."
            ) from exc

        data = response.json()
        answer = data.get("response")
        if not isinstance(answer, str):
            logger.error("Ollama response missing valid response field")
            raise RuntimeError("Ollama response does not contain a valid 'response' field.")
        answer = answer.strip()
        logger.info(
            "Ollama response received: answer_chars=%s elapsed=%.2fs",
            len(answer),
            perf_counter() - start_time,
        )
        return answer
