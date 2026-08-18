import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "add_favicon.py"
spec = importlib.util.spec_from_file_location("add_favicon", MODULE_PATH)
add_favicon = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(add_favicon)


class FaviconTests(unittest.TestCase):
    def test_favicon_asset_exists_and_is_svg(self):
        favicon = ROOT / "site" / "assets" / "favicon.svg"
        self.assertTrue(favicon.is_file())
        content = favicon.read_text(encoding="utf-8")
        self.assertIn("<svg", content)
        self.assertIn("#ffd75a", content)
        self.assertIn("#6fd18a", content)
        self.assertIn("#69b7ff", content)

    def test_injection_adds_icon_link_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "index.html"
            page.write_text("<html><head><title>x</title></head><body></body></html>", encoding="utf-8")
            add_favicon.inject_favicon(page, "./assets/favicon.svg")
            add_favicon.inject_favicon(page, "./assets/favicon.svg")
            rendered = page.read_text(encoding="utf-8")
            self.assertEqual(rendered.count('rel="icon"'), 1)
            self.assertIn('href="./assets/favicon.svg"', rendered)


if __name__ == "__main__":
    unittest.main()
