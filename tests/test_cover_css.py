import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "site" / "evidence.css").read_text(encoding="utf-8")


class CoverCssTests(unittest.TestCase):
    def test_project_covers_are_never_cropped(self):
        self.assertIn(".project-cover img{display:block;width:100%;height:100%;object-fit:contain", CSS)
        self.assertIn(".featured-lead .project-cover img{width:100%;height:100%;object-fit:contain", CSS)
        self.assertNotIn("object-fit:cover", CSS)


if __name__ == "__main__":
    unittest.main()
