#!/usr/bin/env python3
"""Create source-linked learner seeds without overwriting edited pages."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "tt-metal" / "tech_reports"
REWRITES = ROOT / "docs" / "rewrites"
COMMIT = "992f3ca634aac8733c70e48da395aab5361b4166"


def title_for(text: str, path: Path) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return path.stem.replace("_", " ").replace("-", " ").title()


def seed_page(source: Path) -> str:
    text = source.read_text(encoding="utf-8", errors="replace")
    relative = source.relative_to(UPSTREAM)
    path = relative.as_posix()
    title = title_for(text, source)
    source_url = (
        "https://github.com/tenstorrent/tt-metal/blob/"
        f"{COMMIT}/tech_reports/{path}"
    )
    return f"""<!-- rewrite-status: seed -->
# {title}

<p class="source-note">
<strong>Original source:</strong>
<a href="{source_url}"><code>tech_reports/{path}</code> at <code>{COMMIT[:7]}</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/{path}</code>. This learner page
    is intentionally blocked from publication until its report-specific architecture
    explanation, implementation evidence, and answered checks are authored.

## Architecture walkthrough

SOURCE-SPECIFIC WALKTHROUGH REQUIRED. Replace this marker with direct, declarative
explanations of the design pressure, data/control flow, correctness invariant,
implementation evidence, and a falsifiable decision test. Do not publish source
statistics, an outline dump, or future-tense authoring instructions as learner content.

## Code connection

SOURCE-SPECIFIC CODE CONNECTION REQUIRED. Replace this marker with concrete
host/runtime/device boundaries, named symbols or files from the pinned report,
and the invariant each boundary must preserve.

## Source and delta

- **Original source:** [`tech_reports/{path}` at `{COMMIT[:7]}`]({source_url})
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/{path}`
- **Current delta:** provenance, source metrics, and outline. Architecture work
  and questions are added only when source-grounded details and answers are ready.
"""


def main() -> None:
    created = 0
    preserved = 0
    reports = sorted(UPSTREAM.rglob("*.md"), key=lambda item: item.as_posix().lower())
    for source in reports:
        destination = REWRITES / source.relative_to(UPSTREAM)
        if destination.exists():
            preserved += 1
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(seed_page(source), encoding="utf-8", newline="\n")
        created += 1

    print(
        f"Learner coverage: {created} seeds created, {preserved} existing edits preserved, "
        f"{len(reports)} total reports."
    )


if __name__ == "__main__":
    main()
