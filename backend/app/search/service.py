from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass

from app.db.models import Modality, Asset, AssetState
from app.search.query_parser import QueryParser, QueryIntent
from app.search.retrieval import RetrievalService
from app.search.ranking import RankingService, RankedResult
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    asset_id: UUID
    score: float
    modality: Modality
    filename: str
    relative_path: str
    explanation: str
    metadata: dict
    matched_details: dict


@dataclass
class SearchResponse:
    results: List[SearchResult]
    total: int
    query: str
    latency_ms: int


class SearchService:
    def __init__(
        self,
        vector_store: QdrantVectorStore,
        session_factory,
        asset_repo,
    ):
        self.vector_store = vector_store
        self.session_factory = session_factory
        self.asset_repo = asset_repo
        self.query_parser = QueryParser()
        self.retrieval = RetrievalService(vector_store, session_factory)
        self.ranking = RankingService(session_factory)

    async def search(
        self,
        query: str,
        modality_filter: Optional[Modality] = None,
        filters: dict = None,
        limit: int = None,
        offset: int = 0,
    ) -> SearchResponse:
        import time

        start_time = time.time()

        # Parse query intent
        intent = self.query_parser.parse(query, filters)
        if modality_filter:
            intent.modality_filter = modality_filter

        # Retrieve candidates
        candidates = await self.retrieval.retrieve(intent, limit or settings.search_default_limit)

        # Rank results
        ranked = await self.ranking.rank(
            candidates,
            intent.semantic_query,
            intent.modality_filter,
            limit or settings.search_default_limit,
        )

        # Enrich with asset details
        results = await self._enrich_results(ranked)

        # Apply offset
        results = results[offset : offset + (limit or settings.search_default_limit)]

        latency_ms = int((time.time() - start_time) * 1000)

        # Log query
        await self._log_query(query, intent, results, latency_ms)

        return SearchResponse(
            results=results,
            total=len(ranked),
            query=query,
            latency_ms=latency_ms,
        )

    async def _enrich_results(self, ranked: List[RankedResult]) -> List[SearchResult]:
        if not ranked:
            return []

        asset_ids = [r.asset_id for r in ranked]
        assets = {}

        async with self.session_factory() as session:
            from sqlalchemy import select

            stmt = select(Asset).where(Asset.id.in_(asset_ids))
            result = await session.execute(stmt)
            for asset in result.scalars():
                assets[asset.id] = asset

        results = []
        for ranked_result in ranked:
            asset = assets.get(ranked_result.asset_id)
            if not asset or asset.state != AssetState.COMPLETED:
                continue

            matched_details = {}
            if ranked_result.payload.get("timestamp"):
                matched_details["timestamp"] = ranked_result.payload["timestamp"]
            if ranked_result.payload.get("page_number"):
                matched_details["page_number"] = ranked_result.payload["page_number"]
            if ranked_result.payload.get("description"):
                matched_details["description"] = ranked_result.payload["description"]

            results.append(
                SearchResult(
                    asset_id=asset.id,
                    score=ranked_result.final_score,
                    modality=asset.modality,
                    filename=asset.filename,
                    relative_path=asset.relative_path,
                    explanation=ranked_result.explanation,
                    metadata={
                        "file_size": asset.file_size,
                        "modified_time": asset.modified_time.isoformat()
                        if asset.modified_time
                        else None,
                        "extension": asset.extension,
                    },
                    matched_details=matched_details,
                )
            )

        return results

    async def _log_query(
        self,
        query: str,
        intent: QueryIntent,
        results: List[SearchResult],
        latency_ms: int,
    ) -> None:
        from app.db.repositories import SearchQueryRepository
        from app.db.models import SearchQuery

        async with self.session_factory() as session:
            repo = SearchQueryRepository(session)
            await repo.log_query(
                SearchQuery(
                    query_text=query,
                    modality_filter=intent.modality_filter,
                    filters=intent.filters,
                    result_count=len(results),
                    latency_ms=latency_ms,
                    result_ids=[str(r.asset_id) for r in results],
                )
            )
            await session.commit()
