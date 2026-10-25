"""Unit tests for app.utils (crypto, files, windows_startup stubs)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.utils.crypto import decrypt_data, encrypt_data, hash_password, verify_password
from app.utils.files import (
    ensure_directory,
    get_file_extension,
    get_file_hash,
    get_media_type,
    is_audio_file,
    is_document_file,
    is_image_file,
    is_video_file,
    safe_filename,
)
from app.utils.windows_startup import (
    add_to_startup,
    get_app_path,
    is_in_startup,
    remove_from_startup,
    update_startup_setting,
)


@pytest.mark.unit
def test_encrypt_decrypt_roundtrip() -> None:
    """Fernet password encryption round-trips UTF-8 text."""
    secret = "campaign-payload-αβ"
    password = "test-passphrase"
    token = encrypt_data(secret, password)
    assert token != secret
    assert decrypt_data(token, password) == secret


@pytest.mark.unit
def test_encrypt_bytes_and_bad_password() -> None:
    """Bytes input encrypts; wrong password raises ValueError."""
    token = encrypt_data(b"raw-bytes", "ok")
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_data(token, "wrong")


@pytest.mark.unit
def test_hash_and_verify_password() -> None:
    """PBKDF2 password hash verifies and rejects mismatches."""
    stored = hash_password("correct-horse")
    assert verify_password(stored, "correct-horse") is True
    assert verify_password(stored, "wrong") is False
    assert verify_password("not-a-valid-blob!!!", "x") is False


@pytest.mark.unit
def test_file_helpers(tmp_path: Path) -> None:
    """Directory ensure, hash, safe name, and media-type helpers."""
    nested = ensure_directory(tmp_path / "a" / "b")
    assert nested.is_dir()

    sample = nested / "note.txt"
    sample.write_text("hello", encoding="utf-8")
    digest = get_file_hash(sample)
    assert digest is not None
    assert len(digest) == 64

    assert safe_filename('bad<>:"/\\|?*name.pdf') == "bad_________name.pdf"
    assert get_file_extension("Photo.JPG") == ".jpg"
    assert is_image_file("x.png") is True
    assert is_video_file("x.mp4") is True
    assert is_audio_file("x.mp3") is True
    assert is_document_file("x.pdf") is True
    assert get_media_type("x.png") == "image"
    assert get_media_type("x.bin") == "unknown"


@pytest.mark.unit
def test_get_app_path_returns_string() -> None:
    """get_app_path returns a non-empty executable/script path string."""
    path = get_app_path()
    assert isinstance(path, str)
    assert len(path) > 0


@pytest.mark.unit
def test_windows_startup_noops_off_windows() -> None:
    """On non-Windows, registry helpers return False without crashing."""
    if sys.platform == "win32":
        pytest.skip("noop assertions apply only when winreg is unavailable")
    assert add_to_startup("TMAS", "C:\\fake.exe") is False
    assert remove_from_startup("TMAS") is False
    assert is_in_startup("TMAS") is False
    assert update_startup_setting("TMAS", True) is False
    assert update_startup_setting("TMAS", False) is False
