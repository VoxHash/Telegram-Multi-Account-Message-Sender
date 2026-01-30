"""
File utility functions.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, Union


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def get_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> Optional[str]:
    """Get file hash."""
    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception:
        return None


def safe_filename(filename: str) -> str:
    """Make filename safe for filesystem."""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


def get_file_extension(file_path: Union[str, Path]) -> str:
    """Get file extension."""
    return Path(file_path).suffix.lower()


def is_image_file(file_path: Union[str, Path]) -> bool:
    """Check if file is an image."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    return get_file_extension(file_path) in image_extensions


def is_video_file(file_path: Union[str, Path]) -> bool:
    """Check if file is a video."""
    video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}
    return get_file_extension(file_path) in video_extensions


def is_audio_file(file_path: Union[str, Path]) -> bool:
    """Check if file is an audio file."""
    audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
    return get_file_extension(file_path) in audio_extensions


def is_document_file(file_path: Union[str, Path]) -> bool:
    """Check if file is a document."""
    doc_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
    return get_file_extension(file_path) in doc_extensions


def get_media_type(file_path: Union[str, Path]) -> str:
    """Get media type of file."""
    if is_image_file(file_path):
        return "image"
    elif is_video_file(file_path):
        return "video"
    elif is_audio_file(file_path):
        return "audio"
    elif is_document_file(file_path):
        return "document"
    else:
        return "unknown"
