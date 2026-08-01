<!-- rewrite-status: improved-draft -->
# ViT in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md"><code>tech_reports/ViT-TTNN/vit.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned ViT implementation treats layout as part of each operator contract because
the same logical `b x seqL x dim` tensor participates in two different parallel
structures. LayerNorm, fused QKV, self-output, and the FFN use 2-D block sharding so M
is partitioned over core-grid Y and feature/output width over X; the two attention BMMs
use height sharding so each core owns an independent head/image slice. The transitions
are justified by reuse: block-sharded matmuls multicast slices of input 0 along core rows
and slices of interleaved input 1 along columns, whereas a height-sharded BMM needs no
multicast because each core computes one head. Keeping adjacent operations in the same
layout avoids inter-Tensix movement, but head split/concatenate are necessary semantic
redistributions rather than removable conversions.

### How work and data move

`vit_patch_embeddings` receives NHWC pixels, `ttnn.fold`s 16x16 patches, moves the
folded tensor to L1/tile `bfloat8_b`, and projects it with `ttnn.linear`. It returns to
row-major for reshape to 196 patch tokens; `ttnn.concat` prepends the CLS token and
`ttnn.add` applies positional embeddings. `vit_encoder` converts the result to a
row-major-oriented block shard over `CoreGrid(y=batch_size, x=12)` and iterates 12
`vit_layer` calls.

Inside a layer, sharded LayerNorm feeds one fused `ttnn.linear` producing QKV with
`per_core_M=seqL_t`, `per_core_N=3*dim_t__x`, and `transpose_mcast=False`.
`split_query_key_value_and_split_heads` changes the logical shape to
`b x head_count x seqL x head_size` in height-sharded L1. QxK uses
`MatmulMultiCoreReuseProgramConfig` to produce `seqL x seqL` scores per head;
`attention_softmax_` scales/normalizes them, and PxV returns `seqL x head_size`.
`concatenate_heads` restores block-sharded `b x seqL x dim`; self-output linear and the
first residual add stay there. The second LayerNorm feeds FF1, whose
`fused_activation=(GELU, True)` avoids a materialized activation pass; FF2 projects
`4*dim` back to `dim` and is immediately added to its residual.

### What must never break

The first token must remain CLS and the 196 patch tokens must retain fold/reshape order.
Q, K, and V must split the fused feature axis identically to weight preprocessing; K
orientation and the softmax axis must make each row a distribution over the same token
sequence. `head_count * head_size` must equal `dim` (the report uses 12 heads, 768
features, 64 per head), and padded sequence length 224 must not make padded lanes
semantically visible. Each residual must meet the corresponding pre-attention or
pre-FFN tensor in identical logical order and block sharding. A `ttnn.deallocate` may
occur only after the last residual/head consumer; local memory savings do not excuse a
branch lifetime violation.

### Where the report makes it concrete

For the reported configuration, `seqL_t=224/32=7`, `dim_t=768/32=24`, and grid X=12
gives `dim_t__x=2`; the QKV output width is six tiles/core. QxK uses seven sequence tiles
for both `per_core_M` and `per_core_N`, while PxV uses two head-size tiles for N. These
numbers make grid divisibility and L1 block sizes inspectable. The source notes that a
column-major shard placement with `transpose_mcast=True` may fit another device/grid
better; “row-major” here describes shard placement, not `ROW_MAJOR_LAYOUT`. The
architecture trade is therefore multicast direction plus any conversion cost, not a
universal preference for one orientation.

### How the decision is tested

Checkpoint patch embeddings, fused QKV, each Q/K/V head tensor, scores before and after
softmax, context, both residual adds, and FFN output against Torch. Verify logical and
padded shapes, per-head ordering, and PCC/error before timing. Profile a complete layer
with the report's block/height/block sequence, then A/B only a legal shard orientation
or adjacent-layout preservation; count `to_layout`, `to_memory_config`, reshard bytes,
NoC multicast, peak L1, and end-to-end layer time. A faster isolated matmul is rejected
if it introduces a larger head split/concatenate or next-layer conversion. Repeat all
12 layers and the classifier, because small `bfloat8_b` or softmax deviations can
accumulate while one-layer PCC still passes.

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
