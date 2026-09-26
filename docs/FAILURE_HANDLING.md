# Failure Handling Documentation

## Overview

The DAM system is designed for resilience - individual file failures never stop the entire indexing process.

## Processing State Machine

```
DISCOVERED → QUEUED → PROCESSING → COMPLETED
                    ↓
                    FAILED (retryable)
                    ↓
                    QUEUED (retry)
                    ↓
                    FAILED (max retries) → PERMANENTLY_FAILED
                    ↓
                    SKIPPED (if explicitly skipped)
```

## Failure Isolation

Each asset is processed independently:
- One corrupt video doesn't block image processing
- One OCR failure doesn't stop embedding generation
- Database transactions are per-asset

## Error Categories

### Transient Errors (Retryable)
- Network timeouts (Qdrant, Ollama)
- GPU OOM (falls back to CPU)
- Temporary file locks
- Rate limiting

### Permanent Errors (Non-Retryable)
- Corrupt/unreadable files
- Unsupported formats
- Missing codecs
- Permission denied

## Retry Logic

```python
MAX_RETRIES = 3
BASE_DELAY = 60 seconds
BACKOFF = exponential (60s, 300s, 1800s)

# Only retry transient errors
if error_type in TRANSIENT_ERRORS and retry_count < MAX_RETRIES:
    schedule_retry()
else:
    mark_permanently_failed()
```

## Error Tracking

Each failure records:
- `asset_id`
- `processing_stage` (VALIDATION, METADATA_EXTRACTION, AI_ANALYSIS, etc.)
- `error_message`
- `retry_count`
- `started_at`, `completed_at`

## Recovery Mechanisms

### 1. Retry Failed
```bash
POST /api/index/retry-failed
```
Resets failed jobs to QUEUED state and restarts orchestration.

### 2. Rescan
```bash
POST /api/index/start
```
Full rescan detects:
- New files → process
- Changed files (hash mismatch) → reprocess
- Unchanged files → skip
- Deleted files → mark DELETED, remove vectors

### 3. Manual Reprocessing
Individual assets can be reprocessed by:
1. Deleting their embeddings from Qdrant
2. Resetting asset state to QUEUED
3. Creating new processing job

## Monitoring

Dashboard shows:
- Real-time processing status
- Failed asset count with error details
- Retry queue status
- Processing rate (files/minute)

## Logging

Structured logs for every stage:
```
asset=abc123 stage=embedding status=success duration=2.31s
asset=def456 stage=video_transcription status=failed error="ffmpeg: invalid codec" retry_count=1
```

## Best Practices

1. **Monitor failed count** - Alert if > 5% failure rate
2. **Check error patterns** - Common errors indicate systemic issues
3. **Disk space** - Ensure space for temp files during video processing
4. **Memory** - Monitor GPU/CPU memory during batch processing
5. **Model availability** - Verify Ollama/models are running before indexing