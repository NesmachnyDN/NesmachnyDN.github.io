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
        self.assertIn('name="theme-color"', rendered)
        self.assertIn('property="og:image"', rendered)
        self.assertIn(build_site.SITE_URL, rendered)
        self.assertEqual(build_site.SITE_URL, "https://nesmachnydn.github.io/")

    def test_rendered_page_has_curated_navigation_and_selected_work(self):
        rendered = build_site.build_html(self.data)
        self.assertIn('id="selected"', rendered)
        self.assertIn('id="work"', rendered)
        self.assertIn('id="focus"', rendered)
        self.assertIn('class="metrics"', rendered)
        self.assertIn('Skip to content', rendered)
        for category in dict.fromkeys(project["category"] for project in self.data["projects"]):
            self.assertIn(f'id="category-{build_site.slug(category)}"', rendered)

    def test_portrait_and_architecture_preview_are_rendered(self):
        rendered = build_site.build_html(self.data)
        self.assertIn('class="portrait"', rendered)
        self.assertIn(self.data["profile"]["avatar"], rendered)
        previewed = [p for p in self.data["projects"] if p.get("preview")]
        self.assertTrue(previewed)
        for project in previewed:
            self.assertIn(project["preview"], rendered)
            self.assertIn(project["preview_alt"], rendered)

    def test_preview_requires_alt_text(self):
        mutated = json.loads(json.dumps(self.data))
        previewed = next(p for p in mutated["projects"] if p.get("preview"))
        previewed.pop("preview_alt")
        with self.assertRaises(ValueError):
            build_site.validate(mutated)

    def test_duplicate_project_order_is_rejected(self):
        mutated = json.loads(json.dumps(self.data))
        mutated["projects"][1]["order"] = mutated["projects"][0]["order"]
        with self.assertRaises(ValueError):
            build_site.validate(mutated)


if __name__ == "__main__":
    unittest.main()
