"""
Developer SDK polish for plugin / registry submissions.

Validation helpers and CLI for catalog JSON schema checks, local SHA-256
verification against installable entries, and structural checks on plugin
``.py`` packages (absolute imports, Plugin subclass, metadata, versioning).
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

from app.core.plugin import (
    AnalyticsPlugin,
    IntegrationPlugin,
    MessageFilterPlugin,
    NotificationPlugin,
    Plugin,
    PluginAPI,
    PluginMetadata,
    PluginType,
)
from app.services.plugin_registry import (
    RegistryCatalog,
    RegistryPluginEntry,
    parse_catalog,
)

# Catalog schema supported by this app release (bump when format changes).
SUPPORTED_CATALOG_SCHEMA_VERSION = 1

_VERSION_RE = re.compile(
    r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[.-]?([0-9A-Za-z.-]+))?$"
)

KNOWN_PLUGIN_TYPES = {t.value for t in PluginType}

_ABSTRACT_PLUGIN_BASES = (
    Plugin,
    MessageFilterPlugin,
    AnalyticsPlugin,
    NotificationPlugin,
    IntegrationPlugin,
)


@dataclass(frozen=True)
class ValidationIssue:
    """One validation finding."""

    level: str  # "error" | "warning"
    path: str
    message: str


@dataclass
class ValidationReport:
    """Aggregated validation result."""

    target: str
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    def add(self, level: str, path: str, message: str) -> None:
        self.issues.append(ValidationIssue(level=level, path=path, message=message))

    def extend(self, other: "ValidationReport") -> None:
        self.issues.extend(other.issues)


def parse_version_tuple(version: str) -> Tuple[int, ...]:
    """
    Parse a dotted version into comparable integers (major, minor, patch).

    Raises:
        ValueError: when the version string is not a dotted numeric form.
    """
    text = (version or "").strip()
    if not text:
        raise ValueError("version string is empty")
    match = _VERSION_RE.match(text)
    if not match:
        raise ValueError(f"invalid version string: {version!r}")
    major = int(match.group(1))
    minor = int(match.group(2) or 0)
    patch = int(match.group(3) or 0)
    return (major, minor, patch)


def compare_versions(left: str, right: str) -> int:
    """
    Compare two dotted versions.

    Returns -1 if left < right, 0 if equal, 1 if left > right.
    """
    a = parse_version_tuple(left)
    b = parse_version_tuple(right)
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def check_min_app_version(
    min_app_version: Optional[str],
    app_version: str,
) -> Optional[str]:
    """
    Return an error message when ``app_version`` is below ``min_app_version``.

    Returns None when compatible or when ``min_app_version`` is unset/invalid
    enough to only warn at a higher layer.
    """
    if not min_app_version or not str(min_app_version).strip():
        return None
    try:
        if compare_versions(app_version, min_app_version.strip()) < 0:
            return (
                f"app version {app_version} is below plugin min_app_version "
                f"{min_app_version.strip()}"
            )
    except ValueError:
        return f"unparseable version for compatibility check: {min_app_version!r}"
    return None


def compute_file_sha256(path: Path) -> str:
    """SHA-256 hex digest of a file's bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_catalog_schema(
    payload: Any,
    *,
    source: str = "payload",
    app_version: Optional[str] = None,
) -> Tuple[Optional[RegistryCatalog], ValidationReport]:
    """
    Validate catalog JSON and return ``(catalog|None, report)``.

    Uses ``parse_catalog`` then adds schema_version / plugin_type / version checks.
    """
    report = ValidationReport(target=source)
    try:
        catalog = parse_catalog(payload, source=source)
    except Exception as exc:  # noqa: BLE001 - surface catalog parse errors
        report.add("error", source, str(exc))
        return None, report

    if catalog.schema_version > SUPPORTED_CATALOG_SCHEMA_VERSION:
        report.add(
            "error",
            source,
            (
                f"schema_version {catalog.schema_version} is newer than supported "
                f"{SUPPORTED_CATALOG_SCHEMA_VERSION}"
            ),
        )
    elif catalog.schema_version < 1:
        report.add("error", source, "schema_version must be >= 1")

    if not catalog.updated_at.strip():
        report.add("warning", source, "updated_at is empty")

    for entry in catalog.plugins:
        _validate_entry_extras(entry, report, app_version=app_version)

    return catalog, report


