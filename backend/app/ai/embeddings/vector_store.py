from typing import Protocol, List, Optional, Dict, Any
from dataclasses import dataclass
from uuid import UUID


@dataclass
class VectorPoint:
    id: str
    vector: List[float]
    payload: Dict[str, Any]


@dataclass
class SearchResult:
    id: str
    score: float
    payload: Dict[str, Any]


class VectorStore(Protocol):
    async def initialize(self) -> None: ...
    async def close(self) -> None: ...

    async def upsert(self, collection: str, points: List[VectorPoint]) -> None: ...
    async def delete(self, collection: str, ids: List[str]) -> None: ...
    async def delete_by_filter(self, collection: str, filter_dict: Dict[str, Any]) -> None: ...

    async def search(
        self,
        collection: str,
        vector: List[float],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> List[SearchResult]: ...

    async def search_batch(
        self,
        collection: str,
        vectors: List[List[float]],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[List[SearchResult]]: ...

    async def count(self, collection: str, filter_dict: Optional[Dict[str, Any]] = None) -> int: ...
    async def collection_exists(self, collection: str) -> bool: ...
    async def create_collection(
        self, collection: str, vector_size: int, distance: str = "Cosine"
    ) -> None: ...
