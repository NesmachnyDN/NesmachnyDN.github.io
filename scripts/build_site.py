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
EVIDENCE_STYLE_FILE = ROOT / "site" / "evidence.css"
ASSET_DIR = ROOT / "site" / "assets"
OUTPUT_DIR = ROOT / "_site"
SITE_URL = "https://nesmachnydn.github.io/"


def fail(message: str) -> None:
    raise ValueError(message)


def validate_url(value: str, field: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{field} must be an absolute HTTPS URL: {value!r}")


def validate_local_asset(value: str, field: str) -> None:
    if not value.startswith("./assets/") or ".." in value:
        fail(f"{field} must be a local ./assets/ path: {value!r}")
    source = ROOT / "site" / value.removeprefix("./")
    if not source.is_file():
        fail(f"{field} does not exist: {value!r}")


def validate(data: dict) -> None:
    required_profile = {"name", "headline", "summary", "location", "email", "github", "linkedin", "avatar"}
    profile = data.get("profile")
    if not isinstance(profile, dict):
        fail("profile must be an object")
    missing = required_profile - profile.keys()
    if missing:
        fail(f"profile is missing required fields: {sorted(missing)}")
    for field in ("github", "linkedin", "avatar"):
        validate_url(profile[field], f"profile.{field}")

    for list_name in ("focus", "core"):
        values = data.get(list_name)
        if not isinstance(values, list) or not values or not all(isinstance(v, str) and v.strip() for v in values):
            fail(f"{list_name} must be a non-empty list of strings")
        if len(values) != len(set(values)):
            fail(f"{list_name} contains duplicates")

    focus_details = data.get("focus_details")
    if not isinstance(focus_details, dict):
        fail("focus_details must be an object")
    if set(focus_details) != set(data["focus"]):
        fail("focus_details keys must exactly match focus values")
    if not all(isinstance(value, str) and len(value.strip()) >= 40 for value in focus_details.values()):
        fail("focus_details values must be descriptive strings")

    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        fail("projects must be a non-empty list")
    required = {"title", "url", "category", "featured", "order", "summary", "tags"}
    titles: set[str] = set()
    orders: set[int] = set()
    lead_count = 0
    for index, project in enumerate(projects):
        missing = required - project.keys()
        if missing:
            fail(f"projects[{index}] is missing required fields: {sorted(missing)}")
        if project["title"] in titles:
            fail(f"duplicate project title: {project['title']}")
        titles.add(project["title"])
        if project["order"] in orders:
            fail(f"duplicate project order: {project['order']}")
        orders.add(project["order"])
        validate_url(project["url"], f"projects[{index}].url")
        if not project["url"].startswith("https://github.com/NesmachnyDN/"):
            fail(f"projects[{index}].url must point to a NesmachnyDN GitHub repository")
        if not isinstance(project["featured"], bool) or not isinstance(project["order"], int):
            fail(f"projects[{index}] has invalid featured/order values")
        if not isinstance(project["summary"], str) or len(project["summary"].strip()) < 40:
            fail(f"projects[{index}].summary is too short")
        if not isinstance(project["tags"], list) or not project["tags"]:
            fail(f"projects[{index}].tags must be a non-empty list")
        if project.get("lead"):
            lead_count += 1
            if not project["featured"]:
                fail(f"projects[{index}].lead requires featured=true")
        if "cover" in project:
            validate_local_asset(project["cover"], f"projects[{index}].cover")
            if not project.get("cover_alt"):
                fail(f"projects[{index}].cover_alt is required when cover is set")
        if project["featured"] and not project.get("cover"):
            fail(f"projects[{index}] featured projects require a cover")
        evidence = project.get("evidence", [])
        if not isinstance(evidence, list):
            fail(f"projects[{index}].evidence must be a list")
        for evidence_index, item in enumerate(evidence):
            if not isinstance(item, dict) or not {"type", "url", "alt"} <= item.keys():
                fail(f"projects[{index}].evidence[{evidence_index}] must contain type, url and alt")
            validate_url(item["url"], f"projects[{index}].evidence[{evidence_index}].url")
    if lead_count > 1:
        fail("at most one project may be marked lead")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def slug(value: str) -> str:
    return "-".join(value.lower().replace("&", "and").replace("/", " ").split())


def render_tags(tags: list[str]) -> str:
    return "".join(f'<span class="tag">{esc(tag)}</span>' for tag in tags)


def render_card(project: dict, *, featured_card: bool = False) -> str:
    modifiers = ["project-card"]
    if featured_card:
        modifiers.append("featured-card")
    if project.get("lead"):
        modifiers.append("featured-lead")
    badge = '<span class="featured">Selected work</span>' if featured_card else ""
    cover = ""
    if featured_card and project.get("cover"):
        cover = (
            f'<a class="project-cover" href="{esc(project["url"])}" aria-label="Open {esc(project["title"])}">'
            f'<img src="{esc(project["cover"])}" alt="{esc(project["cover_alt"])}" loading="lazy" decoding="async"></a>'
        )
    return (
        f'<article class="{" ".join(modifiers)}">{cover}<div class="project-card-body">'
        f'<div class="project-meta"><span>{esc(project["category"])}</span>{badge}</div>'
        f'<h3><a href="{esc(project["url"])}">{esc(project["title"])}</a></h3>'
        f'<p>{esc(project["summary"])}</p><div class="tags">{render_tags(project["tags"])}</div>'
        f'<a class="project-link" href="{esc(project["url"])}" aria-label="Open {esc(project["title"])} on GitHub">Explore case <span aria-hidden="true">↗</span></a>'
        '</div></article>'
    )


def render_catalog_item(project: dict) -> str:
    return (
        '<article class="catalog-item">'
        f'<div><p class="catalog-category">{esc(project["category"])}</p>'
        f'<h3><a href="{esc(project["url"])}">{esc(project["title"])}</a></h3></div>'
        f'<p>{esc(project["summary"])}</p>'
        f'<a class="catalog-link" href="{esc(project["url"])}" aria-label="Open {esc(project["title"])} on GitHub">GitHub ↗</a>'
        '</article>'
    )


def build_html(data: dict) -> str:
    profile = data["profile"]
    projects = sorted(data["projects"], key=lambda item: item["order"])
    featured_projects = [p for p in projects if p["featured"]]
    categories = list(dict.fromkeys(p["category"] for p in projects))
    category_nav = "".join(f'<a href="#category-{slug(c)}">{esc(c)}</a>' for c in categories)
    featured_cards = "\n".join(render_card(p, featured_card=True) for p in featured_projects)

    sections = []
    for category in categories:
        items = "\n".join(render_catalog_item(p) for p in projects if p["category"] == category)
        sections.append(
            f'<section class="portfolio-section" id="category-{slug(category)}">'
            f'<div class="catalog-heading"><p class="eyebrow">Portfolio track</p><h2>{esc(category)}</h2></div>'
            f'<div class="catalog-list">{items}</div></section>'
        )

    focus_items = "".join(
        f'<li><span class="focus-index">0{i}</span><strong class="focus-title">{esc(item)}</strong>'
        f'<p class="focus-detail">{esc(data["focus_details"][item])}</p></li>'
        for i, item in enumerate(data["focus"], 1)
    )

    structured = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile["name"],
        "jobTitle": profile["headline"],
        "description": profile["summary"],
        "url": SITE_URL,
        "image": profile["avatar"],
        "sameAs": [profile["github"], profile["linkedin"]],
        "knowsAbout": data["core"] + data["focus"],
    }

    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#0b1020"><title>{esc(profile['name'])} — {esc(profile['headline'])}</title><meta name="description" content="{esc(profile['summary'])}"><meta name="author" content="{esc(profile['name'])}"><meta property="og:type" content="website"><meta property="og:url" content="{SITE_URL}"><meta property="og:title" content="{esc(profile['name'])} — {esc(profile['headline'])}"><meta property="og:description" content="{esc(profile['summary'])}"><meta property="og:image" content="{esc(profile['avatar'])}"><meta name="twitter:card" content="summary"><link rel="canonical" href="{SITE_URL}"><link rel="stylesheet" href="./style.css"><link rel="stylesheet" href="./evidence.css"><script type="application/ld+json">{json.dumps(structured, ensure_ascii=False).replace('</', '<\\/')}</script></head><body>
