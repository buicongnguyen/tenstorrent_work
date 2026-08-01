<!-- rewrite-status: improved-draft -->
# Kernel Debugging Tips

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/Kernel_Debugging_Tips.md"><code>tech_reports/Debugging/Kernel_Debugging_Tips.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to classify the target failure as host/JIT,
firmware/watchdog, address/bounds, CB ownership/count, NoC completion, or numerical
compute before adding instrumentation; each class requires different evidence.

### How work and data move

The complete path is the failing program from host launch/runtime arguments through
reader, transport, compute, writer, and host validation, placing TT-TRIAGE, Watcher, and
device-print observations at the first boundary they can verify.

### What must never break

The non-negotiable invariant is for the suspected channel, prove matching
producer/consumer loop counts, valid addresses, reserved storage before movement,
movement completion before publication, and reclamation only after the final consumer.

### Where the report makes it concrete

The report makes the decision concrete by connecting the workflow to
`./tools/tt-triage.py --verbosity=4 --dev=0`, `api/debug/dprint.h`,
`TT_METAL_DPRINT_CORES`, `TT_METAL_WATCHER=1`, and `generated/watcher/watcher.log`.

### How the decision is tested

The controlled procedure is to create a minimal reproduction and intentionally break one
count or address check. **Expected observation:** the selected tool reports the first
violated boundary consistently, while random delays change timing but do not repair the
protocol.

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
