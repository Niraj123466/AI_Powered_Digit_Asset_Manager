from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session, async_session_factory
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
    SearchQueryRepository,
)
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.domain.indexing.orchestrator import IngestionOrchestrator
from app.search.service import SearchService
from app.core.config import settings


# Database dependencies
async def get_asset_repo(session: AsyncSession = Depends(get_session)) -> AssetRepository:
    return AssetRepository(session)


async def get_job_repo(session: AsyncSession = Depends(get_session)) -> ProcessingJobRepository:
    return ProcessingJobRepository(session)


async def get_embedding_repo(session: AsyncSession = Depends(get_session)) -> EmbeddingRepository:
    return EmbeddingRepository(session)


async def get_media_meta_repo(
    session: AsyncSession = Depends(get_session),
) -> MediaMetadataRepository:
    return MediaMetadataRepository(session)


async def get_image_analysis_repo(
    session: AsyncSession = Depends(get_session),
) -> ImageAnalysisRepository:
    return ImageAnalysisRepository(session)


async def get_video_analysis_repo(
    session: AsyncSession = Depends(get_session),
) -> VideoAnalysisRepository:
    return VideoAnalysisRepository(session)


async def get_document_analysis_repo(
    session: AsyncSession = Depends(get_session),
) -> DocumentAnalysisRepository:
    return DocumentAnalysisRepository(session)


async def get_transcript_repo(session: AsyncSession = Depends(get_session)) -> TranscriptRepository:
    return TranscriptRepository(session)


async def get_dup_group_repo(
    session: AsyncSession = Depends(get_session),
) -> DuplicateGroupRepository:
    return DuplicateGroupRepository(session)


async def get_search_query_repo(
    session: AsyncSession = Depends(get_session),
) -> SearchQueryRepository:
    return SearchQueryRepository(session)


# Vector store dependency
_vector_store: QdrantVectorStore = None


async def get_vector_store() -> QdrantVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = QdrantVectorStore()
        await _vector_store.initialize()
    return _vector_store


# Orchestrator dependency
_orchestrator: IngestionOrchestrator = None


async def get_orchestrator(
    asset_repo: AssetRepository = Depends(get_asset_repo),
    job_repo: ProcessingJobRepository = Depends(get_job_repo),
    embedding_repo: EmbeddingRepository = Depends(get_embedding_repo),
    media_meta_repo: MediaMetadataRepository = Depends(get_media_meta_repo),
    image_analysis_repo: ImageAnalysisRepository = Depends(get_image_analysis_repo),
    video_analysis_repo: VideoAnalysisRepository = Depends(get_video_analysis_repo),
    document_analysis_repo: DocumentAnalysisRepository = Depends(get_document_analysis_repo),
    transcript_repo: TranscriptRepository = Depends(get_transcript_repo),
    dup_group_repo: DuplicateGroupRepository = Depends(get_dup_group_repo),
    vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> IngestionOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = IngestionOrchestrator(
            asset_repo=asset_repo,
            job_repo=job_repo,
            embedding_repo=embedding_repo,
            media_meta_repo=media_meta_repo,
            image_analysis_repo=image_analysis_repo,
            video_analysis_repo=video_analysis_repo,
            document_analysis_repo=document_analysis_repo,
            transcript_repo=transcript_repo,
            dup_group_repo=dup_group_repo,
            vector_store=vector_store,
        )
        # Register processors
        from app.processors.image.processor import ImageProcessor
        from app.processors.video.processor import VideoProcessor
        from app.processors.pdf.processor import PDFProcessor

        _orchestrator.register_processors(
            image_processor=ImageProcessor(
                asset_repo, job_repo, embedding_repo, media_meta_repo, 
                image_analysis_repo, video_analysis_repo, document_analysis_repo, transcript_repo, vector_store
            ).process,
            video_processor=VideoProcessor(
                asset_repo, job_repo, embedding_repo, media_meta_repo,
                image_analysis_repo, video_analysis_repo, document_analysis_repo, transcript_repo, vector_store
            ).process,
            document_processor=PDFProcessor(
                asset_repo, job_repo, embedding_repo, media_meta_repo,
                image_analysis_repo, video_analysis_repo, document_analysis_repo, transcript_repo, vector_store
            ).process,
        )
    return _orchestrator


# Search service dependency
_search_service: SearchService = None


async def get_search_service(
    vector_store: QdrantVectorStore = Depends(get_vector_store),
    asset_repo: AssetRepository = Depends(get_asset_repo),
) -> SearchService:
    global _search_service
    if _search_service is None:
        _search_service = SearchService(vector_store, async_session_factory, asset_repo)
    return _search_service
