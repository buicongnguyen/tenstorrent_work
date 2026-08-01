<!-- rewrite-status: improved-draft -->
# [skip ci] ViT in TT-NN for Blackhole

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md"><code>tech_reports/ViT-TTNN/vit_bh.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned Blackhole P150 path fixes a 10x12 full grid for block-sharded projections but
uses a batch-dependent grid for attention. This is a utilization/capacity compromise:
QKV, self-output, LayerNorm, and FFN benefit from all 120 cores, while height-sharded
attention wants its Y dimension tied to batch/head ownership. Consequently the QKV
tensor is explicitly resharded before head split and context is converted back to the
10x12 block grid afterward. For high-resolution images, the dominant constraint changes
from matmul utilization to the quadratic `seqL x seqL` attention matrix. The source
therefore stages Q/K/V in DRAM and uses chunked SDPA rather than materializing the full
score matrix in L1.

### How work and data move

For the standard path, `seqL=224` (196 patches plus CLS and padding), `dim=768`, and 32x32
tiles give `seqL_t=7`, `dim_t=24`, and two feature tiles per grid-X core. LayerNorm and
fused QKV run on `(12,10)`; QKV produces six output tiles/core using
`MatmulMultiCoreReuseMultiCastProgramConfig`. `ttnn.reshard` then moves it to
`config.core_grid`, and `split_query_key_value_and_split_heads` produces height-sharded
`[b,12,224,64]` Q/K/V. QxK yields `[b,12,224,224]`; explicit
`ttnn.mul_(1/sqrt(head_size))` precedes `softmax_in_place` because the alternative
`attention_softmax_` requires a mask and ViT has none. PxV produces context,
`concatenate_heads` restores `[b,seqL,dim]`, and `to_memory_config` places it on the
full block grid for self-output, residuals, and FFN. FF1 fuses GELU and FF2 returns to
`dim` without leaving block-sharded L1.

High resolution uses `scaled_dot_product_attention` with
`SDPAProgramConfig(q_chunk_size=256, k_chunk_size=256,
exp_approx_mode=False)` on the full grid and a `WormholeComputeKernelConfig` set to
HiFi4, exact math mode, and FP32 destination accumulation. `nlp_create_qkv_heads`
outputs Q/K/V directly to DRAM with `transpose_k_heads=False`; SDPA handles K transpose
and streams chunks. Afterward a DRAM staging hop precedes block-sharded self-output.

### What must never break

Every reshard must preserve token and fused-QKV feature order; `12 * 64` must reconstruct
the 768-wide hidden state. Storage padding from 197 logical tokens to a padded length of
224 must not silently become 27 model tokens. Because this Blackhole path explicitly
uses no attention mask, verify the TT-NN operators' logical-shape/padding behavior rather
than assuming a user mask removes those lanes. Standard attention must apply scaling
before the same softmax axis used by the reference. High-resolution SDPA is non-causal
(`is_causal=False`) and must be numerically equivalent to bidirectional ViT attention
despite chunking; accurate
exponential and FP32 accumulation are part of that stability choice. Q/K/V and residual
tensors may be deallocated/reallocated only after their last consumer. Grid arithmetic
must divide padded tile dimensions; otherwise “using more cores” produces padding,
imbalance, or an invalid program rather than free parallelism.

### Where the report makes it concrete

At 768x768 and 16 heads, the source estimates each Q/K/V tensor at about 4.7 MB and all
three at roughly 14 MB. It contrasts a full attention matrix of 169.9 MB with an 18.9 MB
256-query chunk; its table reports reductions growing from 2.3x at sequence 576 to 16x
at sequence 4096. These are arithmetic estimates from the pinned assumptions, not
measured P150 peak memory. The source also names `should_reallocate_in_attention` for
certain batch regimes and describes L1 -> DRAM -> differently sharded L1 when direct
reshard is unavailable. Those operations buy capacity/defragmentation at explicit NoC
and DRAM cost and must appear in end-to-end accounting.

### How the decision is tested

For standard ViT, compare every tensor before/after the two grid transitions, QxK,
scaled softmax, PxV, residuals, and FFN against a fixed Torch run. Sweep batch size
through the branch that toggles `should_reallocate_in_attention` and measure reshard,
reallocate, and matmul time separately. For high resolution, compare manual attention
and SDPA on a size where both fit, then scale sequence while recording actual DRAM/L1
peak, chunk count, NoC bytes, PCC/max error, and latency. A memory-success claim requires
the measured allocator peak, not only the report's score-matrix formula. Finally vary
chunk size and grid only within legal divisibility; accept a Blackhole tuning when the
full encoder remains numerically equivalent and total time/memory improves after all
staging transitions.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md):

- **Generation boundary.** The source's `WormholeComputeKernelConfig` comparison marks a
  configuration inherited from another generation, not a guarantee of Blackhole
  equivalence. Re-establish grid, fidelity, accumulator, and memory assumptions on the
  Blackhole path.

- **Attention/matmul path.** `vit_layer()`, `b × seqL × dim`, and
  `transpose_mcast=False/True` connect model shape to operand distribution. Measure both
  orientations with their conversions and validate encoder output before claiming the
  Blackhole-specific choice is better.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
