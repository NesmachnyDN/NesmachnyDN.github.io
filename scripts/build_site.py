#!/usr/bin/env python3
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

UI = {
    "en": {
        "lang": "en", "locale": "en_US", "skip": "Skip to content", "nav_selected": "Selected", "nav_all": "All work", "nav_focus": "Focus", "nav_contact": "Contact",
        "portfolio": "Enterprise architecture portfolio", "view": "View selected work", "overview": "Portfolio overview", "cases": "public cases", "selected_works": "selected works", "tracks": "architecture tracks", "core": "Core expertise",
        "selected": "Selected work", "selected_title": "Architecture translated into implementation-ready decisions.", "selected_lead": "A curated set of public cases with repository-owned presentation covers. Detailed architecture artifacts remain evidence inside the underlying repositories rather than being forced into thumbnail previews.",
        "all": "Full portfolio", "all_title": "Compact index by architecture track", "all_lead": "Selected work above provides the narrative view; this index is optimized for fast scanning across all public cases.", "track": "Portfolio track",
        "discipline": "Architecture discipline", "focus_title": "What I optimize for", "focus_lead": "Architecture that explains trade-offs, preserves traceability, makes boundaries explicit and gives delivery teams a credible path from baseline to target state.",
        "operating": "Operating model", "approach_title": "Architecture as an engineering discipline", "approach": "I work from business drivers and quality attributes through capability, application, integration and deployment decisions. The objective is not a diagram set; it is a coherent decision system that can be reviewed, implemented and evolved.", "note": "The repositories presented here are curated public portfolio artifacts and use generalized, synthetic or sanitized independently authored material where appropriate.",
        "contact": "Contact", "links": "Professional links", "explore": "Explore case", "badge": "Selected work", "footer": "Portfolio generated from repository-owned data.", "aria_nav": "Primary navigation", "aria_top": "Back to top", "aria_overview": "Profile and portfolio overview", "aria_open": "Open"
    },
    "ru": {
        "lang": "ru", "locale": "ru_RU", "skip": "Перейти к содержимому", "nav_selected": "Избранное", "nav_all": "Все проекты", "nav_focus": "Фокус", "nav_contact": "Контакты",
        "portfolio": "Портфолио корпоративного архитектора", "view": "Смотреть избранные проекты", "overview": "Кратко о портфолио", "cases": "публичных кейсов", "selected_works": "избранных проектов", "tracks": "направлений архитектуры", "core": "Ключевая экспертиза",
        "selected": "Избранные проекты", "selected_title": "Архитектура, доведённая до решений, готовых к реализации.", "selected_lead": "Подборка публичных кейсов с отдельными презентационными обложками. Детальные архитектурные артефакты остаются доказательной базой внутри соответствующих репозиториев и не уменьшаются до нечитаемых превью.",
        "all": "Полное портфолио", "all_title": "Компактный индекс по архитектурным направлениям", "all_lead": "Избранные проекты выше дают контекст и основные кейсы; этот раздел предназначен для быстрого просмотра всех публичных работ.", "track": "Направление портфолио",
        "discipline": "Архитектурная практика", "focus_title": "На что я ориентирую архитектурные решения", "focus_lead": "Архитектура должна объяснять компромиссы, сохранять трассируемость, явно фиксировать границы и давать командам реалистичный путь от текущего состояния к целевому.",
        "operating": "Подход к работе", "approach_title": "Архитектура как инженерная дисциплина", "approach": "Работаю от бизнес-драйверов и атрибутов качества к решениям по бизнес-возможностям, приложениям, интеграции и развёртыванию. Цель — не набор диаграмм, а согласованная система решений, которую можно проверить, реализовать и развивать.", "note": "Публичные репозитории содержат специально подготовленные материалы портфолио: обобщённые, синтетические или санитизированные артефакты без закрытой информации работодателей и заказчиков.",
        "contact": "Контакты", "links": "Профессиональные профили", "explore": "Открыть кейс", "badge": "Избранный проект", "footer": "Портфолио автоматически формируется из данных репозитория.", "aria_nav": "Основная навигация", "aria_top": "Наверх", "aria_overview": "Профиль и краткая информация о портфолио", "aria_open": "Открыть"
    }
}