def _validate_entry_extras(
    entry: RegistryPluginEntry,
    report: ValidationReport,
    *,
    app_version: Optional[str],
) -> None:
    path = f"plugins[{entry.id}]"
    if entry.plugin_type not in KNOWN_PLUGIN_TYPES:
        report.add(
            "warning",
            path,
            (
                f"plugin_type {entry.plugin_type!r} is not a built-in PluginType "
                f"({', '.join(sorted(KNOWN_PLUGIN_TYPES))})"
            ),
        )
    try:
        parse_version_tuple(entry.version)
    except ValueError as exc:
        report.add("error", f"{path}.version", str(exc))

    if entry.min_app_version:
        try:
            parse_version_tuple(entry.min_app_version)
        except ValueError as exc:
            report.add("error", f"{path}.min_app_version", str(exc))
        else:
            if app_version:
                msg = check_min_app_version(entry.min_app_version, app_version)
                if msg:
                    report.add("warning", f"{path}.min_app_version", msg)

    if entry.is_installable and not entry.sha256:
        report.add(
            "warning",
            f"{path}.sha256",
            "installable entry has no sha256; registry install will skip digest check",
        )


def validate_catalog_file(
    path: Path,
    *,
    app_version: Optional[str] = None,
) -> Tuple[Optional[RegistryCatalog], ValidationReport]:
    """Load a catalog JSON file and validate schema + entry extras."""
    report = ValidationReport(target=str(path))
    try:
        raw_text = path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
    except OSError as exc:
        report.add("error", str(path), f"could not read catalog: {exc}")
        return None, report
    except json.JSONDecodeError as exc:
        report.add("error", str(path), f"invalid JSON: {exc}")
        return None, report
    catalog, schema_report = validate_catalog_schema(
        payload, source=str(path), app_version=app_version
    )
    report.extend(schema_report)
    return catalog, report


def validate_catalog_sha256(
    catalog: RegistryCatalog,
    plugins_dir: Path,
) -> ValidationReport:
    """
    Verify local plugin files under ``plugins_dir`` match catalog SHA-256 digests.

    Only installable entries with a filename and sha256 are checked. Missing
    files are errors (submission packages must include the plugin body).
    """
    report = ValidationReport(target=str(plugins_dir))
    if not plugins_dir.is_dir():
        report.add("error", str(plugins_dir), "plugins directory does not exist")
        return report

    for entry in catalog.plugins:
        if not entry.is_installable:
            continue
        if not entry.filename:
            continue
        plugin_path = plugins_dir / entry.filename
        path_label = f"plugins[{entry.id}]/{entry.filename}"
        if not plugin_path.is_file():
            report.add("error", path_label, f"plugin file not found: {plugin_path}")
            continue
        if not entry.sha256:
            continue
        digest = compute_file_sha256(plugin_path)
        if digest.lower() != entry.sha256.lower():
            report.add(
                "error",
                path_label,
                f"SHA-256 mismatch: catalog={entry.sha256} file={digest}",
            )
    return report


