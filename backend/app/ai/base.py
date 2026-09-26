from typing import Protocol, List, Optional
from dataclasses import dataclass
from PIL import Image


@dataclass
class VisionResult:
    description: str
    objects: List[str]
    tags: List[str]
    confidence: float = 1.0


@dataclass
class OCRResult:
    text: str
    confidence: float
    bboxes: List[dict]


@dataclass
class TranscriptResult:
    full_text: str
    segments: List[dict]  # {"start": float, "end": float, "text": str}
    language: str


class EmbeddingProvider(Protocol):
    async def embed_text(self, texts: List[str]) -> List[List[float]]: ...
    async def embed_image(self, images: List[Image.Image]) -> List[List[float]]: ...
    async def embed_single_text(self, text: str) -> List[float]: ...
    async def embed_single_image(self, image: Image.Image) -> List[float]: ...

    @property
    def model_name(self) -> str: ...
    @property
    def dimensions(self) -> int: ...
    @property
    def model_version(self) -> Optional[str]: ...


class VisionProvider(Protocol):
    async def analyze_image(self, image: Image.Image) -> VisionResult: ...
    async def analyze_images(self, images: List[Image.Image]) -> List[VisionResult]: ...

    @property
    def model_name(self) -> str: ...
    @property
    def model_version(self) -> Optional[str]: ...


class OCRProvider(Protocol):
    async def extract_text(self, image: Image.Image) -> OCRResult: ...

    @property
    def model_name(self) -> str: ...


class TranscriptionProvider(Protocol):
    async def transcribe(self, audio_path: str) -> TranscriptResult: ...

    @property
    def model_name(self) -> str: ...
    @property
    def model_version(self) -> Optional[str]: ...


class LLMProvider(Protocol):
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str: ...
    async def summarize(self, text: str, max_length: int = 500) -> str: ...

    @property
    def model_name(self) -> str: ...
    @property
    def model_version(self) -> Optional[str]: ...


class Reranker(Protocol):
    async def rerank(self, query: str, candidates: List[str]) -> List[float]: ...

    @property
    def model_name(self) -> str: ...
