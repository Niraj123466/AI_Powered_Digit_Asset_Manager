import asyncio
import base64
import io
from typing import List, Optional
from PIL import Image

import ollama
from app.ai.base import VisionProvider, VisionResult
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaVisionProvider(VisionProvider):
    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        timeout: int = None,
    ):
        self._model_name = model or settings.vision_model
        self._base_url = base_url or settings.vision_base_url
        self._timeout = timeout or settings.vision_timeout
        self._client: Optional[ollama.AsyncClient] = None
        self._model_version: Optional[str] = None

    async def _get_client(self) -> ollama.AsyncClient:
        if self._client is None:
            self._client = ollama.AsyncClient(host=self._base_url, timeout=self._timeout)
        return self._client

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> Optional[str]:
        return self._model_version

    def _image_to_base64(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _parse_vision_response(self, response: str) -> VisionResult:
        # Parse structured response from vision model
        # Expected format: description with optional objects/tags
        lines = response.strip().split("\n")
        description = lines[0] if lines else "No description available"
        objects = []
        tags = []

        for line in lines[1:]:
            if line.lower().startswith("objects:"):
                objects = [o.strip() for o in line.split(":", 1)[1].split(",") if o.strip()]
            elif line.lower().startswith("tags:"):
                tags = [t.strip() for t in line.split(":", 1)[1].split(",") if t.strip()]

        return VisionResult(
            description=description,
            objects=objects,
            tags=tags,
            confidence=0.9,
        )

    async def analyze_image(self, image: Image.Image) -> VisionResult:
        client = await self._get_client()
        image_b64 = self._image_to_base64(image)

        prompt = """Describe this image in detail. Include:
1. A comprehensive visual description (1-2 sentences)
2. Objects: comma-separated list of main objects/entities
3. Tags: comma-separated list of relevant tags/categories

Format:
<description>
Objects: <comma-separated objects>
Tags: <comma-separated tags>"""

        try:
            response = await client.chat(
                model=self._model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image_b64],
                    }
                ],
            )
            return self._parse_vision_response(response["message"]["content"])
        except Exception as e:
            logger.error("Vision analysis failed", error=str(e), model=self._model_name)
            return VisionResult(
                description="Vision analysis failed",
                objects=[],
                tags=[],
                confidence=0.0,
            )

    async def analyze_images(self, images: List[Image.Image]) -> List[VisionResult]:
        # Process in parallel with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(2)

        async def analyze_one(image: Image.Image) -> VisionResult:
            async with semaphore:
                return await self.analyze_image(image)

        tasks = [analyze_one(img) for img in images]
        return await asyncio.gather(*tasks)


class DummyVisionProvider(VisionProvider):
    """Fallback provider for testing without vision model."""

    def __init__(self):
        self._model_name = "dummy"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model_version(self) -> Optional[str]:
        return "0.0.0"

    async def analyze_image(self, image: Image.Image) -> VisionResult:
        return VisionResult(
            description="Image analysis not available (dummy provider)",
            objects=[],
            tags=[],
            confidence=0.0,
        )

    async def analyze_images(self, images: List[Image.Image]) -> List[VisionResult]:
        return [await self.analyze_image(img) for img in images]
