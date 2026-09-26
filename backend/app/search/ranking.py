from typing import List, Dict, Any, Optional
from uuid import UUID
from dataclasses import dataclass

from app.db.models import Modality, Asset
from app.search.retrieval import RetrievalCandidate
from app.ai.factory import AIProviderFactory
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RankedResult:
    asset_id: UUID
    final_score: float
    semantic_score: float
    lexical_score: float
    modality_score: float
    metadata_score: float
    modality: Modality
    explanation: str
    payload: Dict[str, Any]


class RankingService:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.reranker = AIProviderFactory.get_reranker()

    async def rank(
        self,
        candidates: List[RetrievalCandidate],
        intent_semantic_query: str,
        intent_modality_filter: Optional[Modality] = None,
        limit: int = None,
    ) -> List[RankedResult]:
        limit = limit or settings.search_default_limit

        # Normalize scores
        normalized = self._normalize_scores(candidates)

        # Calculate component scores
        ranked = []
        for candidate in normalized:
            semantic_score = self._get_semantic_score(candidate)
            lexical_score = self._get_lexical_score(candidate)
            modality_score = self._get_modality_score(candidate, intent_modality_filter)
            metadata_score = await self._get_metadata_score(candidate)

            final_score = (
                semantic_score * settings.semantic_weight
                + lexical_score * settings.lexical_weight
                + modality_score * settings.modality_weight
                + metadata_score * settings.metadata_weight
            )

            explanation = self._generate_explanation(
                candidate, semantic_score, lexical_score, modality_score, metadata_score
            )

            ranked.append(
                RankedResult(
                    asset_id=candidate.asset_id,
                    final_score=final_score,
                    semantic_score=semantic_score,
                    lexical_score=lexical_score,
                    modality_score=modality_score,
                    metadata_score=metadata_score,
                    modality=candidate.modality,
                    explanation=explanation,
                    payload=candidate.payload,
                )
            )

        # Sort by final score
        ranked.sort(key=lambda r: r.final_score, reverse=True)

        # Optional reranking
        if self.reranker and len(ranked) > 1:
            ranked = await self._rerank(ranked, intent_semantic_query)

        return ranked[:limit]

    def _normalize_scores(self, candidates: List[RetrievalCandidate]) -> List[RetrievalCandidate]:
        if not candidates:
            return candidates

        # Group by source
        by_source = {}
        for c in candidates:
            by_source.setdefault(c.source, []).append(c)

        # Min-max normalize within each source
        for source, group in by_source.items():
            scores = [c.score for c in group]
            min_s, max_s = min(scores), max(scores)
            if max_s > min_s:
                for c in group:
                    c.score = (c.score - min_s) / (max_s - min_s)
            else:
                for c in group:
                    c.score = 1.0

        return candidates

    def _get_semantic_score(self, candidate: RetrievalCandidate) -> float:
        if candidate.source == "vector":
            return candidate.score
        return 0.0

    def _get_lexical_score(self, candidate: RetrievalCandidate) -> float:
        if candidate.source == "lexical":
            return candidate.score
        return 0.0

    def _get_modality_score(
        self, candidate: RetrievalCandidate, intent_filter: Optional[Modality]
    ) -> float:
        if intent_filter and candidate.modality == intent_filter:
            return 1.0
        return 0.5  # Neutral if no filter or mismatch

    async def _get_metadata_score(self, candidate: RetrievalCandidate) -> float:
        # Could add recency, file size, etc. For now return neutral
        return 0.5

    def _generate_explanation(
        self,
        candidate: RetrievalCandidate,
        semantic: float,
        lexical: float,
        modality: float,
        metadata: float,
    ) -> str:
        parts = []
        if semantic > 0.5:
            parts.append(f"Strong semantic similarity ({semantic:.2f})")
        if lexical > 0.5:
            parts.append(f"Lexical match ({lexical:.2f})")
        if modality > 0.5:
            parts.append(f"Matches modality filter: {candidate.modality.value}")

        # Add payload-specific details
        payload = candidate.payload
        if payload.get("timestamp"):
            parts.append(f"Matched at {payload['timestamp']:.1f}s")
        if payload.get("page_number"):
            parts.append(f"Matched on page {payload['page_number']}")
        if payload.get("description"):
            parts.append(f"Visual: {payload['description'][:100]}")

        return "; ".join(parts) if parts else "Matched via combined signals"

    async def _rerank(
        self,
        results: List[RankedResult],
        query: str,
    ) -> List[RankedResult]:
        # Prepare texts for reranker
        texts = []
        for r in results:
            text_parts = []
            if r.payload.get("description"):
                text_parts.append(r.payload["description"])
            if r.payload.get("text"):
                text_parts.append(r.payload["text"][:500])
            if r.payload.get("ocr_text"):
                text_parts.append(r.payload["ocr_text"][:500])
            texts.append(" ".join(text_parts) if text_parts else f"Asset {r.asset_id}")

        try:
            rerank_scores = await self.reranker.rerank(query, texts)
            for i, result in enumerate(results):
                result.final_score = rerank_scores[i]
                result.explanation += f" [reranked: {rerank_scores[i]:.3f}]"

            results.sort(key=lambda r: r.final_score, reverse=True)
        except Exception as e:
            logger.warning("Reranking failed", error=str(e))

        return results