def _ast_check_absolute_imports(source: str, report: ValidationReport, label: str) -> None:
    """Flag relative imports that break when the file lives under app_data/plugins."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        report.add("error", label, f"syntax error: {exc}")
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level and node.level > 0:
            module = node.module or ""
            if "plugin" in module or module.startswith("core") or module.startswith("app"):
                report.add(
                    "error",
                    label,
                    (
                        f"relative import (level={node.level}) of {module!r} — "
                        "registry plugins must use absolute imports "
                        "(from app.core.plugin import …)"
                    ),
                )
            else:
                report.add(
                    "warning",
                    label,
                    (
                        f"relative import (level={node.level}) of {module or '.'!r} "
                        "may break when installed under app_data/plugins/"
                    ),
                )


def validate_plugin_file(
    path: Path,
    *,
    app_version: Optional[str] = None,
) -> ValidationReport:
    """
    Validate a single plugin ``.py`` package for registry submission readiness.

    Checks: syntax, absolute imports, loadable Plugin subclass, metadata fields,
    known plugin_type, and optional min_app_version vs ``app_version``.
    """
    report = ValidationReport(target=str(path))
    if not path.is_file():
        report.add("error", str(path), "plugin file not found")
        return report
    if path.suffix != ".py":
        report.add("error", str(path), "plugin package must be a .py file")
        return report

    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        report.add("error", str(path), f"could not read plugin: {exc}")
        return report

    if not source.strip():
        report.add("error", str(path), "plugin file is empty")
        return report

    _ast_check_absolute_imports(source, report, str(path))
    if not report.ok:
        # Still try load if only warnings; stop early on syntax/import errors already recorded.
        if any("syntax error" in i.message for i in report.issues):
            return report

    module_name = f"_tmas_plugin_validate_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        report.add("error", str(path), "could not create import spec")
        return report

    module = importlib.util.module_from_spec(spec)
    parent = str(path.parent)
    inserted = False
    if parent not in sys.path:
        sys.path.insert(0, parent)
        inserted = True
    try:
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            report.add("error", str(path), f"failed to import plugin module: {exc}")
            return report

        plugin_class = _find_concrete_plugin_class(module)
        if plugin_class is None:
            report.add("error", str(path), "no concrete Plugin subclass found")
            return report

        api = PluginAPI(
            services={
                "logger": None,
                "settings": None,
                "session": None,
                "campaign_manager": None,
            }
        )
        try:
            instance = plugin_class(api)
        except TypeError as exc:
            report.add(
                "error",
                str(path),
                f"cannot instantiate plugin (abstract methods?): {exc}",
            )
            return report
        except Exception as exc:  # noqa: BLE001
            report.add("error", str(path), f"plugin constructor failed: {exc}")
            return report

        try:
            metadata = instance.metadata
        except Exception as exc:  # noqa: BLE001
            report.add("error", str(path), f"metadata property failed: {exc}")
            return report

        _validate_plugin_metadata(metadata, report, path=str(path), app_version=app_version)

        default_cfg = instance.get_default_config()
        if not isinstance(default_cfg, dict):
            report.add("error", str(path), "get_default_config() must return a dict")
        else:
            ok, err = instance.validate_config(default_cfg)
            if not ok:
                report.add(
                    "error",
                    str(path),
                    f"default config failed validate_config: {err}",
                )
    finally:
        sys.modules.pop(module_name, None)
        if inserted and parent in sys.path:
            sys.path.remove(parent)

    return report


def _find_concrete_plugin_class(module: Any) -> Optional[type]:
    for _name, obj in inspect.getmembers(module, inspect.isclass):
        if not issubclass(obj, Plugin):
            continue
        if obj in _ABSTRACT_PLUGIN_BASES:
            continue
        if getattr(obj, "__module__", None) != module.__name__:
            continue
        return obj
    return None


def _validate_plugin_metadata(
    metadata: Any,
    report: ValidationReport,
    *,
    path: str,
    app_version: Optional[str],
) -> None:
    if not isinstance(metadata, PluginMetadata):
        report.add("error", path, "metadata must be a PluginMetadata instance")
        return
    for field_name in ("name", "version", "description", "author"):
        value = getattr(metadata, field_name, None)
        if not isinstance(value, str) or not value.strip():
            report.add("error", path, f"metadata.{field_name} must be a non-empty string")
    try:
        parse_version_tuple(metadata.version)
    except ValueError as exc:
        report.add("error", path, f"metadata.version: {exc}")
    if metadata.min_app_version:
        try:
            parse_version_tuple(metadata.min_app_version)
        except ValueError as exc:
            report.add("error", path, f"metadata.min_app_version: {exc}")
        else:
            if app_version:
                msg = check_min_app_version(metadata.min_app_version, app_version)
                if msg:
                    report.add("warning", path, msg)


def format_validation_report(report: ValidationReport) -> str:
    """Human-readable multi-line report for CLI stdout."""
    lines = [f"Target: {report.target}", f"Status: {'OK' if report.ok else 'FAILED'}"]
    if not report.issues:
        lines.append("No issues.")
        return "\n".join(lines)
    for issue in report.issues:
        lines.append(f"[{issue.level.upper()}] {issue.path}: {issue.message}")
    return "\n".join(lines)


def parse_plugin_validate_argv(
    argv: Sequence[str],
) -> Tuple[
    bool,
    Optional[Path],
    Optional[Path],
    Optional[str],
    bool,
]:
    """
    Detect ``plugin-validate`` CLI mode.

    Returns
    ``(is_mode, target, plugins_dir, app_version, help_requested)``.
    """
    tokens = list(argv[1:]) if argv else []
    if not tokens:
        return False, None, None, None, False

    cmd = tokens[0].lower().replace("_", "-")
    if cmd not in ("plugin-validate", "validate-plugin", "plugins-validate"):
        return False, None, None, None, False

    target: Optional[Path] = None
    plugins_dir: Optional[Path] = None
    app_version: Optional[str] = None
    help_requested = False
    positional: List[str] = []
    i = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("-h", "--help"):
            help_requested = True
            i += 1
            continue
        if tok in ("--plugins-dir", "-d") and i + 1 < len(tokens):
            plugins_dir = Path(tokens[i + 1])
            i += 2
            continue
        if tok.startswith("--plugins-dir="):
            plugins_dir = Path(tok.split("=", 1)[1])
            i += 1
            continue
        if tok in ("--app-version", "-a") and i + 1 < len(tokens):
            app_version = tokens[i + 1]
            i += 2
            continue
        if tok.startswith("--app-version="):
            app_version = tok.split("=", 1)[1]
            i += 1
            continue
        if tok.startswith("-"):
            # Unknown flag — treat as positional path for clearer CLI errors later.
            positional.append(tok)
            i += 1
            continue
        positional.append(tok)
        i += 1

    if positional:
        target = Path(positional[0])
    return True, target, plugins_dir, app_version, help_requested


def _plugin_validate_help() -> str:
    return """Usage:
  telegram-sender plugin-validate <catalog.json|plugin.py> [--plugins-dir DIR] [--app-version X]

