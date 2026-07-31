#!/usr/bin/env python3
"""Validate provenance, rewrite mapping, and local Markdown links."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
UPSTREAM = ROOT / "upstream" / "tt-metal" / "tech_reports"
EXPECTED_COMMIT = "992f3ca634aac8733c70e48da395aab5361b4166"
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def markdown_files(path: Path) -> list[Path]:
    return sorted(path.rglob("*.md"), key=lambda item: item.as_posix().lower())


def check_upstream(errors: list[str]) -> None:
    reports = markdown_files(UPSTREAM)
    if len(reports) != 57:
        errors.append(f"expected 57 upstream reports, found {len(reports)}")

    provenance = (ROOT / "upstream" / "UPSTREAM.md").read_text(encoding="utf-8")
    if EXPECTED_COMMIT not in provenance:
        errors.append("UPSTREAM.md does not contain the expected full commit")


def check_rewrite_sources(errors: list[str]) -> None:
    rewrite_root = DOCS / "rewrites"
    for rewrite in markdown_files(rewrite_root):
        relative = rewrite.relative_to(rewrite_root)
        source = UPSTREAM / relative
        if not source.is_file():
            errors.append(f"{rewrite.relative_to(ROOT)} has no one-to-one upstream source")
            continue

        expected_url = (
            "https://github.com/tenstorrent/tt-metal/blob/"
            f"{EXPECTED_COMMIT}/tech_reports/{relative.as_posix()}"
        )
        content = rewrite.read_text(encoding="utf-8")
        if expected_url not in content:
            errors.append(
                f"{rewrite.relative_to(ROOT)}: missing commit-pinned original source link"
            )


def check_links(errors: list[str]) -> None:
    for page in markdown_files(DOCS):
        content = page.read_text(encoding="utf-8")
        for raw_target in LINK_RE.findall(content):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue

            path_part = unquote(target.split("#", 1)[0])
            if not path_part:
                continue

            candidate = (page.parent / path_part).resolve()
            if candidate.is_dir():
                candidate = candidate / "index.md"
            if not candidate.exists():
                errors.append(
                    f"{page.relative_to(ROOT)}: broken local link {raw_target!r}"
                )


def check_required_sections(errors: list[str]) -> None:
    required = ("## Code connection", "## Verify your understanding", "## Source and delta")
    for rewrite in markdown_files(DOCS / "rewrites"):
        content = rewrite.read_text(encoding="utf-8")
        for heading in required:
            if heading not in content:
                errors.append(f"{rewrite.relative_to(ROOT)}: missing {heading!r}")


def check_diagrams(errors: list[str]) -> None:
    source_dir = ROOT / "diagram_sources"
    asset_dir = DOCS / "assets" / "diagrams"
    sources = sorted(source_dir.glob("*.mmd"))
    assets = sorted(asset_dir.glob("*.svg"))

    if len(sources) != 14 or len(assets) != 14:
        errors.append(
            f"expected 14 diagram sources and assets, found {len(sources)} and {len(assets)}"
        )

    for source in sources:
        if not (asset_dir / f"{source.stem}.svg").is_file():
            errors.append(f"missing rendered diagram for {source.relative_to(ROOT)}")

    for page in markdown_files(DOCS):
        if "```mermaid" in page.read_text(encoding="utf-8"):
            errors.append(f"{page.relative_to(ROOT)}: runtime Mermaid fence is not allowed")


def main() -> int:
    errors: list[str] = []
    check_upstream(errors)
    check_rewrite_sources(errors)
    check_links(errors)
    check_required_sections(errors)
    check_diagrams(errors)

    if errors:
        print("Documentation validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        "Documentation validation passed: "
        f"{len(markdown_files(UPSTREAM))} upstream reports, "
        f"{len(markdown_files(DOCS / 'rewrites'))} learner rewrite."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
