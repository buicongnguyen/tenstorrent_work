<!-- rewrite-status: seed -->
# Hardware Performance Counters

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PerfCounters/perf-counters.md"><code>tech_reports/PerfCounters/perf-counters.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/PerfCounters/perf-counters.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 1163 |
| Section headings | 27 |
| Fenced code examples | 49 |
| Markdown images | 0 |

### Section outline

- Quick Links
- Overview
- How It Works
  - How to Run
  - Environment Variable
  - Architecture Summary
- Derived Metrics Reference
  - Compute Utilization
  - Pipeline Efficiency
  - Thread Analysis
  - Pipeline Wait Metrics
  - Semaphore Waits
  - TDMA Stall Metrics
  - Instruction Availability Rates
  - Stall Breakdown
  - Write Port Analysis
  - Additional Idle Waits
  - L1 Memory Utilization
  - L1 Backpressure
  - L1 Composite Metrics
  - Additional Pipeline Metrics
- Hardware Register Reference
  - Control registers (`RISCV_DEBUG_REG_PERF_CNT_<X>0..2`)
  - Data registers
- … 3 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PerfCounters/perf-counters.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Source and delta

- **Original source:** [`tech_reports/PerfCounters/perf-counters.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PerfCounters/perf-counters.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/PerfCounters/perf-counters.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
