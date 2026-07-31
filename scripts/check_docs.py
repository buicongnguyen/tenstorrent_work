#!/usr/bin/env python3
"""Validate provenance, rewrite mapping, and local Markdown links."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

from report_layers import LAYERS, report_paths


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
UPSTREAM = ROOT / "upstream" / "tt-metal" / "tech_reports"
EXPECTED_COMMIT = "992f3ca634aac8733c70e48da395aab5361b4166"
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
STATUS_RE = re.compile(r"<!--\s*rewrite-status:\s*([a-z-]+)\s*-->")
ALLOWED_STATUSES = {"seed", "improved-draft", "improved", "review-needed"}


def markdown_files(path: Path) -> list[Path]:
    return sorted(path.rglob("*.md"), key=lambda item: item.as_posix().lower())


def check_upstream(errors: list[str]) -> None:
    reports = markdown_files(UPSTREAM)
    if len(reports) != 57:
        errors.append(f"expected 57 upstream reports, found {len(reports)}")

    provenance = (ROOT / "upstream" / "UPSTREAM.md").read_text(encoding="utf-8")
    if EXPECTED_COMMIT not in provenance:
        errors.append("UPSTREAM.md does not contain the expected full commit")


def check_report_layers(errors: list[str]) -> None:
    upstream_paths = {
        path.relative_to(UPSTREAM).as_posix() for path in markdown_files(UPSTREAM)
    }
    ordered_paths = report_paths()
    duplicates = sorted({path for path in ordered_paths if ordered_paths.count(path) > 1})
    if duplicates:
        errors.append(f"report layer map contains duplicates: {duplicates}")

    missing = sorted(upstream_paths - set(ordered_paths))
    unknown = sorted(set(ordered_paths) - upstream_paths)
    if missing:
        errors.append(f"report layer map is missing: {missing}")
    if unknown:
        errors.append(f"report layer map contains unknown paths: {unknown}")

    navigation = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    for path in ordered_paths:
        rewrite_path = f"rewrites/{path}"
        if rewrite_path not in navigation:
            errors.append(f"sidebar navigation is missing {rewrite_path}")

    catalog = (DOCS / "reference" / "report-catalog.md").read_text(encoding="utf-8")
    for layer in LAYERS:
        anchor = f"#level-{layer['number']}-{layer['slug']}"
        if anchor not in catalog:
            errors.append(f"report catalog is missing layer anchor {anchor}")


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
        status = STATUS_RE.search(content)
        if not status:
            errors.append(f"{rewrite.relative_to(ROOT)}: missing rewrite-status marker")
        elif status.group(1) not in ALLOWED_STATUSES:
            errors.append(
                f"{rewrite.relative_to(ROOT)}: invalid rewrite status {status.group(1)!r}"
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

    if len(sources) < 14 or len(assets) != len(sources):
        errors.append(
            "expected one rendered asset per diagram source and at least 14 diagrams, "
            f"found {len(sources)} sources and {len(assets)} assets"
        )

    for source in sources:
        if not (asset_dir / f"{source.stem}.svg").is_file():
            errors.append(f"missing rendered diagram for {source.relative_to(ROOT)}")

    for page in markdown_files(DOCS):
        content = page.read_text(encoding="utf-8")
        if "```mermaid" in content:
            errors.append(f"{page.relative_to(ROOT)}: runtime Mermaid fence is not allowed")
        diagram_count = content.count("{ .atlas-diagram }")
        full_size_count = content.count("[Open full-size diagram]")
        if diagram_count != full_size_count:
            errors.append(
                f"{page.relative_to(ROOT)}: {diagram_count} diagrams but "
                f"{full_size_count} full-size links"
            )


def check_corsix_workbook(errors: list[str]) -> None:
    series = (DOCS / "resources" / "corsix-wormhole-series.md").read_text(
        encoding="utf-8"
    )
    workbook = (DOCS / "resources" / "corsix-reading-workbook.md").read_text(
        encoding="utf-8"
    )
    navigation = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    for part in range(1, 8):
        source_url = f"https://www.corsix.org/content/tt-wh-part{part}"
        if source_url not in series:
            errors.append(f"Corsix series map is missing Part {part} original link")
        if source_url not in workbook:
            errors.append(f"Corsix workbook is missing Part {part} original link")
        if f"## Part {part} —" not in workbook:
            errors.append(f"Corsix workbook is missing Part {part} section")

    if workbook.count("### Questions while reading") != 7:
        errors.append("Corsix workbook must contain one question section per part")
    if workbook.count("### Verify after reading") != 7:
        errors.append("Corsix workbook must contain one verification section per part")
    if "resources/corsix-reading-workbook.md" not in navigation:
        errors.append("sidebar navigation is missing the Corsix reading workbook")


def check_deepwiki_optimization(errors: list[str]) -> None:
    guide = (DOCS / "resources" / "deepwiki-research-guide.md").read_text(
        encoding="utf-8"
    )
    track = (DOCS / "start" / "optimization-path.md").read_text(encoding="utf-8")
    advanced = (
        DOCS
        / "rewrites"
        / "AdvancedPerformanceOptimizationsForModels"
        / "AdvancedPerformanceOptimizationsForModels.md"
    ).read_text(encoding="utf-8")
    navigation = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    deepwiki_urls = (
        "https://deepwiki.com/tenstorrent/tt-metal",
        "https://deepwiki.com/tenstorrent/tt-metal/2.5-fast-dispatch-and-command-queue-system",
        "https://deepwiki.com/tenstorrent/tt-metal/4.10-program-configuration-and-optimization",
        "https://deepwiki.com/tenstorrent/tt-metal/7.4-performance-optimization-techniques",
        "https://deepwiki.com/tenstorrent/tt-metal/8.4-profiling-and-performance-analysis",
        "https://deepwiki.com/tenstorrent/tt-metal/3-low-level-kernel-apis-%28llk%29",
    )
    for url in deepwiki_urls:
        if url not in guide:
            errors.append(f"DeepWiki research guide is missing original link {url}")

    for marker in ("96d1d1", "page's own", "## Evidence labels for notes"):
        if marker not in guide:
            errors.append(f"DeepWiki research guide is missing {marker!r}")

    track_topics = (
        "Program cache",
        "Fast Dispatch",
        "Metal Trace",
        "Multiple command queues",
        "Transfer the lessons to another NPU",
        "Interview drill",
    )
    for topic in track_topics:
        if topic.lower() not in track.lower():
            errors.append(f"optimization track is missing {topic!r}")

    if "<!-- rewrite-status: improved-draft -->" not in advanced:
        errors.append("advanced optimization learner page was not promoted")
    for topic in ("### Command prefetch is not tensor prefetch", "## Optimization diagnosis lab"):
        if topic not in advanced:
            errors.append(f"advanced optimization learner page is missing {topic!r}")

    for nav_path in (
        "start/optimization-path.md",
        "resources/deepwiki-research-guide.md",
    ):
        if nav_path not in navigation:
            errors.append(f"sidebar navigation is missing {nav_path}")


def check_status_summary(errors: list[str]) -> None:
    counts: dict[str, int] = {}
    for rewrite in markdown_files(DOCS / "rewrites"):
        match = STATUS_RE.search(rewrite.read_text(encoding="utf-8"))
        if match:
            counts[match.group(1)] = counts.get(match.group(1), 0) + 1

    roadmap = (DOCS / "reference" / "rewrite-roadmap.md").read_text(
        encoding="utf-8"
    )
    for status in ("improved-draft", "seed"):
        expected_row = f"| `{status}` | {counts.get(status, 0)} |"
        if expected_row not in roadmap:
            errors.append(
                f"rewrite roadmap status summary is stale for {status!r}: "
                f"expected row starting {expected_row!r}"
            )


def main() -> int:
    errors: list[str] = []
    check_upstream(errors)
    check_report_layers(errors)
    check_rewrite_sources(errors)
    check_links(errors)
    check_required_sections(errors)
    check_diagrams(errors)
    check_corsix_workbook(errors)
    check_deepwiki_optimization(errors)
    check_status_summary(errors)

    if errors:
        print("Documentation validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        "Documentation validation passed: "
        f"{len(markdown_files(UPSTREAM))} upstream reports, "
        f"{len(markdown_files(DOCS / 'rewrites'))} learner rewrites."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
