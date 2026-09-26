from typing import List, Optional, Dict, Any
from uuid import UUID
from dataclasses import dataclass

from app.db.models import Modality
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore, SearchResult
from app.ai.factory import AIProviderFactory
from app.search.query_parser import QueryIntent
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalCandidate:
    asset_id: UUID
    score: float
    source: str  # "vector", "lexical", "metadata"
    modality: Modality
    payload: Dict[str, Any]


class RetrievalService:
    def __init__(self, vector_store: QdrantVectorStore, session_factory):
        self.vector_store = vector_store
        self.session_factory = session_factory
        self.embedding_provider = AIProviderFactory.get_embedding_provider()

    async def retrieve(
        self,
        intent: QueryIntent,
        limit: int = None,
    ) -> List[RetrievalCandidate]:
        limit = limit or settings.search_default_limit
        overfetch_limit = limit * 3

        # Generate query embedding
        query_embedding = await self.embedding_provider.embed_single_text(intent.semantic_query)

        # Determine collections to search
        collections = self._get_collections(intent.modality_filter)

        # Parallel retrieval
        vector_candidates = await self._vector_search(
            collections, query_embedding, intent, overfetch_limit
        )
        lexical_candidates = await self._lexical_search(intent, overfetch_limit)

        # Combine candidates
        all_candidates = vector_candidates + lexical_candidates

        # Deduplicate by asset_id
        deduped = self._deduplicate(all_candidates)

        return deduped[:overfetch_limit]

    def _get_collections(self, modality_filter: Optional[Modality]) -> List[str]:
        if modality_filter == Modality.IMAGE:
            return ["assets_image"]
        elif modality_filter == Modality.VIDEO:
            return ["assets_video"]
        elif modality_filter == Modality.DOCUMENT:
            return ["assets_document"]
        return ["assets_image", "assets_video", "assets_document"]

    async def _vector_search(
        self,
        collections: List[str],
        query_embedding: List[float],
        intent: QueryIntent,
        limit: int,
    ) -> List[RetrievalCandidate]:
        candidates = []

        for collection in collections:
            # Build filter
            filter_dict = {"modality": collection.replace("assets_", "")}
            if intent.filters:
                filter_dict.update(intent.filters)

            try:
                results = await self.vector_store.search(
                    collection=collection,
                    vector=query_embedding,
                    limit=limit,
                    filter_dict=filter_dict,
                )

                for result in results:
                    asset_id = UUID(result.payload.get("asset_id"))
                    candidates.append(
                        RetrievalCandidate(
                            asset_id=asset_id,
                            score=result.score,
                            source="vector",
                            modality=Modality(collection.replace("assets_", "")),
                            payload=result.payload,
                        )
                    )
            except Exception as e:
                logger.warning("Vector search failed", collection=collection, error=str(e))

        return candidates

    async def _lexical_search(
        self,
        intent: QueryIntent,
        limit: int,
    ) -> List[RetrievalCandidate]:
        # PostgreSQL full-text search
        from sqlalchemy import select, func, text
        from app.db.models import (
            Asset,
            ImageAnalysis,
            VideoAnalysis,
            DocumentAnalysis,
            DocumentPage,
            Transcript,
        )

        candidates = []

        async with self.session_factory() as session:
            # Build search query using tsvector
            query = intent.semantic_query
            tsquery = func.plainto_tsquery("english", query)

            # Search across modalities
            if intent.modality_filter in (None, Modality.IMAGE):
                stmt = (
                    select(
                        Asset.id,
                        func.ts_rank_cd(
                            func.to_tsvector(
                                func.coalesce(ImageAnalysis.description, "")
                                + " "
                                + func.coalesce(ImageAnalysis.ocr_text, ""),
                            ),
                            tsquery,
                        ).label("rank"),
                    )
                    .join(ImageAnalysis, Asset.id == ImageAnalysis.asset_id)
                    .where(
                        Asset.modality == Modality.IMAGE,
                        func.coalesce(ImageAnalysis.description, "")
                        + " "
                        + func.coalesce(ImageAnalysis.ocr_text, "")
                        != "",
                    )
                    .order_by(text("rank DESC"))
                    .limit(limit)
                )

                result = await session.execute(stmt)
                for row in result:
                    candidates.append(
                        RetrievalCandidate(
                            asset_id=row.id,
                            score=float(row.rank),
                            source="lexical",
                            modality=Modality.IMAGE,
                            payload={},
                        )
                    )

            if intent.modality_filter in (None, Modality.VIDEO):
                stmt = (
                    select(
                        Asset.id,
                        func.ts_rank_cd(
                            func.to_tsvector(
                                func.coalesce(VideoAnalysis.summary, "")
                                + " "
                                + func.coalesce(Transcript.full_text, ""),
                            ),
                            tsquery,
                        ).label("rank"),
                    )
                    .join(VideoAnalysis, Asset.id == VideoAnalysis.asset_id)
                    .outerjoin(Transcript, Asset.id == Transcript.asset_id)
                    .where(
                        Asset.modality == Modality.VIDEO,
                    )
                    .order_by(text("rank DESC"))
                    .limit(limit)
                )

                result = await session.execute(stmt)
                for row in result:
                    candidates.append(
                        RetrievalCandidate(
                            asset_id=row.id,
                            score=float(row.rank),
                            source="lexical",
                            modality=Modality.VIDEO,
                            payload={},
                        )
                    )

            if intent.modality_filter in (None, Modality.DOCUMENT):
                stmt = (
                    select(
                        Asset.id,
                        func.ts_rank_cd(
                            func.to_tsvector(
                                func.coalesce(DocumentAnalysis.summary, "")
                                + " "
                                + func.coalesce(DocumentPage.text, ""),
                            ),
                            tsquery,
                        ).label("rank"),
                    )
                    .join(DocumentAnalysis, Asset.id == DocumentAnalysis.asset_id)
                    .outerjoin(DocumentPage, Asset.id == DocumentPage.asset_id)
                    .where(
                        Asset.modality == Modality.DOCUMENT,
                    )
                    .order_by(text("rank DESC"))
                    .limit(limit)
                )

                result = await session.execute(stmt)
                for row in result:
                    candidates.append(
                        RetrievalCandidate(
                            asset_id=row.id,
                            score=float(row.rank),
                            source="lexical",
                            modality=Modality.DOCUMENT,
                            payload={},
                        )
                    )

        return candidates

    def _deduplicate(self, candidates: List[RetrievalCandidate]) -> List[RetrievalCandidate]:
        seen = {}
        for candidate in candidates:
            key = candidate.asset_id
            if key not in seen or candidate.score > seen[key].score:
                seen[key] = candidate
        return list(seen.values())
