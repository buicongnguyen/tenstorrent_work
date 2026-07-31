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


def outline_for(text: str) -> list[str]:
    headings: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if match:
            heading = re.sub(r"\s+#+$", "", match.group(2)).replace("|", r"\|")
            headings.append(f"{'  ' * (len(match.group(1)) - 2)}- {heading}")
    return headings


def seed_page(source: Path) -> str:
    text = source.read_text(encoding="utf-8", errors="replace")
    relative = source.relative_to(UPSTREAM)
    path = relative.as_posix()
    title = title_for(text, source)
    source_url = (
        "https://github.com/tenstorrent/tt-metal/blob/"
        f"{COMMIT}/tech_reports/{path}"
    )
    outline = outline_for(text)
    outline_block = "\n".join(outline[:24]) if outline else "- The source has no section headings yet."
    if len(outline) > 24:
        outline_block += f"\n- … {len(outline) - 24} additional headings in the original"

    line_count = len(text.splitlines())
    code_blocks = text.count("```") // 2
    images = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", text))

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
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | {line_count} |
| Section headings | {len(outline)} |
| Fenced code examples | {code_blocks} |
| Markdown images | {images} |

### Section outline

{outline_block}

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report]({source_url}). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Source and delta

- **Original source:** [`tech_reports/{path}` at `{COMMIT[:7]}`]({source_url})
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/{path}`
- **Current delta:** provenance, source metrics, outline, and improvement
  checklist. Questions are added only when source-grounded answers are ready.
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
