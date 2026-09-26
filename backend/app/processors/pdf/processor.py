import asyncio
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple
from PIL import Image
import io

from app.db.models import (
    Asset,
    ProcessingJob,
    ProcessingStage,
    MediaMetadata,
    DocumentAnalysis,
    DocumentPage,
    Modality,
)
from app.db.repositories import (
    AssetRepository,
    ProcessingJobRepository,
    EmbeddingRepository,
    MediaMetadataRepository,
    DocumentAnalysisRepository,
)
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.ai.factory import AIProviderFactory
from app.processors.base import BaseProcessor
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class PDFProcessor(BaseProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ocr_provider = AIProviderFactory.get_ocr_provider()
        self.llm_provider = AIProviderFactory.get_llm_provider()

    async def process(self, asset: Asset, job: ProcessingJob) -> None:
        # Stage: Validation
        await self._update_stage(asset, job, ProcessingStage.VALIDATION)
        await self._validate_pdf(asset)

        # Stage: Metadata Extraction
        await self._update_stage(asset, job, ProcessingStage.METADATA_EXTRACTION)
        metadata, doc = await self._extract_metadata_and_doc(asset)
        await self.media_meta_repo.upsert(metadata)

        # Stage: Text Extraction + OCR
        await self._update_stage(asset, job, ProcessingStage.AI_ANALYSIS)
        pages_data = await self._extract_pages(doc)

        # Stage: Embedding Generation
        await self._update_stage(asset, job, ProcessingStage.EMBEDDING_GENERATION)
        await self._generate_embeddings(asset, pages_data)

        # Generate summary
        full_text = " ".join([p["text"] for p in pages_data if p["text"]])
        summary = "No text content"
        llm_model = self.llm_provider.model_name
        llm_model_version = self.llm_provider.model_version
        if full_text:
            try:
                summary = await self.llm_provider.summarize(full_text)
            except Exception as e:
                logger.warning("LLM summarization failed, using fallback", error=str(e))
                summary = full_text[:500] + "..." if len(full_text) > 500 else full_text
                llm_model = "fallback"
                llm_model_version = "0.0.0"

        # Store analysis
        analysis = DocumentAnalysis(
            asset_id=asset.id,
            summary=summary,
            total_chars=len(full_text),
            ocr_pages_count=sum(1 for p in pages_data if p["is_ocr"]),
            native_text_pages=sum(1 for p in pages_data if not p["is_ocr"]),
            llm_model=self.llm_provider.model_name,
            llm_model_version=self.llm_provider.model_version,
        )
        await self.document_analysis_repo.upsert(analysis)

        # Store pages
        doc_pages = []
        for page_data in pages_data:
            doc_pages.append(
                DocumentPage(
                    asset_id=asset.id,
                    page_number=page_data["page_number"],
                    text=page_data["text"],
                    char_count=len(page_data["text"]),
                    is_ocr=page_data["is_ocr"],
                )
            )
        await self.document_analysis_repo.add_pages(doc_pages)

        doc.close()

    async def _validate_pdf(self, asset: Asset) -> None:
        path = Path(asset.absolute_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")
        try:
            doc = fitz.open(path)
            doc.close()
        except Exception as e:
            raise ValueError(f"Invalid PDF file: {e}")

    async def _extract_metadata_and_doc(self, asset: Asset) -> Tuple[MediaMetadata, fitz.Document]:
        path = Path(asset.absolute_path)
        loop = asyncio.get_event_loop()

        def _extract():
            doc = fitz.open(path)
            page_count = doc.page_count
            pdf_info = doc.metadata
            return doc, page_count, pdf_info

        doc, page_count, pdf_info = await loop.run_in_executor(None, _extract)

        metadata = MediaMetadata(
            asset_id=asset.id,
            page_count=page_count,
            pdf_info=pdf_info,
        )
        return metadata, doc

    async def _extract_pages(self, doc: fitz.Document) -> List[dict]:
        pages_data = []

        for page_num in range(doc.page_count):
            page = doc[page_num]

            # Try native text extraction first
            text = page.get_text()

            is_ocr = False
            if (
                len(text.strip()) < settings.pdf_ocr_threshold_chars_per_page
                and settings.enable_ocr
            ):
                # Low text density - likely scanned, use OCR
                is_ocr = True
                text = await self._ocr_page(page)

            pages_data.append(
                {
                    "page_number": page_num + 1,
                    "text": text.strip(),
                    "is_ocr": is_ocr,
                }
            )

        return pages_data

    async def _ocr_page(self, page: fitz.Page) -> str:
        # Render page to image
        pix = page.get_pixmap(dpi=settings.ocr_dpi)
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))

        ocr_result = await self.ocr_provider.extract_text(image)
        return ocr_result.text

    async def _generate_embeddings(self, asset: Asset, pages_data: List[dict]) -> None:
        # Chunk pages if needed
        chunks = []
        chunk_refs = []

        for page_data in pages_data:
            text = page_data["text"]
            if not text:
                continue

            # Simple chunking by page for now
            chunks.append(text)
            chunk_refs.append(f"page_{page_data['page_number']}")

        if not chunks:
            return

        embeddings = await self.embedding_provider.embed_text(chunks)

        payloads = []
        for i, (text, page_ref) in enumerate(zip(chunks, chunk_refs)):
            payloads.append(
                {
                    "modality": "document",
                    "content_type": "page",
                    "page_number": int(page_ref.split("_")[1]),
                    "text_preview": text[:500],
                    "path": asset.relative_path,
                }
            )

        await self._store_embeddings(
            asset=asset,
            vectors=embeddings,
            payloads=payloads,
            collection="assets_document",
            content_type="page",
            model_name=self.embedding_provider.model_name,
            model_version=self.embedding_provider.model_version,
            content_refs=chunk_refs,
        )
