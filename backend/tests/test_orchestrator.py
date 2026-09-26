import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from pathlib import Path

from app.domain.indexing.orchestrator import IngestionOrchestrator, IngestionStats
from app.domain.indexing.scanner import FileScanner, DiscoveredFile
from app.domain.indexing.duplicate_detector import DuplicateDetector, DuplicateResult
from app.db.models import (
    Asset, AssetState, Modality, ProcessingJob, ProcessingStage,
    MediaMetadata, ImageAnalysis, VideoAnalysis, VideoFrame,
    DocumentAnalysis, DocumentPage, Transcript, Embedding,
    AssetVersion, DuplicateGroup, SearchQuery, SearchQuery
)
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
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.search.query_parser import QueryParser
from app.db.session import async_session_factory
from sqlalchemy import delete


@pytest.fixture(autouse=True)
async def clean_database():
    """Clean the database before each test."""
    async with async_session_factory() as session:
        # Delete all data in reverse dependency order
        await session.execute(delete(SearchQuery))
        await session.execute(delete(DuplicateGroup))
        await session.execute(delete(AssetVersion))
        await session.execute(delete(Transcript))
        await session.execute(delete(DocumentPage))
        await session.execute(delete(DocumentAnalysis))
        await session.execute(delete(VideoFrame))
        await session.execute(delete(VideoAnalysis))
        await session.execute(delete(ImageAnalysis))
        await session.execute(delete(MediaMetadata))
        await session.execute(delete(Embedding))
        await session.execute(delete(ProcessingJob))
        await session.execute(delete(Asset))
        await session.commit()
    yield
    # Clean up after test as well
    async with async_session_factory() as session:
        await session.execute(delete(SearchQuery))
        await session.execute(delete(DuplicateGroup))
        await session.execute(delete(AssetVersion))
        await session.execute(delete(Transcript))
        await session.execute(delete(DocumentPage))
        await session.execute(delete(DocumentAnalysis))
        await session.execute(delete(VideoFrame))
        await session.execute(delete(VideoAnalysis))
        await session.execute(delete(ImageAnalysis))
        await session.execute(delete(MediaMetadata))
        await session.execute(delete(Embedding))
        await session.execute(delete(ProcessingJob))
        await session.execute(delete(Asset))
        await session.commit()


@pytest.fixture
def mock_repos():
    """Create mock repositories."""
    return {
        "asset_repo": AsyncMock(spec=AssetRepository),
        "job_repo": AsyncMock(spec=ProcessingJobRepository),
        "embedding_repo": AsyncMock(spec=EmbeddingRepository),
        "media_meta_repo": AsyncMock(spec=MediaMetadataRepository),
        "image_analysis_repo": AsyncMock(spec=ImageAnalysisRepository),
        "video_analysis_repo": AsyncMock(spec=VideoAnalysisRepository),
        "document_analysis_repo": AsyncMock(spec=DocumentAnalysisRepository),
        "transcript_repo": AsyncMock(spec=TranscriptRepository),
        "dup_group_repo": AsyncMock(spec=DuplicateGroupRepository),
    }


@pytest.fixture
def mock_vector_store():
    return AsyncMock(spec=QdrantVectorStore)


@pytest.fixture
def mock_processors():
    """Create mock processor functions."""
    async def mock_image_processor(asset, job):
        pass

    async def mock_video_processor(asset, job):
        pass

    async def mock_document_processor(asset, job):
        pass

    return {
        "image": mock_image_processor,
        "video": mock_video_processor,
        "document": mock_document_processor,
    }


