<!-- rewrite-status: improved-draft -->
# LLMs in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/llms.md"><code>tech_reports/LLMs/llms.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Prefill and decode traverse the same transformer but present opposite machine shapes.
Prefill has many sequence rows, enough matrix work to favor compute throughput; decode
has one new token per user, repeatedly reads resident weights and an expanding KV cache,
and is more exposed to DRAM, dispatch, and collective latency. The pinned report
therefore uses mode-specific tensor shapes, sharding, RoPE preparation, attention
kernels, and matmul program configurations rather than one static graph.

The durable architectural choice is to keep state and transformations on device. Token
IDs are smaller than embeddings, only the last prefill token needs to return, rotation
matrices should be reused or generated device-side, and sampling can remain on device.
Every host round trip can serialize the next decode step; every unnecessary tilize,
untilize, or reshard consumes bandwidth without model arithmetic.

### How work and data move

An input token is embedded, normalized, projected into Q/K/V, and reshaped into heads.
`ttnn.experimental.rotary_embedding_llama` transforms Q and K. Prefill initializes
cos/sin matrices once for its sequence; decode uses `RotarySetup` to select matrices for
each user's changing position. Its sparse tile-sized transform is replicated per batch
and sharded so each core receives one tile. K/V then enter persistent cache: prefill can
use `ttnn.experimental.paged_fill_cache`, while decode updates `cur_pos` through
`ttnn.experimental.paged_update_cache` using a list or device
`update_idxs_tensor`.

Prefill invokes `ttnn.transformer.scaled_dot_product_attention`; decode uses
`scaled_dot_product_attention_decode` or
`paged_scaled_dot_product_attention_decode` with a page-table tensor. The pinned prose
names the extra argument `page_table_tensor`, while its code example passes
`page_table=page_table`; verify the callable signature in the pinned implementation
instead of copying either spelling without checking. In the report's recommended causal
decode path, `cur_pos`/`cur_pos_tensor` bounds the valid cache and `is_causal=True`
removes the explicit mask; non-causal cross-attention must provide one.
`ttnn.experimental.nlp_concat_heads_decode` restores head layout before
`ttnn.linear` output projection. Residual/normalization and the gated MLP follow, then
final norm and LM head produce logits. A device-resident position tensor can be advanced
with `ttnn.add`, allowing trace replay despite changing token position.

### What must never break

For each request, K and V for token `t` must be written once to the physical page named
by its logical position and page table, then attention may read only permitted positions.
Batch/user identity must survive sharding and head reshape; GQA Q heads must map to their
own KV group. A traced decode graph requires static shapes and addresses, so changing
values live in preallocated device tensors rather than Python lists. Distributed norm
has a related invariant: `rms_norm_pre_all_gather` produces per-shard statistics,
`ttnn.all_gather(dim=3)` replicates all device statistics, and
`rms_norm_post_all_gather(...,stats=...)` normalizes the local hidden shard with global
statistics. Skipping or misordering the gather yields locally normalized but globally
wrong activations.

### Where the report makes it concrete

Matmul configuration converts model shape into core work. In
`ttnn.MatmulMultiCoreReuseMultiCastProgramConfig`, `cores_y` partitions M and `cores_x`
partitions N; `in0_block_w` divides K. `out_subblock_h*out_subblock_w` must fit DST—eight
tiles on Wormhole for BF16 accumulation, four for FP32 in this source. Decode matmuls are
often DRAM-bound and candidates for DRAM sharding; collectives can sometimes overlap
with compute through `ttnn.experimental.all_gather_matmul`. Lower datatype/fidelity may
increase throughput, but accuracy decides whether BFLOAT8_B/BFLOAT4_B and HiFi2/LoFi
are acceptable.

At the graph level, trace removes repeat dispatch; the pinned report says it typically
reduces op-to-op gap below 6 microseconds. It also separates two causes: Python/host time
and device dispatch. Fusing `LayerNorm` or `ScaledDotProductAttentionDecode`, reducing
runtime arguments, and constructing shard/program configs once address different parts
of that gap.

### How the decision is tested

Validate modules first: embedding, RoPE at several positions, distributed norm, paged
cache fill/update, attention, MLP, and LM head each against a host reference. For cache
tests, use distinct values per request/page and verify both physical writes and returned
attention. Then benchmark prefill time-to-first-token separately from steady decode
latency with weights/KV resident. Compare list versus device-tensor `cur_pos`, traced
versus untraced decode, and DRAM-interleaved versus DRAM-sharded matmuls. Profile one
layer with `TT_METAL_DEVICE_PROFILER=1`, `process_ops_logs.py`, and `tt-perf-report`,
using a Tracy signpost to delimit the interval. An optimization is accepted only if it
improves the intended regime without extra collectives/reshards, cache misplacement, or
module-level accuracy loss.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/llms.md):

- **Model-to-operation boundary.** `RotarySetup`,
  `ttnn.experimental.rotary_embedding_llama`, normalization `stats` tensors, attention,
  and cache operations each define a checkpoint with explicit shape, layout, dtype, and
  mesh placement. Validate those checkpoints before assembling the decoder layer.

- **Program selection.** Mesh configurations and model-specific program factories
  determine sharding, core grids, and cached-program identity. A functionally identical
  module can still compile or communicate differently when sequence length, batch,
  KV-cache position, or memory config changes.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/llms.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report maps transformer inference into TT-NN for two distinct regimes:
    throughput-oriented prefill and latency/bandwidth-sensitive autoregressive decode.
    It must manage weights, activations, KV cache, tensor parallelism, and frequent
    layout decisions across many modules.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    For token position `t`, attention may use exactly the permitted key/value positions,
    the KV cache update must land in the slot owned by that sequence, and every
    reshape/shard operation must preserve head, batch, sequence, and hidden-dimension
    meaning.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A token or prompt is embedded → normalization produces Q/K/V inputs → attention
    reads and updates the KV cache → causal attention returns a context vector → output
    projection, residual, normalization, and MLP execute → final normalization/head
    produces logits → the selected next token feeds the next decode iteration.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Model configs, supported sequence lengths, mesh layouts,
    sharding schemes, kernels, data types, and measured performance depend on the model,
    device generation, and TT-NN revision.

    **Durable model.** Separate prefill from decode, follow bytes as closely as FLOPs,
    keep persistent state well owned, amortize weight movement, validate module
    checkpoints, and choose tensor/data parallelism from communication as well as
    compute.

## Source and delta

- **Original source:** [`tech_reports/LLMs/llms.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/llms.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/LLMs/llms.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
