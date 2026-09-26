from typing import List, Optional, Dict, Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams,
    PayloadSchemaType,
)
from app.ai.embeddings.vector_store import VectorStore, VectorPoint, SearchResult
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class QdrantVectorStore(VectorStore):
    def __init__(
        self,
        url: str = None,
        api_key: str = None,
        collection_prefix: str = None,
    ):
        self._url = url or settings.qdrant_url
        self._api_key = api_key or settings.qdrant_api_key
        self._collection_prefix = collection_prefix or settings.qdrant_collection_prefix
        self._client: Optional[AsyncQdrantClient] = None
        self._collections_initialized: Dict[str, bool] = {}

    async def _get_client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(url=self._url, api_key=self._api_key)
        return self._client

    def _collection_name(self, collection: str) -> str:
        return f"{self._collection_prefix}{collection}"

    async def initialize(self) -> None:
        client = await self._get_client()
        # Test connection
        await client.get_collections()
        logger.info("Qdrant connection established")

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def _ensure_collection(
        self, collection: str, vector_size: int, distance: str = "Cosine"
    ) -> None:
        full_name = self._collection_name(collection)
        if full_name in self._collections_initialized:
            return

        client = await self._get_client()
        exists = await client.collection_exists(full_name)

        if not exists:
            distance_enum = Distance.COSINE if distance.lower() == "cosine" else Distance.DOT
            await client.create_collection(
                collection_name=full_name,
                vectors_config=VectorParams(size=vector_size, distance=distance_enum),
            )
            # Create payload indexes for common filter fields
            for field in ["asset_id", "modality", "content_type"]:
                await client.create_payload_index(
                    collection_name=full_name,
                    field_name=field,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            logger.info("Created Qdrant collection", collection=full_name, vector_size=vector_size)

        self._collections_initialized[full_name] = True

    async def upsert(self, collection: str, points: List[VectorPoint]) -> None:
        if not points:
            return

        client = await self._get_client()
        full_name = self._collection_name(collection)
        vector_size = len(points[0].vector)

        await self._ensure_collection(collection, vector_size)

        point_structs = [
            PointStruct(
                id=point.id,
                vector=point.vector,
                payload=point.payload,
            )
            for point in points
        ]

        await client.upsert(collection_name=full_name, points=point_structs)
        logger.debug("Upserted points to Qdrant", collection=full_name, count=len(points))

    async def delete(self, collection: str, ids: List[str]) -> None:
        if not ids:
            return

        client = await self._get_client()
        full_name = self._collection_name(collection)

        await client.delete(collection_name=full_name, points_selector=ids)
        logger.debug("Deleted points from Qdrant", collection=full_name, count=len(ids))

    async def delete_by_filter(self, collection: str, filter_dict: Dict[str, Any]) -> None:
        client = await self._get_client()
        full_name = self._collection_name(collection)

        qdrant_filter = self._build_filter(filter_dict)
        await client.delete(collection_name=full_name, points_selector=qdrant_filter)
        logger.debug(
            "Deleted points by filter from Qdrant", collection=full_name, filter=filter_dict
        )

    def _build_filter(self, filter_dict: Dict[str, Any]) -> Filter:
        conditions = []
        for key, value in filter_dict.items():
            if isinstance(value, list):
                # Multiple values = OR
                for v in value:
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=v)))
            else:
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

        return Filter(must=conditions) if conditions else None

    async def search(
        self,
        collection: str,
        vector: List[float],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> List[SearchResult]:
        client = await self._get_client()
        full_name = self._collection_name(collection)

        qdrant_filter = self._build_filter(filter_dict) if filter_dict else None

        if hasattr(client, "search"):
            results = await client.search(
                collection_name=full_name,
                query_vector=vector,
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=with_payload,
                with_vectors=with_vectors,
                search_params=SearchParams(hnsw_ef=128, exact=False),
            )
        else:
            response = await client.query_points(
                collection_name=full_name,
                query=vector,
                query_filter=qdrant_filter,
                limit=limit,
                with_payload=with_payload,
                with_vectors=with_vectors,
            )
            results = response.points

        return [
            SearchResult(
                id=str(r.id),
                score=r.score,
                payload=r.payload or {},
            )
            for r in results
        ]

    async def search_batch(
        self,
        collection: str,
        vectors: List[List[float]],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[List[SearchResult]]:
        client = await self._get_client()
        full_name = self._collection_name(collection)

        qdrant_filter = self._build_filter(filter_dict) if filter_dict else None

        # Qdrant doesn't have native batch search, so we parallelize
        import asyncio

        async def search_one(vector: List[float]) -> List[SearchResult]:
            if hasattr(client, "search"):
                results = await client.search(
                    collection_name=full_name,
                    query_vector=vector,
                    query_filter=qdrant_filter,
                    limit=limit,
                    with_payload=True,
                    search_params=SearchParams(hnsw_ef=128, exact=False),
                )
            else:
                response = await client.query_points(
                    collection_name=full_name,
                    query=vector,
                    query_filter=qdrant_filter,
                    limit=limit,
                    with_payload=True,
                )
                results = response.points
            return [
                SearchResult(id=str(r.id), score=r.score, payload=r.payload or {}) for r in results
            ]

        tasks = [search_one(v) for v in vectors]
        return await asyncio.gather(*tasks)

    async def count(self, collection: str, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        client = await self._get_client()
        full_name = self._collection_name(collection)

        qdrant_filter = self._build_filter(filter_dict) if filter_dict else None
        result = await client.count(
            collection_name=full_name, count_filter=qdrant_filter, exact=True
        )
        return result.count

    async def collection_exists(self, collection: str) -> bool:
        client = await self._get_client()
        full_name = self._collection_name(collection)
        return await client.collection_exists(full_name)

    async def create_collection(
        self, collection: str, vector_size: int, distance: str = "Cosine"
    ) -> None:
        await self._ensure_collection(collection, vector_size, distance)