@pytest.fixture
def orchestrator(mock_repos, mock_vector_store, mock_processors):
    orch = IngestionOrchestrator(
        asset_repo=mock_repos["asset_repo"],
        job_repo=mock_repos["job_repo"],
        embedding_repo=mock_repos["embedding_repo"],
        media_meta_repo=mock_repos["media_meta_repo"],
        image_analysis_repo=mock_repos["image_analysis_repo"],
        video_analysis_repo=mock_repos["video_analysis_repo"],
        document_analysis_repo=mock_repos["document_analysis_repo"],
        transcript_repo=mock_repos["transcript_repo"],
        dup_group_repo=mock_repos["dup_group_repo"],
        vector_store=mock_vector_store,
    )
    orch.register_processors(
        image_processor=mock_processors["image"],
        video_processor=mock_processors["video"],
        document_processor=mock_processors["document"],
    )
    return orch


@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    # The orchestrator fixture registers processors, so check they're there
    assert "image" in orchestrator._processors
    assert "video" in orchestrator._processors
    assert "document" in orchestrator._processors
    assert orchestrator._semaphore is None
    assert orchestrator.stats.total_discovered == 0


@pytest.mark.asyncio
async def test_orchestrator_register_processors(orchestrator):
    assert "image" in orchestrator._processors
    assert "video" in orchestrator._processors
    assert "document" in orchestrator._processors


@pytest.mark.asyncio
async def test_orchestrator_handle_duplicate(orchestrator, mock_repos):
    from app.domain.indexing.scanner import DiscoveredFile

    file = DiscoveredFile(
        path=Path("/media/dup_test_unique.jpg"),
        relative_path="dup_test_unique.jpg",
        filename="dup_test_unique.jpg",
        extension="jpg",
        mime_type="image/jpeg",
        file_size=1000,
        modified_time=datetime.now(),
        sha256="abc123",
        modality="image",
    )
    existing_asset_id = uuid4()

    mock_repos["asset_repo"].create = AsyncMock()

    await orchestrator._handle_duplicate(file, existing_asset_id)

    # Should create a duplicate asset record
    mock_repos["asset_repo"].create.assert_called_once()
    call_args = mock_repos["asset_repo"].create.call_args[0][0]
    assert call_args.state == AssetState.DUPLICATE


@pytest.mark.asyncio
async def test_orchestrator_process_job_success(orchestrator, mock_repos):
    from app.domain.indexing.scanner import DiscoveredFile

    file = DiscoveredFile(
        path=Path("/media/test_success.jpg"),
        relative_path="test_success.jpg",
        filename="test_success.jpg",
        extension="jpg",
        mime_type="image/jpeg",
        file_size=1000,
        modified_time=datetime.now(),
        sha256="abc123",
        modality="image",
    )
    job = ProcessingJob(
        id=uuid4(), asset_id=uuid4(), state=AssetState.QUEUED, max_retries=3
    )

    # Mock processor that succeeds
    async def success_processor(asset, job):
        pass

    orchestrator._processors = {"image": success_processor}
    orchestrator._semaphore = asyncio.Semaphore(1)
    orchestrator._running = True

    # Use _process_jobs with a single job
    await orchestrator._process_jobs([(file, job)])

    # Check stats were updated
    assert orchestrator.stats.total_processed == 1
    assert orchestrator.stats.total_failed == 0

    # Verify update_state was called on repos
    assert mock_repos["job_repo"].update_state.called
    assert mock_repos["asset_repo"].update_state.called


@pytest.mark.asyncio
async def test_orchestrator_process_job_failure(orchestrator, mock_repos):
    from app.domain.indexing.scanner import DiscoveredFile

    file = DiscoveredFile(
        path=Path("/media/test_fail.jpg"),
        relative_path="test_fail.jpg",
        filename="test_fail.jpg",
        extension="jpg",
        mime_type="image/jpeg",
        file_size=1000,
        modified_time=datetime.now(),
        sha256="abc123",
        modality="image",
    )
    job = ProcessingJob(
        id=uuid4(), asset_id=uuid4(), state=AssetState.QUEUED, max_retries=3
    )

    # Mock processor that fails
    async def fail_processor(asset, job):
        raise ValueError("Processing failed")

    orchestrator._processors = {"image": fail_processor}
    orchestrator._semaphore = asyncio.Semaphore(1)
    orchestrator._running = True

    # Use _process_jobs with a single job
    await orchestrator._process_jobs([(file, job)])

    # Check stats were updated
    assert orchestrator.stats.total_failed == 1
    assert orchestrator.stats.total_processed == 0

    # Verify update_state was called on repos
    assert mock_repos["job_repo"].update_state.called
    assert mock_repos["asset_repo"].update_state.called


