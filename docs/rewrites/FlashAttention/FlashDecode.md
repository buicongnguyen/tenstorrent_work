<!-- rewrite-status: improved-draft -->
# FlashDecode on Tenstorrent's Wormhole Architecture

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashDecode.md"><code>tech_reports/FlashAttention/FlashDecode.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Autoregressive decode has one new query token but a KV cache that grows with context.
Tenstorrent storage and compute operate on 32x32 tiles, so leaving sequence length one in
the query's tile-height dimension wastes 31 rows. The pinned layout instead uses query
shape `[1,bsz,n_q_heads,head_dim]`: query heads occupy tile rows, while work units are
`bsz*n_kv_heads` and the `n_qh_per_kvh` grouped-query heads execute within one core. The
kernel receives `cur_pos` in causal mode, so it reads only valid cache positions and
does not materialize a mask.

That mapping can still underfill a 64-core grid. The report's Llama 3.1 70B example on
eight devices has batch 16 and one KV head per device—16 independent work units for 64
cores. FlashDecode splits one KV head's sequence across multiple workers and reduces
their partial attention states. More workers expose DRAM bandwidth, but also add NoC
gather and reduction cost, so `SDPAProgramConfig.max_cores_per_head_batch` caps the fanout
at 16 in this snapshot.

### How work and data move

Each `(batch,kv_head)` receives `n_cores // (bsz*n_kv_heads)` cores when sufficient cores
exist. Query is small enough to process whole; `k_chunk_size` partitions both K and V.
Workers stream their assigned KV ranges from DRAM and compute a local online-attention
result. One reducer owns the final merge. A worker obtains the reducer's 64-bit NoC
address with `get_noc_addr`, writes its `cb_out` payload into a distinct offset of
`cb_gather_out` with `noc_async_write`, waits on `noc_async_write_barrier()`, and only
then increments the reducer semaphore with `noc_semaphore_inc`. The reducer waits with
`noc_semaphore_wait(...,num_workers)` before consuming gathered partials. Circular
buffers and semaphores use the same local address on every core, while the high address
bits select the core; correctness therefore depends on consistent allocation and unique
worker offsets.

When work units exceed cores, a core processes multiple full KV heads and no reduction
is needed. When one work unit fans out broadly, the same reduction path may dominate.
The average-case illustration uses `bsz=16`, one KV head, eight Q heads padded to 32,
and 64 cores; inputs come from DRAM and output remains in L1.

### What must never break

KV partitions for one batch/head must be disjoint and cover exactly the intended range.
Every Q head maps to its correct KV head through
`n_qh_per_kvh=n_q_heads//n_kv_heads`. A worker's payload must become globally visible
before its semaphore increment; otherwise the reducer can consume incomplete data.
Offsets in `cb_gather_out` cannot overlap, and the semaphore count must equal actual
workers. Online-softmax partials must be merged in one numerical frame, rescaling for
different maxima before sums and weighted values combine. In causal mode, each batch's
`cur_pos` bounds reads; in non-causal mode the full KV length is processed and the
provided `attn_mask` supplies validity. Mixing these contracts gives plausible but
incorrect attention.

### Where the report makes it concrete

The TT-NN entry point shown is
`ttnn.transformer.scaled_dot_product_attention_decode`; causal callers pass `cur_pos` or
a row-major `cur_pos_tensor`, while arbitrary non-causal masking supports cross-attention.
The performance denominator is
`4*bsz*kv_len*head_dim*n_q_heads/kernel_runtime`; the coarse BFP8 KV traffic estimate is
`2*bsz*head_dim*n_kv_heads*kv_len/kernel_runtime`. The report observes 2–10x over its
baseline and labels the result up to 180 Gb/s versus a cited 250 Gb/s Wormhole maximum
(even though the displayed estimate is defined in bytes per second). Its long-context
experiment reveals two slopes: before maximum core use, NoC reduction dominates; after
that, memory bandwidth dominates. For the T3K shape, 16 cores outperform all 64 because
all cores would reduce one KV head. Generic small query sequence lengths such as 4 or 8
remain future work; `share_cache` only emulates a narrower case via the batch dimension.

### How the decision is tested

Use identical Q/K/V and sweep context length, `k_chunk_size`, and
`max_cores_per_head_batch` across 1, 2, 4, 8, 16, 32, and 64 workers where legal. Verify
causal output per batch position and non-causal output with an explicit mask. Instrument
worker write completion, semaphore arrival, reducer start, and DRAM bytes. The expected
curve improves while additional workers expose KV bandwidth, then regresses when NoC
gather dominates; the reducer must never start before all barrier-ordered payloads are
visible. Repeat an extreme with more work units than cores to confirm that the no-reduce
path produces the same grouped-query mapping and numerical result.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashDecode.md):

- **Partition identity.** `n_qh_per_kvh`, `n_q_heads`, `n_kv_heads`, and the
  `bsz*n_kv_heads` worker partition decide which query heads share each KV head.
  Validate divisibility and head ownership before interpreting tile-volume or
  load-balance formulas.

- **Distributed reduction.** KV-cache readers produce local score blocks; reduction
  kernels combine partial maximum, sum, and weighted value with the required rescaling.
  The final normalization is correct only if each contributing shard participates
  exactly once and uses the same causal/current-position mask.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashDecode.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    Decode has a very small query length but an expanding KV cache, so ordinary
    attention parallelism under-utilizes compute and becomes dominated by reading K/V.
    The report splits the long key sequence across workers and combines partial
    online-softmax results.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Each partition's partial maximum, exponential sum, and weighted-value numerator must
    be merged with the global maximum using the exact rescaling factors. Token position,
    causal range, and KV-cache indices must refer to the same decode step.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The current query is distributed to workers → each worker reads its shard of K/V
    cache → it computes partial scores and a local `(max, sum, weighted value)` → a
    reduction finds/propagates the global maximum and rescales partials → sums and
    numerators combine → division produces the attention output.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Worker count, KV sharding, reduction topology, tile shape,
    memory placement, batch limits, and Wormhole performance numbers are
    implementation-specific.

    **Durable model.** When one dimension is too small for parallelism, split a
    reduction dimension, carry sufficient associative state for exact recombination,
    balance memory bandwidth across workers, and count the cost of the final reduction.

## Source and delta

- **Original source:** [`tech_reports/FlashAttention/FlashDecode.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashDecode.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/FlashAttention/FlashDecode.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
