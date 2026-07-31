<!-- rewrite-status: seed -->
# FlashDecode on Tenstorrent's Wormhole Architecture

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashDecode.md"><code>tech_reports/FlashAttention/FlashDecode.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/FlashAttention/FlashDecode.md</code>. This learner page
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 186 |
| Section headings | 17 |
| Fenced code examples | 6 |
| Markdown images | 5 |

### Section outline

- 1 Introduction
  - 1.1 Common Terminology
  - 1.2 Group Query Attention (GQA)
- 2 Background
  - 2.1 What is KV Cache and How it Can Speed Up Decoding
  - 2.2 How to Smartly Utilize Tenstorrent's Tile-based Architecture for Attention Decoding
  - 2.3 FlashDecode
- 3 Implementation Details
  - 3.1 Parallelization
  - 3.2 Step-by-step Visualization of an Average Case
  - 3.3 Asynchronous Execution, NOC, Circular Buffers, and Semaphores
  - 3.4 Causal vs. Non-causal
- 4 Performance Analysis
  - 4.1 Generic Performance
  - 4.2 Long Context Length Performance on Llama 3.1 8B, Tensor Parallelism on 1,2,4,8 Devices
- 5 Future work
- References

## Improvement plan

1. **Architecture pressure.** Explain why decode's small query dimension under-fills cores
   while the growing KV cache dominates bytes, and calculate when splitting the KV sequence
   can amortize its final cross-worker reduction.

2. **Flow to make explicit.** Draw `query distribution → per-worker K/V shard read → local
   scores/mask → partial max/sum/weighted value → global max propagation/rescaling →
   sum/numerator reduction → normalized output`.

3. **Invariant to prove.** Prove each partition covers a disjoint permitted KV range and
   that partial online-softmax state is combined with the global maximum exactly, preserving
   token position, causal range, and grouped-query head mapping.

4. **TT-Metal evidence to connect.** Connect the plan to `n_qh_per_kvh`, `n_q_heads`,
   `n_kv_heads`, the report's `bsz*n_kv_heads` partitioning, tile-volume expressions,
   KV-cache readers, and reduction kernels.

5. **Experiment and expected observation.** Sweep context length and worker count with
   identical queries/cache; expected result: parallel KV bandwidth improves long-context
   decode until reduction/synchronization dominates, while short contexts may favor fewer
   workers.

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
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