@pytest.mark.asyncio
async def test_orchestrator_stats_tracking(orchestrator):
    """Test that stats are properly initialized and updated."""
    assert orchestrator.stats.total_discovered == 0
    assert orchestrator.stats.total_new == 0
    assert orchestrator.stats.total_duplicates == 0
    assert orchestrator.stats.total_processed == 0
    assert orchestrator.stats.total_failed == 0
    assert orchestrator.stats.current_file is None
    assert orchestrator.stats.current_stage is None


# Scanner tests
@pytest.mark.asyncio
async def test_file_scanner_integration():
    """Integration test for file scanner with temp directory."""
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test files
        (tmpdir / "image.jpg").write_bytes(b"fake jpg")
        (tmpdir / "video.mp4").write_bytes(b"fake mp4")
        (tmpdir / "doc.pdf").write_bytes(b"fake pdf")
        (tmpdir / "text.txt").write_bytes(b"text file")

        # Create subdirectory
        subdir = tmpdir / "subfolder"
        subdir.mkdir()
        (subdir / "nested.png").write_bytes(b"fake png")

        scanner = FileScanner(tmpdir)
        results = scanner.scan()

        assert len(results) == 4  # jpg, mp4, pdf, png
        extensions = {r.extension for r in results}
        assert extensions == {"jpg", "mp4", "pdf", "png"}

        # Check modalities
        modalities = {r.modality for r in results}
        assert modalities == {"image", "video", "document"}


@pytest.mark.asyncio
async def test_duplicate_detector_integration(mock_repos):
    """Integration test for duplicate detection."""
    from app.domain.indexing.scanner import DiscoveredFile

    detector = DuplicateDetector(mock_repos["asset_repo"], mock_repos["dup_group_repo"])

    # Test new files
    mock_repos["asset_repo"].get_by_hash = AsyncMock(return_value=None)

    files = [
        DiscoveredFile(
            path=Path("/media/new1.jpg"),
            relative_path="new1.jpg",
            filename="new1.jpg",
            extension="jpg",
            mime_type="image/jpeg",
            file_size=1000,
            modified_time=datetime.now(),
            sha256="hash1",
            modality="image",
        ),
        DiscoveredFile(
            path=Path("/media/new2.jpg"),
            relative_path="new2.jpg",
            filename="new2.jpg",
            extension="jpg",
            mime_type="image/jpeg",
            file_size=2000,
            modified_time=datetime.now(),
            sha256="hash2",
            modality="image",
        ),
    ]

    result = await detector.process(files)

    assert len(result.new_files) == 2
    assert len(result.duplicates) == 0
    assert mock_repos["asset_repo"].get_by_hash.call_count == 2


