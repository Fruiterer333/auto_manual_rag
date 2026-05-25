import requests

from app.core.config import Settings
from app.rag.llms.base import BaseLLMClient


class OllamaClient(BaseLLMClient):
    """Ollama LLM client."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, prompt: str) -> str:
        url = f"{self.settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        payload = {
            "model": self.settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                "Failed to call Ollama. Please make sure Ollama is running "
                f"at {self.settings.OLLAMA_BASE_URL} and model "
                f"{self.settings.OLLAMA_MODEL} is available."
            ) from exc

        data = response.json()
        answer = data.get("response")
        if not isinstance(answer, str):
            raise RuntimeError("Ollama response does not contain a valid 'response' field.")
        return answer.strip()
