<!-- rewrite-status: seed -->
# Kernel Debugging Tips

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/Kernel_Debugging_Tips.md"><code>tech_reports/Debugging/Kernel_Debugging_Tips.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/Debugging/Kernel_Debugging_Tips.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 53 |
| Section headings | 5 |
| Fenced code examples | 1 |
| Markdown images | 0 |

### Section outline

- TT-TRIAGE
- DPRINT
  - Printing data from CBs
- Watcher
- General tips

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/Kernel_Debugging_Tips.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/Kernel_Debugging_Tips.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report provides a layered method for diagnosing compile failures, hangs, illegal
    memory access, synchronization bugs, and wrong values in device kernels using triage
    tools, device printing, Watcher, and progressively smaller reproductions.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Diagnostics must preserve the kernel's required ordering and address bounds. In
    particular, every circular-buffer wait must have a matching producer, every NoC
    operation must target valid storage, and instrumentation must not be treated as
    proof that data movement completed.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The host builds and dispatches a minimal program → a data-movement or compute RISC
    reaches waits, NoC operations, or arithmetic → Watcher/triage checks
    firmware-visible state and `DEVICE_PRINT` emits selected values → the host collects logs →
    the failing stage is isolated and reduced.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Tool names, environment variables, Watcher checks, firmware
    diagnostics, log formats, and supported core filters change with TT-Metal releases
    and hardware.

    **Durable model.** Reproduce minimally, classify the failure before editing,
    instrument boundary conditions, verify address and ownership invariants, and move
    from host launch to producer to transport to consumer in causal order.

## Source and delta

- **Original source:** [`tech_reports/Debugging/Kernel_Debugging_Tips.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/Kernel_Debugging_Tips.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Debugging/Kernel_Debugging_Tips.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
