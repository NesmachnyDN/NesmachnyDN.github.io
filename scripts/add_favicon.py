#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
FAVICON = ROOT / "site" / "assets" / "favicon.svg"


def inject_favicon(page: Path, href: str) -> None:
    html = page.read_text(encoding="utf-8")
    marker = "</head>"
    if marker not in html:
        raise ValueError(f"Missing </head> in {page}")
    if 'rel="icon"' in html:
        return
    link = f'<link rel="icon" type="image/svg+xml" href="{href}">'
    page.write_text(html.replace(marker, link + marker, 1), encoding="utf-8")


def main() -> None:
    if not FAVICON.is_file():
        raise SystemExit(f"Missing favicon asset: {FAVICON}")
    pages = [
        (SITE / "index.html", "./assets/favicon.svg"),
        (SITE / "en" / "index.html", "../assets/favicon.svg"),
    ]
    for page, href in pages:
        if not page.is_file():
            raise SystemExit(f"Missing generated page: {page}")
        inject_favicon(page, href)
    print("Injected architecture favicon into RU and EN pages")


if __name__ == "__main__":
    main()
