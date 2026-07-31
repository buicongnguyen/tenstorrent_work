#!/usr/bin/env python3
"""Generate the source-report catalog from the pinned upstream snapshot."""

from __future__ import annotations

import re
from pathlib import Path

from report_layers import LAYERS, report_paths


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "tt-metal" / "tech_reports"
REWRITES = ROOT / "docs" / "rewrites"
OUTPUT = ROOT / "docs" / "reference" / "report-catalog.md"
COMMIT = "992f3ca634aac8733c70e48da395aab5361b4166"
STATUS_RE = re.compile(r"<!--\s*rewrite-status:\s*([a-z-]+)\s*-->")


def title_for(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^#\s+(.+?)\s*$", text, flags=re.MULTILINE)
    return match.group(1).replace("|", r"\|") if match else path.stem.replace("_", " ")


def status_for(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = STATUS_RE.search(text)
    return match.group(1) if match else "draft"


def main() -> None:
    reports_by_path = {
        report.relative_to(UPSTREAM).as_posix(): report
        for report in UPSTREAM.rglob("*.md")
    }
    ordered_paths = report_paths()
    duplicates = sorted({path for path in ordered_paths if ordered_paths.count(path) > 1})
    missing = sorted(set(reports_by_path) - set(ordered_paths))
    unknown = sorted(set(ordered_paths) - set(reports_by_path))
    if duplicates or missing or unknown:
        raise RuntimeError(
            "Invalid report layer map: "
            f"duplicates={duplicates}, missing={missing}, unknown={unknown}"
        )

    report_count = len(reports_by_path)
    lines = [
        "# Upstream report catalog",
        "",
        f"This index covers all **{report_count}** Markdown reports in the pinned ",
        f"[official snapshot](https://github.com/tenstorrent/tt-metal/tree/{COMMIT}/tech_reports).",
        "The snapshot also includes each report's images, media, and helper scripts.",
        "",
        "Every source has a one-to-one learner page. Status is intentionally",
        "conservative: `seed` means provenance and a reading map exist, while",
        "`improved-draft` means a substantive rewrite still awaits final review.",
        "",
        "## Read from high level to low level",
        "",
        "Levels 0–4 form the main descent from stack vocabulary to device-kernel",
        "dataflow. Levels 5 and 6 are advanced branches for measurement and scale.",
        "Level 7 is the lowest layer and should be architecture-qualified.",
        "",
        "The catalog tells you **what to read**. Each expert guide teaches "
        "**how to reason** at that layer through contracts, a worked problem, "
        "tradeoffs, evidence, and fully explained answers.",
        "",
        "| Level | Abstraction | Main question | Expert guide | Reports |",
        "|---:|---|---|---|---:|",
    ]

    for layer in LAYERS:
        lines.append(
            f"| [{layer['number']}](#level-{layer['number']}-{layer['slug']}) "
            f"| {layer['abstraction']} | {layer['focus']} "
            f"| [Reason through Level {layer['number']}](layers/{layer['guide']}) "
            f"| {len(layer['paths'])} |"
        )

    sequence = 0
    for layer in LAYERS:
        lines.extend(
            [
                "",
                f"## Level {layer['number']} — {layer['title']} "
                f"{{ #level-{layer['number']}-{layer['slug']} }}",
                "",
                layer["focus"],
                "",
                f"**Start this level when:** {layer['start_when']}.",
                "",
                f"**Architect's task:** {layer['architect_task']}",
                "",
                f"**Reasoning path:** `{layer['reasoning_path']}`",
                "",
                f"[Open the Level {layer['number']} expert reasoning guide →]"
                f"(layers/{layer['guide']})"
                "{ .md-button .md-button--primary }",
                "",
                "| Step | Report | Upstream original | Learner edition | Status |",
                "|---:|---|---|---|---|",
            ]
        )
        for report_path in layer["paths"]:
            sequence += 1
            report = reports_by_path[report_path]
            relative = report.relative_to(UPSTREAM)
            source_url = (
                "https://github.com/tenstorrent/tt-metal/blob/"
                f"{COMMIT}/tech_reports/{relative.as_posix()}"
            )
            rewrite = REWRITES / relative
            if rewrite.exists():
                rewrite_link = Path("..", "rewrites", relative).as_posix()
                learner = f"[Open learner page]({rewrite_link})"
                status = f"`{status_for(rewrite)}`"
            else:
                learner = "—"
                status = "`source-only`"
            lines.append(
                f"| {sequence} | {title_for(report)} | "
                f"[`{relative.as_posix()}`]({source_url}) | {learner} | {status} |"
            )

        if layer["number"] == 7:
            lines.extend(
                [
                    "",
                    "Continue below the report set with the "
                    "[official TT-LLK and ISA guide](../resources/isa-reference.md) "
                    "and the [Corsix Wormhole field notes](../resources/corsix-wormhole-series.md).",
                ]
            )

    lines.extend(
        [
            "",
            "## Additional foundation document",
            "",
            f"- [`METALIUM_GUIDE.md`](https://github.com/tenstorrent/tt-metal/blob/{COMMIT}/METALIUM_GUIDE.md)",
            "",
            "## Regenerate this page",
            "",
            "```console",
            "python scripts/build_catalog.py",
            "python scripts/check_docs.py",
            "```",
            "",
        ]
    )
    OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {report_count} reports in {len(LAYERS)} levels.")


if __name__ == "__main__":
    main()

