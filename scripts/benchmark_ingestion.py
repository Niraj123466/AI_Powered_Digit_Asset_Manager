#!/usr/bin/env python
"""Benchmark ingestion performance."""

import asyncio
import time
import sys
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.session import init_db, async_session_factory
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.db.repositories import (
    AssetRepository, ProcessingJobRepository, EmbeddingRepository,
    MediaMetadataRepository, ImageAnalysisRepository, VideoAnalysisRepository,
    DocumentAnalysisRepository, TranscriptRepository, DuplicateGroupRepository
)
from app.domain.indexing.orchestrator import IngestionOrchestrator
from app.processors.image.processor import ImageProcessor
from app.processors.video.processor import VideoProcessor
from app.processors.pdf.processor import PDFProcessor
from app.domain.indexing.scanner import scan_media_root

logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    total_files: int
    total_size_bytes: int
    total_time_seconds: float
    files_per_minute: float
    avg_time_per_file: float
    by_modality: dict
    failed: int
    skipped: int
    duplicates: int


async def main():
    setup_logging()
    
    print("Starting ingestion benchmark...")
    print(f"Media root: {settings.media_root}")
    print("=" * 60)
    
    # Scan files first
    print("Scanning media root...")
    start_scan = time.time()
    discovered = await scan_media_root()
    scan_time = time.time() - start_scan
    
    print(f"Discovered {len(discovered)} files in {scan_time:.2f}s")
    
    if not discovered:
        print("No files to benchmark!")
        return
    
    # Calculate total size
    total_size = sum(f.file_size for f in discovered)
    print(f"Total size: {total_size / (1024**3):.2f} GB")
    
    # Count by modality
    by_modality = {}
    for f in discovered:
        by_modality[f.modality] = by_modality.get(f.modality, 0) + 1
    print(f"By modality: {by_modality}")
    
    # Initialize services
    await init_db()
    
    vector_store = QdrantVectorStore()
    await vector_store.initialize()
    
    # Run indexing with timing
    async with async_session_factory() as session:
        asset_repo = AssetRepository(session)
        job_repo = ProcessingJobRepository(session)
        embedding_repo = EmbeddingRepository(session)
        media_meta_repo = MediaMetadataRepository(session)
        image_analysis_repo = ImageAnalysisRepository(session)
        video_analysis_repo = VideoAnalysisRepository(session)
        document_analysis_repo = DocumentAnalysisRepository(session)
        transcript_repo = TranscriptRepository(session)
        dup_group_repo = DuplicateGroupRepository(session)
        
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
        
        print("\nStarting indexing...")
        start_index = time.time()
        stats = await orchestrator.run_full_scan()
        index_time = time.time() - start_index
    
    # Calculate results
    total_time = scan_time + index_time
    files_per_minute = len(discovered) / (total_time / 60) if total_time > 0 else 0
    avg_time = total_time / len(discovered) if discovered else 0
    
    result = BenchmarkResult(
        total_files=len(discovered),
        total_size_bytes=total_size,
        total_time_seconds=total_time,
        files_per_minute=files_per_minute,
        avg_time_per_file=avg_time,
        by_modality=by_modality,
        failed=stats.total_failed,
        skipped=stats.total_skipped,
        duplicates=stats.total_duplicates,
    )
    
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Total files: {result.total_files}")
    print(f"Total size: {result.total_size_bytes / (1024**3):.2f} GB")
    print(f"Total time: {result.total_time_seconds:.2f}s")
    print(f"Files/minute: {result.files_per_minute:.1f}")
    print(f"Avg time/file: {result.avg_time_per_file:.2f}s")
    print(f"By modality: {result.by_modality}")
    print(f"Processed: {stats.total_processed}")
    print(f"Failed: {result.failed}")
    print(f"Skipped: {result.skipped}")
    print(f"Duplicates: {result.duplicates}")
    
    # Save results
    output_file = Path(__file__).parent / "benchmark_results.json"
    with open(output_file, "w") as f:
        json.dump(asdict(result), f, indent=2)
    print(f"\nResults saved to {output_file}")
    
    await vector_store.close()


if __name__ == "__main__":
    asyncio.run(main())