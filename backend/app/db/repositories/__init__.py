from typing import Optional, List, Sequence
from uuid import UUID
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Asset,
    AssetState,
    Modality,
    ProcessingJob,
    ProcessingStage,
    MediaMetadata,
    ImageAnalysis,
    VideoAnalysis,
    VideoFrame,
    DocumentAnalysis,
    DocumentPage,
    Transcript,
    Embedding,
    DuplicateGroup,
    SearchQuery,
    AssetVersion,
)


class AssetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, asset: Asset) -> Asset:
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def get_by_id(self, asset_id: UUID) -> Optional[Asset]:
        result = await self.session.execute(
            select(Asset).options(selectinload(Asset.media_metadata)).where(Asset.id == asset_id)
        )
        return result.scalar_one_or_none()

    async def get_by_path(self, relative_path: str) -> Optional[Asset]:
        result = await self.session.execute(
            select(Asset).where(Asset.relative_path == relative_path)
        )
        return result.scalar_one_or_none()

    async def get_by_hash(
        self, sha256: str, modality: Optional[Modality] = None
    ) -> Optional[Asset]:
        stmt = select(Asset).where(Asset.sha256 == sha256)
        if modality:
            stmt = stmt.where(Asset.modality == modality)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_hash_all(self, sha256: str) -> Sequence[Asset]:
        result = await self.session.execute(select(Asset).where(Asset.sha256 == sha256))
        return result.scalars().all()

    async def update_state(
        self,
        asset_id: UUID,
        state: AssetState,
        error_message: Optional[str] = None,
        stage: Optional[ProcessingStage] = None,
        retry_count: Optional[int] = None,
    ) -> None:
        values = {"state": state, "updated_at": func.now()}
        if error_message is not None:
            values["error_message"] = error_message
        if stage is not None:
            values["processing_stage"] = stage
        if retry_count is not None:
            values["retry_count"] = retry_count
        if state == AssetState.PROCESSING:
            values["started_at"] = func.now()
        elif state in (AssetState.COMPLETED, AssetState.FAILED, AssetState.SKIPPED):
            values["completed_at"] = func.now()

        await self.session.execute(update(Asset).where(Asset.id == asset_id).values(**values))

    async def increment_version(self, asset_id: UUID) -> int:
        result = await self.session.execute(select(Asset.version).where(Asset.id == asset_id))
        current_version = result.scalar_one()
        new_version = current_version + 1
        await self.session.execute(
            update(Asset)
            .where(Asset.id == asset_id)
            .values(version=new_version, updated_at=func.now())
        )
        return new_version

    async def list_assets(
        self,
        modality: Optional[Modality] = None,
        state: Optional[AssetState] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Asset]:
        stmt = (
            select(Asset)
            .options(selectinload(Asset.media_metadata))
            .order_by(Asset.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if modality:
            stmt = stmt.where(Asset.modality == modality)
        if state:
            stmt = stmt.where(Asset.state == state)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_assets(
        self, modality: Optional[Modality] = None, state: Optional[AssetState] = None
    ) -> int:
        stmt = select(func.count(Asset.id))
        if modality:
            stmt = stmt.where(Asset.modality == modality)
        if state:
            stmt = stmt.where(Asset.state == state)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_failed_assets(self, limit: int = 100) -> Sequence[Asset]:
        result = await self.session.execute(
            select(Asset)
            .where(Asset.state == AssetState.FAILED)
            .order_by(Asset.updated_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def delete_asset(self, asset_id: UUID) -> bool:
        result = await self.session.execute(delete(Asset).where(Asset.id == asset_id))
        return result.rowcount > 0


class ProcessingJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job: ProcessingJob) -> ProcessingJob:
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_queued_jobs(self, limit: int = 100) -> Sequence[ProcessingJob]:
        result = await self.session.execute(
            select(ProcessingJob)
            .where(ProcessingJob.state == AssetState.QUEUED)
            .order_by(ProcessingJob.created_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_retryable_jobs(self, limit: int = 100) -> Sequence[ProcessingJob]:
        result = await self.session.execute(
            select(ProcessingJob)
            .where(
                ProcessingJob.state == AssetState.FAILED,
                ProcessingJob.retry_count < ProcessingJob.max_retries,
            )
            .order_by(ProcessingJob.updated_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_state(
        self,
        job_id: UUID,
        state: AssetState,
        stage: Optional[ProcessingStage] = None,
        error_message: Optional[str] = None,
        increment_retry: bool = False,
    ) -> None:
        values = {"state": state, "updated_at": func.now()}
        if stage is not None:
            values["stage"] = stage
        if error_message is not None:
            values["error_message"] = error_message
        if increment_retry:
            values["retry_count"] = ProcessingJob.retry_count + 1
        if state == AssetState.PROCESSING:
            values["started_at"] = func.now()
        elif state in (AssetState.COMPLETED, AssetState.FAILED):
            values["completed_at"] = func.now()

        await self.session.execute(
            update(ProcessingJob).where(ProcessingJob.id == job_id).values(**values)
        )


class EmbeddingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, embedding: Embedding) -> Embedding:
        self.session.add(embedding)
        await self.session.flush()
        return embedding

    async def get_by_asset(self, asset_id: UUID) -> Sequence[Embedding]:
        result = await self.session.execute(select(Embedding).where(Embedding.asset_id == asset_id))
        return result.scalars().all()

    async def delete_by_asset(self, asset_id: UUID) -> int:
        result = await self.session.execute(delete(Embedding).where(Embedding.asset_id == asset_id))
        return result.rowcount


class DuplicateGroupRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_hash(self, sha256: str) -> Optional[DuplicateGroup]:
        result = await self.session.execute(
            select(DuplicateGroup).where(DuplicateGroup.sha256 == sha256)
        )
        return result.scalar_one_or_none()

    async def create(self, group: DuplicateGroup) -> DuplicateGroup:
        self.session.add(group)
        await self.session.flush()
        return group

    async def increment_count(self, sha256: str) -> int:
        result = await self.session.execute(
            update(DuplicateGroup)
            .where(DuplicateGroup.sha256 == sha256)
            .values(reference_count=DuplicateGroup.reference_count + 1, updated_at=func.now())
            .returning(DuplicateGroup.reference_count)
        )
        return result.scalar_one()

    async def decrement_count(self, sha256: str) -> int:
        result = await self.session.execute(
            update(DuplicateGroup)
            .where(DuplicateGroup.sha256 == sha256)
            .values(reference_count=DuplicateGroup.reference_count - 1, updated_at=func.now())
            .returning(DuplicateGroup.reference_count)
        )
        return result.scalar_one()


class SearchQueryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_query(self, query: SearchQuery) -> SearchQuery:
        self.session.add(query)
        await self.session.flush()
        return query


class MediaMetadataRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, metadata: MediaMetadata) -> MediaMetadata:
        existing = await self.session.get(MediaMetadata, metadata.asset_id)
        if existing:
            for key, value in metadata.__dict__.items():
                if not key.startswith("_") and key != "id" and key != "asset_id":
                    setattr(existing, key, value)
            return existing
        else:
            self.session.add(metadata)
            await self.session.flush()
            return metadata


class ImageAnalysisRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, analysis: ImageAnalysis) -> ImageAnalysis:
        existing = await self.session.get(ImageAnalysis, analysis.asset_id)
        if existing:
            for key, value in analysis.__dict__.items():
                if not key.startswith("_") and key != "id" and key != "asset_id":
                    setattr(existing, key, value)
            return existing
        else:
            self.session.add(analysis)
            await self.session.flush()
            return analysis


class VideoAnalysisRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, analysis: VideoAnalysis) -> VideoAnalysis:
        existing = await self.session.get(VideoAnalysis, analysis.asset_id)
        if existing:
            for key, value in analysis.__dict__.items():
                if not key.startswith("_") and key != "id" and key != "asset_id":
                    setattr(existing, key, value)
            return existing
        else:
            self.session.add(analysis)
            await self.session.flush()
            return analysis

    async def add_frames(self, frames: List[VideoFrame]) -> List[VideoFrame]:
        for frame in frames:
            self.session.add(frame)
        await self.session.flush()
        return frames


class DocumentAnalysisRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, analysis: DocumentAnalysis) -> DocumentAnalysis:
        existing = await self.session.get(DocumentAnalysis, analysis.asset_id)
        if existing:
            for key, value in analysis.__dict__.items():
                if not key.startswith("_") and key != "id" and key != "asset_id":
                    setattr(existing, key, value)
            return existing
        else:
            self.session.add(analysis)
            await self.session.flush()
            return analysis

    async def add_pages(self, pages: List[DocumentPage]) -> List[DocumentPage]:
        for page in pages:
            self.session.add(page)
        await self.session.flush()
        return pages


class TranscriptRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, transcript: Transcript) -> Transcript:
        existing = await self.session.get(Transcript, transcript.asset_id)
        if existing:
            for key, value in transcript.__dict__.items():
                if not key.startswith("_") and key != "id" and key != "asset_id":
                    setattr(existing, key, value)
            return existing
        else:
            self.session.add(transcript)
            await self.session.flush()
            return transcript
