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
        for field in (
            "architect_task",
            "reasoning_path",
            "guide",
            "decision",
            "mechanism",
            "benefit",
            "cost",
            "evidence",
        ):
            if field not in layer:
                errors.append(
                    f"report layer {layer['number']} is missing curriculum field {field!r}"
                )


def check_layer_guides(errors: list[str]) -> None:
    navigation = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    catalog = (DOCS / "reference" / "report-catalog.md").read_text(
        encoding="utf-8"
    )
    guide_root = DOCS / "reference" / "layers"
    required_sections = (
        "## The architecture contract",
        "## Architecture reasoning loop",
        "## Worked problem",
        "## Tradeoffs an architect tracks",
        "## Report-by-report architecture decisions",
        "## Questions and expert answers",
        "## Evidence checklist",
    )

    for layer in LAYERS:
        number = layer["number"]
        filename = layer["guide"]
        nav_path = f"reference/layers/{filename}"
        catalog_path = f"layers/{filename}"
        guide_path = guide_root / filename

        if nav_path not in navigation:
            errors.append(f"sidebar navigation is missing Level {number} expert guide")
        if catalog_path not in catalog:
            errors.append(f"report catalog is missing Level {number} expert guide link")
        if not guide_path.exists():
            errors.append(f"Level {number} expert guide is missing")
            continue

        content = guide_path.read_text(encoding="utf-8")
        for section in required_sections:
            if section not in content:
                errors.append(f"Level {number} expert guide is missing {section!r}")

        questions = len(re.findall(r"^### \d+\.", content, flags=re.MULTILINE))
        answers = content.count('???+ note "Expert answer — reasoning"')
        if questions != 4 or answers != 4:
            errors.append(
                f"Level {number} expert guide must contain four questions and "
                f"four expanded answers; found {questions} questions and {answers} answers"
            )

        if f"layer{number}-" not in content:
            errors.append(f"Level {number} expert guide is missing its reasoning diagram")

        if "## Report-by-report architecture decisions" in content:
            decision_section = content.split(
                "## Report-by-report architecture decisions", maxsplit=1
            )[1].split("\n## Questions and expert answers", maxsplit=1)[0]
            expected_records = len(layer["paths"])
            headings = len(re.findall(r"^### ", decision_section, flags=re.MULTILINE))
            for marker in (
                "**Why this design exists.**",
                "**Mechanism and benefit.**",
                "**Price and rejected shortcut.**",
                "**Architect's evidence test.**",
            ):
                count = decision_section.count(marker)
                if count != expected_records:
                    errors.append(
                        f"Level {number} must contain {expected_records} instances "
                        f"of {marker!r}; found {count}"
                    )
            if headings != expected_records:
                errors.append(
                    f"Level {number} must contain one architecture decision record "
                    f"per report; expected {expected_records}, found {headings}"
                )
            for report_path in layer["paths"]:
                if report_path not in decision_section:
                    errors.append(
                        f"Level {number} architecture decisions do not link "
                        f"report {report_path}"
                    )
            decision_words = len(re.findall(r"\b[\w'-]+\b", decision_section))
            minimum_words = expected_records * 120
            if decision_words < minimum_words:
                errors.append(
                    f"Level {number} architecture decisions are too shallow: "
                    f"expected at least {minimum_words} words, found {decision_words}"
                )


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
    required = (
        "## Code connection",
        "## Verify your understanding",
        "## Source and delta",
    )
    total_questions = 0
    total_answers = 0
    improvement_sections: list[tuple[Path, str]] = []
    improvement_labels = (
        "**Architecture pressure.**",
        "**Flow to make explicit.**",
        "**Invariant to prove.**",
        "**TT-Metal evidence to connect.**",
        "**Experiment and expected observation.**",
    )
    forbidden_improvement_text = (
        "The learner edition should make these parts explicit before it can move beyond",
        "State the problem and the hardware/software boundary involved.",
        "Draw the data or control flow, including ownership and synchronization.",
        "Extract correctness invariants and architecture-specific assumptions.",
        "Connect the concepts to concrete TT-Metal symbols or examples.",
        "Add a small verification exercise with an expected observation.",
        "SOURCE-SPECIFIC PLAN REQUIRED",
    )
    for rewrite in markdown_files(DOCS / "rewrites"):
        content = rewrite.read_text(encoding="utf-8")
        for heading in required:
            if heading not in content:
                errors.append(f"{rewrite.relative_to(ROOT)}: missing {heading!r}")

        if "Before rewriting this page, answer from the original:" in content:
            errors.append(
                f"{rewrite.relative_to(ROOT)}: contains unanswered seed questions"
            )

        for forbidden in forbidden_improvement_text:
            if forbidden in content:
                errors.append(
                    f"{rewrite.relative_to(ROOT)}: contains generic improvement-plan "
                    f"text {forbidden!r}"
                )

        status_match = STATUS_RE.search(content)
        if status_match and status_match.group(1) == "seed":
            if "## Improvement plan" not in content:
                errors.append(
                    f"{rewrite.relative_to(ROOT)}: seed page is missing its "
                    "source-specific Improvement plan"
                )
            else:
                improvement_section = content.split(
                    "## Improvement plan", maxsplit=1
                )[1].split("\n## ", maxsplit=1)[0]
                improvement_sections.append((rewrite, improvement_section))
                for label in improvement_labels:
                    count = improvement_section.count(label)
                    if count != 1:
                        errors.append(
                            f"{rewrite.relative_to(ROOT)}: Improvement plan must contain "
                            f"exactly one {label!r}; found {count}"
                        )
                word_count = len(re.findall(r"\b[\w'-]+\b", improvement_section))
                if word_count < 120:
                    errors.append(
                        f"{rewrite.relative_to(ROOT)}: source-specific Improvement plan "
                        f"is too shallow; found {word_count} words"
                    )

        if "## Verify your understanding" not in content:
            continue

        section = content.split("## Verify your understanding", maxsplit=1)[1]
        section = section.split("\n## ", maxsplit=1)[0]
        question_blocks = re.split(r"^### \d+\. ", section, flags=re.MULTILINE)[1:]
        answers = section.count("???+ note \"Expert answer")
        total_questions += len(question_blocks)
        total_answers += answers

        if not question_blocks or len(question_blocks) != answers:
            errors.append(
                f"{rewrite.relative_to(ROOT)}: verification questions must "
                f"have one-to-one answers; found {len(question_blocks)} questions "
                f"and {answers} answers"
            )

        for index, block in enumerate(question_blocks, start=1):
            block_answers = block.count("???+ note \"Expert answer")
            if block_answers != 1:
                errors.append(
                    f"{rewrite.relative_to(ROOT)}: verification question {index} "
                    f"must be followed by exactly one expert answer; found {block_answers}"
                )
                continue
            answer_body = block.split("???+ note \"Expert answer", maxsplit=1)[1]
            answer_body = answer_body.split("\n", maxsplit=1)[-1]
            word_count = len(re.findall(r"\b[\w'-]+\b", answer_body))
            if word_count < 30:
                errors.append(
                    f"{rewrite.relative_to(ROOT)}: verification question {index} "
                    f"needs an expanded answer; found only {word_count} words"
                )

    if total_questions != 233 or total_answers != 233:
        errors.append(
            "rewrite curriculum must retain all 233 verification questions and "
            f"answers; found {total_questions} questions and {total_answers} answers"
        )

    if len(improvement_sections) != 49:
        errors.append(
            "rewrite curriculum must retain 49 source-specific Improvement plans; "
            f"found {len(improvement_sections)}"
        )

    normalized_plans: dict[str, list[Path]] = {}
    for rewrite, section in improvement_sections:
        normalized = re.sub(r"\s+", " ", section).strip()
        normalized_plans.setdefault(normalized, []).append(rewrite)
    for duplicates in normalized_plans.values():
        if len(duplicates) > 1:
            paths = ", ".join(str(path.relative_to(ROOT)) for path in duplicates)
            errors.append(f"duplicate Improvement plans found: {paths}")


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

    part_files = (
        "part1-physicalities.md",
        "part2-disabled-rows.md",
        "part3-noc-latency.md",
        "part4-ethernet.md",
        "part5-tile-architecture.md",
        "part6-vector-isa.md",
        "part7-matmul.md",
    )
    expected_answers = (6, 6, 6, 6, 7, 7, 7)
    parts_root = DOCS / "resources" / "corsix-parts"

    for part, (filename, answer_count) in enumerate(
        zip(part_files, expected_answers, strict=True), start=1
    ):
        source_url = f"https://www.corsix.org/content/tt-wh-part{part}"
        if source_url not in series:
            errors.append(f"Corsix series map is missing Part {part} original link")
        if f"corsix-parts/{filename}" not in workbook:
            errors.append(f"Corsix course hub is missing Part {part} lesson link")
        if f"resources/corsix-parts/{filename}" not in navigation:
            errors.append(f"sidebar navigation is missing Corsix Part {part}")

        page_path = parts_root / filename
        if not page_path.exists():
            errors.append(f"Corsix Part {part} guided page is missing")
            continue
        page = page_path.read_text(encoding="utf-8")
        if source_url not in page:
            errors.append(f"Corsix Part {part} page is missing its original link")
        for marker in (
            "## Follow the reasoning",
            "## Questions and guided answers",
            "## Verify and extend",
            "Architecture review",
        ):
            if marker not in page:
                errors.append(f"Corsix Part {part} page is missing {marker!r}")

        answers = page.count('??? note "Guided answer"')
        questions = len(re.findall(r"^### \d+\.", page, flags=re.MULTILINE))
        if answers != answer_count or questions != answer_count:
            errors.append(
                f"Corsix Part {part} must contain {answer_count} questions and "
                f"guided answers; found {questions} questions and {answers} answers"
            )

        expected_diagram = f"corsix-part{part}-"
        if expected_diagram not in page:
            errors.append(f"Corsix Part {part} page is missing its flow diagram")

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

    course_pages = (
        ("research-method.md", "https://deepwiki.com/tenstorrent/tt-metal", "deepwiki-research-method"),
        ("fast-dispatch.md", "https://deepwiki.com/tenstorrent/tt-metal/2.5-fast-dispatch-and-command-queue-system", "deepwiki-fast-dispatch"),
        ("program-cache.md", "https://deepwiki.com/tenstorrent/tt-metal/2.4-program-and-kernel-system", "deepwiki-program-cache"),
        ("command-queues-events.md", "https://deepwiki.com/tenstorrent/tt-metal/7.4-performance-optimization-techniques", "deepwiki-command-queues"),
        ("metal-trace.md", "https://deepwiki.com/tenstorrent/tt-metal/7.4-performance-optimization-techniques", "deepwiki-metal-trace"),
        ("memory-placement.md", "https://deepwiki.com/tenstorrent/tt-metal/2.7-memory-management-and-allocators", "deepwiki-memory-placement"),
        ("kernel-pipeline.md", "https://deepwiki.com/tenstorrent/tt-metal/2.12-data-movement-and-buffer-operations", "deepwiki-kernel-pipeline"),
        ("profiling.md", "https://deepwiki.com/tenstorrent/tt-metal/8.4-profiling-and-performance-analysis", "deepwiki-profiling-ladder"),
        ("model-to-operation.md", "https://deepwiki.com/tenstorrent/tt-metal/9.7-model-tracer-and-operation-extraction", "deepwiki-model-to-operation"),
        ("llk-isa.md", "https://deepwiki.com/tenstorrent/tt-metal/3-low-level-kernel-apis-%28llk%29", "deepwiki-llk-isa"),
    )
    course_root = DOCS / "resources" / "deepwiki"
    for filename, source_url, diagram in course_pages:
        nav_path = f"resources/deepwiki/{filename}"
        index_path = f"deepwiki/{filename}"
        page_path = course_root / filename

        if nav_path not in navigation:
            errors.append(f"sidebar navigation is missing DeepWiki lesson {filename}")
        if index_path not in guide:
            errors.append(f"DeepWiki course index is missing lesson {filename}")
        if not page_path.exists():
            errors.append(f"DeepWiki lesson {filename} is missing")
            continue

        content = page_path.read_text(encoding="utf-8")
        for marker in (
            source_url,
            "source-note",
            "## Questions and expert answers",
            "## Experiment to complete",
            "???+ note \"Expert answer — reasoning\"",
            diagram,
        ):
            if marker not in content:
                errors.append(f"DeepWiki lesson {filename} is missing {marker!r}")

        questions = len(re.findall(r"^### \d+\.", content, flags=re.MULTILINE))
        answers = content.count('???+ note "Expert answer — reasoning"')
        if questions != 3 or answers != 3:
            errors.append(
                f"DeepWiki lesson {filename} must contain three questions and "
                f"three expanded expert answers; found {questions} questions and "
                f"{answers} answers"
            )

        if len(content.split()) < 700:
            errors.append(
                f"DeepWiki lesson {filename} is too short for a detailed lesson"
            )


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
    check_layer_guides(errors)
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
