"""
Unit tests for media cache utilities.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.utils.media_cache import MediaCache, MediaCacheError


def test_resolve_local_file(tmp_path):
    media_file = tmp_path / "photo.jpg"
    media_file.write_bytes(b"image-bytes")

    cache = MediaCache(cache_dir=tmp_path / "cache")
    resolved = cache.resolve(str(media_file))

    assert resolved == str(media_file.resolve())


def test_resolve_missing_local_file_returns_none(tmp_path):
    cache = MediaCache(cache_dir=tmp_path / "cache")
    assert cache.resolve(str(tmp_path / "missing.jpg")) is None


def test_resolve_url_downloads_and_reuses(tmp_path):
    cache = MediaCache(cache_dir=tmp_path / "cache")
    url = "https://example.com/assets/promo.png"
    payload = b"remote-image"

    with patch("app.utils.media_cache.urlopen") as mock_urlopen:
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = payload
        mock_response.headers = {"Content-Type": "image/png"}

        first = cache.resolve(url)
        second = cache.resolve(url)

    assert first == second
    assert Path(first).is_file()
    assert Path(first).read_bytes() == payload
    assert mock_urlopen.call_count == 1


def test_resolve_url_download_failure_raises(tmp_path):
    cache = MediaCache(cache_dir=tmp_path / "cache")

    with patch("app.utils.media_cache.urlopen", side_effect=OSError("network down")):
        with pytest.raises(MediaCacheError, match="Failed to download"):
            cache.resolve("https://example.com/file.bin")


def test_cache_eviction_removes_oldest_entry(tmp_path):
    cache = MediaCache(cache_dir=tmp_path / "cache", max_bytes=20)
    url_one = "https://example.com/one.png"
    url_two = "https://example.com/two.png"

    with patch("app.utils.media_cache.urlopen") as mock_urlopen:
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.headers = {"Content-Type": "image/png"}

        mock_response.read.return_value = b"a" * 12
        cache.resolve(url_one)

        mock_response.read.return_value = b"b" * 12
        cache.resolve(url_two)

    filenames = {entry["filename"] for entry in cache._index["urls"].values()}
    assert len(filenames) == 1
