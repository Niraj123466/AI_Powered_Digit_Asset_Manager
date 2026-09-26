import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from app.domain.indexing.duplicate_detector import DuplicateDetector, DuplicateResult
from app.domain.indexing.scanner import DiscoveredFile
from app.db.models import Asset, DuplicateGroup, AssetState, Modality
from datetime import datetime


@pytest.fixture
def mock_asset_repo():
    return AsyncMock()


@pytest.fixture
def mock_dup_group_repo():
    return AsyncMock()


@pytest.fixture
def sample_files():
    return [
        DiscoveredFile(
            path=None,
            relative_path="new/image1.jpg",
            filename="image1.jpg",
            extension="jpg",
            mime_type="image/jpeg",
            file_size=100,
            modified_time=datetime.now(),
            sha256="hash1",
            modality="image",
        ),
        DiscoveredFile(
            path=None,
            relative_path="new/image2.jpg",
            filename="image2.jpg",
            extension="jpg",
            mime_type="image/jpeg",
            file_size=200,
            modified_time=datetime.now(),
            sha256="hash2",
            modality="image",
        ),
    ]


@pytest.mark.asyncio
async def test_duplicate_detector_new_files(mock_asset_repo, mock_dup_group_repo, sample_files):
    """Test that new files are detected correctly."""
    mock_asset_repo.get_by_hash.return_value = None

    detector = DuplicateDetector(mock_asset_repo, mock_dup_group_repo)
    result = await detector.process(sample_files)

    assert len(result.new_files) == 2
    assert len(result.duplicates) == 0
    assert mock_asset_repo.get_by_hash.call_count == 2


@pytest.mark.asyncio
async def test_duplicate_detector_exact_duplicates(
    mock_asset_repo, mock_dup_group_repo, sample_files
):
    """Test that exact duplicates are detected."""
    existing_asset = Asset(
        id=uuid4(), sha256="hash1", modality=Modality.IMAGE, state=AssetState.COMPLETED
    )
    mock_asset_repo.get_by_hash.side_effect = [existing_asset, None]
    mock_asset_repo.get_by_path.return_value = None
    mock_dup_group_repo.get_by_hash.return_value = None

    detector = DuplicateDetector(mock_asset_repo, mock_dup_group_repo)
    result = await detector.process(sample_files)

    assert len(result.new_files) == 1
    assert len(result.duplicates) == 1
    assert result.duplicates[0][1] == existing_asset.id
    mock_dup_group_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_duplicate_detector_existing_duplicate_group(
    mock_asset_repo, mock_dup_group_repo, sample_files
):
    """Test that existing duplicate group increments count."""
    existing_asset = Asset(
        id=uuid4(), sha256="hash1", modality=Modality.IMAGE, state=AssetState.COMPLETED
    )
    existing_group = DuplicateGroup(
        id=uuid4(), sha256="hash1", canonical_asset_id=existing_asset.id, reference_count=2
    )
    mock_asset_repo.get_by_hash.side_effect = [existing_asset, None]
    mock_asset_repo.get_by_path.return_value = None
    mock_dup_group_repo.get_by_hash.return_value = existing_group
    mock_dup_group_repo.increment_count.return_value = 3

    detector = DuplicateDetector(mock_asset_repo, mock_dup_group_repo)
    result = await detector.process(sample_files)

    assert len(result.duplicates) == 1
    mock_dup_group_repo.increment_count.assert_called_once_with("hash1")


@pytest.mark.asyncio
async def test_duplicate_detector_same_path_skip(mock_asset_repo, mock_dup_group_repo):
    """Test that same file path with same hash is skipped."""
    existing_asset = Asset(
        id=uuid4(), sha256="hash1", modality=Modality.IMAGE, state=AssetState.COMPLETED
    )
    mock_asset_repo.get_by_hash.return_value = existing_asset
    mock_asset_repo.get_by_path.return_value = existing_asset  # Same path, same asset

    # Create a file with same path and hash as existing
    same_file = DiscoveredFile(
        path=None,
        relative_path="existing.jpg",
        filename="existing.jpg",
        extension="jpg",
        mime_type="image/jpeg",
        file_size=100,
        modified_time=datetime.now(),
        sha256="hash1",
        modality="image",
    )

    detector = DuplicateDetector(mock_asset_repo, mock_dup_group_repo)
    result = await detector.process([same_file])

    assert len(result.new_files) == 0  # Skipped as already indexed
    assert len(result.duplicates) == 0
