<!-- rewrite-status: seed -->
# Data Reuse in [matmul_multicore_reuse]

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md"><code>tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md</code>. This learner page
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 231 |
| Section headings | 4 |
| Fenced code examples | 11 |
| Markdown images | 0 |

### Section outline

- Fine-Grained Block Size Control
- Intermediate Circular Buffer Configuration
- Stride Kernel Arguments
- Conclusion

## Improvement plan

1. **Architecture pressure.** Derive A/B reuse from the M/N/K block nest and select
   fine-grained block sizes that fit input CBs, destination/intermediate state, and double
   buffering while keeping edge cores useful.

2. **Flow to make explicit.** Draw A/B block reads, CB reserve/publish, repeated
   output-subblock compute with one resident operand, intermediate K accumulation, final
   pack, output CB publication, and writer reclamation.

3. **Invariant to prove.** Prove each output tile receives all K-block products exactly once
   and that partial state is never packed, overwritten, or exposed as final before the
   reduction completes.

4. **TT-Metal evidence to connect.** Connect the plan to `get_large_matmul_params`,
   `interm0_cb_index`, `bmm_tile_layout.cpp`, `bmm_large_block_zm.cpp`, `cb_reserve_back`,
   `cb_wait_front`, and `pack_tile`.

5. **Experiment and expected observation.** Sweep one block/reuse dimension at fixed math
   and output partition; expected result: operand read bytes and compute input waits
   decrease until L1 pressure, reduced buffering, or imbalance offsets additional reuse.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md):

- **Block configuration.** `get_large_matmul_params` chooses block sizes that drive
  `bmm_tile_layout.cpp` movement and `bmm_large_block_zm.cpp` compute. The chosen tiles
  must fit circular-buffer and destination capacity while covering M, N, and K exactly.

- **Ownership loop.** `cb_reserve_back`, producer writes, push, `cb_wait_front`,
  `pack_tile`, and pop form the reuse protocol; `interm0_cb_index` carries intermediate
  state. Match loop counts and release points so a block is retained for all intended
  reuse and reclaimed immediately afterward.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The optimization blocks matmul so each A or B block is reused for several output
    sub-blocks before eviction, increasing arithmetic intensity and reducing DRAM/NoC
    demand relative to rereading operands for every output tile.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    For every output tile, all K blocks must be accumulated exactly once in the correct
    pairings; an intermediate destination/CB cannot be packed, overwritten, or exposed
    as final output before its K reduction is complete.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Readers load a block of A and B into circular buffers → compute iterates output
    sub-blocks that reuse one resident operand → partial sums remain in destination or an
    intermediate CB across K blocks → the final K step packs completed output tiles →
    writers commit them to memory.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Block dimensions, stride arguments, destination capacity, CB
    allocation, fidelity, tile shape, and optimal reuse direction depend on architecture
    and tensor shape.

    **Durable model.** Choose blocking from local capacity, maximize reuse before
    eviction, make the reduction lifetime explicit, balance reuse against parallelism,
    and verify that reduced reads—not only changed loop structure—appear in profiling.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md`
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
