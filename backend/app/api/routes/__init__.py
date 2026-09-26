from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pathlib import Path

from app.api.dependencies import (
    get_orchestrator,
    get_search_service,
    get_asset_repo,
    get_job_repo,
    get_vector_store,
    get_search_query_repo,
)
from app.domain.indexing.orchestrator import (
    IngestionOrchestrator,
    IngestionEvent,
    IngestionEventType,
)
from app.search.service import SearchService
from app.db.repositories import AssetRepository, ProcessingJobRepository, SearchQueryRepository
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.db.models import Asset, AssetState, Modality
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Health check
@router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# Indexing endpoints
class IndexStartResponse(BaseModel):
    message: str
    status: str


@router.post("/index/start", response_model=IndexStartResponse)
async def start_indexing(
    background_tasks: BackgroundTasks,
    orchestrator: IngestionOrchestrator = Depends(get_orchestrator),
):
    # Run indexing in background
    background_tasks.add_task(orchestrator.run_full_scan)
    return IndexStartResponse(message="Indexing started", status="started")


class IndexStatusResponse(BaseModel):
    running: bool
    stats: dict


@router.get("/index/status", response_model=IndexStatusResponse)
async def index_status(
    orchestrator: IngestionOrchestrator = Depends(get_orchestrator),
):
    return IndexStatusResponse(
        running=orchestrator._running,
        stats=orchestrator.stats.__dict__,
    )


@router.post("/index/retry-failed")
async def retry_failed(
    background_tasks: BackgroundTasks,
    orchestrator: IngestionOrchestrator = Depends(get_orchestrator),
    job_repo: ProcessingJobRepository = Depends(get_job_repo),
):
    # Reset failed jobs to queued
    failed_jobs = await job_repo.get_retryable_jobs(limit=1000)
    for job in failed_jobs:
        await job_repo.update_state(job.id, AssetState.QUEUED)

    background_tasks.add_task(orchestrator.run_full_scan)
    return {"message": f"Retrying {len(failed_jobs)} failed jobs", "status": "started"}


# Asset endpoints
class AssetResponse(BaseModel):
    id: UUID
    filename: str
    relative_path: str
    extension: str
    mime_type: str
    file_size: int
    modality: Modality
    state: AssetState
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict] = None


def _to_asset_response(asset) -> AssetResponse:
    meta_dict = {
        "file_size": asset.file_size,
        "modified_time": asset.modified_time.isoformat() if asset.modified_time else None,
        "extension": asset.extension,
    }
    if hasattr(asset, "media_metadata") and asset.media_metadata:
        m = asset.media_metadata
        if m.width is not None:
            meta_dict["width"] = m.width
        if m.height is not None:
            meta_dict["height"] = m.height
        if m.duration is not None:
            meta_dict["duration"] = m.duration
        if m.page_count is not None:
            meta_dict["page_count"] = m.page_count
        if m.format is not None:
            meta_dict["format"] = m.format
    return AssetResponse(
        id=asset.id,
        filename=asset.filename,
        relative_path=asset.relative_path,
        extension=asset.extension,
        mime_type=asset.mime_type,
        file_size=asset.file_size,
        modality=asset.modality,
        state=asset.state,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        metadata=meta_dict,
    )


class AssetListResponse(BaseModel):
    assets: List[AssetResponse]
    total: int
    limit: int
    offset: int


@router.get("/assets", response_model=AssetListResponse)
async def list_assets(
    modality: Optional[Modality] = None,
    state: Optional[AssetState] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    assets = await asset_repo.list_assets(
        modality=modality, state=state, limit=limit, offset=offset
    )
    total = await asset_repo.count_assets(modality=modality, state=state)

    return AssetListResponse(
        assets=[_to_asset_response(a) for a in assets],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    asset = await asset_repo.get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return _to_asset_response(asset)


# Search endpoints
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    modality: Optional[Modality] = None
    filters: Optional[dict] = None
    limit: int = Field(20, le=100)
    offset: int = Field(0, ge=0)


class SearchResultItem(BaseModel):
    asset_id: UUID
    score: float
    modality: Modality
    filename: str
    relative_path: str
    explanation: str
    metadata: dict
    matched_details: dict


class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    total: int
    query: str
    latency_ms: int


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service),
):
    response = await search_service.search(
        query=request.query,
        modality_filter=request.modality,
        filters=request.filters,
        limit=request.limit,
        offset=request.offset,
    )
    # Convert SearchResult to SearchResultItem
    results = []
    for r in response.results:
        results.append(SearchResultItem(
            asset_id=r.asset_id,
            score=r.score,
            modality=r.modality,
            filename=r.filename,
            relative_path=r.relative_path,
            explanation=r.explanation,
            metadata=r.metadata,
            matched_details=r.matched_details,
        ))
    return SearchResponse(
        results=results,
        total=response.total,
        query=response.query,
        latency_ms=response.latency_ms,
    )


