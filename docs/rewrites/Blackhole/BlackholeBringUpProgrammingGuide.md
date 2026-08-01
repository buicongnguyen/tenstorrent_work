<!-- rewrite-status: improved-draft -->
# Blackhole Bring-Up Programming Guide

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md"><code>tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to separate Blackhole enablement into reset/boot, L1
cache behavior, DRAM, NoC, Ethernet, debug, and CI gates. Record exactly which Wormhole
assumption is invalid at each gate instead of treating a failed application as one
bring-up problem.

### How work and data move

The complete path is `host architecture detection → Blackhole descriptor/config → reset
→ firmware/service cores → DRAM/NoC/Ethernet initialization → minimal worker kernel → CI
promotion`, including the owner and observable completion of every transition.

### What must never break

The non-negotiable invariant is that binaries, descriptors, coordinates, cache policy,
and reset sequence match the detected Blackhole device and that a higher-layer test runs
only after every dependency below it has passed its minimal check.

### Where the report makes it concrete

The report makes the decision concrete by connecting the analysis to
`set_l1_data_cache<true/false>()`, `invalidate_l1_cache()`,
`TT_METAL_ENABLE_HW_CACHE_INVALIDATION`, `tt-smi -r 0`, and the architecture-qualified
multicast/CI cases named by the source.

### How the decision is tested

The controlled procedure is to toggle L1 caching on one minimal memory test and compare
stale/correct observations before and after explicit invalidation. **Expected observation:** cache-dependent behavior changes only at the documented boundary, while
reset returns the device to a reproducible baseline.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md):

- **Cache-policy controls.** `set_l1_data_cache<true>()` selects cached L1 access, while
  `invalidate_l1_cache()` and `TT_METAL_ENABLE_HW_CACHE_INVALIDATION` define when cached
  state becomes trustworthy. Review them together; enabling a cache without an
  invalidation boundary creates a correctness bug, not merely a performance difference.

- **Reset and qualification.** `tt-smi -r 0` restores a known device state before the
  architecture-qualified multicast and CI cases exercise DRAM, NoC, Ethernet, and worker
  paths. A passing worker test does not substitute for those subsystem-specific gates.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
