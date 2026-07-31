#!/usr/bin/env python3
"""Generate the source-report catalog from the pinned upstream snapshot."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "tt-metal" / "tech_reports"
REWRITES = ROOT / "docs" / "rewrites"
OUTPUT = ROOT / "docs" / "reference" / "report-catalog.md"
COMMIT = "992f3ca634aac8733c70e48da395aab5361b4166"


def title_for(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^#\s+(.+?)\s*$", text, flags=re.MULTILINE)
    return match.group(1).replace("|", r"\|") if match else path.stem.replace("_", " ")


def main() -> None:
    reports = sorted(UPSTREAM.rglob("*.md"), key=lambda item: item.as_posix().lower())
    lines = [
        "# Upstream report catalog",
        "",
        f"This index covers all **{len(reports)}** Markdown reports in the pinned ",
        f"[official snapshot](https://github.com/tenstorrent/tt-metal/tree/{COMMIT}/tech_reports).",
        "The snapshot also includes each report's images, media, and helper scripts.",
        "",
        "Status is intentionally conservative: a page remains `source-only` until a",
        "one-to-one learner edition exists and review is explicit.",
        "",
        "| # | Report | Upstream path | Learner edition | Status |",
        "|---:|---|---|---|---|",
    ]

    for index, report in enumerate(reports, start=1):
        relative = report.relative_to(UPSTREAM)
        url_path = "/".join(relative.parts)
        source_url = (
            "https://github.com/tenstorrent/tt-metal/blob/"
            f"{COMMIT}/tech_reports/{url_path}"
        )
        rewrite = REWRITES / relative
        if rewrite.exists():
            rewrite_link = Path("..", "rewrites", relative).as_posix()
            learner = f"[Open rewrite]({rewrite_link})"
            status = "`draft`"
        else:
            learner = "—"
            status = "`source-only`"
        lines.append(
            f"| {index} | {title_for(report)} | "
            f"[`{relative.as_posix()}`]({source_url}) | {learner} | {status} |"
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
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(reports)} reports.")


if __name__ == "__main__":
    main()