# Stats endpoint
class StatsResponse(BaseModel):
    total_assets: int
    images: int
    videos: int
    documents: int
    indexed: int
    processing: int
    failed: int
    duplicates: int


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    total = await asset_repo.count_assets()
    images = await asset_repo.count_assets(modality=Modality.IMAGE)
    videos = await asset_repo.count_assets(modality=Modality.VIDEO)
    documents = await asset_repo.count_assets(modality=Modality.DOCUMENT)
    indexed = await asset_repo.count_assets(state=AssetState.COMPLETED)
    processing = await asset_repo.count_assets(state=AssetState.PROCESSING)
    failed = await asset_repo.count_assets(state=AssetState.FAILED)
    duplicates = await asset_repo.count_assets(state=AssetState.DUPLICATE)

    return StatsResponse(
        total_assets=total,
        images=images,
        videos=videos,
        documents=documents,
        indexed=indexed,
        processing=processing,
        failed=failed,
        duplicates=duplicates,
    )


# Filters endpoint
@router.get("/filters")
async def get_filters():
    return {
        "modalities": [m.value for m in Modality],
        "states": [s.value for s in AssetState],
        "extensions": {
            "image": ["jpg", "jpeg", "png", "webp"],
            "video": ["mp4", "mov", "mkv", "avi", "webm"],
            "document": ["pdf"],
        },
    }


