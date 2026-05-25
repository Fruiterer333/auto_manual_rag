from app.core.config import Settings
from app.rag.llms.base import BaseLLMClient


class OllamaClient(BaseLLMClient):
    """Ollama LLM client placeholder. Real HTTP calls will be added later."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, prompt: str) -> str:
        raise NotImplementedError("Ollama generation will be implemented in V1.")
