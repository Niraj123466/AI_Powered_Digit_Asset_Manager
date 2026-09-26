from abc import ABC, abstractmethod
from uuid import UUID
from app.db.models import Asset, AssetState, ProcessingJob, ProcessingStage
from app.db.repositories import (
    AssetRepository,
    ProcessingJobRepository,
    EmbeddingRepository,
    MediaMetadataRepository,
    ImageAnalysisRepository,
    VideoAnalysisRepository,
    DocumentAnalysisRepository,
    TranscriptRepository,
)
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.ai.factory import AIProviderFactory
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseProcessor(ABC):
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
        vector_store: QdrantVectorStore,
    ):
        self.asset_repo = asset_repo
        self.job_repo = job_repo
        self.embedding_repo = embedding_repo
        self.media_meta_repo = media_meta_repo
        self.image_analysis_repo = image_analysis_repo
        self.video_analysis_repo = video_analysis_repo
        self.document_analysis_repo = document_analysis_repo
        self.transcript_repo = transcript_repo
        self.vector_store = vector_store
        self.embedding_provider = AIProviderFactory.get_embedding_provider()

    @abstractmethod
    async def process(self, asset: Asset, job: ProcessingJob) -> None:
        pass

    async def _update_stage(self, asset: Asset, job: ProcessingJob, stage: ProcessingStage) -> None:
        await self.job_repo.update_state(job.id, AssetState.PROCESSING, stage)
        await self.asset_repo.update_state(asset.id, AssetState.PROCESSING, stage)
        logger.debug("Stage updated", asset_id=str(asset.id), stage=stage.value)

    async def _store_embeddings(
        self,
        asset: Asset,
        vectors: list,
        payloads: list,
        collection: str,
        content_type: str,
        model_name: str,
        model_version: str = None,
        content_refs: list = None,
    ) -> None:
        from app.db.models import Embedding, Modality
        import uuid

        points = []
        embeddings = []

        for i, (vector, payload) in enumerate(zip(vectors, payloads)):
            vector_id = str(uuid.uuid4())
            embedding = Embedding(
                asset_id=asset.id,
                modality=asset.modality,
                content_type=content_type,
                content_ref=content_refs[i] if content_refs else None,
                vector_id=vector_id,
                model_name=model_name,
                model_version=model_version,
                dimensions=len(vector),
            )
            embeddings.append(embedding)
            points.append(
                {
                    "id": vector_id,
                    "vector": vector,
                    "payload": {
                        **payload,
                        "asset_id": str(asset.id),
                        "embedding_id": str(embedding.id),
                    },
                }
            )

        # Store in PostgreSQL
        for emb in embeddings:
            await self.embedding_repo.create(emb)

        # Store in Qdrant
        from app.ai.embeddings.vector_store import VectorPoint

        qdrant_points = [VectorPoint(**p) for p in points]
        await self.vector_store.upsert(collection, qdrant_points)