<a class="skip-link" href="#content">Skip to content</a><header class="site-header"><a class="brand" href="#top" aria-label="Back to top">DN</a><nav aria-label="Primary navigation"><a href="#selected">Selected</a><a href="#work">All work</a><a href="#focus">Focus</a><a href="#contact">Contact</a></nav></header><main id="content">
<section class="hero" id="top"><div class="hero-copy"><p class="eyebrow">Enterprise architecture portfolio</p><h1>{esc(profile['name'])}</h1><p class="headline">{esc(profile['headline'])}</p><p class="hero-summary">{esc(profile['summary'])}</p><div class="actions"><a class="button primary" href="#selected">View selected work</a><a class="button" href="{esc(profile['linkedin'])}">LinkedIn ↗</a><a class="button" href="{esc(profile['github'])}">GitHub ↗</a></div></div><aside class="hero-panel" aria-label="Profile and portfolio overview"><div class="portrait-row"><img class="portrait" src="{esc(profile['avatar'])}" alt="{esc(profile['name'])}" width="96" height="96"><div><p class="eyebrow">Portfolio overview</p><strong class="portrait-name">{esc(profile['name'])}</strong><span class="portrait-role">{esc(profile['headline'])}</span></div></div><div class="metrics"><div><strong>{len(projects)}</strong><span>public cases</span></div><div><strong>{len(featured_projects)}</strong><span>selected works</span></div><div><strong>{len(data['focus'])}</strong><span>architecture tracks</span></div></div><div class="hero-rule"></div><p class="panel-label">Core expertise</p><div class="tags large">{render_tags(data['core'])}</div></aside></section>
<section class="selected-section" id="selected"><div class="selected-intro"><div class="section-heading"><p class="eyebrow">Selected work</p><h2>Architecture translated into implementation-ready decisions.</h2></div><p class="section-lead">A curated set of public cases with repository-owned presentation covers. Detailed architecture artifacts remain evidence inside the underlying repositories rather than being forced into thumbnail previews.</p></div><div class="featured-grid">{featured_cards}</div></section>
<section class="work-index" id="work"><div><p class="eyebrow">Full portfolio</p><h2>Compact index by architecture track</h2><p class="section-lead">Selected work above provides the narrative view; this index is optimized for fast scanning across all public cases.</p></div><div class="track-links">{category_nav}</div></section>{''.join(sections)}
<section class="focus-section" id="focus"><div class="section-heading"><p class="eyebrow">Architecture discipline</p><h2>What I optimize for</h2><p class="section-lead">Architecture that explains trade-offs, preserves traceability, makes boundaries explicit and gives delivery teams a credible path from baseline to target state.</p></div><ul class="focus-grid">{focus_items}</ul></section>
<section class="approach-section"><div class="section-heading"><p class="eyebrow">Operating model</p><h2>Architecture as an engineering discipline</h2></div><div class="approach-grid"><p>I work from business drivers and quality attributes through capability, application, integration and deployment decisions. The objective is not a diagram set; it is a coherent decision system that can be reviewed, implemented and evolved.</p><p class="muted">The repositories presented here are curated public portfolio artifacts and use generalized, synthetic or sanitized independently authored material where appropriate.</p></div></section>
<section class="contact-section" id="contact"><div><p class="eyebrow">Contact</p><h2>Professional links</h2></div><div class="contact-links"><a href="mailto:{esc(profile['email'])}">{esc(profile['email'])}</a><a href="{esc(profile['linkedin'])}">LinkedIn ↗</a><a href="{esc(profile['github'])}">GitHub ↗</a></div></section></main><footer><span>© {esc(profile['name'])}</span><span>Portfolio generated from repository-owned data.</span></footer></body></html>'''


def main() -> None:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    validate(data)
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    (OUTPUT_DIR / "index.html").write_text(build_html(data), encoding="utf-8")
    shutil.copy2(STYLE_FILE, OUTPUT_DIR / "style.css")
    shutil.copy2(EVIDENCE_STYLE_FILE, OUTPUT_DIR / "evidence.css")
    shutil.copytree(ASSET_DIR, OUTPUT_DIR / "assets")
    (OUTPUT_DIR / ".nojekyll").write_text("", encoding="utf-8")
    (OUTPUT_DIR / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    (OUTPUT_DIR / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE_URL}</loc></url></urlset>\n', encoding="utf-8")
    print(f"Built portfolio site in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
