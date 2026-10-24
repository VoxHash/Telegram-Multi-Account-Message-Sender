"""Validate Linux/macOS packaging metadata used for file associations."""

from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
LINUX = ROOT / "packaging" / "linux"
MACOS = ROOT / "packaging" / "macos"


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