@pytest.mark.asyncio
async def test_duplicate_detector_exact_duplicate(mock_repos):
    """Test exact duplicate detection."""
    from app.domain.indexing.scanner import DiscoveredFile

    detector = DuplicateDetector(mock_repos["asset_repo"], mock_repos["dup_group_repo"])

    existing_asset = Asset(
        id=uuid4(), sha256="hash1", modality=Modality.IMAGE, state=AssetState.COMPLETED
    )
    mock_repos["asset_repo"].get_by_hash = AsyncMock(return_value=existing_asset)
    mock_repos["asset_repo"].get_by_path = AsyncMock(return_value=None)
    mock_repos["dup_group_repo"].get_by_hash = AsyncMock(return_value=None)
    mock_repos["dup_group_repo"].create = AsyncMock()

    files = [
        DiscoveredFile(
            path=Path("/media/dup.jpg"),
            relative_path="dup.jpg",
            filename="dup.jpg",
            extension="jpg",
            mime_type="image/jpeg",
            file_size=1000,
            modified_time=datetime.now(),
            sha256="hash1",  # Same hash as existing
            modality="image",
        ),
    ]

    result = await detector.process(files)

    assert len(result.new_files) == 0
    assert len(result.duplicates) == 1
    assert result.duplicates[0][1] == existing_asset.id
    mock_repos["dup_group_repo"].create.assert_called_once()


@pytest.mark.asyncio
async def test_duplicate_detector_same_path_skip(mock_repos):
    """Test that same path with same asset is skipped."""
    from app.domain.indexing.scanner import DiscoveredFile

    detector = DuplicateDetector(mock_repos["asset_repo"], mock_repos["dup_group_repo"])

    existing_asset = Asset(
        id=uuid4(), sha256="hash1", modality=Modality.IMAGE, state=AssetState.COMPLETED
    )
    mock_repos["asset_repo"].get_by_hash = AsyncMock(return_value=existing_asset)
    mock_repos["asset_repo"].get_by_path = AsyncMock(return_value=existing_asset)

    files = [
        DiscoveredFile(
            path=Path("/media/existing.jpg"),
            relative_path="existing.jpg",
            filename="existing.jpg",
            extension="jpg",
            mime_type="image/jpeg",
            file_size=1000,
            modified_time=datetime.now(),
            sha256="hash1",
            modality="image",
        ),
    ]

    result = await detector.process(files)

    assert len(result.new_files) == 0
    assert len(result.duplicates) == 0  # Skipped as already indexed


# Video frame sampling tests
def test_frame_sampling_short_video():
    """Test frame sampling for short videos (< 60s)."""
    from app.processors.video.processor import VideoProcessor

    # Create a mock VideoProcessor with all required dependencies
    mock_asset_repo = AsyncMock()
    mock_job_repo = AsyncMock()
    mock_embedding_repo = AsyncMock()
    mock_media_meta_repo = AsyncMock()
    mock_image_analysis_repo = AsyncMock()
    mock_video_analysis_repo = AsyncMock()
    mock_document_analysis_repo = AsyncMock()
    mock_transcript_repo = AsyncMock()
    mock_vector_store = AsyncMock()

    processor = VideoProcessor(
        mock_asset_repo, mock_job_repo, mock_embedding_repo,
        mock_media_meta_repo, mock_image_analysis_repo,
        mock_video_analysis_repo, mock_document_analysis_repo,
        mock_transcript_repo, mock_vector_store
    )

    # Mock the settings
    import app.processors.video.processor as vp_module
    original_interval = vp_module.settings.video_sample_interval_seconds
    original_max = vp_module.settings.video_max_frames

    try:
        vp_module.settings.video_sample_interval_seconds = 2
        vp_module.settings.video_max_frames = 30

        frames, interval = processor._calculate_frame_plan(30.0)  # 30 second video
        # int(30/2) + 1 = 16 frames (at 0, 2, 4, ..., 30)
        assert frames == 16
        assert abs(interval - 1.875) < 0.01
    finally:
        vp_module.settings.video_sample_interval_seconds = original_interval
        vp_module.settings.video_max_frames = original_max


