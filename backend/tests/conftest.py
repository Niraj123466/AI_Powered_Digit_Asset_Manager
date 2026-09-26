"""Shared test configuration and fixtures."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.db.models import Asset, AssetState, Modality, ProcessingJob, ProcessingStage
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


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_asset():
    return Asset(
        id=uuid4(),
        sha256="abc123",
        filename="test.jpg",
        relative_path="test.jpg",
        absolute_path="/media/test.jpg",
        extension="jpg",
        mime_type="image/jpeg",
        file_size=1000,
        modified_time=datetime.now(),
        modality=Modality.IMAGE,
        state=AssetState.COMPLETED,
    )


@pytest.fixture
def sample_video_asset():
    return Asset(
        id=uuid4(),
        sha256="vid456",
        filename="video.mp4",
        relative_path="video.mp4",
        absolute_path="/media/video.mp4",
        extension="mp4",
        mime_type="video/mp4",
        file_size=1000000,
        modified_time=datetime.now(),
        modality=Modality.VIDEO,
        state=AssetState.COMPLETED,
    )


@pytest.fixture
def sample_document_asset():
    return Asset(
        id=uuid4(),
        sha256="doc789",
        filename="document.pdf",
        relative_path="document.pdf",
        absolute_path="/media/document.pdf",
        extension="pdf",
        mime_type="application/pdf",
        file_size=500000,
        modified_time=datetime.now(),
        modality=Modality.DOCUMENT,
        state=AssetState.COMPLETED,
    )


@pytest.fixture
def sample_processing_job(sample_asset):
    return ProcessingJob(
        id=uuid4(),
        asset_id=sample_asset.id,
        state=AssetState.QUEUED,
        stage=ProcessingStage.VALIDATION,
        max_retries=3,
    )


# Mock repository fixtures
@pytest.fixture
def mock_asset_repo():
    repo = AsyncMock(spec=AssetRepository)
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_path = AsyncMock()
    repo.get_by_hash = AsyncMock()
    repo.get_by_hash_all = AsyncMock()
    repo.update_state = AsyncMock()
    repo.increment_version = AsyncMock()
    repo.list_assets = AsyncMock()
    repo.count_assets = AsyncMock()
    repo.get_failed_assets = AsyncMock()
    repo.delete_asset = AsyncMock()
    return repo


@pytest.fixture
def mock_job_repo():
    repo = AsyncMock(spec=ProcessingJobRepository)
    repo.create = AsyncMock()
    repo.get_queued_jobs = AsyncMock()
    repo.get_retryable_jobs = AsyncMock()
    repo.update_state = AsyncMock()
    return repo


@pytest.fixture
def mock_embedding_repo():
    repo = AsyncMock(spec=EmbeddingRepository)
    repo.create = AsyncMock()
    repo.get_by_asset = AsyncMock()
    repo.delete_by_asset = AsyncMock()
    return repo


@pytest.fixture
def mock_media_meta_repo():
    repo = AsyncMock(spec=MediaMetadataRepository)
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def mock_image_analysis_repo():
    repo = AsyncMock(spec=ImageAnalysisRepository)
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def mock_video_analysis_repo():
    repo = AsyncMock(spec=VideoAnalysisRepository)
    repo.upsert = AsyncMock()
    repo.add_frames = AsyncMock()
    return repo


@pytest.fixture
def mock_document_analysis_repo():
    repo = AsyncMock(spec=DocumentAnalysisRepository)
    repo.upsert = AsyncMock()
    repo.add_pages = AsyncMock()
    return repo


@pytest.fixture
def mock_transcript_repo():
    repo = AsyncMock(spec=TranscriptRepository)
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def mock_dup_group_repo():
    repo = AsyncMock(spec=DuplicateGroupRepository)
    repo.get_by_hash = AsyncMock()
    repo.create = AsyncMock()
    repo.increment_count = AsyncMock()
    repo.decrement_count = AsyncMock()
    return repo


@pytest.fixture
def mock_search_query_repo():
    repo = AsyncMock(spec=SearchQueryRepository)
    repo.log_query = AsyncMock()
    return repo


# AI Provider mocks
@pytest.fixture
def mock_embedding_provider():
    provider = AsyncMock()
    provider.model_name = "test-embedding-model"
    provider.dimensions = 512
    provider.model_version = "1.0"
    provider.embed_text = AsyncMock(return_value=[[0.1] * 512])
    provider.embed_image = AsyncMock(return_value=[[0.1] * 512])
    provider.embed_single_text = AsyncMock(return_value=[0.1] * 512)
    provider.embed_single_image = AsyncMock(return_value=[0.1] * 512)
    return provider


@pytest.fixture
def mock_vision_provider():
    provider = AsyncMock()
    provider.model_name = "test-vision-model"
    provider.model_version = "1.0"
    provider.analyze_image = AsyncMock(
        return_value=MagicMock(
            description="Test image description",
            objects=["object1", "object2"],
            tags=["tag1", "tag2"],
            confidence=0.9,
        )
    )
    provider.analyze_images = AsyncMock(
        return_value=[
            MagicMock(description="Frame 1", objects=["obj1"], tags=["tag1"]),
            MagicMock(description="Frame 2", objects=["obj2"], tags=["tag2"]),
        ]
    )
    return provider


@pytest.fixture
def mock_ocr_provider():
    provider = AsyncMock()
    provider.model_name = "tesseract"
    provider.extract_text = AsyncMock(
        return_value=MagicMock(text="OCR extracted text", confidence=0.85, bboxes=[])
    )
    return provider


@pytest.fixture
def mock_transcription_provider():
    provider = AsyncMock()
    provider.model_name = "whisper-base"
    provider.model_version = "1.0"
    provider.transcribe = AsyncMock(
        return_value=MagicMock(
            full_text="Transcribed audio text",
            segments=[{"start": 0.0, "end": 5.0, "text": "Hello world"}],
            language="en",
        )
    )
    return provider


@pytest.fixture
def mock_llm_provider():
    provider = AsyncMock()
    provider.model_name = "test-llm"
    provider.model_version = "1.0"
    provider.generate = AsyncMock(return_value="Generated text")
    provider.summarize = AsyncMock(return_value="Summary of document")
    return provider


# Vector store mock
@pytest.fixture
def mock_vector_store():
    from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
    from app.ai.embeddings.vector_store import SearchResult, VectorPoint

    store = AsyncMock(spec=QdrantVectorStore)
    store.initialize = AsyncMock()
    store.close = AsyncMock()
    store.upsert = AsyncMock()
    store.delete = AsyncMock()
    store.delete_by_filter = AsyncMock()
    store.search = AsyncMock(
        return_value=[
            SearchResult(id=str(uuid4()), score=0.9, payload={"asset_id": str(uuid4())}),
            SearchResult(id=str(uuid4()), score=0.8, payload={"asset_id": str(uuid4())}),
        ]
    )
    store.search_batch = AsyncMock(
        return_value=[
            [SearchResult(id=str(uuid4()), score=0.9, payload={})],
            [SearchResult(id=str(uuid4()), score=0.8, payload={})],
        ]
    )
    store.count = AsyncMock(return_value=100)
    store.collection_exists = AsyncMock(return_value=True)
    store.create_collection = AsyncMock()
    return store
