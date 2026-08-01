<!-- rewrite-status: improved-draft -->
# FlashAttention on Tenstorrent’s Wormhole Architecture

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md"><code>tech_reports/FlashAttention/FlashAttention.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The naive `matmul -> softmax -> matmul` path materializes a score matrix that grows with
sequence length squared. Sharding those three operations in L1 removes some DRAM round
trips, but the pinned report says long sequences still exceed L1 and spill
intermediates. FlashAttention-2 changes the algorithm: hold one Q chunk and online
softmax state locally while K/V chunks stream through, so the full score matrix never
becomes an external tensor. This is one of the cases where a fused operator has an
algorithmic memory-complexity advantage beyond TT-NN's normal sharded-op composition.

Wormhole's execution structure makes this mapping natural. An 8x10 Tensix grid shares a
NoC and 12 GDDR6 channels; each Tensix has 1.5 MB L1 and five concurrent RISC-V roles.
Two issue L1/DRAM or L1/L1 NoC transfers, while Unpack, Math, and Pack drive tile compute.
Chunk sizes must therefore fit Q, double-buffered K/V, output accumulator, and softmax
statistics in per-core L1 while supplying enough 32x32 tile work to hide movement.

### How work and data move

The output is partitioned over batch, head, and Q sequence chunks. A reader loads a Q
chunk, then iterates over K and V chunks from DRAM. Compute updates the online attention
result and statistics in L1; only after all permitted KV chunks are consumed does the
writer return that output chunk to DRAM. Circular buffers are producer/consumer queues
between the concurrent reader, compute, and writer RISCs. Q, K, and V CBs hold two
chunks, so while compute consumes one slot the reader can fill the other. Compute waits
for the first Q/K data, the reader waits before overwriting a V slot still in use, and
the writer waits for a complete output—these waits are the ownership edges that make
overlap correct.

Causal scheduling removes two kinds of waste. Q chunk `Qi` reads only K/V chunks at
equal or earlier token indices. Consecutive Q assignment would leave later-Q cores with
more inner-loop work, so core 0 receives low/high pair `Q0,Q(n-1)`, core 1 receives
`Q1,Q(n-2)`, and so on. The report attributes a 1.6x speedup to this balanced assignment.
Only diagonal score chunks require the causal mask, reducing mask reads from DRAM.

### What must never break

Each Q output owner must cover every allowed KV chunk exactly once and no future chunk.
Its online maximum, normalization sum, and weighted-value accumulator must describe the
same set of keys after every iteration; changing the running maximum requires rescaling
prior partial state before combination. A CB slot cannot be refilled until its consumer
releases it, and output cannot be published before the last KV update. Low/high load
balancing changes assignment only, never causal membership or final output order.
Failures appear as incorrect causal tokens, chunk-boundary-dependent numerical error,
deadlock from mismatched CB counts, or nondeterminism from premature slot reuse.

### Where the report makes it concrete

Tilized tensors place each 32x32 tile contiguously, enabling large NoC bursts and matching
the matrix engine's native granularity. `q_chunk_size` and `k_chunk_size` are explicitly
swept per input shape; V shares K's chunk size. The pinned benchmark varies head
dimension 64/128/256 and sequence 512–16K while keeping total tokens 16K, and compares
BF16 with BFP8. It reports 9x–44x speedup, 20x on average, over a baseline that writes
intermediates to DRAM. BFP8 does not deliver the twofold speedup its roughly halved input
bytes might suggest, evidence that matmul or softmax compute becomes limiting. Proposed
DST reuse, automatic DST accumulation, matmul/softmax compute-unit pipelining, K/V
multicast, and backward support are explicitly future work, not properties of this
implementation.

### How the decision is tested

Compare fused and materialized attention at identical batch/head/sequence/head-dimension
and causal settings, checking every Q-chunk boundary rather than only global PCC. Sweep
`q_chunk_size` and `k_chunk_size`, recording L1 fit, CB stalls, DRAM bytes, and device
time. Then compare consecutive-Q assignment with low/high pairing: total KV iterations
per core should balance and output remain unchanged. BF16/BFP8 timing plus reader/compute
occupancy distinguishes movement from compute limits. The expected signature is bounded
L1 intermediates, no quadratic score write, overlapped reader/compute activity, and a
causal work distribution consistent with the source's reported 1.6x scheduling gain.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md):

- **Mathematical state.** The tiled algorithm carries a running row maximum, exponential
  rescale, denominator, and weighted-value numerator across key/value blocks. Tensor
  dimensions and masking determine which tiles may contribute; those state updates must
  match the stable-softmax recurrence.

- **Asynchronous pipeline.** Reader circular buffers bring Q/K/V tiles, matrix
  operations form scores and value products, SFPU work performs exponentials and
  reductions, and writer buffers store normalized output. The source's pipeline overlap
  is valid only when CB ownership and partial-state dependencies remain ordered.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The bottleneck is the quadratic memory traffic and storage created by materializing
    the full attention-score matrix. The implementation tiles the sequence and computes
    an exact, numerically stable softmax online so K/V blocks can be streamed through
    limited L1 while matrix units remain useful.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    For every processed key block, the running maximum, normalization sum, and
    accumulated weighted value must represent all keys seen so far after rescaling into
    one common softmax frame. Masked entries must contribute neither probability mass
    nor output.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A query block is loaded and kept local → key and value blocks stream through
    circular buffers → QKᵀ produces a score tile → masking and the online maximum update
    rescale the old accumulator → exponentials update the running denominator and
    weighted-value numerator → the final normalized block is written.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Tile dimensions, L1 capacity, core partition, circular-buffer
    depths, math fidelity, Wormhole NoC behavior, and measured performance belong to the
    target implementation.

    **Durable model.** Use IO-aware tiling, fuse reductions with the consumer
    computation, maintain a stable online reduction state, double-buffer movement with
    compute, and choose parallelism from both capacity and reduction cost.

## Source and delta

- **Original source:** [`tech_reports/FlashAttention/FlashAttention.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/FlashAttention/FlashAttention.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