def test_frame_sampling_long_video():
    """Test frame sampling for long videos (> 300s)."""
    from app.processors.video.processor import VideoProcessor

    mock_asset_repo = AsyncMock()
    mock_job_repo = AsyncMock()
    mock_embedding_repo = AsyncMock()
    mock_media_meta_repo = AsyncMock()
    mock_image_analysis_repo = AsyncMock()
    mock_video_analysis_repo = AsyncMock()
    mock_document_analysis_repo = AsyncMock()
    mock_transcript_repo = AsyncMock()
    mock_vector_store = AsyncMock()

    processor = VideoProcessor(
        mock_asset_repo, mock_job_repo, mock_embedding_repo,
        mock_media_meta_repo, mock_image_analysis_repo,
        mock_video_analysis_repo, mock_document_analysis_repo,
        mock_transcript_repo, mock_vector_store
    )

    import app.processors.video.processor as vp_module
    original_interval = vp_module.settings.video_sample_interval_seconds
    original_max = vp_module.settings.video_max_frames

    try:
        vp_module.settings.video_sample_interval_seconds = 10
        vp_module.settings.video_max_frames = 64

        frames, interval = processor._calculate_frame_plan(3600.0)  # 1 hour video
        assert frames == 64  # capped at max
        assert abs(interval - 56.25) < 0.01
    finally:
        vp_module.settings.video_sample_interval_seconds = original_interval
        vp_module.settings.video_max_frames = original_max


# Search tests
@pytest.mark.asyncio
async def test_query_parser_modality_detection():
    from app.search.query_parser import QueryParser
    parser = QueryParser()

    # Test video detection
    intent = parser.parse("construction video footage")
    assert intent.modality_filter == Modality.VIDEO
    assert "construction" in intent.semantic_query

    # Test image detection
    intent = parser.parse("modern living room photo")
    assert intent.modality_filter == Modality.IMAGE
    assert "modern living room" in intent.semantic_query

    # Test document detection
    intent = parser.parse("residential project brochure pdf")
    assert intent.modality_filter == Modality.DOCUMENT
    assert "residential project" in intent.semantic_query

    # Test no modality
    intent = parser.parse("modern interior")
    assert intent.modality_filter is None
    assert intent.semantic_query == "modern interior"


@pytest.mark.asyncio
async def test_query_parser_explicit_filters():
    from app.search.query_parser import QueryParser
    parser = QueryParser()
    intent = parser.parse("test query", explicit_filters={"file_size": 1000})
    assert intent.filters == {"file_size": 1000}


@pytest.mark.asyncio
async def test_ranking_service_normalization():
    from app.search.ranking import RankingService
    from app.search.retrieval import RetrievalCandidate
    from app.db.models import Modality
    from uuid import uuid4

    class MockSessionFactory:
        def __call__(self):
            return AsyncMock()

    ranking = RankingService(MockSessionFactory())

    candidates = [
        RetrievalCandidate(asset_id=uuid4(), score=0.9, source="vector", modality=Modality.IMAGE, payload={}),
        RetrievalCandidate(asset_id=uuid4(), score=0.5, source="vector", modality=Modality.IMAGE, payload={}),
        RetrievalCandidate(asset_id=uuid4(), score=0.1, source="vector", modality=Modality.IMAGE, payload={}),
    ]

    normalized = RankingService._normalize_scores(None, candidates)

    scores = [c.score for c in normalized]
    assert max(scores) == 1.0
    assert min(scores) == 0.0
    assert scores[0] > scores[1] > scores[2]


@pytest.mark.asyncio
async def test_normalize_scores_same_value():
    from app.search.ranking import RankingService
    from app.search.retrieval import RetrievalCandidate
    from app.db.models import Modality
    from uuid import uuid4

    class MockSessionFactory:
        def __call__(self):
            return AsyncMock()

    ranking = RankingService(MockSessionFactory())

    candidates = [
        RetrievalCandidate(asset_id=uuid4(), score=0.5, source="vector", modality=Modality.IMAGE, payload={}),
        RetrievalCandidate(asset_id=uuid4(), score=0.5, source="vector", modality=Modality.IMAGE, payload={}),
    ]

    normalized = RankingService._normalize_scores(None, candidates)

    assert all(c.score == 1.0 for c in normalized)


