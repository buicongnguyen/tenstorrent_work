# Rewrite playbook

The goal is not to make an official report longer. The goal is to make its
reasoning easier to reconstruct without changing its technical meaning.

## Keep a one-to-one path

An upstream file at:

```text
upstream/tt-metal/tech_reports/<topic>/<name>.md
```

should normally have its learner edition at:

```text
docs/rewrites/<topic>/<name>.md
```

Use synthesis pages under `docs/start/` only when the teaching concept truly
crosses several reports.

## Required page anatomy

1. **Source note** — upstream path, full commit, and review status.
2. **Problem** — what constraint or workload motivates the feature.
3. **Placement** — where it sits in the host/software/hardware stack.
4. **Data or control flow** — actors, ownership, movement, and ordering.
5. **Invariants** — what must remain true for correctness.
6. **Trade-offs** — capacity, precision, latency, bandwidth, or complexity.
7. **Code connection** — symbols and examples in `tt-metal`.
8. **Verification** — questions or an experiment with an expected result.
9. **Delta** — what this edition added, clarified, or intentionally omitted.

The source note must contain a clickable URL in this form:

```text
https://github.com/tenstorrent/tt-metal/blob/<full-commit>/tech_reports/<path>.md
```

Do not link a one-to-one rewrite only to `main`: commit-pinned comparison is
what makes later upstream changes detectable. If a page uses Corsix or the ISA
repository as supporting material, link the exact article/file separately and
label it `community · verify` or `official · living`.

## Diagram rule

Every diagram must answer at least one question:

- **Structure:** what contains what?
- **Flow:** what moves between which places?
- **Order:** what must happen before what?
- **Ownership:** which actor may read or write now?
- **Trade-off:** what changes when a choice changes?

Label edges with the thing that moves or the event that occurs. Avoid a box-
and-arrow picture whose arrows do not have a precise meaning.

## Technical review

Before marking a rewrite complete:

- [ ] Compare every numeric claim with the pinned upstream report.
- [ ] Mark architecture-specific statements (Grayskull, Wormhole, Blackhole).
- [ ] Distinguish current API behavior from the durable mental model.
- [ ] Follow one concrete page/tile/message end to end.
- [ ] Search the pinned source revision for every named symbol.
- [ ] Check relative links and render every Mermaid diagram.
- [ ] Ask whether the new explanation accidentally implies more than upstream.

## Status values

| Status | Meaning |
|---|---|
| `source-only` | Upstream copy exists; no learner edition yet |
| `draft` | Rewrite exists but technical/visual review is incomplete |
| `improved` | Rewrite passed the checklist against the pinned revision |
| `review-needed` | Upstream changed after the last completed review |

The pilot layout chapter starts as `draft`: its structure is ready, but a
hardware practitioner should still validate architecture-sensitive nuances.
