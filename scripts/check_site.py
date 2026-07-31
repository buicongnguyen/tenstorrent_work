#!/usr/bin/env python3
"""Validate the rendered MkDocs site, including paths, fragments, IDs, and images."""

from __future__ import annotations

import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = ROOT / "site"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.links: list[str] = []
        self.images: list[tuple[str, str | None]] = []
        self.h1_count = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ids.append(element_id)
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"] or "")
        if tag == "img":
            self.images.append((attributes.get("src") or "", attributes.get("alt")))
        if tag == "h1":
            self.h1_count += 1


def site_prefix() -> str:
    configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    match = re.search(r"^site_url:\s*(\S+)\s*$", configuration, flags=re.MULTILINE)
    if not match:
        raise RuntimeError("mkdocs.yml is missing site_url")
    path = urlparse(match.group(1)).path
    return f"/{path.strip('/')}/" if path.strip("/") else "/"


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def expected_output(markdown: Path) -> Path:
    relative = markdown.relative_to(DOCS)
    if relative.name == "index.md":
        return SITE / relative.parent / "index.html"
    return SITE / relative.with_suffix("") / "index.html"


def main() -> int:
    if not SITE.is_dir():
        print("Rendered-site validation failed: site/ does not exist; run mkdocs build first.")
        return 1

    errors: list[str] = []
    prefix = site_prefix()
    origin = "https://rendered-site.invalid"
    pages = {path.resolve(): parse_page(path) for path in SITE.rglob("*.html")}

    markdown_pages = sorted(DOCS.rglob("*.md"))
    for markdown in markdown_pages:
        output = expected_output(markdown)
        if not output.is_file():
            errors.append(
                f"{markdown.relative_to(ROOT)} has no rendered page at "
                f"{output.relative_to(ROOT)}"
            )

    for page_path, parser in list(pages.items()):
        relative = page_path.relative_to(SITE).as_posix()
        if relative.endswith("index.html"):
            route = relative[: -len("index.html")]
        else:
            route = relative
        source_url = f"{origin}{prefix}{route}"

        if parser.h1_count != 1:
            errors.append(f"site/{relative}: expected one h1, found {parser.h1_count}")

        for element_id, count in Counter(parser.ids).items():
            if count > 1:
                errors.append(f"site/{relative}: duplicate id {element_id!r} x{count}")

        for source, alt in parser.images:
            if alt is None or not alt.strip():
                errors.append(f"site/{relative}: image {source!r} has no alt text")
            parsed_source = urlparse(source)
            if parsed_source.scheme in {"http", "https", "data"}:
                continue
            target_url = urlparse(urljoin(source_url, source))
            if not target_url.path.startswith(prefix):
                errors.append(
                    f"site/{relative}: image escapes site prefix: {source!r}"
                )
                continue
            image_path = unquote(target_url.path[len(prefix) :])
            if not (SITE / image_path).is_file():
                errors.append(f"site/{relative}: missing image {source!r}")

        for href in parser.links:
            parsed_href = urlparse(href)
            if parsed_href.scheme in {"http", "https", "mailto", "javascript"}:
                continue

            target_url = urlparse(urljoin(source_url, href))
            if not target_url.path.startswith(prefix):
                errors.append(f"site/{relative}: internal link escapes site prefix: {href!r}")
                continue

            local_path = unquote(target_url.path[len(prefix) :])
            target = SITE / local_path
            if target_url.path.endswith("/"):
                target = target / "index.html"
            elif not target.suffix:
                target = target / "index.html"

            if not target.exists():
                errors.append(f"site/{relative}: missing target for {href!r}")
                continue

            if target_url.fragment and target.suffix == ".html":
                resolved = target.resolve()
                target_parser = pages.get(resolved)
                if target_parser is None:
                    target_parser = parse_page(target)
                    pages[resolved] = target_parser
                fragment = unquote(target_url.fragment)
                if fragment not in target_parser.ids:
                    errors.append(
                        f"site/{relative}: fragment {fragment!r} is missing in {href!r}"
                    )

    if errors:
        print("Rendered-site validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        "Rendered-site validation passed: "
        f"{len(markdown_pages)} Markdown pages, {len(pages)} HTML pages."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
