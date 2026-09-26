import hashlib
import mimetypes
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Set
from datetime import datetime
import fnmatch

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DiscoveredFile:
    path: Path
    relative_path: str
    filename: str
    extension: str
    mime_type: str
    file_size: int
    modified_time: datetime
    sha256: str
    modality: str  # "image", "video", "document"


class FileScanner:
    def __init__(self, media_root: Path = None):
        self.media_root = media_root or settings.media_root
        self.supported_extensions = set(settings.all_supported_extensions)
        self.ignore_patterns = settings.ignore_patterns_list
        self.image_extensions = set(settings.supported_image_exts_list)
        self.video_extensions = set(settings.supported_video_exts_list)
        self.doc_extensions = set(settings.supported_doc_exts_list)

    def _should_ignore(self, path: Path) -> bool:
        relative = path.relative_to(self.media_root)
        relative_str = str(relative)
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(relative_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
        return False

    def _get_modality(self, extension: str) -> Optional[str]:
        ext = extension.lower().lstrip(".")
        if ext in self.image_extensions:
            return "image"
        elif ext in self.video_extensions:
            return "video"
        elif ext in self.doc_extensions:
            return "document"
        return None

    def _get_mime_type(self, path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(str(path))
        return mime_type or "application/octet-stream"

    def _calculate_sha256(self, path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def scan(self) -> List[DiscoveredFile]:
        if not self.media_root.exists():
            logger.warning("Media root does not exist", path=str(self.media_root))
            return []

        discovered = []
        for file_path in self.media_root.rglob("*"):
            if not file_path.is_file():
                continue

            if self._should_ignore(file_path):
                continue

            extension = file_path.suffix.lower().lstrip(".")
            if extension not in self.supported_extensions:
                continue

            modality = self._get_modality(extension)
            if not modality:
                continue

            try:
                stat = file_path.stat()
                relative_path = str(file_path.relative_to(self.media_root))
                sha256 = self._calculate_sha256(file_path)

                discovered.append(
                    DiscoveredFile(
                        path=file_path,
                        relative_path=relative_path,
                        filename=file_path.name,
                        extension=extension,
                        mime_type=self._get_mime_type(file_path),
                        file_size=stat.st_size,
                        modified_time=datetime.fromtimestamp(stat.st_mtime),
                        sha256=sha256,
                        modality=modality,
                    )
                )
            except Exception as e:
                logger.error("Failed to process file", path=str(file_path), error=str(e))

        logger.info("Scan completed", total_files=len(discovered))
        return discovered


async def scan_media_root(media_root: Path = None) -> List[DiscoveredFile]:
    scanner = FileScanner(media_root)
    return scanner.scan()
