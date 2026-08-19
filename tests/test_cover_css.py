import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "site" / "evidence.css").read_text(encoding="utf-8")


class CoverCssTests(unittest.TestCase):
    def test_project_covers_are_never_cropped(self):
        self.assertIn(".project-cover img{display:block;width:100%;height:100%;object-fit:contain", CSS)
        self.assertIn(".featured-lead .project-cover img{width:100%;height:100%;object-fit:contain", CSS)
        self.assertNotIn("object-fit:cover", CSS)

    def test_iam_cover_matches_standard_card_aspect_ratio(self):
        cover = (ROOT / "site" / "assets" / "covers" / "enterprise-platform-iam-integration-case.svg").read_text(encoding="utf-8")
        self.assertIn('width="1280" height="640"', cover)
        self.assertIn('viewBox="0 0 1280 640"', cover)


if __name__ == "__main__":
    unittest.main()
