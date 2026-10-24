"""Unit tests for desktop file-association launch argument parsing."""

from pathlib import Path

from app.core.launch_args import (
    BACKUP_PACKAGE_SUFFIX,
    filter_qt_argv,
    find_backup_package_arg,
    is_backup_package_path,
    resolve_existing_backup_package,
)


class TestLaunchArgs:
    def test_is_backup_package_path(self):
        assert is_backup_package_path("foo.tmas-backup.zip")
        assert is_backup_package_path(Path("/tmp/x.TMAS-BACKUP.ZIP"))
        assert not is_backup_package_path("foo.zip")
        assert not is_backup_package_path("notes.txt")

    def test_find_backup_package_arg_skips_flags(self, tmp_path):
        package = tmp_path / f"demo{BACKUP_PACKAGE_SUFFIX}"
        argv = ["telegram-multi-account-sender", "--verbose", str(package)]
        found = find_backup_package_arg(argv)
        assert found == package

    def test_resolve_existing_requires_file(self, tmp_path):
        missing = tmp_path / f"missing{BACKUP_PACKAGE_SUFFIX}"
        assert resolve_existing_backup_package(["app", str(missing)]) is None

        present = tmp_path / f"present{BACKUP_PACKAGE_SUFFIX}"
        present.write_bytes(b"zip")
        resolved = resolve_existing_backup_package(["app", str(present)])
        assert resolved == present.resolve()

    def test_filter_qt_argv_removes_backup_path(self, tmp_path):
        package = tmp_path / f"open{BACKUP_PACKAGE_SUFFIX}"
        argv = ["app", "--style", "Fusion", str(package)]
        filtered = filter_qt_argv(argv)
        assert filtered == ["app", "--style", "Fusion"]
