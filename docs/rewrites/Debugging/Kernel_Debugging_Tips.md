<!-- rewrite-status: improved-draft -->
# Kernel Debugging Tips

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/Kernel_Debugging_Tips.md"><code>tech_reports/Debugging/Kernel_Debugging_Tips.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned note organizes debugging by *where evidence can still escape*. A hung process
may never return host results, so `tt-triage.py` samples RISC stack traces while the
process remains alive. Watcher records kernels and waypoints for post-mortem inspection.
Device printing exposes values and circular-buffer contents from inside the dataflow or
compute kernel. These are complementary observation planes: use the least intrusive
one that can distinguish the suspected boundary, then reduce the system until the first
incorrect observation is isolated.

This is why the report starts with minimization rather than broad instrumentation.
Multiple operators, devices, and cores multiply the number of producers, consumers,
addresses, and scheduling interleavings. Reducing to one operation, one device, and the
smallest core grid converts a distributed symptom into a reproducible ownership path.
Turning program cache off separately distinguishes stale/reused program state from a
kernel algorithm failure; fixed zeros or ones remove input entropy while preserving the
control protocol.

### How work and data move

For a hang, keep the test process running and execute
`./tools/tt-triage.py --verbosity=4 --dev=0` in another terminal. Its stacks across all
RISCs and cores tell whether participants are still executing and where they wait. With
`TT_METAL_WATCHER=1`, kill the hung test only after evidence is captured, then inspect
`generated/watcher/watcher.log` for the launched kernels and last waypoints.

For wrong numeric output or a deterministic stall, include `api/debug/dprint.h`, scope
output to a core using `TT_METAL_DPRINT_CORES="(0,0)"`, and print the smallest value that
crosses the suspected boundary. Reader/writer kernels can inspect BF16 or FP32 CB pages
with `print_bf16_pages` or `print_f32_pages`; compute kernels can use
`print_full_tile` from `tt_metal/hw/inc/debug/dprint_pages.h`. The example iterates a
32x32 tile row by row with `SliceRange` and `TileSlice(cb_id, tile_id, ..., true,
untilize)`. `DPRINT_DATA0` versus `DPRINT_DATA1` selects the relevant data-movement
processor, so the observation is made by the actual owner rather than a remote observer.

### What must never break

Every comparison must keep the same CB id, tile index, datatype, tilized/untilized
interpretation, core, and RISC role. Printing an FP32 page as BF16 or asking the wrong
data-movement RISC can fabricate a numerical diagnosis. The debugging tool must not be
treated as a repair: print calls and Watcher change timing, and a race that disappears
under instrumentation still violates the original protocol. Fixed-value inputs are
useful only if the expected result remains independently known. Program-cache-off and
reduced-grid experiments must preserve the failing logical operation or their success
does not falsify the original bug.

### Where the report makes it concrete

Read the three evidence types as a causal sequence. A stack repeatedly waiting points
to a coordination boundary but does not prove which peer is wrong. Watcher's last
waypoint identifies which kernel/core advanced far enough to become that peer. A scoped
tile/page print then tests the payload immediately before or after that boundary. If
control reaches the writer but PCC fails, inspect compute output and writer input rather
than adding more host logs. If a minimal single-op run succeeds only with program cache
disabled, compare cached and uncached compile/runtime arguments before changing kernel
math. The source calls TT-TRIAGE still in development, so its output is evidence to
corroborate, not an infallible verdict.

### How the decision is tested

Run a small diagnostic matrix: original versus one-op reproduction; full grid versus one
core; program cache on versus off; random input versus all ones. For a hang, capture
TT-TRIAGE stacks before termination and correlate them with the Watcher log. For a PCC
failure, print exactly one known tile at producer output and consumer input using the
correct page helper and core selector. The expected result is not merely "more logs": it
is the earliest boundary where two otherwise identical runs diverge. Repeat without
device printing to ensure instrumentation did not change the failure, and retain the
smallest case that reproduces it for the eventual unit test.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/Kernel_Debugging_Tips.md):

- **First-failure triage.** `./tools/tt-triage.py --verbosity=4 --dev=0` and Watcher
  (`TT_METAL_WATCHER=1`) expose device state and protocol violations without depending
  on a kernel's own print path. Start there for hangs, invalid NoC accesses, and
  circular-buffer misuse.

- **Focused instrumentation.** `api/debug/dprint.h` plus `TT_METAL_DPRINT_CORES` narrows
  prints to the suspected cores; `generated/watcher/watcher.log` preserves Watcher's
  evidence. Correlate both with producer/consumer counts so added printing does not
  become the only timing change that makes the failure disappear.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