# Asset preview/download endpoints
@router.get("/assets/{asset_id}/preview")
async def preview_asset(
    asset_id: UUID,
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    asset = await asset_repo.get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Security: ensure path is within MEDIA_ROOT
    media_root = settings.media_root.resolve()
    asset_path = Path(asset.absolute_path).resolve()

    try:
        asset_path.relative_to(media_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not asset_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Determine media type for proper serving
    media_type = asset.mime_type
    if asset.modality == Modality.VIDEO:
        # For video, support range requests for seeking
        return FileResponse(
            path=asset_path,
            media_type=media_type,
            filename=asset.filename,
        )

    return FileResponse(
        path=asset_path,
        media_type=media_type,
        filename=asset.filename,
    )


@router.get("/assets/{asset_id}/download")
async def download_asset(
    asset_id: UUID,
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    asset = await asset_repo.get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Security: ensure path is within MEDIA_ROOT
    media_root = settings.media_root.resolve()
    asset_path = Path(asset.absolute_path).resolve()

    try:
        asset_path.relative_to(media_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    if not asset_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=asset_path,
        media_type="application/octet-stream",
        filename=asset.filename,
    )


# Asset detail endpoint with full analysis
class AssetDetailResponse(BaseModel):
    asset: AssetResponse
    image_analysis: Optional[dict] = None
    video_analysis: Optional[dict] = None
    video_frames: List[dict] = []
    document_analysis: Optional[dict] = None
    document_pages: List[dict] = []
    transcript: Optional[dict] = None
    embeddings: List[dict] = []


@router.get("/assets/{asset_id}/detail", response_model=AssetDetailResponse)
async def get_asset_detail(
    asset_id: UUID,
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    from sqlalchemy import select
    from app.db.session import async_session_factory
    from app.db.models import (
        ImageAnalysis,
        VideoAnalysis,
        VideoFrame,
        DocumentAnalysis,
        DocumentPage,
        Transcript,
        Embedding,
    )

    asset = await asset_repo.get_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    async with async_session_factory() as session:
        # Get all related data
        image_analysis = None
        video_analysis = None
        video_frames = []
        document_analysis = None
        document_pages = []
        transcript = None
        embeddings = []

        if asset.modality == Modality.IMAGE:
            result = await session.execute(
                select(ImageAnalysis).where(ImageAnalysis.asset_id == asset_id)
            )
            ia = result.scalar_one_or_none()
            if ia:
                image_analysis = {
                    "description": ia.description,
                    "objects": ia.objects,
                    "tags": ia.tags,
                    "ocr_text": ia.ocr_text,
                    "ocr_confidence": ia.ocr_confidence,
                    "vision_model": ia.vision_model,
                    "ocr_provider": ia.ocr_provider,
                }

        elif asset.modality == Modality.VIDEO:
            result = await session.execute(
                select(VideoAnalysis).where(VideoAnalysis.asset_id == asset_id)
            )
            va = result.scalar_one_or_none()
            if va:
                video_analysis = {
                    "summary": va.summary,
                    "frame_count": va.frame_count,
                    "processed_frames": va.processed_frames,
                    "keyframes": va.keyframes,
                    "vision_model": va.vision_model,
                }

            result = await session.execute(
                select(VideoFrame)
                .where(VideoFrame.asset_id == asset_id)
                .order_by(VideoFrame.frame_number)
            )
            video_frames = [
                {
                    "frame_number": vf.frame_number,
                    "timestamp": vf.timestamp,
                    "description": vf.description,
                    "objects": vf.objects,
                    "embedding_id": str(vf.embedding_id) if vf.embedding_id else None,
                }
                for vf in result.scalars()
            ]

            result = await session.execute(
                select(Transcript).where(Transcript.asset_id == asset_id)
            )
            tr = result.scalar_one_or_none()
            if tr:
                transcript = {
                    "full_text": tr.full_text,
                    "segments": tr.segments,
                    "language": tr.language,
                    "transcription_model": tr.transcription_model,
                }

        elif asset.modality == Modality.DOCUMENT:
            result = await session.execute(
                select(DocumentAnalysis).where(DocumentAnalysis.asset_id == asset_id)
            )
            da = result.scalar_one_or_none()
            if da:
                document_analysis = {
                    "summary": da.summary,
                    "total_chars": da.total_chars,
                    "ocr_pages_count": da.ocr_pages_count,
                    "native_text_pages": da.native_text_pages,
                    "llm_model": da.llm_model,
                }

            result = await session.execute(
                select(DocumentPage)
                .where(DocumentPage.asset_id == asset_id)
                .order_by(DocumentPage.page_number)
            )
            document_pages = [
                {
                    "page_number": dp.page_number,
                    "text": dp.text,
                    "char_count": dp.char_count,
                    "is_ocr": dp.is_ocr,
                    "embedding_id": str(dp.embedding_id) if dp.embedding_id else None,
                }
                for dp in result.scalars()
            ]

        # Get embeddings for all modalities
        result = await session.execute(select(Embedding).where(Embedding.asset_id == asset_id))
        embeddings = [
            {
                "id": str(e.id),
                "content_type": e.content_type,
                "content_ref": e.content_ref,
                "vector_id": e.vector_id,
                "model_name": e.model_name,
                "dimensions": e.dimensions,
            }
            for e in result.scalars()
        ]

        return AssetDetailResponse(
            asset=AssetResponse(
                id=asset.id,
                filename=asset.filename,
                relative_path=asset.relative_path,
                extension=asset.extension,
                mime_type=asset.mime_type,
                file_size=asset.file_size,
                modality=asset.modality,
                state=asset.state,
                created_at=asset.created_at,
                updated_at=asset.updated_at,
                metadata={
                    "file_size": asset.file_size,
                    "modified_time": asset.modified_time.isoformat() if asset.modified_time else None,
                    "extension": asset.extension,
                },
            ),
            image_analysis=image_analysis,
            video_analysis=video_analysis,
            video_frames=video_frames,
            document_analysis=document_analysis,
            document_pages=document_pages,
            transcript=transcript,
            embeddings=embeddings,
        )
