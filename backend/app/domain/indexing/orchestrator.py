import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from app.db.repositories import (
    AssetRepository,
    ProcessingJobRepository,
    EmbeddingRepository,
    MediaMetadataRepository,
    ImageAnalysisRepository,
    VideoAnalysisRepository,
    DocumentAnalysisRepository,
    TranscriptRepository,
    DuplicateGroupRepository,
)
from app.db.models import Asset, AssetState, ProcessingJob, ProcessingStage, Modality
from app.domain.indexing.scanner import DiscoveredFile
from app.domain.indexing.duplicate_detector import DuplicateDetector, DuplicateResult
from app.ai.factory import AIProviderFactory
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import async_session_factory

logger = get_logger(__name__)


class IngestionEventType(str, Enum):
    STARTED = "started"
    FILE_DISCOVERED = "file_discovered"
    DUPLICATE_FOUND = "duplicate_found"
    PROCESSING_STARTED = "processing_started"
    STAGE_COMPLETED = "stage_completed"
    FILE_COMPLETED = "file_completed"
    FILE_FAILED = "file_failed"
    PROGRESS = "progress"
    COMPLETED = "completed"


@dataclass
class IngestionEvent:
    type: IngestionEventType
    data: dict


@dataclass
class IngestionStats:
    total_discovered: int = 0
    total_new: int = 0
    total_duplicates: int = 0
    total_processed: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    current_file: Optional[str] = None
    current_stage: Optional[str] = None


