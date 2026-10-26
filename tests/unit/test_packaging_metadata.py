"""Validate Linux/macOS/Windows packaging metadata used for file associations."""

from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
LINUX = ROOT / "packaging" / "linux"
MACOS = ROOT / "packaging" / "macos"
WINDOWS = ROOT / "packaging" / "windows"


class TestLinuxPackaging:
    def test_desktop_file_declares_mime_and_exec(self):
        desktop = (LINUX / "dev.voxhash.telegram-multi-account-sender.desktop").read_text(
            encoding="utf-8"
        )
        assert "Type=Application" in desktop
        assert "MimeType=application/x-tmas-backup;" in desktop
        assert "Exec=telegram-multi-account-sender %f" in desktop
        assert "Icon=dev.voxhash.telegram-multi-account-sender" in desktop

    def test_mime_xml_registers_tmas_backup_glob(self):
        mime_path = LINUX / "application-x-tmas-backup.xml"
        root = ET.parse(mime_path).getroot()
        mime_type = root.find("{http://www.freedesktop.org/standards/shared-mime-info}mime-type")
        assert mime_type is not None
        assert mime_type.attrib.get("type") == "application/x-tmas-backup"
        globs = [
            el.attrib.get("pattern")
            for el in mime_type.findall(
                "{http://www.freedesktop.org/standards/shared-mime-info}glob"
            )
        ]
        assert "*.tmas-backup.zip" in globs

    def test_install_and_assemble_scripts_exist(self):
        assert (LINUX / "install.sh").is_file()
        assert (LINUX / "assemble-dist.sh").is_file()


class TestMacosPackaging:
    def test_info_plist_declares_document_type(self):
        plist = (MACOS / "Info.plist").read_text(encoding="utf-8")
        assert "dev.voxhash.telegram-multi-account-sender" in plist
        assert "tmas-backup.zip" in plist
        assert "dev.voxhash.tmas-backup" in plist
        assert "CFBundleDocumentTypes" in plist

    def test_assemble_and_icns_scripts_exist(self):
        assert (MACOS / "assemble-app.sh").is_file()
        assert (MACOS / "build-icns.sh").is_file()

    def test_entitlements_declare_hardened_runtime_keys(self):
        entitlements = (MACOS / "entitlements.plist").read_text(encoding="utf-8")
        assert "com.apple.security.cs.allow-jit" in entitlements
        assert "com.apple.security.cs.allow-unsigned-executable-memory" in entitlements
        assert "com.apple.security.cs.disable-library-validation" in entitlements
        assert "com.apple.security.network.client" in entitlements
        assert "com.apple.security.files.user-selected.read-write" in entitlements

    def test_sign_and_notarize_scripts_exist_and_self_check(self):
        sign_script = MACOS / "sign-and-notarize.sh"
        import_script = MACOS / "import-identity.sh"
        assert sign_script.is_file()
        assert import_script.is_file()
        for script in (sign_script, import_script):
            text = script.read_text(encoding="utf-8")
            assert text.startswith("#!/usr/bin/env bash")
            assert "\r\n" not in text
            assert "APPLE_" in text
        # Self-check runs on any host (does not call codesign)
        completed = subprocess.run(
            ["bash", str(sign_script), "--self-check"],
            check=True,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert "self-check passed" in completed.stdout
        assert "APPLE_CERTIFICATE_BASE64" in completed.stdout
        completed_import = subprocess.run(
            ["bash", str(import_script), "--self-check"],
            check=True,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert "self-check OK" in completed_import.stdout

    def test_sign_and_notarize_exits_2_without_identity(self, tmp_path):
        fake_app = tmp_path / "Fake.app"
        (fake_app / "Contents" / "MacOS").mkdir(parents=True)
        (fake_app / "Contents" / "MacOS" / "telegram-multi-account-sender").write_text(
            "#!/bin/sh\n", encoding="utf-8"
        )
        env = {k: v for k, v in __import__("os").environ.items() if not k.startswith("APPLE_")}
        # On non-Darwin hosts the script exits 1 (host); on Darwin without identity exits 2.
        completed = subprocess.run(
            ["bash", str(MACOS / "sign-and-notarize.sh"), str(fake_app), "--skip-notarize"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            env=env,
        )
        assert completed.returncode in (1, 2)
        combined = completed.stdout + completed.stderr
        assert "APPLE_SIGNING_IDENTITY" in combined or "must run on macOS" in combined


class TestWindowsPackaging:
    def test_install_ps1_registers_progid_and_extension(self):
        script = (WINDOWS / "install.ps1").read_text(encoding="utf-8")
        assert '$ProgId = "dev.voxhash.tmas-backup"' in script
        assert '$Extension = ".tmas-backup.zip"' in script
        assert "HKCU:\\Software\\Classes" in script
        assert "shell\\open\\command" in script
        assert "OpenWithProgids" in script
        assert "SHChangeNotify" in script
        assert "[switch]$Uninstall" in script
        assert "telegram-multi-account-sender.exe" in script

    def test_install_and_assemble_scripts_exist(self):
        assert (WINDOWS / "install.ps1").is_file()
        assert (WINDOWS / "assemble-dist.sh").is_file()

    def test_assemble_dist_copies_exe_and_installer(self, tmp_path):
        fake_exe = tmp_path / "telegram-multi-account-sender.exe"
        fake_exe.write_bytes(b"MZ-fake")
        out_dir = tmp_path / "win-dist"
        script = WINDOWS / "assemble-dist.sh"
        subprocess.run(
            ["bash", str(script), str(fake_exe), str(out_dir), "v1.2.50"],
            check=True,
            cwd=str(ROOT),
        )
        assert (out_dir / "telegram-multi-account-sender.exe").is_file()
        assert (out_dir / "install.ps1").is_file()
        install_txt = (out_dir / "INSTALL.txt").read_text(encoding="utf-8")
        assert "v1.2.50" in install_txt
        assert "install.ps1" in install_txt
        assert "*.tmas-backup.zip" in install_txt
