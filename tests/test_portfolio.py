import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_site.py"
spec = importlib.util.spec_from_file_location("build_site", MODULE_PATH)
build_site = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(build_site)


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "portfolio.json").read_text(encoding="utf-8"))

    def test_portfolio_data_is_valid(self):
        build_site.validate(self.data)

    def test_rendered_page_contains_all_projects(self):
        rendered = build_site.build_html(self.data)
        for project in self.data["projects"]:
            self.assertIn(project["title"], rendered)
            self.assertIn(project["url"], rendered)

    def test_rendered_page_has_expected_metadata(self):
        rendered = build_site.build_html(self.data)
        self.assertIn('<meta name="description"', rendered)
        self.assertIn('application/ld+json', rendered)
        self.assertIn('rel="canonical"', rendered)
        self.assertIn(build_site.SITE_URL, rendered)
        self.assertEqual(build_site.SITE_URL, "https://nesmachnydn.github.io/")

    def test_duplicate_project_order_is_rejected(self):
        mutated = json.loads(json.dumps(self.data))
        mutated["projects"][1]["order"] = mutated["projects"][0]["order"]
        with self.assertRaises(ValueError):
            build_site.validate(mutated)


if __name__ == "__main__":
    unittest.main()
