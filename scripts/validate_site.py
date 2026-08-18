#!/usr/bin/env python3
"""Validate the generated static site without external dependencies."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.ids: set[str] = set()
        self.title_seen = False
        self.description_seen = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag == "a" and values.get("href"):
            self.links.append(("href", values["href"] or ""))
        if tag == "link" and values.get("href"):
            self.links.append(("href", values["href"] or ""))
        if tag == "meta" and values.get("name") == "description" and values.get("content"):
            self.description_seen = True
        if tag == "title":
            self.title_seen = True


def main() -> None:
    required = ["index.html", "style.css", ".nojekyll", "robots.txt", "sitemap.xml"]
    missing = [name for name in required if not (SITE / name).exists()]
    if missing:
        raise SystemExit(f"Missing generated files: {missing}")

    parser = LinkCollector()
    parser.feed((SITE / "index.html").read_text(encoding="utf-8"))
    if not parser.title_seen:
        raise SystemExit("index.html has no title element")
    if not parser.description_seen:
        raise SystemExit("index.html has no meta description")

    failures: list[str] = []
    for _, link in parser.links:
        if link.startswith("#"):
            anchor = link[1:]
            if anchor and anchor not in parser.ids:
                failures.append(f"Missing anchor target: {link}")
            continue
        parsed = urlparse(link)
        if parsed.scheme in {"https", "mailto"}:
            continue
        if parsed.scheme:
            failures.append(f"Unsupported link scheme: {link}")
            continue
        path = parsed.path[2:] if parsed.path.startswith("./") else parsed.path
        if path and not (SITE / path).exists():
            failures.append(f"Missing local target: {link}")

    if failures:
        raise SystemExit("\n".join(failures))

    html_text = (SITE / "index.html").read_text(encoding="utf-8")
    forbidden = ["localhost", "127.0.0.1", "http://"]
    found = [token for token in forbidden if token in html_text]
    if found:
        raise SystemExit(f"Generated site contains forbidden/internal URL markers: {found}")

    print(f"Validated {len(parser.links)} links and {len(parser.ids)} anchors")


if __name__ == "__main__":
    main()
