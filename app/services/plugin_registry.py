"""
Official plugin marketplace / registry client.

Discovers third-party (and curated) plugins from a JSON catalog. Fetches the
remote catalog when online, falls back to the bundled offline copy, and can
install downloadable ``.py`` plugins into the user plugins directory after
optional SHA-256 verification. Uses stdlib ``urllib`` only.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from app.services.cloud.network import check_network_available, is_network_exception

DEFAULT_REGISTRY_URL = (
    "https://raw.githubusercontent.com/VoxHash/Telegram-Multi-Account-Message-Sender"
    "/main/registry/catalog.json"
)
DEFAULT_TIMEOUT_SECONDS = 30.0
_MAX_CATALOG_BYTES = 2 * 1024 * 1024
_MAX_PLUGIN_BYTES = 2 * 1024 * 1024
_PLUGIN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")

UrlOpen = Callable[..., Any]
NetworkCheck = Callable[[], bool]


class PluginRegistryError(Exception):
    """Base error for plugin registry operations."""


class PluginRegistryOfflineError(PluginRegistryError):
    """Raised when the network is unavailable for a remote registry request."""


class PluginRegistryInstallError(PluginRegistryError):
    """Raised when a catalog install cannot complete."""


@dataclass(frozen=True)
class RegistryPluginEntry:
    """One curated catalog entry."""

    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: str
    tags: List[str] = field(default_factory=list)
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    min_app_version: Optional[str] = None
    download_url: str = ""
    sha256: str = ""
    filename: str = ""
    bundled: bool = False
    local_only: bool = False

    @property
    def is_installable(self) -> bool:
        """True when the entry can be downloaded and installed."""
        return bool(self.download_url.strip()) and not self.local_only


@dataclass(frozen=True)
class RegistryCatalog:
    """Parsed registry catalog."""

    schema_version: int
    name: str
    updated_at: str
    homepage: Optional[str]
    plugins: List[RegistryPluginEntry]
    source: str  # "remote" | "bundled" | "path"


def bundled_catalog_path() -> Path:
    """Path to the offline catalog shipped with the package."""
    return Path(__file__).resolve().parent.parent / "plugins" / "registry" / "catalog.json"


def default_install_dir(app_data_dir: str | Path) -> Path:
    """User plugins directory used for registry installs."""
    path = Path(app_data_dir) / "plugins"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _require_str(data: Dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PluginRegistryError(f"Catalog entry missing required string field: {key}")
    return value.strip()


def parse_catalog(payload: Any, *, source: str) -> RegistryCatalog:
    """
    Validate and parse a catalog JSON object.

    Raises:
        PluginRegistryError: when the payload is invalid.
    """
    if not isinstance(payload, dict):
        raise PluginRegistryError("Catalog root must be a JSON object")

    schema_version = payload.get("schema_version", 1)
    if not isinstance(schema_version, int) or schema_version < 1:
        raise PluginRegistryError("schema_version must be a positive integer")

    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        raise PluginRegistryError("Catalog name is required")

    updated_at = payload.get("updated_at", "")
    if not isinstance(updated_at, str):
        raise PluginRegistryError("updated_at must be a string")

    homepage = payload.get("homepage")
    if homepage is not None and not isinstance(homepage, str):
        raise PluginRegistryError("homepage must be a string when present")

    raw_plugins = payload.get("plugins")
    if not isinstance(raw_plugins, list):
        raise PluginRegistryError("plugins must be a list")

    plugins: List[RegistryPluginEntry] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_plugins):
        if not isinstance(raw, dict):
            raise PluginRegistryError(f"plugins[{index}] must be an object")
        entry = _parse_entry(raw, index=index)
        if entry.id in seen_ids:
            raise PluginRegistryError(f"Duplicate plugin id: {entry.id}")
        seen_ids.add(entry.id)
        plugins.append(entry)

    return RegistryCatalog(
        schema_version=schema_version,
        name=name.strip(),
        updated_at=updated_at.strip(),
        homepage=homepage.strip() if isinstance(homepage, str) and homepage.strip() else None,
        plugins=plugins,
        source=source,
    )


def _parse_entry(raw: Dict[str, Any], *, index: int) -> RegistryPluginEntry:
    plugin_id = _require_str(raw, "id")
    if not _PLUGIN_ID_RE.match(plugin_id):
        raise PluginRegistryError(f"plugins[{index}].id is invalid: {plugin_id}")

    name = _require_str(raw, "name")
    version = _require_str(raw, "version")
    description = _require_str(raw, "description")
    author = _require_str(raw, "author")
    plugin_type = _require_str(raw, "plugin_type").lower()

    tags_raw = raw.get("tags", [])
    if tags_raw is None:
        tags_raw = []
    if not isinstance(tags_raw, list) or not all(isinstance(t, str) for t in tags_raw):
        raise PluginRegistryError(f"plugins[{index}].tags must be a list of strings")
    tags = [t.strip() for t in tags_raw if t.strip()]

    bundled = bool(raw.get("bundled", False))
    local_only = bool(raw.get("local_only", False))
    download_url = raw.get("download_url") or ""
    if not isinstance(download_url, str):
        raise PluginRegistryError(f"plugins[{index}].download_url must be a string")
    download_url = download_url.strip()

    sha256 = raw.get("sha256") or ""
    if not isinstance(sha256, str):
        raise PluginRegistryError(f"plugins[{index}].sha256 must be a string")
    sha256 = sha256.strip()

    filename = raw.get("filename") or ""
    if not isinstance(filename, str):
        raise PluginRegistryError(f"plugins[{index}].filename must be a string")
    filename = filename.strip()

    if local_only or bundled:
        # Documentation / already-shipped entries need no download fields.
        pass
    else:
        if not download_url.startswith("https://"):
            raise PluginRegistryError(
                f"plugins[{index}].download_url must be an https URL for installable entries"
            )
        if not filename or not filename.endswith(".py") or "/" in filename or "\\" in filename:
            raise PluginRegistryError(
                f"plugins[{index}].filename must be a bare .py file name"
            )
        if sha256 and not _SHA256_RE.match(sha256):
            raise PluginRegistryError(f"plugins[{index}].sha256 must be 64 hex characters")

    def _opt_str(key: str) -> Optional[str]:
        value = raw.get(key)
        if value is None or value == "":
            return None
        if not isinstance(value, str):
            raise PluginRegistryError(f"plugins[{index}].{key} must be a string")
        return value.strip()

    return RegistryPluginEntry(
        id=plugin_id,
        name=name,
        version=version,
        description=description,
        author=author,
        plugin_type=plugin_type,
        tags=tags,
        homepage=_opt_str("homepage"),
        repository=_opt_str("repository"),
        license=_opt_str("license"),
        min_app_version=_opt_str("min_app_version"),
        download_url=download_url,
        sha256=sha256,
        filename=filename,
        bundled=bundled,
        local_only=local_only,
    )


def load_catalog_from_path(path: Path, *, source: str = "path") -> RegistryCatalog:
    """Load and parse a catalog JSON file from disk."""
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PluginRegistryError(f"Could not read catalog: {path}") from exc
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise PluginRegistryError(f"Invalid catalog JSON in {path}: {exc}") from exc
    return parse_catalog(payload, source=source)


def search_catalog(
    catalog: RegistryCatalog,
    *,
    query: str = "",
    plugin_type: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
) -> List[RegistryPluginEntry]:
    """Filter catalog entries by free-text query, type, and/or tags."""
    q = query.strip().lower()
    type_filter = plugin_type.strip().lower() if plugin_type else None
    tag_filters = {t.strip().lower() for t in (tags or []) if t and t.strip()}

    results: List[RegistryPluginEntry] = []
    for entry in catalog.plugins:
        if type_filter and entry.plugin_type != type_filter:
            continue
        if tag_filters and not tag_filters.intersection({t.lower() for t in entry.tags}):
            continue
        if q:
            haystack = " ".join(
                [
                    entry.id,
                    entry.name,
                    entry.description,
                    entry.author,
                    entry.plugin_type,
                    " ".join(entry.tags),
                ]
            ).lower()
            if q not in haystack:
                continue
        results.append(entry)
    return results


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PluginRegistryService:
    """Fetch, search, and install plugins from the official registry catalog."""

    def __init__(
        self,
        *,
        registry_url: str = DEFAULT_REGISTRY_URL,
        install_dir: Path,
        bundled_path: Optional[Path] = None,
        urlopen: UrlOpen = urllib.request.urlopen,
        network_check: NetworkCheck = check_network_available,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.registry_url = (registry_url or DEFAULT_REGISTRY_URL).strip() or DEFAULT_REGISTRY_URL
        self.install_dir = Path(install_dir)
        self.bundled_path = bundled_path or bundled_catalog_path()
        self._urlopen = urlopen
        self._network_check = network_check
        self.timeout_seconds = timeout_seconds
        self._last_catalog: Optional[RegistryCatalog] = None

    @property
    def last_catalog(self) -> Optional[RegistryCatalog]:
        return self._last_catalog

    def load_bundled_catalog(self) -> RegistryCatalog:
        """Load the offline catalog shipped with the application."""
        catalog = load_catalog_from_path(self.bundled_path, source="bundled")
        self._last_catalog = catalog
        return catalog

    def fetch_catalog(self, *, prefer_remote: bool = True) -> RegistryCatalog:
        """
        Return the registry catalog.

        Tries the remote URL when ``prefer_remote`` is True and the network is
        available; on any remote failure, reuses the last successful catalog
        when present, otherwise falls back to the bundled catalog.
        """
        if prefer_remote:
            if not self._network_check():
                if self._last_catalog is not None:
                    return self._last_catalog
                return self.load_bundled_catalog()
            try:
                catalog = self._fetch_remote_catalog()
                self._last_catalog = catalog
                return catalog
            except PluginRegistryError:
                if self._last_catalog is not None:
                    return self._last_catalog
                return self.load_bundled_catalog()
        return self.load_bundled_catalog()

    def _fetch_remote_catalog(self) -> RegistryCatalog:
        request = urllib.request.Request(
            self.registry_url,
            headers={"Accept": "application/json", "User-Agent": "TMMS-PluginRegistry/1.0"},
            method="GET",
        )
        try:
            with self._urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(_MAX_CATALOG_BYTES + 1)
        except Exception as exc:  # noqa: BLE001 - map network/parse failures
            if is_network_exception(exc) or isinstance(exc, urllib.error.URLError):
                raise PluginRegistryOfflineError(
                    f"Plugin registry unreachable: {exc}"
                ) from exc
            raise PluginRegistryError(f"Failed to download catalog: {exc}") from exc

        if len(raw) > _MAX_CATALOG_BYTES:
            raise PluginRegistryError("Remote catalog exceeds size limit")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PluginRegistryError(f"Remote catalog is not valid JSON: {exc}") from exc
        return parse_catalog(payload, source="remote")

    def search(
        self,
        *,
        query: str = "",
        plugin_type: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
        prefer_remote: bool = True,
    ) -> List[RegistryPluginEntry]:
        """Fetch (or reuse) the catalog and return filtered entries."""
        catalog = self.fetch_catalog(prefer_remote=prefer_remote)
        return search_catalog(
            catalog, query=query, plugin_type=plugin_type, tags=tags
        )

    def get_entry(self, plugin_id: str, *, prefer_remote: bool = True) -> RegistryPluginEntry:
        """Look up a single catalog entry by id."""
        catalog = self.fetch_catalog(prefer_remote=prefer_remote)
        for entry in catalog.plugins:
            if entry.id == plugin_id:
                return entry
        raise PluginRegistryError(f"Unknown registry plugin id: {plugin_id}")

    def is_installed(self, entry: RegistryPluginEntry) -> bool:
        """True when the entry's target file exists in the install directory."""
        if entry.local_only or entry.bundled:
            # Bundled examples live under app/plugins; treat as available, not "installed".
            return True
        if not entry.filename:
            return False
        return (self.install_dir / entry.filename).is_file()

    def install(
        self,
        plugin_id: str,
        *,
        prefer_remote: bool = True,
        overwrite: bool = False,
    ) -> Path:
        """
        Download and install a catalog plugin into the user plugins directory.

        Does not enable the plugin — callers should load/enable via PluginManager.
        """
        entry = self.get_entry(plugin_id, prefer_remote=prefer_remote)
        if not entry.is_installable:
            raise PluginRegistryInstallError(
                f"Registry entry {plugin_id} is documentation-only; install local plugins manually."
            )
        if not entry.filename.endswith(".py"):
            raise PluginRegistryInstallError("Only .py plugin files are supported")

        target = self.install_dir / entry.filename
        if target.exists() and not overwrite:
            raise PluginRegistryInstallError(
                f"Plugin file already exists: {target.name} (pass overwrite=True to replace)"
            )

        if not self._network_check():
            raise PluginRegistryOfflineError(
                "Network unavailable; cannot download registry plugin"
            )

        request = urllib.request.Request(
            entry.download_url,
            headers={"User-Agent": "TMMS-PluginRegistry/1.0"},
            method="GET",
        )
        try:
            with self._urlopen(request, timeout=self.timeout_seconds) as response:
                data = response.read(_MAX_PLUGIN_BYTES + 1)
        except Exception as exc:  # noqa: BLE001
            if is_network_exception(exc) or isinstance(exc, urllib.error.URLError):
                raise PluginRegistryOfflineError(
                    f"Plugin download unreachable: {exc}"
                ) from exc
            raise PluginRegistryInstallError(f"Failed to download plugin: {exc}") from exc

        if len(data) > _MAX_PLUGIN_BYTES:
            raise PluginRegistryInstallError("Plugin package exceeds size limit")
        if not data.strip():
            raise PluginRegistryInstallError("Downloaded plugin file is empty")

        if entry.sha256:
            digest = _sha256_hex(data)
            if digest.lower() != entry.sha256.lower():
                raise PluginRegistryInstallError(
                    f"SHA-256 mismatch for {entry.id}: expected {entry.sha256}, got {digest}"
                )

        self.install_dir.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target


def get_plugin_registry_service(
    *,
    registry_url: Optional[str] = None,
    app_data_dir: Optional[str] = None,
) -> PluginRegistryService:
    """Build a registry service from settings defaults when args are omitted."""
    from app.services.settings import get_settings

    settings = get_settings()
    url = registry_url
    if url is None:
        url = getattr(settings, "plugin_registry_url", None) or DEFAULT_REGISTRY_URL
    data_dir = app_data_dir or settings.app_data_dir
    return PluginRegistryService(
        registry_url=str(url),
        install_dir=default_install_dir(data_dir),
    )
