# Video Processing Documentation

## Overview

The video processing pipeline extracts visual and audio information from video files for semantic search.

## Pipeline Stages

### 1. Metadata Extraction
- Uses `ffprobe` to extract:
  - Duration, FPS, resolution
  - Video/audio codecs
  - Bitrate, channels, sample rate

### 2. Frame Sampling
Adaptive sampling strategy based on video duration:

| Duration | Interval | Max Frames |
|----------|----------|------------|
| ≤ 60s | 2s | 30 |
| 60-300s | 5s | 60 |
| > 300s | 10s | 64 |

Configurable via:
- `VIDEO_SAMPLE_INTERVAL_SECONDS`
- `VIDEO_MAX_FRAMES`

### 3. Frame Extraction
- Uses `ffmpeg` to extract frames at calculated timestamps
- Outputs JPEG frames to temporary directory
- Loads frames as PIL Images for processing

### 4. Visual Analysis
For each sampled frame:
- Vision model generates description, objects, tags
- CLIP embedding generated for semantic search
- Results stored per-frame with timestamps

### 5. Video-Level Aggregation
- Combines frame descriptions into video summary
- Keyframes stored with timestamps for result explanation

### 6. Audio Transcription (Optional)
If `ENABLE_VIDEO_TRANSCRIPTION=true`:
- Extracts audio track via ffmpeg (16kHz mono WAV)
- Runs faster-whisper transcription
- Stores segments with timestamps
- Generates transcript embedding for search

## Configuration

```env
VIDEO_MAX_FRAMES=64
VIDEO_SAMPLE_INTERVAL_SECONDS=5
VIDEO_FFMPEG_PATH=ffmpeg
ENABLE_VIDEO_TRANSCRIPTION=false
TRANSCRIPTION_MODEL=base
TRANSCRIPTION_DEVICE=auto
```

## Search Result Explanation

Video search results include:
- **Matched timestamp**: Frame timestamp where match occurred
- **Frame description**: Visual description at that timestamp
- **Transcript segment**: Relevant transcript text (if available)

Example:
```
Result: construction_site.mp4
Score: 0.87
Matched at: 03:24
Visual: "Construction workers operating excavator"
Transcript: "The excavator is digging the foundation..."
```

## Storage Schema

### PostgreSQL
- `media_metadata`: Video technical metadata
- `video_analysis`: Summary, frame count, keyframes
- `video_frame`: Per-frame descriptions, objects, embedding refs
- `transcript`: Full text, segments with timestamps

### Qdrant
Collection: `dam_assets_video`
- Points: One per frame + video-level aggregate
- Vectors: Frame embeddings (512-dim)
- Payload: asset_id, timestamp, frame_number, description, modality

## Performance Considerations

- Frame extraction is I/O bound (ffmpeg)
- Vision analysis is GPU/CPU bound
- Transcription is CPU/GPU bound
- Parallel processing via `INGESTION_WORKERS`

## Limitations

- No scene detection (fixed interval sampling)
- Transcription optional (resource intensive)
- No object tracking across frames
- Limited to 64 frames by default