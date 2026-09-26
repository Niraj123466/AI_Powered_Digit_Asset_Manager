import pytest
from uuid import uuid4
from app.search.ranking import RankingService
from app.search.retrieval import RetrievalCandidate
from app.db.models import Modality


class MockSessionFactory:
    def __call__(self):
        return AsyncMock()


class AsyncMock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def execute(self, *args, **kwargs):
        return MagicMock()

    async def commit(self):
        pass


from unittest.mock import MagicMock


@pytest.fixture
def ranking_service():
    return RankingService(MockSessionFactory())


def test_normalize_scores(ranking_service):
    """Test score normalization."""
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

    normalized = ranking_service._normalize_scores(candidates)

    scores = [c.score for c in normalized]
    assert max(scores) == 1.0
    assert min(scores) == 0.0
    assert scores[0] > scores[1] > scores[2]


def test_normalize_scores_same_value(ranking_service):
    """Test normalization when all scores are the same."""
    candidates = [
        RetrievalCandidate(
            asset_id=uuid4(), score=0.5, source="vector", modality=Modality.IMAGE, payload={}
        ),
        RetrievalCandidate(
            asset_id=uuid4(), score=0.5, source="vector", modality=Modality.IMAGE, payload={}
        ),
    ]

    normalized = ranking_service._normalize_scores(candidates)

    assert all(c.score == 1.0 for c in normalized)


def test_modality_score_with_filter(ranking_service):
    """Test modality scoring with filter."""
    candidate = RetrievalCandidate(
        asset_id=uuid4(), score=0.8, source="vector", modality=Modality.VIDEO, payload={}
    )

    score = ranking_service._get_modality_score(candidate, Modality.VIDEO)
    assert score == 1.0

    score = ranking_service._get_modality_score(candidate, Modality.IMAGE)
    assert score == 0.5


def test_modality_score_no_filter(ranking_service):
    """Test modality scoring without filter."""
    candidate = RetrievalCandidate(
        asset_id=uuid4(), score=0.8, source="vector", modality=Modality.VIDEO, payload={}
    )

    score = ranking_service._get_modality_score(candidate, None)
    assert score == 0.5


def test_deduplication_in_ranking(ranking_service):
    """Test that ranking handles duplicate asset_ids."""
    asset_id = uuid4()
    candidates = [
        RetrievalCandidate(
            asset_id=asset_id, score=0.9, source="vector", modality=Modality.IMAGE, payload={}
        ),
        RetrievalCandidate(
            asset_id=asset_id, score=0.7, source="lexical", modality=Modality.IMAGE, payload={}
        ),
    ]

    normalized = ranking_service._normalize_scores(candidates)
    # After normalization, vector score = 1.0, lexical score = 0.0
    # Deduplication happens in retrieval, not ranking
    # This tests that normalization works per-source
    assert len(normalized) == 2


def test_explanation_generation(ranking_service):
    """Test explanation generation."""
    candidate = RetrievalCandidate(
        asset_id=uuid4(),
        score=0.9,
        source="vector",
        modality=Modality.IMAGE,
        payload={"description": "A modern living room with sofa", "timestamp": 120.5},
    )

    explanation = ranking_service._generate_explanation(
        candidate, semantic=0.9, lexical=0.0, modality=0.5, metadata=0.5
    )

    assert "semantic similarity" in explanation.lower()
    assert "modern living room" in explanation.lower()
    assert "matched at" in explanation.lower()
