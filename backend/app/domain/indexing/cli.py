#!/usr/bin/env python
"""CLI for running indexing."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.session import init_db, async_session_factory
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
from app.domain.indexing.orchestrator import IngestionOrchestrator
from app.processors.image.processor import ImageProcessor
from app.processors.video.processor import VideoProcessor
from app.processors.pdf.processor import PDFProcessor

logger = get_logger(__name__)


async def main():
    setup_logging()
    logger.info("Starting indexing CLI")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize vector store
    vector_store = QdrantVectorStore()
    await vector_store.initialize()
    logger.info("Vector store initialized")

    # Create session
    async with async_session_factory() as session:
        # Create repositories
        asset_repo = AssetRepository(session)
        job_repo = ProcessingJobRepository(session)
        embedding_repo = EmbeddingRepository(session)
        media_meta_repo = MediaMetadataRepository(session)
        image_analysis_repo = ImageAnalysisRepository(session)
        video_analysis_repo = VideoAnalysisRepository(session)
        document_analysis_repo = DocumentAnalysisRepository(session)
        transcript_repo = TranscriptRepository(session)
        dup_group_repo = DuplicateGroupRepository(session)

        # Create orchestrator
        orchestrator = IngestionOrchestrator(
            asset_repo=asset_repo,
            job_repo=job_repo,
            embedding_repo=embedding_repo,
            media_meta_repo=media_meta_repo,
            image_analysis_repo=image_analysis_repo,
            video_analysis_repo=video_analysis_repo,
            document_analysis_repo=document_analysis_repo,
            transcript_repo=transcript_repo,
            dup_group_repo=dup_group_repo,
            vector_store=vector_store,
        )

        # Register processors
        orchestrator.register_processors(
            image_processor=ImageProcessor(
                asset_repo, job_repo, embedding_repo, media_meta_repo, vector_store
            ).process,
            video_processor=VideoProcessor(
                asset_repo, job_repo, embedding_repo, media_meta_repo, vector_store
            ).process,
            document_processor=PDFProcessor(
                asset_repo, job_repo, embedding_repo, media_meta_repo, vector_store
            ).process,
        )

        # Run indexing
        logger.info("Starting full scan...")
        stats = await orchestrator.run_full_scan()

        logger.info("Indexing completed", stats=stats.__dict__)

        # Print summary
        print("\n=== Indexing Summary ===")
        print(f"Total discovered: {stats.total_discovered}")
        print(f"New files: {stats.total_new}")
        print(f"Duplicates: {stats.total_duplicates}")
        print(f"Processed: {stats.total_processed}")
        print(f"Failed: {stats.total_failed}")
        print(f"Skipped: {stats.total_skipped}")

    await vector_store.close()


if __name__ == "__main__":
    asyncio.run(main())
