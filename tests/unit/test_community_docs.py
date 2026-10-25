"""Community channel docs and beta-tester template presence."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCUSSIONS = "https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/discussions"
BETA_DISCUSSION = f"{DISCUSSIONS}/2"


class TestCommunityDocs:
    def test_support_is_discussions_first(self) -> None:
        support = (ROOT / "SUPPORT.md").read_text(encoding="utf-8")
        assert "Discussions-first" in support
        assert DISCUSSIONS in support
        assert BETA_DISCUSSION in support
        assert "no public discord invite" in support.lower()
        assert "beta_tester.md" in support

    def test_readme_links_discussions_and_beta(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        assert DISCUSSIONS in readme
        assert "discussions/2" in readme
        assert "SUPPORT.md" in readme

    def test_contributing_points_at_discussions(self) -> None:
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        assert DISCUSSIONS in contributing
        assert "beta_tester.md" in contributing
        assert "no Discord" in contributing

    def test_beta_tester_issue_template_exists(self) -> None:
        template = ROOT / ".github" / "ISSUE_TEMPLATE" / "beta_tester.md"
        text = template.read_text(encoding="utf-8")
        assert template.is_file()
        assert "name: Beta tester interest" in text
        assert "labels: beta-tester" in text
        assert BETA_DISCUSSION in text
        assert "API keys" in text or "session" in text.lower()

    def test_roadmap_marks_community_done(self) -> None:
        roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        assert "v1.2.46" in roadmap
        assert "Discussions-first community channel" in roadmap
        assert "[x] Discussions-first community channel" in roadmap
        assert "[x] Beta tester list for cloud-backup MVP" in roadmap