Validate a registry catalog submission and/or a plugin .py package.

  catalog.json   Schema version, entry fields, plugin_type, versions
  --plugins-dir  Verify SHA-256 of installable entries against local .py files
  plugin.py      Absolute imports, Plugin subclass, metadata, default config

Examples:
  telegram-sender plugin-validate registry/catalog.json --plugins-dir registry/plugins
  telegram-sender plugin-validate registry/plugins/url_strip_filter.py
  telegram-sender plugin-validate registry/templates/sample_filter_plugin.py --app-version 1.2.30
"""


def run_plugin_validate_cli(argv: Sequence[str]) -> int:
    """CLI entry for ``plugin-validate``. Returns process exit code."""
    is_mode, target, plugins_dir, app_version, help_requested = parse_plugin_validate_argv(
        argv
    )
    if not is_mode:
        raise ValueError("run_plugin_validate_cli requires a plugin-validate argv")

    if help_requested:
        print(_plugin_validate_help())
        return 0
    if target is None:
        print(_plugin_validate_help())
        return 1

    if app_version is None:
        from app import __version__

        app_version = __version__

    exit_code = 0
    suffix = target.suffix.lower()

    if suffix == ".json":
        catalog, report = validate_catalog_file(target, app_version=app_version)
        print(format_validation_report(report))
        if not report.ok:
            exit_code = 1
        if catalog is not None and plugins_dir is not None:
            sha_report = validate_catalog_sha256(catalog, plugins_dir)
            print()
            print(format_validation_report(sha_report))
            if not sha_report.ok:
                exit_code = 1
        elif catalog is not None and plugins_dir is None:
            # Hint for submitters validating the official tree.
            installable = [e for e in catalog.plugins if e.is_installable and e.sha256]
            if installable:
                print()
                print(
                    "Note: pass --plugins-dir to verify SHA-256 digests against local plugin files."
                )
        return exit_code

    if suffix == ".py":
        report = validate_plugin_file(target, app_version=app_version)
        print(format_validation_report(report))
        return 0 if report.ok else 1

    print(f"Unsupported target type: {target} (expected .json catalog or .py plugin)")
    print()
    print(_plugin_validate_help())
    return 1
