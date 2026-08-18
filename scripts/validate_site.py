#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"


class Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.title_seen = False
        self.description_seen = False
        self.lang = ""

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "html": self.lang = values.get("lang", "") or ""
        if values.get("id"): self.ids.add(values["id"] or "")
        if tag in {"a", "link"} and values.get("href"): self.links.append(values["href"] or "")
        if tag == "img" and values.get("src"): self.links.append(values["src"] or "")
        if tag == "meta" and values.get("name") == "description" and values.get("content"): self.description_seen = True
        if tag == "title": self.title_seen = True


def validate_page(path: Path, expected_lang: str) -> tuple[int, int]:
    parser = Collector()
    text = path.read_text(encoding="utf-8")
    parser.feed(text)
    failures: list[str] = []
    if not parser.title_seen: failures.append(f"{path}: missing title")
    if not parser.description_seen: failures.append(f"{path}: missing description")
    if parser.lang != expected_lang: failures.append(f"{path}: expected lang={expected_lang}")
    for link in parser.links:
        if link.startswith("#"):
            if link[1:] and link[1:] not in parser.ids: failures.append(f"{path}: missing anchor {link}")
            continue
        parsed = urlparse(link)
        if parsed.scheme in {"https", "mailto"}: continue
        if parsed.scheme:
            failures.append(f"{path}: unsupported scheme {link}")
            continue
        target = (path.parent / parsed.path).resolve()
        if parsed.path.endswith("/"): target = target / "index.html"
        if parsed.path and not target.exists(): failures.append(f"{path}: missing local target {link}")
    for token in ("localhost", "127.0.0.1", "http://"):
        if token in text: failures.append(f"{path}: forbidden marker {token}")
    if failures: raise SystemExit("\n".join(failures))
    return len(parser.links), len(parser.ids)


def main() -> None:
    required = [SITE / "index.html", SITE / "en" / "index.html", SITE / "style.css", SITE / "evidence.css", SITE / ".nojekyll", SITE / "robots.txt", SITE / "sitemap.xml"]
    missing = [str(p.relative_to(SITE)) for p in required if not p.exists()]
    if missing: raise SystemExit(f"Missing generated files: {missing}")
    ru = validate_page(SITE / "index.html", "ru")
    en = validate_page(SITE / "en" / "index.html", "en")
    sitemap = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    if "https://nesmachnydn.github.io/en/" not in sitemap: raise SystemExit("sitemap is missing English page")
    print(f"Validated RU {ru[0]} links/{ru[1]} anchors and EN {en[0]} links/{en[1]} anchors")

if __name__ == "__main__": main()
