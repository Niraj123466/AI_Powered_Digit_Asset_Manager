import asyncio
from pathlib import Path
from uuid import UUID
from PIL import Image, ExifTags
import io

from app.db.models import (
    Asset,
    ProcessingJob,
    ProcessingStage,
    MediaMetadata,
    ImageAnalysis,
    Modality,
)
from app.db.repositories import (
    AssetRepository,
    ProcessingJobRepository,
    EmbeddingRepository,
    MediaMetadataRepository,
    ImageAnalysisRepository,
)
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.ai.factory import AIProviderFactory
from app.processors.base import BaseProcessor
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ImageProcessor(BaseProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vision_provider = AIProviderFactory.get_vision_provider()
        self.ocr_provider = AIProviderFactory.get_ocr_provider()

    async def process(self, asset: Asset, job: ProcessingJob) -> None:
        # Stage: Validation
        await self._update_stage(asset, job, ProcessingStage.VALIDATION)
        await self._validate_image(asset)

        # Stage: Metadata Extraction
        await self._update_stage(asset, job, ProcessingStage.METADATA_EXTRACTION)
        metadata = await self._extract_metadata(asset)
        await self.media_meta_repo.upsert(metadata)

        # Stage: AI Analysis
        await self._update_stage(asset, job, ProcessingStage.AI_ANALYSIS)
        image = await self._load_image(asset)
        vision_result, ocr_result = await asyncio.gather(
            self.vision_provider.analyze_image(image),
            self._extract_ocr(image) if settings.enable_ocr else asyncio.sleep(0, result=None),
        )

        # Stage: Embedding Generation
        await self._update_stage(asset, job, ProcessingStage.EMBEDDING_GENERATION)
        image_embedding = await self.embedding_provider.embed_single_image(image)

        # Combine text for text embedding
        text_parts = []
        if vision_result.description:
            text_parts.append(vision_result.description)
        if ocr_result and ocr_result.text:
            text_parts.append(ocr_result.text)

        text_embedding = None
        if text_parts:
            combined_text = " ".join(text_parts)
            text_embedding = await self.embedding_provider.embed_single_text(combined_text)

        # Store analysis
        analysis = ImageAnalysis(
            asset_id=asset.id,
            description=vision_result.description,
            objects=vision_result.objects,
            tags=vision_result.tags,
            ocr_text=ocr_result.text if ocr_result else None,
            ocr_confidence=ocr_result.confidence if ocr_result else None,
            ocr_bboxes=ocr_result.bboxes if ocr_result else None,
            vision_model=self.vision_provider.model_name,
            vision_model_version=self.vision_provider.model_version,
            ocr_provider=self.ocr_provider.model_name if settings.enable_ocr else None,
        )
        await self.image_analysis_repo.upsert(analysis)

        # Store embeddings
        vectors = [image_embedding]
        payloads = [
            {
                "modality": "image",
                "content_type": "image",
                "description": vision_result.description,
                "ocr_text": ocr_result.text if ocr_result else "",
                "path": asset.relative_path,
            }
        ]
        content_refs = ["image"]

        if text_embedding:
            vectors.append(text_embedding)
            payloads.append(
                {
                    "modality": "image",
                    "content_type": "text",
                    "text": " ".join(text_parts),
                    "path": asset.relative_path,
                }
            )
            content_refs.append("text")

        await self._store_embeddings(
            asset=asset,
            vectors=vectors,
            payloads=payloads,
            collection="assets_image",
            content_type="image",
            model_name=self.embedding_provider.model_name,
            model_version=self.embedding_provider.model_version,
            content_refs=content_refs,
        )

    async def _validate_image(self, asset: Asset) -> None:
        path = Path(asset.absolute_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        try:
            with Image.open(path) as img:
                img.verify()
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")

    async def _load_image(self, asset: Asset) -> Image.Image:
        path = Path(asset.absolute_path)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: Image.open(path).convert("RGB"))

    async def _extract_metadata(self, asset: Asset) -> MediaMetadata:
        path = Path(asset.absolute_path)
        loop = asyncio.get_event_loop()

        def _extract():
            with Image.open(path) as img:
                width, height = img.size
                format = img.format
                exif_data = {}
                if hasattr(img, "_getexif") and img._getexif():
                    for tag_id, value in img._getexif().items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        exif_data[tag] = str(value)
                return width, height, format, exif_data

        width, height, format, exif_data = await loop.run_in_executor(None, _extract)

        return MediaMetadata(
            asset_id=asset.id,
            width=width,
            height=height,
            format=format,
            exif_data=exif_data,
        )

    async def _extract_ocr(self, image: Image.Image):
        if not settings.enable_ocr:
            return None
        return await self.ocr_provider.extract_text(image)
