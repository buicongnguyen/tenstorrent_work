<!-- rewrite-status: seed -->
# [skip ci] ViT in TT-NN for Blackhole

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md"><code>tech_reports/ViT-TTNN/vit_bh.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ViT-TTNN/vit_bh.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 1266 |
| Section headings | 48 |
| Fenced code examples | 46 |
| Markdown images | 19 |

### Section outline

- Contents
- 1. Overview
- 2. Blackhole Architecture Differences
  - 2.1 Core Grid Configuration
  - 2.2 Compute Kernel Configuration
- 3. ViT TT-NN Optimization Techniques
  - 3.1 Sharding on all relevant OPs
  - 3.2 Matmul sharding variants in ViT
    - 3.2.1 Matmul Reuse (BMM)
    - 3.2.2 Matmul Reuse Mcast (2D)
    - 3.2.3 Matmul Reuse Mcast (1D)
  - 3.3 Transformer optimizations
- 4. ViT TT-NN Code Structure
  - 4.1 Top-level modules
  - 4.2 Embeddings module
  - 4.3 Encoder module
  - 4.4 Encoder One Layer module
- 5. ViT Encoder Layer TT-NN Deep Dive for Blackhole
  - 5.1 Input
  - 5.2 Sharding parametrization
  - 5.3 Layer Normalization (Layernorm)
  - 5.4 Multi-Head Self-Attention
    - 5.4.1 Q,K,V Generation (Fused Linear)
    - 5.4.2 Resharding (Core Grid Transition)
- … 24 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The Blackhole report retargets and optimizes the ViT path for a new generation whose
    core, memory, and operation characteristics differ from the earlier implementation.
    The key task is separating portable model logic from hardware-specific program
    choices.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    For identical inputs and weights, the Blackhole path must preserve the same logical
    token sequence, attention/MLP computation, residual graph, and output interpretation
    as the validated reference, within an explicitly chosen numerical tolerance.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The image follows patch embedding and encoder stages → TT-NN selects
    Blackhole-specific layouts/program configurations for attention and MLP → sharded activations
    flow through residual boundaries → the classifier output is composed/read back →
    checkpoints compare with reference and prior-generation behavior.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Blackhole architecture differences, core grids, L1/NoC
    assumptions, operation availability, program configs, and benchmark results are
    generation-specific.

    **Durable model.** Retarget from a correctness baseline, isolate device-specific
    policy behind configuration, re-derive capacity and parallelism rather than copying
    numbers, and use identical checkpoint tests to distinguish architecture bugs from
    model bugs.

## Source and delta

- **Original source:** [`tech_reports/ViT-TTNN/vit_bh.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ViT-TTNN/vit_bh.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