class IngestionOrchestrator:
    def __init__(
        self,
        asset_repo: AssetRepository,
        job_repo: ProcessingJobRepository,
        embedding_repo: EmbeddingRepository,
        media_meta_repo: MediaMetadataRepository,
        image_analysis_repo: ImageAnalysisRepository,
        video_analysis_repo: VideoAnalysisRepository,
        document_analysis_repo: DocumentAnalysisRepository,
        transcript_repo: TranscriptRepository,
        dup_group_repo: DuplicateGroupRepository,
        vector_store: QdrantVectorStore,
        event_callback: Optional[Callable[[IngestionEvent], Awaitable[None]]] = None,
    ):
        self.asset_repo = asset_repo
        self.job_repo = job_repo
        self.embedding_repo = embedding_repo
        self.media_meta_repo = media_meta_repo
        self.image_analysis_repo = image_analysis_repo
        self.video_analysis_repo = video_analysis_repo
        self.document_analysis_repo = document_analysis_repo
        self.transcript_repo = transcript_repo
        self.dup_group_repo = dup_group_repo
        self.vector_store = vector_store
        self.event_callback = event_callback

        self.stats = IngestionStats()
        self._running = False
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._processors = {}

    async def _emit(self, event: IngestionEvent) -> None:
        if self.event_callback:
            await self.event_callback(event)

    def _register_processor(self, modality: str, processor_factory: Callable) -> None:
        self._processors[modality] = processor_factory

    def _get_processor_for_asset(self, asset, job, repos: dict):
        modality = asset.modality.value
        if modality not in self._processors:
            raise ValueError(f"No processor for modality: {modality}")

        if modality == "image":
            from app.processors.image.processor import ImageProcessor
            return ImageProcessor(
                repos['asset_repo'], repos['job_repo'], repos['embedding_repo'],
                repos['media_meta_repo'], repos['image_analysis_repo'],
                repos['video_analysis_repo'], repos['document_analysis_repo'],
                repos['transcript_repo'], repos['vector_store']
            ).process
        elif modality == "video":
            from app.processors.video.processor import VideoProcessor
            return VideoProcessor(
                repos['asset_repo'], repos['job_repo'], repos['embedding_repo'],
                repos['media_meta_repo'], repos['image_analysis_repo'],
                repos['video_analysis_repo'], repos['document_analysis_repo'],
                repos['transcript_repo'], repos['vector_store']
            ).process
        elif modality == "document":
            from app.processors.pdf.processor import PDFProcessor
            return PDFProcessor(
                repos['asset_repo'], repos['job_repo'], repos['embedding_repo'],
                repos['media_meta_repo'], repos['image_analysis_repo'],
                repos['video_analysis_repo'], repos['document_analysis_repo'],
                repos['transcript_repo'], repos['vector_store']
            ).process
        else:
            raise ValueError(f"No processor for modality: {modality}")

    async def run_full_scan(self) -> IngestionStats:
        from app.domain.indexing.scanner import scan_media_root

        self._running = True
        self.stats = IngestionStats()
        self._semaphore = asyncio.Semaphore(settings.ingestion_workers)

        await self._emit(IngestionEvent(IngestionEventType.STARTED, {}))

        try:
            discovered_files = await scan_media_root()
            self.stats.total_discovered = len(discovered_files)

            dup_detector = DuplicateDetector(self.asset_repo, self.dup_group_repo)
            dup_result = await dup_detector.process(discovered_files)

            self.stats.total_new = len(dup_result.new_files)
            self.stats.total_duplicates = len(dup_result.duplicates)

            jobs_to_process = []
            for file in dup_result.new_files:
                job = ProcessingJob(
                    asset_id=uuid.uuid4(),
                    state=AssetState.QUEUED,
                    max_retries=settings.ingestion_max_retries,
                )
                jobs_to_process.append((file, job))

            for file, existing_asset_id in dup_result.duplicates:
                await self._handle_duplicate(file, existing_asset_id)
                await self._emit(IngestionEvent(IngestionEventType.DUPLICATE_FOUND, {
                    "path": file.relative_path,
                    "existing_asset_id": str(existing_asset_id),
                }))

            if jobs_to_process:
                await self._process_jobs(jobs_to_process)

            await self._emit(IngestionEvent(IngestionEventType.COMPLETED, {
                "stats": self.stats.__dict__,
            }))

        finally:
            self._running = False

        return self.stats

    async def _handle_duplicate(self, file: DiscoveredFile, existing_asset_id: UUID) -> None:
        async with async_session_factory() as session:
            asset_repo = AssetRepository(session)
            asset = Asset(
                sha256=file.sha256,
                filename=file.filename,
                relative_path=file.relative_path,
                absolute_path=str(file.path),
                extension=file.extension,
                mime_type=file.mime_type,
                file_size=file.file_size,
                modified_time=file.modified_time,
                modality=Modality(file.modality),
                state=AssetState.DUPLICATE,
            )
            await asset_repo.create(asset)
            await session.commit()

    async def _process_jobs(self, jobs: List[tuple]) -> None:
        async def process_one(file: DiscoveredFile, job: ProcessingJob) -> None:
            async with self._semaphore:
                if not self._running:
                    return

                async with async_session_factory() as session:
                    asset_repo = AssetRepository(session)
                    job_repo = ProcessingJobRepository(session)
                    embedding_repo = EmbeddingRepository(session)
                    media_meta_repo = MediaMetadataRepository(session)
                    image_analysis_repo = ImageAnalysisRepository(session)
                    video_analysis_repo = VideoAnalysisRepository(session)
                    document_analysis_repo = DocumentAnalysisRepository(session)
                    transcript_repo = TranscriptRepository(session)
                    dup_group_repo = DuplicateGroupRepository(session)

                    asset = Asset(
                        sha256=file.sha256,
                        filename=file.filename,
                        relative_path=file.relative_path,
                        absolute_path=str(file.path),
                        extension=file.extension,
                        mime_type=file.mime_type,
                        file_size=file.file_size,
                        modified_time=file.modified_time,
                        modality=Modality(file.modality),
                        state=AssetState.DISCOVERED,
                    )
                    await asset_repo.create(asset)
                    await session.flush()

                    vector_store = self.vector_store
                    processor = self._get_processor_for_asset(asset, job, {
                        'asset_repo': asset_repo,
                        'job_repo': job_repo,
                        'embedding_repo': embedding_repo,
                        'media_meta_repo': media_meta_repo,
                        'image_analysis_repo': image_analysis_repo,
                        'video_analysis_repo': video_analysis_repo,
                        'document_analysis_repo': document_analysis_repo,
                        'transcript_repo': TranscriptRepository(session),
                        'vector_store': vector_store,
                    })

                    await job_repo.update_state(
                        job.id, AssetState.PROCESSING, ProcessingStage.VALIDATION
                    )

                    self.stats.current_file = asset.relative_path
                    self.stats.current_stage = "VALIDATION"
                    await self._emit(
                        IngestionEvent(
                            IngestionEventType.PROCESSING_STARTED,
                            {
                                "asset_id": str(asset.id),
                                "path": asset.relative_path,
                            },
                        )
                    )

                    try:
                        await processor(asset, job)

                        await job_repo.update_state(job.id, AssetState.COMPLETED)
                        await asset_repo.update_state(asset.id, AssetState.COMPLETED)
                        self.stats.total_processed += 1
                        await self._emit(
                            IngestionEvent(
                                IngestionEventType.FILE_COMPLETED,
                                {
                                    "asset_id": str(asset.id),
                                },
                            )
                        )

                    except Exception as e:
                        logger.error("Processing failed", asset_id=str(asset.id), error=str(e))
                        await job_repo.update_state(
                            job.id, AssetState.FAILED, error_message=str(e), increment_retry=True
                        )
                        await asset_repo.update_state(
                            asset.id, AssetState.FAILED, error_message=str(e)
                        )
                        self.stats.total_failed += 1

                    finally:
                        try:
                            await session.commit()
                        except Exception as e:
                            logger.error("Commit failed", asset_id=str(asset.id), error=str(e))
                            await session.rollback()

                        self.stats.current_file = None
                        self.stats.current_stage = None
                        await self._emit(
                            IngestionEvent(
                                IngestionEventType.PROGRESS,
                                {
                                    "processed": self.stats.total_processed,
                                    "failed": self.stats.total_failed,
                                    "total": self.stats.total_new,
                                },
                            )
                        )

        tasks = [process_one(file, job) for file, job in jobs]
        await asyncio.gather(*tasks)

    def register_processors(
        self,
        image_processor: Callable,
        video_processor: Callable,
        document_processor: Callable,
    ) -> None:
        self._processors["image"] = image_processor
        self._processors["video"] = video_processor
        self._processors["document"] = document_processor