def fail(message: str) -> None:
    raise ValueError(message)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def slug(value: str) -> str:
    return "-".join(value.lower().replace("&", "and").replace("/", " ").split())


def validate_url(value: str, field: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        fail(f"{field} must be an absolute HTTPS URL")


def validate_local_asset(value: str, field: str) -> None:
    if not value.startswith("./assets/") or ".." in value or not (ROOT / "site" / value.removeprefix("./")).is_file():
        fail(f"{field} must reference an existing ./assets/ file")


def validate(data: dict) -> None:
    profile = data.get("profile", {})
    for field in ("name", "headline", "summary", "email", "github", "linkedin", "avatar", "ru"):
        if field not in profile:
            fail(f"profile.{field} is required")
    for field in ("github", "linkedin", "avatar"):
        validate_url(profile[field], f"profile.{field}")
    for field in ("name", "headline", "summary"):
        if not profile["ru"].get(field):
            fail(f"profile.ru.{field} is required")
    focus = data.get("focus", [])
    if not focus or set(data.get("focus_details", {})) != set(focus) or set(data.get("focus_ru", {})) != set(focus):
        fail("focus localization must exactly match focus values")
    if len(data.get("core", [])) != len(data.get("core_ru", [])):
        fail("core_ru must match core length")
    projects = data.get("projects", [])
    if not projects:
        fail("projects must be non-empty")
    orders: set[int] = set()
    leads = 0
    for index, project in enumerate(projects):
        for field in ("title", "url", "category", "featured", "order", "summary", "tags", "ru"):
            if field not in project:
                fail(f"projects[{index}].{field} is required")
        if project["order"] in orders:
            fail("project order values must be unique")
        orders.add(project["order"])
        validate_url(project["url"], f"projects[{index}].url")
        for field in ("title", "category", "summary", "tags"):
            if not project["ru"].get(field):
                fail(f"projects[{index}].ru.{field} is required")
        if project.get("lead"):
            leads += 1
            if not project["featured"]:
                fail("lead project must be featured")
        if project["featured"]:
            if not project.get("cover") or not project.get("cover_alt") or not project["ru"].get("cover_alt"):
                fail("featured projects require localized cover metadata")
            validate_local_asset(project["cover"], f"projects[{index}].cover")
        for evidence in project.get("evidence", []):
            validate_url(evidence["url"], "evidence.url")
    if leads > 1:
        fail("at most one project may be lead")


def localized_profile(data: dict, locale: str) -> dict:
    profile = dict(data["profile"])
    if locale == "ru":
        profile.update(profile["ru"])
    return profile


def localized_project(project: dict, locale: str) -> dict:
    result = dict(project)
    if locale == "ru":
        result.update(project["ru"])
    return result


def render_tags(tags: list[str]) -> str:
    return "".join(f'<span class="tag">{esc(tag)}</span>' for tag in tags)


def render_card(project: dict, ui: dict, asset_prefix: str) -> str:
    classes = ["project-card", "featured-card"]
    if project.get("lead"):
        classes.append("featured-lead")
    cover = project["cover"].replace("./", asset_prefix, 1)
    return (
        f'<article class="{" ".join(classes)}"><a class="project-cover" href="{esc(project["url"])}" aria-label="{ui["aria_open"]} {esc(project["title"])}">'
        f'<img src="{esc(cover)}" alt="{esc(project["cover_alt"])}" loading="lazy" decoding="async"></a><div class="project-card-body">'
        f'<div class="project-meta"><span>{esc(project["category"])}</span><span class="featured">{ui["badge"]}</span></div>'
        f'<h3><a href="{esc(project["url"])}">{esc(project["title"])}</a></h3><p>{esc(project["summary"])}</p><div class="tags">{render_tags(project["tags"])}</div>'
        f'<a class="project-link" href="{esc(project["url"])}">{ui["explore"]} <span aria-hidden="true">↗</span></a></div></article>'
    )


def render_catalog(project: dict, ui: dict) -> str:
    return f'<article class="catalog-item"><div><p class="catalog-category">{esc(project["category"])}</p><h3><a href="{esc(project["url"])}">{esc(project["title"])}</a></h3></div><p>{esc(project["summary"])}</p><a class="catalog-link" href="{esc(project["url"])}">GitHub ↗</a></article>'


def build_html(data: dict, locale: str = "ru") -> str:
    ui = UI[locale]
    profile = localized_profile(data, locale)
    projects = [localized_project(p, locale) for p in sorted(data["projects"], key=lambda p: p["order"])]
    featured = [p for p in projects if p["featured"]]
    asset_prefix = "./" if locale == "ru" else "../"
    page_url = SITE_URL if locale == "ru" else SITE_URL + "en/"
    alt_url = SITE_URL + "en/" if locale == "ru" else SITE_URL
    alt_label = "EN" if locale == "ru" else "RU"
    categories = list(dict.fromkeys(p["category"] for p in projects))
    cat_nav = "".join(f'<a href="#category-{i}">{esc(c)}</a>' for i, c in enumerate(categories, 1))
    cards = "\n".join(render_card(p, ui, asset_prefix) for p in featured)
    sections = []
    for i, category in enumerate(categories, 1):
        items = "\n".join(render_catalog(p, ui) for p in projects if p["category"] == category)
        sections.append(f'<section class="portfolio-section" id="category-{i}"><div class="catalog-heading"><p class="eyebrow">{ui["track"]}</p><h2>{esc(category)}</h2></div><div class="catalog-list">{items}</div></section>')
    if locale == "ru":
        focus_items = "".join(f'<li><span class="focus-index">0{i}</span><strong class="focus-title">{esc(data["focus_ru"][key]["title"])}</strong><p class="focus-detail">{esc(data["focus_ru"][key]["detail"])}</p></li>' for i, key in enumerate(data["focus"], 1))
        core = data["core_ru"]
    else:
        focus_items = "".join(f'<li><span class="focus-index">0{i}</span><strong class="focus-title">{esc(key)}</strong><p class="focus-detail">{esc(data["focus_details"][key])}</p></li>' for i, key in enumerate(data["focus"], 1))
        core = data["core"]
    structured = {"@context":"https://schema.org","@type":"Person","name":profile["name"],"jobTitle":profile["headline"],"description":profile["summary"],"url":page_url,"image":data["profile"]["avatar"],"sameAs":[data["profile"]["github"],data["profile"]["linkedin"]],"knowsAbout":core}
    return f'''<!doctype html><html lang="{ui['lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b1020"><title>{esc(profile['name'])} — {esc(profile['headline'])}</title><meta name="description" content="{esc(profile['summary'])}"><meta property="og:type" content="website"><meta property="og:locale" content="{ui['locale']}"><meta property="og:url" content="{page_url}"><meta property="og:title" content="{esc(profile['name'])} — {esc(profile['headline'])}"><meta property="og:description" content="{esc(profile['summary'])}"><meta property="og:image" content="{esc(data['profile']['avatar'])}"><link rel="canonical" href="{page_url}"><link rel="alternate" hreflang="ru" href="{SITE_URL}"><link rel="alternate" hreflang="en" href="{SITE_URL}en/"><link rel="alternate" hreflang="x-default" href="{SITE_URL}"><link rel="stylesheet" href="{asset_prefix}style.css"><link rel="stylesheet" href="{asset_prefix}evidence.css"><script type="application/ld+json">{json.dumps(structured,ensure_ascii=False).replace('</','<\\/')}</script></head><body><a class="skip-link" href="#content">{ui['skip']}</a><header class="site-header"><a class="brand" href="#top" aria-label="{ui['aria_top']}">DN</a><div class="header-actions"><nav aria-label="{ui['aria_nav']}"><a href="#selected">{ui['nav_selected']}</a><a href="#work">{ui['nav_all']}</a><a href="#focus">{ui['nav_focus']}</a><a href="#contact">{ui['nav_contact']}</a></nav><a class="language-switch" href="{alt_url}" hreflang="{'en' if locale=='ru' else 'ru'}" aria-label="{'English version' if locale=='ru' else 'Русская версия'}">{alt_label}</a></div></header><main id="content"><section class="hero" id="top"><div class="hero-copy"><p class="eyebrow">{ui['portfolio']}</p><h1>{esc(profile['name'])}</h1><p class="headline">{esc(profile['headline'])}</p><p class="hero-summary">{esc(profile['summary'])}</p><div class="actions"><a class="button primary" href="#selected">{ui['view']}</a><a class="button" href="{esc(data['profile']['linkedin'])}">LinkedIn ↗</a><a class="button" href="{esc(data['profile']['github'])}">GitHub ↗</a></div></div><aside class="hero-panel" aria-label="{ui['aria_overview']}"><div class="portrait-row"><img class="portrait" src="{esc(data['profile']['avatar'])}" alt="{esc(profile['name'])}" width="96" height="96"><div><p class="eyebrow">{ui['overview']}</p><strong class="portrait-name">{esc(profile['name'])}</strong><span class="portrait-role">{esc(profile['headline'])}</span></div></div><div class="metrics"><div><strong>{len(projects)}</strong><span>{ui['cases']}</span></div><div><strong>{len(featured)}</strong><span>{ui['selected_works']}</span></div><div><strong>{len(data['focus'])}</strong><span>{ui['tracks']}</span></div></div><div class="hero-rule"></div><p class="panel-label">{ui['core']}</p><div class="tags large">{render_tags(core)}</div></aside></section><section class="selected-section" id="selected"><div class="selected-intro"><div class="section-heading"><p class="eyebrow">{ui['selected']}</p><h2>{ui['selected_title']}</h2></div><p class="section-lead">{ui['selected_lead']}</p></div><div class="featured-grid">{cards}</div></section><section class="work-index" id="work"><div><p class="eyebrow">{ui['all']}</p><h2>{ui['all_title']}</h2><p class="section-lead">{ui['all_lead']}</p></div><div class="track-links">{cat_nav}</div></section>{''.join(sections)}<section class="focus-section" id="focus"><div class="section-heading"><p class="eyebrow">{ui['discipline']}</p><h2>{ui['focus_title']}</h2><p class="section-lead">{ui['focus_lead']}</p></div><ul class="focus-grid">{focus_items}</ul></section><section class="approach-section"><div class="section-heading"><p class="eyebrow">{ui['operating']}</p><h2>{ui['approach_title']}</h2></div><div class="approach-grid"><p>{ui['approach']}</p><p class="muted">{ui['note']}</p></div></section><section class="contact-section" id="contact"><div><p class="eyebrow">{ui['contact']}</p><h2>{ui['links']}</h2></div><div class="contact-links"><a href="mailto:{esc(data['profile']['email'])}">{esc(data['profile']['email'])}</a><a href="{esc(data['profile']['linkedin'])}">LinkedIn ↗</a><a href="{esc(data['profile']['github'])}">GitHub ↗</a></div></section></main><footer><span>© {esc(profile['name'])}</span><span>{ui['footer']}</span></footer></body></html>'''


def main() -> None:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    validate(data)
    if OUTPUT_DIR.exists(): shutil.rmtree(OUTPUT_DIR)
    (OUTPUT_DIR / "en").mkdir(parents=True)
    (OUTPUT_DIR / "index.html").write_text(build_html(data, "ru"), encoding="utf-8")
    (OUTPUT_DIR / "en" / "index.html").write_text(build_html(data, "en"), encoding="utf-8")
    shutil.copy2(STYLE_FILE, OUTPUT_DIR / "style.css")
    shutil.copy2(EVIDENCE_STYLE_FILE, OUTPUT_DIR / "evidence.css")
    shutil.copytree(ASSET_DIR, OUTPUT_DIR / "assets")
    (OUTPUT_DIR / ".nojekyll").write_text("", encoding="utf-8")
    (OUTPUT_DIR / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    (OUTPUT_DIR / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE_URL}</loc></url><url><loc>{SITE_URL}en/</loc></url></urlset>', encoding="utf-8")
    print("Built RU default and EN alternate portfolio pages")

if __name__ == "__main__": main()
