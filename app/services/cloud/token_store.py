"""
Encrypted on-disk storage for Google Drive OAuth tokens.
"""

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from app.utils.crypto import decrypt_data, encrypt_data

TOKEN_FILENAME = "google_drive_token.enc"
KEY_FILENAME = ".drive_token_key"


class DriveTokenStore:
    """Persist OAuth token JSON encrypted under the application data directory."""

    def __init__(self, cloud_dir: Optional[Path] = None):
        if cloud_dir is None:
            from app.services.settings import get_settings

            cloud_dir = Path(get_settings().app_data_dir) / "cloud"
        self.cloud_dir = Path(cloud_dir)
        self.cloud_dir.mkdir(parents=True, exist_ok=True)
        self.token_path = self.cloud_dir / TOKEN_FILENAME
        self.key_path = self.cloud_dir / KEY_FILENAME

    def save(self, token_data: Dict[str, Any]) -> None:
        """Encrypt and write token payload."""
        payload = json.dumps(token_data)
        encrypted = encrypt_data(payload, self._encryption_secret())
        self.token_path.write_text(encrypted, encoding="utf-8")

    def load(self) -> Optional[Dict[str, Any]]:
        """Load and decrypt token payload, or None if not configured."""
        if not self.token_path.exists():
            return None
        try:
            decrypted = decrypt_data(self.token_path.read_text(encoding="utf-8"), self._encryption_secret())
            return json.loads(decrypted)
        except (ValueError, json.JSONDecodeError):
            return None

    def clear(self) -> None:
        """Remove stored token."""
        if self.token_path.exists():
            self.token_path.unlink()

    def _encryption_secret(self) -> str:
        if not self.key_path.exists():
            self.key_path.write_bytes(os.urandom(32))
        return base64.urlsafe_b64encode(self.key_path.read_bytes()).decode("ascii")
