"""
Disk cache for campaign media files and remote media URLs.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.services import get_logger
from app.services.settings import get_settings

DEFAULT_MAX_CACHE_BYTES = 512 * 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 60


class MediaCacheError(Exception):
    """Raised when media cannot be resolved or cached."""


class MediaCache:
    """Cache remote media locally and validate local media paths before send."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_bytes: int = DEFAULT_MAX_CACHE_BYTES,
    ):
        settings = get_settings()
        self.cache_dir = Path(cache_dir or (Path(settings.app_data_dir) / "media_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.index_path = self.cache_dir / "index.json"
        self.logger = get_logger()
        self._index = self._load_index()

    def resolve(self, media_path: str) -> Optional[str]:
        """
        Return a filesystem path suitable for Telethon ``send_file``.

        Local paths are returned when the file exists. HTTP(S) URLs are downloaded
        once and reused until evicted.
        """
        if not media_path or not str(media_path).strip():
            return None

        media_path = str(media_path).strip()
        if media_path.startswith(("http://", "https://")):
            cached = self._resolve_url(media_path)
            return str(cached) if cached else None

        local_path = Path(media_path).expanduser()
        if local_path.is_file():
            return str(local_path.resolve())

        self.logger.warning(f"Media path does not exist: {media_path}")
        return None

    def _resolve_url(self, url: str) -> Path:
        cache_key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        urls_index: Dict[str, Any] = self._index.setdefault("urls", {})
        entry = urls_index.get(cache_key)

        if entry:
            cached_path = self.cache_dir / entry["filename"]
            if cached_path.is_file() and entry.get("url") == url:
                entry["last_used"] = time.time()
                self._save_index()
                return cached_path
            self._remove_entry(cache_key, entry)

        filename = self._download_url(url, cache_key)
        cached_path = self.cache_dir / filename
        urls_index[cache_key] = {
            "url": url,
            "filename": filename,
            "size": cached_path.stat().st_size,
            "last_used": time.time(),
        }
        self._save_index()
        self._enforce_size_limit()
        return cached_path

    def _download_url(self, url: str, cache_key: str) -> str:
        request = Request(url, headers={"User-Agent": "Telegram-Multi-Account-Message-Sender/1.2"})
        try:
            with urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
                content = response.read()
                content_type = response.headers.get("Content-Type", "")
        except (URLError, OSError) as exc:
            raise MediaCacheError(f"Failed to download media URL: {exc}") from exc

        extension = self._guess_extension(url, content_type)
        filename = f"{cache_key}{extension}"
        target = self.cache_dir / filename
        target.write_bytes(content)
        self.logger.info(f"Cached remote media to {target}")
        return filename

    @staticmethod
    def _guess_extension(url: str, content_type: str) -> str:
        path_suffix = Path(urlparse(url).path).suffix
        if path_suffix and len(path_suffix) <= 8:
            return path_suffix.lower()

        if content_type:
            mime = content_type.split(";")[0].strip()
            guessed = mimetypes.guess_extension(mime)
            if guessed:
                return guessed

        return ".bin"

    def _enforce_size_limit(self) -> None:
        urls_index: Dict[str, Any] = self._index.get("urls", {})
        total_size = 0
        entries = []

        for key, entry in urls_index.items():
            path = self.cache_dir / entry.get("filename", "")
            size = path.stat().st_size if path.is_file() else 0
            entry["size"] = size
            total_size += size
            entries.append((key, entry, path))

        if total_size <= self.max_bytes:
            self._save_index()
            return

        entries.sort(key=lambda item: item[1].get("last_used", 0))
        for key, entry, path in entries:
            if total_size <= self.max_bytes:
                break
            if path.is_file():
                path.unlink(missing_ok=True)
            total_size -= int(entry.get("size", 0))
            urls_index.pop(key, None)

        self._save_index()

    def _remove_entry(self, cache_key: str, entry: Dict[str, Any]) -> None:
        path = self.cache_dir / entry.get("filename", "")
        if path.is_file():
            path.unlink(missing_ok=True)
        self._index.get("urls", {}).pop(cache_key, None)
        self._save_index()

    def _load_index(self) -> Dict[str, Any]:
        if not self.index_path.exists():
            return {"urls": {}}
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"urls": {}}

    def _save_index(self) -> None:
        self.index_path.write_text(json.dumps(self._index, indent=2), encoding="utf-8")


_media_cache: Optional[MediaCache] = None


def get_media_cache() -> MediaCache:
    """Return the process-wide media cache singleton."""
    global _media_cache
    if _media_cache is None:
        _media_cache = MediaCache()
    return _media_cache
