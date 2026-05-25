from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate an answer from a prompt."""
