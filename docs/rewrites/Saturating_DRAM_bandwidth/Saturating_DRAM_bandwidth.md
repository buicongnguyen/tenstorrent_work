<!-- rewrite-status: improved-draft -->
# Saturating DRAM bandwidth

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md"><code>tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned report reaches DRAM bandwidth by solving two separate queueing problems.
Within one bank, a reader that issues one block and immediately waits at a global read
barrier leaves a request gap: after the bank returns the last data, it receives no next
command until the RISC resumes. Across banks, adding readers can still underperform when
their deterministic NoC routes share links or one reader monopolizes a virtual channel.
The chosen architecture therefore pipelines tagged block requests for temporal
continuity, then places one reader per bank and engineers routes/VCs for spatial
independence.

This is why “more outstanding reads” and “more cores” are not sufficient explanations.
Outstanding work needs destination capacity and a completion boundary per consumer
block; extra cores must correspond to independent banks and non-conflicting return
paths. The pinned claim—over 92% on its Wormhole/Grayskull microbenchmark—depends on all
three conditions.

### How work and data move

For a single bank, one data-movement RISC issues asynchronous NoC reads for
application-sized blocks. Instead of draining block 1 before issuing block 2, the report
assigns transaction tag 1 to the first block and tag 2 to the second. It primes both requests,
then waits only for the tag of the block needed by compute: wait tag 1 while tag 2
remains in flight, issue the next tag-1 block, then wait tag 2, alternating. At least one
future request is therefore visible to DRAM while the current block crosses its
producer-consumer boundary. This is double buffering at the transaction/completion
level; the report does not name a specific API, so the tag/barrier mechanism should not
be replaced here by an invented symbol.

At full-device scale, the source assigns exactly one reader to each bank—8 on Grayskull,
12 on Wormhole—and each reader accesses only its bank. Concentrating Wormhole readers on
top rows creates overlapping NoC-0 paths because the pinned routing goes horizontally
right, then downward; the example identifies bank-2 and bank-10 routes as a conflict.
Placing each reader next to its bank reduces returned data to one hop and separates
routes. Two banks can still share a row, so their request traffic uses different NoC
virtual channels. Since arbitration is first-come-first-served within one VC but
round-robins across VCs, this prevents one reader from starving its row peer.

Harvesting complicates the geometric solution. N150 has one harvested worker row and
N300 two in this pinned Wormhole scope, with positions not fixed. If a bank-adjacent core
is unavailable, the placement procedure moves the reader right/up until it finds an
unused row whose route does not overlap an assigned route. Placement must therefore be
computed from the available physical grid, not hard-coded from logical row number.

The model example converts placement into tensor ownership. `in1` is width-sharded over
12 DRAM banks so each reader consumes only its local partition; `in0` is width-sharded
on top-row workers and multicasted to the bank-local compute cores. Both input streams
are double buffered so compute overlaps data movement. After local matmul, output shards
return to top rows to satisfy the pinned contiguous-shard allocation convention.

### What must never break

Each transaction tag must identify a distinct destination block, and compute may consume
only the tag whose completion barrier has passed. A buffer cannot be overwritten while
its request is outstanding or its prior contents are in use. Full-device mapping must be
one reader/one bank; allowing two readers to target one bank reintroduces contention and
invalidates aggregate scaling. Physical routes and VCs must match the harvested device,
and per-bank byte counts must be balanced. In the matmul mapping, every `in1` shard is
owned once, every compute core receives the matching `in0` shard, and output return
cannot overwrite contiguous top-row storage still in use.

### Where the report makes it concrete

The pinned measurements separate theoretical channel rate from application realization.
At 12 GB/s and 14 GB/s bank settings, aggregate specifications are 288 and 336 GB/s;
the microbenchmark reports 267 and 310 GB/s. Llama3-70 decode is 239–260 and 247–294
GB/s; Mixtral8x7b is 243–261 and 267–300 GB/s. The gap from microbenchmark to matmul is
expected: multicast, compute balance, output traffic, and shard padding enter the latter.
The report's future-work note explains one remaining imbalance—tile width 32 rarely
divides an `in1` width evenly across 12 banks; proposed 32x16 or 32x8 tiles reduce padding
but are not demonstrated as an implemented result in this source.

### How the decision is tested

Start with one reader/bank and compare block-then-barrier against the two-tag pipeline at
identical bytes and block size. A timeline should show the idle request gap disappear;
verify block contents before measuring bandwidth. Scale one bank at a time, recording
per-bank service rate, reader issue/barrier time, link/VC utilization, and aggregate
GB/s. Compare concentrated readers with bank-adjacent placement, then enable distinct
VCs for same-row pairs. On harvested systems, log the actual physical mapping and audit
route overlap before attributing a regression to DRAM.

For the sharded matmul, compare interleaved and bank-sharded `in1` with identical math,
including double buffering and `in0` multicast. Measure useful (unpadded) bytes as well
as transferred bytes and slowest-core work. The causal success pattern is continuous
single-bank requests, near-linear bank scaling, balanced per-bank traffic, and model
bandwidth below but tracking the microbenchmark ceiling. Adding readers to a hot bank or
padding one shard heavily should not be reported as a DRAM-frequency limitation.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md):

- **Single-bank baseline.** The source's one-bank reader establishes burst size,
  outstanding `noc_async_read` operations, barrier cadence, and circular-buffer depth
  without cross-bank balance. Its plateau is a path-specific baseline, not full-device
  DRAM bandwidth.

- **Full-device scaling.** Wormhole reader/core mapping and sharded-DRAM examples
  distribute traffic across architecture banks. Verify bank placement, equal bytes per
  reader, and per-bank utilization; adding cores that target the same constrained bank
  should not be counted as useful scaling.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report shows why one reader or one bank cannot deliver full-device DRAM
    bandwidth and how to use bank-level parallel readers, suitable burst/page sizes,
    placement, and enough outstanding NoC reads to approach the memory roofline.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every read must use an aligned valid DRAM range and a reserved destination region; a
    circular-buffer page may be published only after its NoC read completes, and it may
    not be reused before the consumer releases it.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Pages are distributed across DRAM banks → a reader assigned to each bank issues
    asynchronous NoC reads → bursts arrive in reserved L1/CB pages → a read barrier
    establishes arrival → pages are published to the consumer or measured sink → the
    next batch keeps multiple banks busy.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** DRAM bank count, bank-to-NoC placement, burst thresholds,
    worker mapping, NoC choice, channel bandwidth, and measured saturation point are
    architecture-specific.

    **Durable model.** Exploit independent banks, maintain enough memory-level
    parallelism, align transfers, avoid hot spots, double-buffer producer/consumer work,
    and distinguish per-bank saturation from aggregate-device saturation.

## Source and delta

- **Original source:** [`tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
