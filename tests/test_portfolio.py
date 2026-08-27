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

    def test_russian_is_default_and_english_is_alternate(self):
        ru = build_site.build_html(self.data, "ru")
        en = build_site.build_html(self.data, "en")
        self.assertIn('<html lang="ru">', ru)
        self.assertIn('<html lang="en">', en)
        self.assertIn(self.data["profile"]["ru"]["headline"], ru)
        self.assertIn(self.data["profile"]["headline"], en)
        self.assertIn('href="https://nesmachnydn.github.io/en/"', ru)
        self.assertIn('href="https://nesmachnydn.github.io/"', en)
        self.assertIn('hreflang="ru"', ru)
        self.assertIn('hreflang="en"', en)

    def test_all_projects_are_localized(self):
        ru = build_site.build_html(self.data, "ru")
        en = build_site.build_html(self.data, "en")
        for project in self.data["projects"]:
            self.assertIn(project["title"], en)
            self.assertIn(project["ru"]["title"], ru)
            if project.get("url"):
                self.assertIn(project["url"], ru)
                self.assertIn(project["url"], en)

    def test_evidence_and_provenance_are_rendered(self):
        ru = build_site.build_html(self.data, "ru")
        en = build_site.build_html(self.data, "en")
        for project in self.data["projects"]:
            proof = project["proof"]
            self.assertIn(build_site.PROOF_ACCESS["ru"][proof["access"]], ru)
            self.assertIn(build_site.PROOF_ORIGIN["ru"][proof["origin"]], ru)
            self.assertIn(build_site.PROOF_ACCESS["en"][proof["access"]], en)
            self.assertIn(build_site.PROOF_ORIGIN["en"][proof["origin"]], en)

    def test_live_demo_case_may_omit_public_url(self):
        case = next(p for p in self.data["projects"] if p["title"] == "Career Operations Automation Platform")
        self.assertNotIn("url", case)
        ru = build_site.build_html(self.data, "ru")
        en = build_site.build_html(self.data, "en")
        self.assertIn(case["ru"]["title"], ru)
        self.assertIn(case["title"], en)
        self.assertIn("Демонстрация вживую", ru)
        self.assertIn("Live demo on request", en)

    def test_proof_metadata_is_required(self):
        mutated = json.loads(json.dumps(self.data))
        mutated["projects"][0].pop("proof")
        with self.assertRaises(ValueError):
            build_site.validate(mutated)

    def test_proof_badges_have_html_fallback_spacing(self):
        ru = build_site.build_html(self.data, "ru")
        self.assertIn('</span> <span class="proof-badge origin">', ru)

    def test_stylesheets_are_cache_busted(self):
        ru = build_site.build_html(self.data, "ru")
        en = build_site.build_html(self.data, "en")
        self.assertRegex(ru, r'href="\.\/style\.css\?v=[0-9a-f]{10}"')
        self.assertRegex(ru, r'href="\.\/evidence\.css\?v=[0-9a-f]{10}"')
        self.assertRegex(en, r'href="\.\.\/style\.css\?v=[0-9a-f]{10}"')
        self.assertRegex(en, r'href="\.\.\/evidence\.css\?v=[0-9a-f]{10}"')

    def test_metadata_is_language_specific(self):
        ru = build_site.build_html(self.data, "ru")
        en = build_site.build_html(self.data, "en")
        self.assertIn('property="og:locale" content="ru_RU"', ru)
        self.assertIn('property="og:locale" content="en_US"', en)
        self.assertIn('rel="canonical" href="https://nesmachnydn.github.io/"', ru)
        self.assertIn('rel="canonical" href="https://nesmachnydn.github.io/en/"', en)

    def test_selected_project_covers_are_not_evidence_thumbnails(self):
        for locale in ("ru", "en"):
            rendered = build_site.build_html(self.data, locale)
            featured = [p for p in self.data["projects"] if p["featured"]]
            self.assertEqual(rendered.count('class="project-cover'), len(featured))
            for item in [e for p in self.data["projects"] for e in p.get("evidence", [])]:
                self.assertNotIn(item["url"], rendered)

    def test_russian_focus_content_is_rendered(self):
        rendered = build_site.build_html(self.data, "ru")
        for key in self.data["focus"]:
            self.assertIn(self.data["focus_ru"][key]["title"], rendered)
            self.assertIn(self.data["focus_ru"][key]["detail"], rendered)

    def test_homepage_is_content_first_not_site_explanation(self):
        ru = build_site.build_html(self.data, "ru")
        self.assertIn("Избранные архитектурные кейсы", ru)
        self.assertIn("Все кейсы портфолио", ru)
        self.assertIn("Профессиональный фокус", ru)
        self.assertNotIn("этот раздел предназначен", ru)
        self.assertNotIn("не уменьшаются до нечитаемых превью", ru)
        self.assertNotIn("Портфолио автоматически формируется", ru)
        self.assertNotIn("Архитектура как инженерная дисциплина", ru)

    def test_localization_is_mandatory(self):
        mutated = json.loads(json.dumps(self.data))
        mutated["projects"][0]["ru"].pop("summary")
        with self.assertRaises(ValueError):
            build_site.validate(mutated)

    def test_only_one_lead_project_is_allowed(self):
        mutated = json.loads(json.dumps(self.data))
        featured = [p for p in mutated["projects"] if p["featured"]]
        featured[1]["lead"] = True
        with self.assertRaises(ValueError):
            build_site.validate(mutated)

    def test_duplicate_project_order_is_rejected(self):
        mutated = json.loads(json.dumps(self.data))
        mutated["projects"][1]["order"] = mutated["projects"][0]["order"]
        with self.assertRaises(ValueError):
            build_site.validate(mutated)


if __name__ == "__main__":
    unittest.main()
