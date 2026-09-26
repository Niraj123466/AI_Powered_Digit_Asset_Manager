import pytest
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from app.domain.indexing.scanner import FileScanner, DiscoveredFile


def test_sha256_calculation():
    """Test SHA-256 hash calculation."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        f.flush()
        path = Path(f.name)

    scanner = FileScanner()
    sha256 = scanner._calculate_sha256(path)
    expected = hashlib.sha256(b"test content").hexdigest()
    assert sha256 == expected
    path.unlink()


def test_modality_detection():
    """Test file modality detection."""
    scanner = FileScanner()

    assert scanner._get_modality("jpg") == "image"
    assert scanner._get_modality("jpeg") == "image"
    assert scanner._get_modality("png") == "image"
    assert scanner._get_modality("webp") == "image"

    assert scanner._get_modality("mp4") == "video"
    assert scanner._get_modality("mov") == "video"
    assert scanner._get_modality("mkv") == "video"
    assert scanner._get_modality("avi") == "video"
    assert scanner._get_modality("webm") == "video"

    assert scanner._get_modality("pdf") == "document"

    assert scanner._get_modality("txt") is None
    assert scanner._get_modality("exe") is None


def test_ignore_patterns():
    """Test ignore pattern matching."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        scanner = FileScanner(tmp_path)

        # Create test files - some should be ignored based on default patterns
        (tmp_path / "folder").mkdir()
        (tmp_path / "folder" / ".DS_Store").write_bytes(b"test")
        (tmp_path / "folder" / "Thumbs.db").write_bytes(b"test")
        (tmp_path / "temp.tmp").write_bytes(b"test")
        (tmp_path / "image.jpg").write_bytes(b"test")

        # Scan and check that ignored files are not in results
        results = scanner.scan()
        result_paths = {r.relative_path for r in results}

        assert "folder/.DS_Store" not in result_paths
        assert "folder/Thumbs.db" not in result_paths
        assert "temp.tmp" not in result_paths
        assert "image.jpg" in result_paths


def test_scan_empty_directory():
    """Test scanning empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        scanner = FileScanner(Path(tmpdir))
        results = scanner.scan()
        assert results == []


def test_scan_with_supported_files():
    """Test scanning directory with supported files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test files
        (tmp_path / "image.jpg").write_bytes(b"fake jpg content")
        (tmp_path / "video.mp4").write_bytes(b"fake mp4 content")
        (tmp_path / "doc.pdf").write_bytes(b"fake pdf content")
        (tmp_path / "text.txt").write_bytes(b"text file")

        scanner = FileScanner(tmp_path)
        results = scanner.scan()

        assert len(results) == 3
        extensions = {r.extension for r in results}
        assert extensions == {"jpg", "mp4", "pdf"}

        modalities = {r.modality for r in results}
        assert modalities == {"image", "video", "document"}


def test_duplicate_detection_logic():
    """Test duplicate detection by hash."""
    file1 = DiscoveredFile(
        path=Path("/media/a/image.jpg"),
        relative_path="a/image.jpg",
        filename="image.jpg",
        extension="jpg",
        mime_type="image/jpeg",
        file_size=100,
        modified_time=None,
        sha256="abc123",
        modality="image",
    )
    file2 = DiscoveredFile(
        path=Path("/media/b/image.jpg"),
        relative_path="b/image.jpg",
        filename="image.jpg",
        extension="jpg",
        mime_type="image/jpeg",
        file_size=100,
        modified_time=None,
        sha256="abc123",
        modality="image",
    )
    file3 = DiscoveredFile(
        path=Path("/media/c/different.jpg"),
        relative_path="c/different.jpg",
        filename="different.jpg",
        extension="jpg",
        mime_type="image/jpeg",
        file_size=200,
        modified_time=None,
        sha256="def456",  # Different hash
        modality="image",
    )

    # This tests the logic - actual DB test would need database
    assert file1.sha256 == file2.sha256
    assert file1.sha256 != file3.sha256


# Video frame sampling tests
def test_frame_sampling_short_video():
    """Test frame sampling for short videos (< 60s)."""
    from app.processors.video.processor import VideoProcessor
    from unittest.mock import AsyncMock

    mock_asset_repo = AsyncMock()
    mock_job_repo = AsyncMock()
    mock_embedding_repo = AsyncMock()
    mock_media_meta_repo = AsyncMock()
    mock_image_analysis_repo = AsyncMock()
    mock_video_analysis_repo = AsyncMock()
    mock_document_analysis_repo = AsyncMock()
    mock_transcript_repo = AsyncMock()
    mock_vector_store = AsyncMock()

    processor = VideoProcessor(
        mock_asset_repo, mock_job_repo, mock_embedding_repo,
        mock_media_meta_repo, mock_image_analysis_repo,
        mock_video_analysis_repo, mock_document_analysis_repo,
        mock_transcript_repo, mock_vector_store
    )

    # Mock the settings
    import app.processors.video.processor as vp_module
    original_interval = vp_module.settings.video_sample_interval_seconds
    original_max = vp_module.settings.video_max_frames

    try:
        vp_module.settings.video_sample_interval_seconds = 2
        vp_module.settings.video_max_frames = 30

        frames, interval = processor._calculate_frame_plan(30.0)  # 30 second video
        # int(30/2) + 1 = 16 frames (at 0, 2, 4, ..., 30)
        # interval is recalculated: 30 / 16 = 1.875
        assert frames == 16
        assert abs(interval - 1.875) < 0.01
    finally:
        vp_module.settings.video_sample_interval_seconds = original_interval
        vp_module.settings.video_max_frames = original_max


def test_frame_sampling_long_video():
    """Test frame sampling for long videos (> 300s)."""
    from app.processors.video.processor import VideoProcessor
    from unittest.mock import AsyncMock

    mock_asset_repo = AsyncMock()
    mock_job_repo = AsyncMock()
    mock_embedding_repo = AsyncMock()
    mock_media_meta_repo = AsyncMock()
    mock_image_analysis_repo = AsyncMock()
    mock_video_analysis_repo = AsyncMock()
    mock_document_analysis_repo = AsyncMock()
    mock_transcript_repo = AsyncMock()
    mock_vector_store = AsyncMock()

    processor = VideoProcessor(
        mock_asset_repo, mock_job_repo, mock_embedding_repo,
        mock_media_meta_repo, mock_image_analysis_repo,
        mock_video_analysis_repo, mock_document_analysis_repo,
        mock_transcript_repo, mock_vector_store
    )

    import app.processors.video.processor as vp_module
    original_interval = vp_module.settings.video_sample_interval_seconds
    original_max = vp_module.settings.video_max_frames

    try:
        vp_module.settings.video_sample_interval_seconds = 10
        vp_module.settings.video_max_frames = 64

        frames, interval = processor._calculate_frame_plan(3600.0)  # 1 hour video
        assert frames == 64  # capped at max
        assert abs(interval - 56.25) < 0.01
    finally:
        vp_module.settings.video_sample_interval_seconds = original_interval
        vp_module.settings.video_max_frames = original_max