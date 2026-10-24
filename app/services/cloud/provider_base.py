"""
Abstract cloud provider interface for backup upload and restore.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class RemoteBackupItem:
    """Metadata for a backup stored in a cloud provider."""

    remote_id: str
    name: str
    size_bytes: int
    created_at: datetime


class CloudProvider(ABC):
    """Base class for cloud storage providers (Google Drive, OneDrive, etc.)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""

    @abstractmethod
    def authenticate(self) -> bool:
        """Run provider authentication; return True when connected."""

    @abstractmethod
    def upload(self, local_path: Path, remote_name: str) -> str:
        """Upload a local backup package; return remote file identifier."""

    @abstractmethod
    def download(self, remote_id: str, local_path: Path) -> Path:
        """Download a remote backup to a local path."""

    @abstractmethod
    def list_backups(self) -> List[RemoteBackupItem]:
        """List remote backup packages for this application."""

    @abstractmethod
    def delete(self, remote_id: str) -> bool:
        """Delete a remote backup package."""
