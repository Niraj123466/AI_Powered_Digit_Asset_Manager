import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.search.service import SearchService
from app.search.query_parser import QueryParser, QueryIntent
from app.search.retrieval import RetrievalService, RetrievalCandidate
from app.search.ranking import RankingService, RankedResult
from app.db.models import Modality, Asset, AssetState
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore, SearchResult
import pytest_asyncio


class MockEmbeddingProvider:
    def __init__(self):
        self.model_name = "test-model"
        self.dimensions = 512
        self.model_version = "1.0"

    async def embed_single_text(self, text: str):
        return [0.1] * 512

    async def embed_text(self, texts: list[str]):
        return [[0.1] * 512 for _ in texts]


class MockVectorStore:
    def __init__(self):
        self.collections = {}

    async def initialize(self):
        pass

    async def close(self):
        pass

    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
        filter_dict: dict = None,
        with_payload: bool = True,
        with_vectors: bool = False,
    ):
        # Return mock results
        return [
            SearchResult(
                id=str(uuid4()),
                score=0.9,
                payload={
                    "asset_id": str(uuid4()),
                    "modality": "image",
                    "description": "test image",
                    "path": "/test/image.jpg",
                },
            ),
            SearchResult(
                id=str(uuid4()),
                score=0.8,
                payload={
                    "asset_id": str(uuid4()),
                    "modality": "image",
                    "description": "another image",
                    "path": "/test/image2.jpg",
                },
            ),
        ]

    async def search_batch(
        self, collection: str, vectors: list[list[float]], limit: int = 10, filter_dict: dict = None
    ):
        return [await self.search(collection, v, limit, filter_dict) for v in vectors]


class MockSessionFactory:
    def __init__(self):
        self.assets = {}

    def __call__(self):
        return AsyncMockSession(self.assets)


class AsyncMockSession:
    def __init__(self, assets):
        self.assets = assets

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def execute(self, stmt):
        result = MagicMock()
        # Check if selecting Asset
        if "asset" in str(stmt).lower():
            result.scalars.return_value.all.return_value = list(self.assets.values())
            result.scalars.return_value.first.return_value = (
                list(self.assets.values())[0] if self.assets else None
            )
        return result

    async def commit(self):
        pass

    async def flush(self):
        pass

    def add(self, obj):
        pass


@pytest.fixture
def mock_vector_store():
    return MockVectorStore()


@pytest.fixture
def mock_session_factory():
    return MockSessionFactory()


@pytest.fixture
def mock_asset_repo():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.list_assets = AsyncMock(return_value=[])
    repo.count_assets = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def search_service(mock_vector_store, mock_session_factory, mock_asset_repo):
    return SearchService(mock_vector_store, mock_session_factory, mock_asset_repo)


@pytest.mark.asyncio
async def test_query_parser_modality_detection():
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
    parser = QueryParser()
    intent = parser.parse("test query", explicit_filters={"file_size": 1000})
    assert intent.filters == {"file_size": 1000}


@pytest.mark.asyncio
async def test_retrieval_service_vector_search(mock_vector_store, mock_session_factory):
    retrieval = RetrievalService(mock_vector_store, mock_session_factory)

    intent = QueryIntent(
        original_query="test", semantic_query="test", modality_filter=None, filters={}
    )

    candidates = await retrieval.retrieve(intent, limit=10)
    assert len(candidates) > 0
    assert all(isinstance(c, RetrievalCandidate) for c in candidates)


@pytest.mark.asyncio
async def test_ranking_service_normalization():
    ranking = RankingService(MockSessionFactory())

    candidates = [
        RetrievalCandidate(
            asset_id=uuid4(), score=0.9, source="vector", modality=Modality.IMAGE, payload={}
        ),
        RetrievalCandidate(
            asset_id=uuid4(), score=0.5, source="vector", modality=Modality.IMAGE, payload={}
        ),
        RetrievalCandidate(
            asset_id=uuid4(), score=0.1, source="vector", modality=Modality.IMAGE, payload={}
        ),
    ]

    normalized = ranking._normalize_scores(candidates)
    scores = [c.score for c in normalized]
    assert max(scores) == 1.0
    assert min(scores) == 0.0


