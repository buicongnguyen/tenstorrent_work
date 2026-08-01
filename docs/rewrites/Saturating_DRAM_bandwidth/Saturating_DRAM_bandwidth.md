<!-- rewrite-status: improved-draft -->
# Saturating DRAM bandwidth

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md"><code>tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to calculate per-bank and aggregate bandwidth targets,
outstanding-read depth, burst/page size, reader-core placement, L1 destination capacity,
and NoC route pressure instead of assuming more readers imply more bandwidth.

### How work and data move

The complete path is pages interleaved/sharded across DRAM banks through one reader per
bank, asynchronous NoC reads, reserved L1/CB pages, read barriers, consumer publication,
and page reclamation.

### What must never break

The non-negotiable invariant is that every transfer is aligned and in range,
destinations are reserved before issue, pages publish only after completion, and
bank/core work is balanced enough that one channel does not determine the device rate.

### Where the report makes it concrete

The report makes the decision concrete by connecting the report's single-bank and
full-device reader examples to architecture bank placement, `noc_async_read`/barrier
loops, CB depth, Wormhole reader/core mapping, and sharded-DRAM examples.

### How the decision is tested

The controlled procedure is to scale from one bank/reader to all banks while recording
per-bank bytes and aggregate rate. **Expected observation:** near-linear growth until
NoC, issue, or consumer capacity becomes the new ceiling, with no gain from extra
readers on one hot bank.

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
