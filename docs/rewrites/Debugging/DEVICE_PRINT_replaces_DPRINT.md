<!-- rewrite-status: seed -->
# Deprecating `DPRINT` in favor of `DEVICE_PRINT`

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md"><code>tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md</code>. This learner page
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 250 |
| Section headings | 12 |
| Fenced code examples | 13 |
| Markdown images | 0 |

### Section outline

- 1. Why we changed it
- 2. Deprecation plan
  - Phase 1 – Opt‑in (completed)
  - Phase 2 – Deprecation window (completed)
  - Phase 3 – Alias and cleanup (completed)
- 3. Usage examples – `DPRINT` vs `DEVICE_PRINT`
  - 3.1 Basic value printing
  - 3.2 Number formatting
  - 3.3 Enum printing
  - 3.4 Tile / `TileSlice` printing
  - 3.5 Core-specific prints
  - 3.6 Enabling `DEVICE_PRINT` (historical — transition only)

## Improvement plan

1. **Architecture pressure.** Document the concrete migration and behavioral differences
   between deprecated `DPRINT` and supported `DEVICE_PRINT`, including enablement,
   formatting, core/RISC selection, buffering, drain, and teardown—not merely a macro
   rename.

2. **Flow to make explicit.** Draw `selected device thread → DEVICE_PRINT record encoding →
   device debug buffer/transport → runtime drain → host console/log`, including when records
   become observable and which component owns flushing.

3. **Invariant to prove.** Prove that diagnostic output comes from the intended core/RISC,
   remains within supported buffer/format limits, is drained before teardown, and is never
   used as a substitute for a NoC barrier or CB/event dependency.

4. **TT-Metal evidence to connect.** Connect old/new examples to `DPRINT`, `DEVICE_PRINT`,
   `TT_METAL_DEVICE_PRINT=1`, the former stream syntax `DPRINT << ... << ENDL()`, and the
   current debug include/runtime path.

5. **Experiment and expected observation.** Run the same minimal kernel with printing
   disabled, enabled on one core, and enabled broadly; expected result: functional output is
   unchanged, scoped output identifies the producer, and measured perturbation grows with
   print volume.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md):

- **Compile-time surface.** The old `DPRINT << value << ENDL()` stream syntax and the
  replacement `DEVICE_PRINT` macros generate different device-side records. Use the
  include and invocation form that belongs to the pinned runtime; mixing the two
  surfaces can fail at compilation before any device output exists.

- **Runtime transport.** `TT_METAL_DEVICE_PRINT=1` selected the new backend only during
  the documented transition; the report says the flag was later removed when
  `DEVICE_PRINT` became the sole backend. For the pinned phase being studied, separate
  backend selection from core/thread filtering, device-buffer transport, and host drain.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The programming task is migrating kernel diagnostics from `DPRINT` to `DEVICE_PRINT`
    while preserving useful device-side visibility and removing reliance on a deprecated
    interface. The constraint is that debugging output crosses a device/host boundary
    with limited buffering.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    A print record must be emitted only from the intended core/RISC, remain well formed
    in the device debug buffer, and be drained before teardown. Adding a print must not
    be mistaken for synchronization or change the correctness contract of the kernel
    being observed.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A selected device thread reaches a diagnostic point → `DEVICE_PRINT` encodes text
    and values into the debug transport → runtime support drains the record → the host
    formats it on the console/log → the developer correlates it with the issuing core
    and program point.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Macro syntax, enable flags, supported value types, buffer
    capacities, core-selection controls, and the deprecation timeline are
    revision-specific.

    **Durable model.** Keep instrumentation scoped, identify the producer, account for
    buffering and perturbation, flush before shutdown, and use printing to test a
    hypothesis rather than as a substitute for ownership or completion primitives.

## Source and delta

- **Original source:** [`tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md`
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