@pytest.mark.asyncio
async def test_ranking_service_modality_boost():
    ranking = RankingService(MockSessionFactory())

    candidate = RetrievalCandidate(
        asset_id=uuid4(), score=0.8, source="vector", modality=Modality.VIDEO, payload={}
    )

    score = ranking._get_modality_score(candidate, Modality.VIDEO)
    assert score == 1.0

    score = ranking._get_modality_score(candidate, Modality.IMAGE)
    assert score == 0.5


@pytest.mark.asyncio
async def test_search_service_integration(search_service):
    # Mock the retrieval and ranking
    search_service.retrieval.retrieve = AsyncMock(
        return_value=[
            RetrievalCandidate(
                asset_id=uuid4(),
                score=0.9,
                source="vector",
                modality=Modality.IMAGE,
                payload={"description": "test image", "path": "/test.jpg"},
            )
        ]
    )
    search_service.ranking.rank = AsyncMock(
        return_value=[
            RankedResult(
                asset_id=uuid4(),
                final_score=0.9,
                semantic_score=0.9,
                lexical_score=0.0,
                modality_score=0.5,
                metadata_score=0.5,
                modality=Modality.IMAGE,
                explanation="Test explanation",
                payload={"description": "test image"},
            )
        ]
    )
    search_service.asset_repo.get_by_id = AsyncMock(
        return_value=Asset(
            id=uuid4(),
            filename="test.jpg",
            relative_path="test.jpg",
            extension="jpg",
            mime_type="image/jpeg",
            file_size=1000,
            modality=Modality.IMAGE,
            state=AssetState.COMPLETED,
        )
    )

    response = await search_service.search(query="test query", limit=10)

    assert response.results is not None
    assert response.latency_ms >= 0


# Integration-style tests for the pipeline
@pytest.mark.asyncio
async def test_full_search_pipeline():
    """Test the complete search pipeline from query to results."""
    # This would be an integration test with real services
    # For now, we test the components individually
    pass


# Test deduplication
@pytest.mark.asyncio
async def test_candidate_deduplication():
    ranking = RankingService(MockSessionFactory())

    asset_id = uuid4()
    candidates = [
        RetrievalCandidate(
            asset_id=asset_id, score=0.9, source="vector", modality=Modality.IMAGE, payload={}
        ),
        RetrievalCandidate(
            asset_id=asset_id, score=0.7, source="lexical", modality=Modality.IMAGE, payload={}
        ),
    ]

    # Deduplication happens in retrieval, not ranking
    # This tests that normalization works per-source
    normalized = ranking._normalize_scores(candidates)
    assert len(normalized) == 2


# Test explanation generation
@pytest.mark.asyncio
async def test_explanation_generation():
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


# Test ranking with multiple sources
@pytest.mark.asyncio
async def test_ranking_multiple_sources():
    ranking = RankingService(MockSessionFactory())

    candidates = [
        RetrievalCandidate(
            asset_id=uuid4(), score=0.9, source="vector", modality=Modality.IMAGE, payload={}
        ),
        RetrievalCandidate(
            asset_id=uuid4(), score=0.8, source="lexical", modality=Modality.IMAGE, payload={}
        ),
    ]

    # Mock asset repo to return assets
    async def mock_session_factory():
        return AsyncMockSession({})

    ranking = RankingService(mock_session_factory)

    ranked = await ranking.rank(candidates, "test query", None, 10)

    assert len(ranked) == 2
    assert all(isinstance(r, RankedResult) for r in ranked)
    assert ranked[0].final_score >= ranked[1].final_score