@pytest.mark.asyncio
async def test_modality_score_with_filter():
    from app.search.ranking import RankingService
    from app.search.retrieval import RetrievalCandidate
    from app.db.models import Modality
    from uuid import uuid4

    class MockSessionFactory:
        def __call__(self):
            return AsyncMock()

    ranking = RankingService(MockSessionFactory())

    candidate = RetrievalCandidate(
        asset_id=uuid4(), score=0.8, source="vector", modality=Modality.VIDEO, payload={}
    )

    score = ranking._get_modality_score(candidate, Modality.VIDEO)
    assert score == 1.0

    score = ranking._get_modality_score(candidate, Modality.IMAGE)
    assert score == 0.5


@pytest.mark.asyncio
async def test_modality_score_no_filter():
    from app.search.ranking import RankingService
    from app.search.retrieval import RetrievalCandidate
    from app.db.models import Modality
    from uuid import uuid4

    class MockSessionFactory:
        def __call__(self):
            return AsyncMock()

    ranking = RankingService(MockSessionFactory())

    candidate = RetrievalCandidate(
        asset_id=uuid4(), score=0.8, source="vector", modality=Modality.VIDEO, payload={}
    )

    score = ranking._get_modality_score(candidate, None)
    assert score == 0.5


@pytest.mark.asyncio
async def test_deduplication_in_ranking():
    from app.search.ranking import RankingService
    from app.search.retrieval import RetrievalCandidate
    from app.db.models import Modality
    from uuid import uuid4

    class MockSessionFactory:
        def __call__(self):
            return AsyncMock()

    ranking = RankingService(MockSessionFactory())

    asset_id = uuid4()
    candidates = [
        RetrievalCandidate(asset_id=asset_id, score=0.9, source="vector", modality=Modality.IMAGE, payload={}),
        RetrievalCandidate(asset_id=asset_id, score=0.7, source="lexical", modality=Modality.IMAGE, payload={}),
    ]

    normalized = ranking._normalize_scores(candidates)
    assert len(normalized) == 2


@pytest.mark.asyncio
async def test_explanation_generation():
    from app.search.ranking import RankingService
    from app.search.retrieval import RetrievalCandidate
    from app.db.models import Modality
    from uuid import uuid4

    class MockSessionFactory:
        def __call__(self):
            return AsyncMock()

    ranking = RankingService(MockSessionFactory())

    candidate = RetrievalCandidate(
        asset_id=uuid4(),
        score=0.9,
        source="vector",
        modality=Modality.IMAGE,
        payload={"description": "A modern living room with sofa", "timestamp": 120.5},
    )

    explanation = ranking._generate_explanation(
        candidate, semantic=0.9, lexical=0.0, modality=0.5, metadata=0.5
    )

    assert "semantic similarity" in explanation.lower()
    assert "modern living room" in explanation.lower()
    assert "matched at" in explanation.lower()


@pytest.mark.asyncio
async def test_ranking_multiple_sources():
    from app.search.ranking import RankingService
    from app.search.retrieval import RetrievalCandidate
    from app.db.models import Modality
    from uuid import uuid4

    class MockSessionFactory:
        def __call__(self):
            return AsyncMock()

    ranking = RankingService(MockSessionFactory())

    candidates = [
        RetrievalCandidate(asset_id=uuid4(), score=0.9, source="vector", modality=Modality.IMAGE, payload={}),
        RetrievalCandidate(asset_id=uuid4(), score=0.8, source="lexical", modality=Modality.IMAGE, payload={}),
    ]

    # Mock asset repo to return assets
    async def mock_session_factory():
        return AsyncMock()

    ranking = RankingService(mock_session_factory)

    ranked = await ranking.rank(candidates, "test query", None, 10)

    assert len(ranked) == 2
    assert all(isinstance(r, RetrievalCandidate) for r in ranked)
    assert ranked[0].final_score >= ranked[1].final_score