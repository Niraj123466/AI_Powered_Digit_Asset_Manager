from typing import List, Tuple
from uuid import UUID
from dataclasses import dataclass

from app.db.repositories import AssetRepository, DuplicateGroupRepository
from app.db.models import Asset, DuplicateGroup, AssetState
from app.domain.indexing.scanner import DiscoveredFile
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DuplicateResult:
    new_files: List[DiscoveredFile]
    duplicates: List[Tuple[DiscoveredFile, UUID]]  # (file, existing_asset_id)


class DuplicateDetector:
    def __init__(self, asset_repo: AssetRepository, dup_group_repo: DuplicateGroupRepository):
        self.asset_repo = asset_repo
        self.dup_group_repo = dup_group_repo

    async def process(self, files: List[DiscoveredFile]) -> DuplicateResult:
        new_files = []
        duplicates = []

        for file in files:
            existing_asset = await self.asset_repo.get_by_hash(file.sha256)

            if existing_asset:
                # Check if this exact path already exists
                path_asset = await self.asset_repo.get_by_path(file.relative_path)
                if path_asset and path_asset.id == existing_asset.id:
                    # Same file, already indexed
                    logger.debug(
                        "File already indexed",
                        path=file.relative_path,
                        asset_id=str(existing_asset.id),
                    )
                    continue

                # Duplicate content, different path
                dup_group = await self.dup_group_repo.get_by_hash(file.sha256)
                if dup_group:
                    await self.dup_group_repo.increment_count(file.sha256)
                else:
                    dup_group = DuplicateGroup(
                        sha256=file.sha256,
                        canonical_asset_id=existing_asset.id,
                        reference_count=2,
                    )
                    await self.dup_group_repo.create(dup_group)

                duplicates.append((file, existing_asset.id))
                logger.info(
                    "Duplicate detected",
                    new_path=file.relative_path,
                    existing_asset_id=str(existing_asset.id),
                )
            else:
                new_files.append(file)

        return DuplicateResult(new_files=new_files, duplicates=duplicates)
