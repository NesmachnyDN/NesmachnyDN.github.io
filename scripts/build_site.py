#!/usr/bin/env python3
"""Build the static GitHub Pages portfolio from repository-owned data."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "portfolio.json"
STYLE_FILE = ROOT / "site" / "style.css"
OUTPUT_DIR = ROOT / "_site"
SITE_URL = "https://nesmachnydn.github.io/"


def fail(message: str) -> None:
    raise ValueError(message)


def validate_url(value: str, field: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{field} must be an absolute HTTPS URL: {value!r}")


def validate(data: dict) -> None:
    required_profile = {"name", "headline", "summary", "location", "email", "github", "linkedin"}
    profile = data.get("profile")
    if not isinstance(profile, dict):
        fail("profile must be an object")
    missing = required_profile - profile.keys()
    if missing:
        fail(f"profile is missing required fields: {sorted(missing)}")

    validate_url(profile["github"], "profile.github")
    validate_url(profile["linkedin"], "profile.linkedin")

    for list_name in ("focus", "core"):
        values = data.get(list_name)
        if not isinstance(values, list) or not values or not all(isinstance(v, str) and v.strip() for v in values):
            fail(f"{list_name} must be a non-empty list of strings")
        if len(values) != len(set(values)):
            fail(f"{list_name} contains duplicates")

    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        fail("projects must be a non-empty list")

    required_project = {"title", "url", "category", "featured", "order", "summary", "tags"}
    titles: set[str] = set()
    orders: set[int] = set()
    for index, project in enumerate(projects):
        if not isinstance(project, dict):
            fail(f"projects[{index}] must be an object")
        missing = required_project - project.keys()
        if missing:
            fail(f"projects[{index}] is missing required fields: {sorted(missing)}")
        if not isinstance(project["title"], str) or not project["title"].strip():
            fail(f"projects[{index}].title must be a non-empty string")
        if project["title"] in titles:
            fail(f"duplicate project title: {project['title']}")
        titles.add(project["title"])
        validate_url(project["url"], f"projects[{index}].url")
        if not project["url"].startswith("https://github.com/NesmachnyDN/"):
            fail(f"projects[{index}].url must point to a NesmachnyDN GitHub repository")
        if not isinstance(project["category"], str) or not project["category"].strip():
            fail(f"projects[{index}].category must be a non-empty string")
        if not isinstance(project["featured"], bool):
            fail(f"projects[{index}].featured must be boolean")
        if not isinstance(project["order"], int):
            fail(f"projects[{index}].order must be integer")
        if project["order"] in orders:
            fail(f"duplicate project order: {project['order']}")
        orders.add(project["order"])
        if not isinstance(project["summary"], str) or len(project["summary"].strip()) < 40:
            fail(f"projects[{index}].summary is too short")
        tags = project["tags"]
        if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) and tag.strip() for tag in tags):
            fail(f"projects[{index}].tags must be a non-empty list of strings")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_tags(tags: list[str]) -> str:
    return "".join(f'<span class="tag">{esc(tag)}</span>' for tag in tags)


def render_card(project: dict) -> str:
    featured = '<span class="featured">Featured</span>' if project["featured"] else ""
    return f"""
      <article class="project-card">
        <div class="project-meta"><span>{esc(project['category'])}</span>{featured}</div>
        <h3><a href="{esc(project['url'])}">{esc(project['title'])}</a></h3>
        <p>{esc(project['summary'])}</p>
        <div class="tags">{render_tags(project['tags'])}</div>
        <a class="project-link" href="{esc(project['url'])}" aria-label="View {esc(project['title'])} on GitHub">View case →</a>
      </article>
    """


def build_html(data: dict) -> str:
    profile = data["profile"]
    projects = sorted(data["projects"], key=lambda item: item["order"])
    categories: list[str] = []
    for project in projects:
        if project["category"] not in categories:
            categories.append(project["category"])

    project_sections = []
    for category in categories:
        cards = "\n".join(render_card(project) for project in projects if project["category"] == category)
        section_id = "category-" + "-".join(category.lower().replace("&", "and").split())
        project_sections.append(
            f'<section class="portfolio-section" id="{esc(section_id)}"><div class="section-heading"><p class="eyebrow">Portfolio</p><h2>{esc(category)}</h2></div><div class="project-grid">{cards}</div></section>'
        )

    focus_items = "".join(f"<li>{esc(item)}</li>" for item in data["focus"])
    core_tags = render_tags(data["core"])
    structured = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile["name"],
        "jobTitle": profile["headline"],
        "url": SITE_URL,
        "sameAs": [profile["github"], profile["linkedin"]],
    }

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(profile['name'])} — {esc(profile['headline'])}</title>
  <meta name="description" content="{esc(profile['summary'])}">
  <meta name="author" content="{esc(profile['name'])}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE_URL}">
  <meta property="og:title" content="{esc(profile['name'])} — {esc(profile['headline'])}">
  <meta property="og:description" content="{esc(profile['summary'])}">
  <meta name="twitter:card" content="summary">
  <link rel="canonical" href="{SITE_URL}">
  <link rel="stylesheet" href="./style.css">
  <script type="application/ld+json">{json.dumps(structured, ensure_ascii=False).replace('</', '<\\/')}</script>
</head>
<body>
  <header class="site-header">
    <a class="brand" href="#top">DN</a>
    <nav aria-label="Primary navigation">
      <a href="#work">Work</a>
      <a href="#focus">Focus</a>
      <a href="#contact">Contact</a>
    </nav>
  </header>

  <main id="top">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Architecture portfolio</p>
        <h1>{esc(profile['name'])}</h1>
        <p class="headline">{esc(profile['headline'])}</p>
        <p class="hero-summary">{esc(profile['summary'])}</p>
        <div class="actions">
          <a class="button primary" href="#work">View architecture portfolio</a>
          <a class="button" href="{esc(profile['linkedin'])}">LinkedIn</a>
          <a class="button" href="{esc(profile['github'])}">GitHub</a>
        </div>
      </div>
      <aside class="hero-panel" aria-label="Core expertise">
        <p class="eyebrow">Core expertise</p>
        <div class="tags large">{core_tags}</div>
      </aside>
    </section>

    <div id="work">{''.join(project_sections)}</div>

    <section class="focus-section" id="focus">
      <div class="section-heading"><p class="eyebrow">Architecture discipline</p><h2>Architecture focus</h2></div>
      <ul class="focus-grid">{focus_items}</ul>
    </section>

    <section class="approach-section">
      <div class="section-heading"><p class="eyebrow">Operating model</p><h2>How I approach architecture</h2></div>
      <p>I treat architecture as an engineering discipline rather than a diagramming activity. A useful architecture should make boundaries explicit, explain trade-offs, preserve traceability to business drivers and requirements, constrain implementation where necessary, and provide a realistic path from baseline to target state.</p>
      <p class="muted">The repositories presented here are curated public portfolio artifacts and use generalized, synthetic or sanitized independently authored material where appropriate.</p>
    </section>

    <section class="contact-section" id="contact">
      <div><p class="eyebrow">Contact</p><h2>Professional links</h2></div>
      <div class="contact-links">
        <a href="mailto:{esc(profile['email'])}">{esc(profile['email'])}</a>
        <a href="{esc(profile['linkedin'])}">LinkedIn</a>
        <a href="{esc(profile['github'])}">GitHub</a>
      </div>
    </section>
  </main>

  <footer><span>© {esc(profile['name'])}</span><span>Generated from repository-owned portfolio data.</span></footer>
</body>
</html>
"""


def main() -> None:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    validate(data)
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    (OUTPUT_DIR / "index.html").write_text(build_html(data), encoding="utf-8")
    shutil.copy2(STYLE_FILE, OUTPUT_DIR / "style.css")
    (OUTPUT_DIR / ".nojekyll").write_text("", encoding="utf-8")
    (OUTPUT_DIR / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    (OUTPUT_DIR / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE_URL}</loc></url></urlset>\n',
        encoding="utf-8",
    )
    print(f"Built portfolio site in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
