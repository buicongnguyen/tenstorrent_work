<!-- rewrite-status: improved-draft -->
# ViT in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md"><code>tech_reports/ViT-TTNN/vit.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to identify which ViT encoder boundaries—patch
embedding, QKV/head transforms, attention, projection/residual, and MLP—justify
preserving, changing, or sharding layouts based on their next consumer and production
shape.

### How work and data move

The complete path is image patches and class/position tokens through `vit_layer`,
normalization, `vit_attention`, Q/K/V transforms, attention/projection, residual, MLP,
second residual, class-token extraction, and classifier output.

### What must never break

The non-negotiable invariant is that token/class order, head reshape/transpose,
scaling/masking, residual pairing, padded lanes, and classifier interpretation remain
reference-equivalent through every layout or sharding optimization.

### Where the report makes it concrete

The report makes the decision concrete by connecting the plan to `vit_layer()`, `b ×
seqL × dim`, `vit_attention`, `ROW_MAJOR`, column/row-major choices,
`transpose_mcast=False`, and the source's encoder configuration/code structure.

### How the decision is tested

The controlled procedure is to A/B-test one encoder layer with a canonical-layout
boundary removed. **Expected observation:** fewer conversion bytes and lower layer
latency with unchanged module PCC and no new conversion before the next consumer.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md):

- **Layer contract.** `vit_layer()` consumes and produces `b × seqL × dim`;
  `vit_attention` owns head partitioning and attention layout. Record every
  reshape/transpose so encoder residual paths meet again in the same logical order.

- **Matmul orientation.** `ROW_MAJOR`, column/row-major choices, and
  `transpose_mcast=False` select operand movement and multicast behavior. Compare
  conversion/reshard bytes with matmul time; an isolated faster kernel can lose
  end-to-end when its required orientation differs from adjacent layers.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
