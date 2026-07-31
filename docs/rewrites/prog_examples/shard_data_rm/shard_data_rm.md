<!-- rewrite-status: seed -->
# Data Sharding (Multicore)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md"><code>tech_reports/prog_examples/shard_data_rm/shard_data_rm.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 197 |
| Section headings | 1 |
| Fenced code examples | 11 |
| Markdown images | 0 |

### Section outline

- Building and Running the Example

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The example distributes row-major tensor pages across several cores so later work
    can consume local L1 shards instead of repeatedly gathering an interleaved global
    buffer. Its task is both address mapping and ownership transfer.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The shard specification and per-core ranges must cover the logical tensor exactly
    once in the promised order. Page size, row stride, orientation, and writer
    reconstruction must agree so no row is skipped, duplicated, or assigned to the wrong
    core.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Row-major pages begin in an interleaved/global buffer → host runtime arguments
    assign page ranges to cores → readers calculate source bank/offset and move pages
    over NoC → each core fills its local shard → downstream work or writers consume
    those pages → optional recomposition restores logical order.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Core grid, shard shape/orientation, interleaving banks, page
    alignment, NoC coordinates, and buffer APIs depend on the example and architecture.

    **Durable model.** Define logical page order first, partition it deterministically,
    make placement metadata shared by producer and consumer, validate reconstruction,
    and choose sharding only when it improves the next consumer's locality.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/shard_data_rm/shard_data_rm.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
