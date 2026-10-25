"""
Cloud backup services (package builder and provider abstraction).
"""

from .backup_package import (
    BACKUP_FILE_EXTENSION,
    BACKUP_SCHEMA_VERSION,
    PURPOSE_CLOUD_BACKUP,
    PURPOSE_ENTITY_TRANSFER,
    PURPOSE_OPERATOR_HANDOFF,
    SESSIONS_DIRNAME,
    BackupPackageBuilder,
    BackupPackageError,
)
from .cloud_backup_service import CloudBackupService, CloudBackupServiceError
from .entity_transfer import (
    ENTITIES_FILENAME,
    ENTITY_CAMPAIGNS,
    ENTITY_TEMPLATES,
    IMPORT_MODE_MERGE,
    IMPORT_MODE_REPLACE,
    EntityTransferError,
    collect_entities,
    import_entities,
    parse_entity_kinds,
)
from .dropbox_provider import DropboxError, DropboxProvider
from .google_drive import GoogleDriveError, GoogleDriveProvider
from .network import (
    check_network_available,
    format_offline_error,
    is_offline_error_message,
)
from .onedrive_provider import OneDriveError, OneDriveProvider
from .proton_drive_provider import ProtonDriveError, ProtonDriveProvider
from .provider_base import CloudProvider, RemoteBackupItem
from .s3_compatible import S3CompatibleError, S3CompatibleProvider
from .token_store import DriveTokenStore

__all__ = [
    "BACKUP_FILE_EXTENSION",
    "BACKUP_SCHEMA_VERSION",
    "ENTITIES_FILENAME",
    "ENTITY_CAMPAIGNS",
    "ENTITY_TEMPLATES",
    "IMPORT_MODE_MERGE",
    "IMPORT_MODE_REPLACE",
    "PURPOSE_CLOUD_BACKUP",
    "PURPOSE_ENTITY_TRANSFER",
    "PURPOSE_OPERATOR_HANDOFF",
    "SESSIONS_DIRNAME",
    "BackupPackageBuilder",
    "BackupPackageError",
    "CloudBackupService",
    "CloudBackupServiceError",
    "CloudProvider",
    "DriveTokenStore",
    "DropboxError",
    "DropboxProvider",
    "EntityTransferError",
    "GoogleDriveError",
    "GoogleDriveProvider",
    "OneDriveError",
    "OneDriveProvider",
    "ProtonDriveError",
    "ProtonDriveProvider",
    "RemoteBackupItem",
    "S3CompatibleError",
    "S3CompatibleProvider",
    "check_network_available",
    "collect_entities",
    "format_offline_error",
    "import_entities",
    "is_offline_error_message",
    "parse_entity_kinds",
]