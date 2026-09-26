from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from app.db.models import Modality
from app.core.config import settings


@dataclass
class QueryIntent:
    original_query: str
    semantic_query: str
    modality_filter: Optional[Modality] = None
    filters: Dict[str, Any] = None

    def __post_init__(self):
        if self.filters is None:
            self.filters = {}


class QueryParser:
    def __init__(self):
        self.video_keywords = set(settings.modality_video_keywords_list)
        self.image_keywords = set(settings.modality_image_keywords_list)
        self.document_keywords = set(settings.modality_document_keywords_list)

    def parse(self, query: str, explicit_filters: Dict[str, Any] = None) -> QueryIntent:
        query_lower = query.lower()
        words = query_lower.split()

        # Detect modality intent
        modality_filter = None
        filtered_words = []

        for word in words:
            if word in self.video_keywords:
                modality_filter = Modality.VIDEO
            elif word in self.image_keywords:
                modality_filter = Modality.IMAGE
            elif word in self.document_keywords:
                modality_filter = Modality.DOCUMENT
            else:
                filtered_words.append(word)

        semantic_query = " ".join(filtered_words) if filtered_words else query

        # Merge explicit filters
        filters = explicit_filters or {}

        return QueryIntent(
            original_query=query,
            semantic_query=semantic_query,
            modality_filter=modality_filter,
            filters=filters,
        )
