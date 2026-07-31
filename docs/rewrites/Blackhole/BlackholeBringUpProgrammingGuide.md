<!-- rewrite-status: seed -->
# Blackhole Bring-Up Programming Guide

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md"><code>tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 111 |
| Section headings | 10 |
| Fenced code examples | 1 |
| Markdown images | 0 |

### Section outline

- Introduction
- Wormhole N150 vs. Blackhole
  - L1 Data Cache
  - Ethernet Cores
  - DRAM
  - NoC
- Debug
- Resetting
- CI
- Issue Tracking

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The task is controlled Blackhole bring-up: port a Wormhole-oriented software and
    validation flow while accounting for changed L1 caching, Ethernet cores, DRAM, NoC
    behavior, reset, and debug paths. The bottleneck is not one kernel; it is
    uncertainty about which hardware/software layer failed during initialization.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every binary, firmware image, descriptor, coordinate, and reset sequence must match
    the detected device, and each lower layer must be operational before a higher-layer
    test is trusted. A compute test cannot prove Ethernet initialization, and a stale
    Wormhole assumption must not silently enter a Blackhole run.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The host detects Blackhole and loads its SoC/runtime description → reset establishes
    a known state → firmware and service cores start → DRAM and NoC paths are
    initialized → a minimal kernel is dispatched → debug output and CI record the result
    before broader tests are enabled.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** The exact L1 cache behavior, Ethernet-core organization, DRAM
    channels, NoC coordinates, reset commands, CI labels, and issue references belong to
    the documented Blackhole snapshot.

    **Durable model.** Bring up one dependency layer at a time, use a minimal observable
    test at every boundary, preserve a known reset state, and never infer that success
    in one subsystem proves the next subsystem. Those habits transfer to any new
    accelerator generation.

## Source and delta

- **Original source:** [`tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
