from time import perf_counter

import requests

from app.core.config import Settings
from app.core.logger import get_logger
from app.rag.llms.base import BaseLLMClient


logger = get_logger(__name__)


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
        payload = {
            "model": self.settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        logger.info(
            "Calling Ollama: base_url=%s model=%s prompt_chars=%s",
            self.settings.OLLAMA_BASE_URL,
            self.settings.OLLAMA_MODEL,
            len(prompt),
        )

        try:
            response = requests.post(url, json=payload, timeout=120)
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
