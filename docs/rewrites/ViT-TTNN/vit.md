<!-- rewrite-status: seed -->
# ViT in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md"><code>tech_reports/ViT-TTNN/vit.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ViT-TTNN/vit.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 712 |
| Section headings | 30 |
| Fenced code examples | 21 |
| Markdown images | 17 |

### Section outline

- Contents
- 1. Overview
- 2. ViT TT-NN Optimization Techniques
  - 2.1 Sharding on all relevant OPs
  - 2.2 Matmul sharding variants in ViT
    - 2.2.1 Matmul Reuse (BMM)
    - 2.2.2 Matmul Reuse Mcast (2D)
    - 2.2.3 Matmul Reuse Mcast (1D)
  - 2.3 Transformer optimizations
- 3. ViT TT-NN Code Structure
  - 3.1 Top-level modules
  - 3.2 Embeddings module
  - 3.3 Encoder module
  - 3.4 Encoder One Layer module
- 4. ViT Encoder Layer TT-NN Deep Dive
  - 4.1 Input
  - 4.2 Sharding parametrization
  - 4.3 Layer Normalization (Layernorm)
  - 4.4 Multi-Head Self-Attention
    - 4.4.1 Q,K,V Generation using the Fused Linear OP
    - 4.4.2 Splitting into Q-K-V
    - 4.4.3 Attention Mechanism
    - 4.4.4 Matmul with Value
    - 4.4.5 Concatenating Heads and Self-Output Linear OP
- … 6 additional headings in the original

## Improvement plan

1. **Architecture pressure.** Identify which ViT encoder boundaries—patch embedding,
   QKV/head transforms, attention, projection/residual, and MLP—justify preserving,
   changing, or sharding layouts based on their next consumer and production shape.

2. **Flow to make explicit.** Draw image patches and class/position tokens through
   `vit_layer`, normalization, `vit_attention`, Q/K/V transforms, attention/projection,
   residual, MLP, second residual, class-token extraction, and classifier output.

3. **Invariant to prove.** Prove token/class order, head reshape/transpose, scaling/masking,
   residual pairing, padded lanes, and classifier interpretation remain reference-equivalent
   through every layout or sharding optimization.

4. **TT-Metal evidence to connect.** Connect the plan to `vit_layer()`, `b × seqL × dim`,
   `vit_attention`, `ROW_MAJOR`, column/row-major choices, `transpose_mcast=False`, and the
   source's encoder configuration/code structure.

5. **Experiment and expected observation.** A/B one encoder layer with a canonical-layout
   boundary removed; expected result: fewer conversion bytes and lower layer latency with
   unchanged module PCC and no new conversion before the next consumer.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report brings Vision Transformer inference into TT-NN and tunes patch embedding,
    attention, MLP, residuals, layout changes, sharding, and operation fusion so the
    model remains accurate while avoiding data-movement and launch overhead.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Patch/token order, class-token position, head reshapes, attention scaling/masking,
    residual pairing, and classifier output must match the reference model. Padding and
    sharding may change storage but not logical token semantics.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    An image becomes patch embeddings plus positional/class tokens → each encoder layer
    normalizes → forms Q/K/V → computes attention and projection → applies residual →
    runs normalized MLP and second residual → the class token reaches the classifier
    head → host output is compared.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Core grids, shard specs, fused TT-NN operations, supported
    batch/shape, data types, program configs, and Wormhole performance are
    implementation-specific.

    **Durable model.** Validate transformer submodules independently, preserve
    token/head meaning through reshapes, minimize layout round trips, keep reusable
    weights/local activations resident, and profile attention and MLP separately.

## Source and delta

- **Original source:** [`tech_reports/ViT-TTNN/vit.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ViT-TTNN/vit.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
