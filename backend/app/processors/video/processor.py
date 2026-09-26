import asyncio
import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image

from app.db.models import (
    Asset,
    ProcessingJob,
    ProcessingStage,
    MediaMetadata,
    VideoAnalysis,
    VideoFrame,
    Transcript,
    Modality,
)
from app.db.repositories import (
    AssetRepository,
    ProcessingJobRepository,
    EmbeddingRepository,
    MediaMetadataRepository,
    VideoAnalysisRepository,
    TranscriptRepository,
)
from app.ai.embeddings.qdrant_vector_store import QdrantVectorStore
from app.ai.factory import AIProviderFactory
from app.processors.base import BaseProcessor
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VideoProcessor(BaseProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vision_provider = AIProviderFactory.get_vision_provider()
        self.transcription_provider = AIProviderFactory.get_transcription_provider()

    async def process(self, asset: Asset, job: ProcessingJob) -> None:
        # Stage: Validation
        await self._update_stage(asset, job, ProcessingStage.VALIDATION)
        await self._validate_video(asset)

        # Stage: Metadata Extraction
        await self._update_stage(asset, job, ProcessingStage.METADATA_EXTRACTION)
        metadata = await self._extract_metadata(asset)
        await self.media_meta_repo.upsert(metadata)

        # Stage: Frame Extraction
        await self._update_stage(asset, job, ProcessingStage.FRAME_EXTRACTION)
        frames, timestamps = await self._extract_frames(asset, metadata.duration or 0)

        if not frames:
            logger.warning("No frames extracted from video", asset_id=str(asset.id))
            await self._create_empty_analysis(asset)
            return

        # Stage: AI Analysis
        await self._update_stage(asset, job, ProcessingStage.AI_ANALYSIS)
        vision_results = await self.vision_provider.analyze_images(frames)

        # Stage: Embedding Generation
        await self._update_stage(asset, job, ProcessingStage.EMBEDDING_GENERATION)
        frame_embeddings = await self.embedding_provider.embed_image(frames)

        # Create frame records
        video_frames = []
        for i, (frame_result, timestamp) in enumerate(zip(vision_results, timestamps)):
            video_frames.append(
                VideoFrame(
                    asset_id=asset.id,
                    frame_number=i,
                    timestamp=timestamp,
                    description=frame_result.description,
                    objects=frame_result.objects,
                )
            )

        # Store frame embeddings
        frame_vectors = []
        frame_payloads = []
        frame_content_refs = []

        for i, (embedding, frame_result, timestamp) in enumerate(
            zip(frame_embeddings, vision_results, timestamps)
        ):
            video_frames[i].embedding_id = None  # Will be set after embedding creation
            frame_vectors.append(embedding)
            frame_payloads.append(
                {
                    "modality": "video",
                    "content_type": "frame",
                    "timestamp": timestamp,
                    "frame_number": i,
                    "description": frame_result.description,
                    "path": asset.relative_path,
                }
            )
            frame_content_refs.append(f"frame_{i}")

        await self._store_embeddings(
            asset=asset,
            vectors=frame_vectors,
            payloads=frame_payloads,
            collection="assets_video",
            content_type="frame",
            model_name=self.embedding_provider.model_name,
            model_version=self.embedding_provider.model_version,
            content_refs=frame_content_refs,
        )

        # Update frame records with embedding IDs
        embeddings = await self.embedding_repo.get_by_asset(asset.id)
        frame_emb_map = {
            f"frame_{i}": e.id for i, e in enumerate(embeddings) if e.content_type == "frame"
        }
        for frame in video_frames:
            if frame.content_ref and frame.content_ref in frame_emb_map:
                frame.embedding_id = frame_emb_map[frame.content_ref]

        # Store video analysis
        analysis = VideoAnalysis(
            asset_id=asset.id,
            summary=self._generate_summary(vision_results),
            frame_count=len(frames),
            processed_frames=len(frames),
            keyframes=[
                {"timestamp": ts, "description": vr.description}
                for ts, vr in zip(timestamps, vision_results)
            ],
            vision_model=self.vision_provider.model_name,
            vision_model_version=self.vision_provider.model_version,
        )
        await self.video_analysis_repo.upsert(analysis)
        await self.video_analysis_repo.add_frames(video_frames)

        # Stage: Transcription (optional)
        if settings.enable_video_transcription:
            await self._update_stage(asset, job, ProcessingStage.TRANSCRIPTION)
            await self._transcribe_audio(asset)

    async def _validate_video(self, asset: Asset) -> None:
        path = Path(asset.absolute_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {path}")

    async def _extract_metadata(self, asset: Asset) -> MediaMetadata:
        path = Path(asset.absolute_path)
        loop = asyncio.get_event_loop()

        def _probe():
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return json.loads(result.stdout)

        probe_data = await loop.run_in_executor(None, _probe)

        duration = 0.0
        fps = 0.0
        width = 0
        height = 0
        codec = None
        bitrate = 0
        audio_codec = None
        audio_channels = 0
        audio_sample_rate = 0

        for stream in probe_data.get("streams", []):
            if stream.get("codec_type") == "video":
                duration = float(
                    stream.get("duration", 0) or probe_data.get("format", {}).get("duration", 0)
                )
                fps = self._parse_fps(stream.get("r_frame_rate", "0/1"))
                width = stream.get("width", 0)
                height = stream.get("height", 0)
                codec = stream.get("codec_name")
                bitrate = int(
                    stream.get("bit_rate", 0) or probe_data.get("format", {}).get("bit_rate", 0)
                )
            elif stream.get("codec_type") == "audio":
                audio_codec = stream.get("codec_name")
                audio_channels = stream.get("channels", 0)
                audio_sample_rate = int(stream.get("sample_rate", 0))

        return MediaMetadata(
            asset_id=asset.id,
            width=width,
            height=height,
            format=codec,
            duration=duration,
            fps=fps,
            codec=codec,
            bitrate=bitrate,
            audio_codec=audio_codec,
            audio_channels=audio_channels,
            audio_sample_rate=audio_sample_rate,
        )

    def _parse_fps(self, fps_str: str) -> float:
        try:
            num, den = fps_str.split("/")
            return float(num) / float(den)
        except:
            return 0.0

    def _calculate_frame_plan(self, duration: float) -> Tuple[int, float]:
        if duration <= 60:
            interval = 2
            max_frames = 30
        elif duration <= 300:
            interval = 5
            max_frames = 60
        else:
            interval = 10
            max_frames = settings.video_max_frames

        # Override with config
        interval = settings.video_sample_interval_seconds
        max_frames = settings.video_max_frames

        estimated_frames = int(duration / interval) + 1
        actual_frames = min(estimated_frames, max_frames)
        actual_interval = duration / actual_frames if actual_frames > 0 else interval

        return actual_frames, actual_interval

    async def _extract_frames(
        self, asset: Asset, duration: float
    ) -> Tuple[List[Image.Image], List[float]]:
        path = Path(asset.absolute_path)
        num_frames, interval = self._calculate_frame_plan(duration)

        timestamps = [i * interval for i in range(num_frames)]

        # Use ffmpeg to extract frames
        loop = asyncio.get_event_loop()

        def _extract():
            frames = []
            with tempfile.TemporaryDirectory() as tmpdir:
                for i, ts in enumerate(timestamps):
                    output_path = Path(tmpdir) / f"frame_{i:04d}.jpg"
                    cmd = [
                        settings.video_ffmpeg_path,
                        "-y",
                        "-ss",
                        str(ts),
                        "-i",
                        str(path),
                        "-vframes",
                        "1",
                        "-q:v",
                        "2",
                        str(output_path),
                    ]
                    subprocess.run(cmd, capture_output=True)
                    if output_path.exists():
                        with Image.open(output_path) as img:
                            frames.append(img.convert("RGB"))
            return frames

        frames = await loop.run_in_executor(None, _extract)
        return frames, timestamps[: len(frames)]

    def _generate_summary(self, vision_results: List) -> str:
        descriptions = [vr.description for vr in vision_results if vr.description]
        if not descriptions:
            return "No visual content detected"

        # Simple summary: combine unique descriptions
        unique_descs = []
        for d in descriptions:
            if d not in unique_descs:
                unique_descs.append(d)
        return " | ".join(unique_descs[:5])

    async def _transcribe_audio(self, asset: Asset) -> None:
        path = Path(asset.absolute_path)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_path = tmp.name

        try:
            # Extract audio
            loop = asyncio.get_event_loop()

            def _extract_audio():
                cmd = [
                    settings.video_ffmpeg_path,
                    "-y",
                    "-i",
                    str(path),
                    "-vn",
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    audio_path,
                ]
                subprocess.run(cmd, capture_output=True)

            await loop.run_in_executor(None, _extract_audio)

            if os.path.getsize(audio_path) > 0:
                transcript_result = await self.transcription_provider.transcribe(audio_path)

                transcript = Transcript(
                    asset_id=asset.id,
                    full_text=transcript_result.full_text,
                    segments=transcript_result.segments,
                    language=transcript_result.language,
                    transcription_model=self.transcription_provider.model_name,
                    transcription_model_version=self.transcription_provider.model_version,
                )
                await self.transcript_repo.upsert(transcript)

                # Add transcript text to embeddings
                if transcript_result.full_text:
                    text_embedding = await self.embedding_provider.embed_single_text(
                        transcript_result.full_text
                    )
                    await self._store_embeddings(
                        asset=asset,
                        vectors=[text_embedding],
                        payloads=[
                            {
                                "modality": "video",
                                "content_type": "transcript",
                                "text": transcript_result.full_text[:1000],
                                "path": asset.relative_path,
                            }
                        ],
                        collection="assets_video",
                        content_type="transcript",
                        model_name=self.embedding_provider.model_name,
                        model_version=self.embedding_provider.model_version,
                        content_refs=["transcript"],
                    )
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)

    async def _create_empty_analysis(self, asset: Asset) -> None:
        analysis = VideoAnalysis(
            asset_id=asset.id,
            summary="No frames could be extracted",
            frame_count=0,
            processed_frames=0,
        )
        await self.video_analysis_repo.upsert(analysis)
