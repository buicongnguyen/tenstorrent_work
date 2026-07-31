<!-- rewrite-status: seed -->
# SFPU Eltwise Chain

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md"><code>tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 299 |
| Section headings | 17 |
| Fenced code examples | 13 |
| Markdown images | 0 |

### Section outline

- Building and Running the Example
- Main Program Overview
  - Device and Program Setup
  - Core Configuration
  - Input Data Preparation
  - Memory Buffers
  - Circular Buffers
  - Kernel Setup
  - Running and Validation
- Kernel Descriptions
  - Reader Kernel
  - Writer Kernel
  - Compute Kernel - The SFPU Chaining
  - Key SFPU Chaining Concepts
- Expected Output
- Benefits of SFPU Chaining
  - Important Notes on SFPU Precision

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The example chains several elementwise SFPU operations while a tile remains in the
    compute pipeline, eliminating intermediate pack-to-memory, writer, reader, and
    unpack stages between operations. The saved traffic and launches are the intended
    performance gain.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The fused instruction order, constants, approximation modes, and final rounding must
    implement the intended mathematical chain. The tile must stay owned by the compute
    stage until the chain is complete and be published exactly once afterward.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A reader publishes an input tile → compute waits and unpacks it → SFPU applies the
    ordered elementwise operations to the live tile/register state → pack converts the
    final result → the output CB is published → a writer stores it for host comparison.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Available SFPU functions, approximation behavior,
    tile/register APIs, fidelity, CB identifiers, and cycle savings depend on the Tensix
    generation and low-level library.

    **Durable model.** Fuse producer-consumer chains when intermediates have no external
    users, preserve operation order and numerical policy, keep ownership local through
    the fusion, and measure eliminated movement against any register-pressure cost.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
