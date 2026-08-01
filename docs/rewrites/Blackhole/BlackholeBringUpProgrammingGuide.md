<!-- rewrite-status: improved-draft -->
# Blackhole Bring-Up Programming Guide

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md"><code>tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

This pinned bring-up note is a compatibility map, not a claim that Blackhole is a larger
Wormhole. That distinction matters because a kernel can compile and still inherit an
invalid timing, cache-coherence, alignment, or resource assumption. At commit `992f3ca`,
Blackhole exposes a `13x10` compute grid from `14x10` Tensix cores, 14 Ethernet cores
with two RISC-V processors and 512 KB L1, eight roughly 4 GB DRAM banks whose hardware
table lists one RISC-V and 128 KB L1, 64-byte DRAM/PCIe reads, and rectangular, strided,
and L-shaped NoC multicast. Capability is not the same as runtime availability: the
same pinned report says runtime access to program the DRAM RISC-V was **not enabled**.
It does say access to the second RISC-V on idle Ethernet cores was enabled, while Fast
Dispatch from those cores had been added but was temporarily disabled during multichip
Ethernet bring-up. The Wormhole N150 comparison is deliberately concrete:
`8x8` compute cores, 16 single-RISC Ethernet cores, twelve 1 GB DRAM banks, and 32-byte
DRAM/PCIe reads. Software therefore needs architecture-qualified resource discovery;
hard-coded Wormhole grids, bank counts, alignment expectations, or multicast schedules
are not safe defaults.

The most subtle new boundary is Blackhole's optional four-entry, 16-byte-cache-line,
write-through L1 data cache. It accelerates repeated local loads, but it does not turn
distributed L1 into coherent shared memory. A remote writer can update an address while
a reader retains an older line. Explicit invalidation is therefore part of the
producer-consumer protocol, not merely a tuning switch.

### How work and data move

For a cache-sensitive handoff, follow the actual ownership chain. A kernel enables its
local cache with `set_l1_data_cache<true>()`, reads an L1 address, and may retain the
line. Another core then writes the same address. Before the first core consumes the
new value, that reader—not the writer—must call `invalidate_l1_cache()` if it previously
read the address. The kernel restores the default with `set_l1_data_cache<false>()`
before exit. Global experiments can instead select BR, NC, TR, or ER RISC classes with
`TT_METAL_ENABLE_L1_DATA_CACHE_RISCVS`; randomized hardware invalidation exists behind
`TT_METAL_ENABLE_HW_CACHE_INVALIDATION`, but the source calls it slower and says its
timeout is disabled by default.

NoC publication has a second, independent ordering edge. The report records Blackhole
ND mismatches and hangs when kernels issued NoC commands without explicit flushes:
data and semaphore updates could be issued faster than the NoC serviced earlier
commands. The safe chain is therefore `reserve destination -> issue data movement ->
flush/complete required NoC work -> publish semaphore -> consumer reads`, rather than
assuming older Wormhole RISC-to-L1 latency accidentally provides ordering. Cache
invalidation cannot replace that NoC completion edge, and a NoC flush cannot invalidate
a reader's cached copy.

### What must never break

Three invariants must hold together. First, logical work is mapped only onto the
discovered Blackhole resources; available Tensix cores, Ethernet programmability, and
the pinned eight-bank DRAM organization cannot be inferred from Wormhole. Second, the
producer makes payload data visible before publishing its associated ready signal, and
the consumer reads that payload only after observing the signal; this requires explicit
NoC ordering. Third, a cached reader invalidates before observing a location modified
by another core. Violating the second invariant produces partial data, ND output, or a hang;
violating the third can return a stable but stale value. Disabling the L1 cache may hide
the latter and is useful diagnosis, but it is not a correctness fix for code that later
reenables caching.

### Where the report makes it concrete

The report's concrete multicast evidence is
`MeshDispatchFixture.DRAMtoL1MulticastExcludeRegionUpLeft`, which exercises a
non-rectangular Blackhole shape. Watcher is recommended while triaging operator failures
because alignment faults are plausible at this porting boundary. Reset behavior is also
firmware-dependent: `tt-smi -r 0` may fail and require a board reboot. Finally, the
pinned CI claim is narrow—only C++ tests were running, with post-commit coverage still
work in progress—so a passing C++ smoke test is evidence for one layer, not validation
of the complete TT-NN stack.

### How the decision is tested

Use two minimal tests before a model workload. In the first, have one core cache a known
L1 value, have a second core overwrite it, then compare cache disabled, cache enabled
without invalidation, and cache enabled with `invalidate_l1_cache()`. The final case must
reliably observe the overwrite; the middle case is intentionally not a correctness
configuration. In the second, transfer data and then signal a semaphore both with and
without the required NoC flush while Watcher is enabled. The flushed version must be
deterministic across repeated runs. Also run the named multicast gtest to validate the
architecture-specific routing shape. These checks isolate cache visibility, NoC
ordering, and routing instead of allowing one failure to be mislabeled as generic
"Blackhole bring-up instability."

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
