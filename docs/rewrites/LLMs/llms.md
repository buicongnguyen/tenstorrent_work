<!-- rewrite-status: improved-draft -->
# LLMs in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/llms.md"><code>tech_reports/LLMs/llms.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to split the model plan into prefill and decode
regimes, then identify which transformer modules are compute-bound,
KV/weight-bandwidth-bound, launch-bound, or constrained by tensor-parallel communication
for production shapes.

### How work and data move

The complete path follows one token from embedding through normalization, Q/K/V and
rotary application, KV-cache update/read, causal attention, projection/residual, MLP,
final normalization/head, logits, and the next decode iteration.

### What must never break

The non-negotiable invariant is to preserve batch, sequence, head, hidden-dimension,
causal position, and KV ownership semantics through every reshape/shard; token `t` must
read only the permitted cache positions and update exactly its assigned slot.

### Where the report makes it concrete

The report makes the decision concrete by connecting modules to concrete operations such
as `ttnn.experimental.rotary_embedding_llama`, `RotarySetup`, normalization `stats`
tensors, attention/cache operations, mesh configs, and model-specific program factories
named by the source.

### How the decision is tested

The controlled procedure is to measure prefill time-to-first-token and steady decode
token latency separately while keeping weights/KV resident. **Expected observation:**
regime-specific configurations improve their targeted metric without cache growth,
reorder, or module-PCC errors.

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
