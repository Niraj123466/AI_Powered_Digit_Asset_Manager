import asyncio
from typing import List, Optional
from PIL import Image
import torch
from sentence_transformers import SentenceTransformer

from app.ai.base import EmbeddingProvider
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SentenceTransformersEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        model_name: str = None,
        device: str = None,
        batch_size: int = None,
    ):
        self._model_name = model_name or settings.embedding_model
        self._device = self._resolve_device(device or settings.embedding_device)
        self._batch_size = batch_size or settings.embedding_batch_size
        self._model: Optional[SentenceTransformer] = None
        self._dimensions: Optional[int] = None

    def _resolve_device(self, device: str) -> str:
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        return device

    def _load_model(self) -> None:
        if self._model is None:
            logger.info("Loading embedding model", model=self._model_name, device=self._device)
            self._model = SentenceTransformer(self._model_name, device=self._device)
            # Get dimensions from model
            test_embedding = self._model.encode(["test"], convert_to_tensor=False)
            self._dimensions = len(test_embedding[0])
            logger.info("Embedding model loaded", dimensions=self._dimensions)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        if self._dimensions is None:
            self._load_model()
        return self._dimensions

    @property
    def model_version(self) -> Optional[str]:
        return None  # sentence-transformers doesn't expose version easily

    async def embed_text(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(
                texts,
                batch_size=self._batch_size,
                convert_to_tensor=False,
                show_progress_bar=False,
                normalize_embeddings=True,
            ),
        )
        return embeddings.tolist()

    async def embed_image(self, images: List[Image.Image]) -> List[List[float]]:
        self._load_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(
                images,
                batch_size=self._batch_size,
                convert_to_tensor=False,
                show_progress_bar=False,
                normalize_embeddings=True,
            ),
        )
        return embeddings.tolist()

    async def embed_single_text(self, text: str) -> List[float]:
        results = await self.embed_text([text])
        return results[0]

    async def embed_single_image(self, image: Image.Image) -> List[float]:
        results = await self.embed_image([image])
        return results[0]


# Fallback for when model is not available
class DummyEmbeddingProvider(EmbeddingProvider):
    """Fallback provider that returns zero vectors for testing."""

    def __init__(self, dimensions: int = 512):
        self._dimensions = dimensions
        self._model_name = "dummy"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_version(self) -> Optional[str]:
        return "0.0.0"

    async def embed_text(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * self._dimensions for _ in texts]

    async def embed_image(self, images: List[Image.Image]) -> List[List[float]]:
        return [[0.0] * self._dimensions for _ in images]

    async def embed_single_text(self, text: str) -> List[float]:
        return [0.0] * self._dimensions

    async def embed_single_image(self, image: Image.Image) -> List[float]:
        return [0.0] * self._dimensions
