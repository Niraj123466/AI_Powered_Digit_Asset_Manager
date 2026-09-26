import ollama
from typing import Optional
from app.ai.base import LLMProvider
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaLLMProvider(LLMProvider):
    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        temperature: float = None,
        max_tokens: int = None,
    ):
        self._model_name = model or settings.llm_model
        self._base_url = base_url or settings.llm_base_url
        self._temperature = temperature if temperature is not None else settings.llm_temperature
        self._max_tokens = max_tokens or settings.llm_max_tokens
        self._client: Optional[ollama.AsyncClient] = None
        self._model_version: Optional[str] = None

    async def _get_client(self) -> ollama.AsyncClient:
        if self._client is None:
            self._client = ollama.AsyncClient(host=self._base_url)
        return self._client

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> Optional[str]:
        return self._model_version

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        client = await self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await client.chat(
                model=self._model_name,
                messages=messages,
                options={
                    "temperature": self._temperature,
                    "num_predict": self._max_tokens,
                },
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error("LLM generation failed", error=str(e), model=self._model_name)
            raise

    async def summarize(self, text: str, max_length: int = 500) -> str:
        prompt = f"""Summarize the following text in at most {max_length} characters. 
Focus on the main topics, key information, and actionable content.

Text:
{text[:8000]}"""

        return await self.generate(
            prompt, system_prompt="You are a helpful summarization assistant."
        )


class DummyLLMProvider(LLMProvider):
    """Fallback provider for testing without LLM."""

    def __init__(self):
        self._model_name = "dummy"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> Optional[str]:
        return "0.0.0"

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        return "LLM generation not available (dummy provider)"

    async def summarize(self, text: str, max_length: int = 500) -> str:
        return text[:max_length] + "..." if len(text) > max_length else text
