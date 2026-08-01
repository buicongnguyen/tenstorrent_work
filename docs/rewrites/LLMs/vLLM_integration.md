<!-- rewrite-status: improved-draft -->
# Integrating TT Models into vLLM

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/vLLM_integration.md"><code>tech_reports/LLMs/vLLM_integration.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

vLLM owns request admission, continuous batching, logical KV blocks, and serving; the TT
generation class owns model initialization, physical cache tensors, fixed-shape device
execution, and result placement. The integration contract exists because these systems
optimize different kinds of dynamism. vLLM changes active requests and page mappings
every step, while TT-NN trace replay requires constant input shapes. The pinned backend
therefore pads decode `tokens` and `start_pos` to `max_batch_size` and `page_table` to
`(max_batch_size,max_num_blocks)`. Values and occupancy change inside stable buffers;
the compiled graph shape does not.

Paged attention is mandatory in the pinned integration contract. Its page table
decouples a request's logical KV-block order from the physical cache blocks supplied to
the device, so scheduler-visible mappings can change without requiring those resident
blocks to be laid out contiguously in request order. TT-NN's `paged_fill_cache`,
`paged_update_cache`, and `paged_scaled_dot_product_attention_decode` consume that
mapping when selecting physical cache locations; they do not transfer ownership of the
blocks to the page table itself.

### How work and data move

`TTModelLoader::load_model` calls
`initialize_vllm_model(hf_config,mesh_device,max_batch_size,tt_data_parallel,
optimizations)`. Here `max_batch_size` spans all data-parallel groups/single-process
lanes, and `tt_data_parallel` counts KV-cache replicas/submeshes. Next,
`TTModelRunner::initialize_kv_cache` asks `allocate_kv_cache` for each layer with shape
`(max_num_blocks,num_kv_heads,block_size,head_size)`.

During prefill, `_prepare_model_inputs` supplies zero-padded `tokens`, `page_table`, and
`prompt_lens`; `prefill_forward` fills the paged cache and returns host outputs. During
decode, `decode_forward` receives fixed maximum shapes, updates pages at each
`start_pos`, runs paged attention, and returns host output unless
`read_from_device=False`. That latter mode supports asynchronous decode: submission and
readback can be separated so the scheduler need not block on each device step. Sampling
parameters (`temperature`, `top_p`, `top_k`) may be omitted for default host sampling or
used by explicitly enabled device sampling. `warmup_model_prefill` compiles the model
and captures prefill traces before serving traffic.

### What must never break

The page-table row used for a request, its token row, start position, KV replica/DP group,
and returned output row must remain one identity chain. Padding rows are capacity, not
requests, and may not mutate a live cache. `empty_slots` identifies a request's global
DP group only; the report explicitly says it is not the request's current batch index.
For fully-DP or DP-attention, each group's padded batch is concatenated consistently.
Trace may replay only after warmup has allocated matching shapes. A model must advertise
optional behavior honestly through `model_capabilities`; absent
`supports_prefix_caching`, `supports_async_decode`, or `supports_sample_on_device` keys
default to false, preventing the scheduler from exercising an unimplemented path.

### Where the report makes it concrete

The actual backend boundary is distributed across `platform.py` (configuration and
runtime class), `model_registry.py` (registration), `loader.py` (model construction),
`worker.py` (device/KV ownership), `model_runner.py` (input preparation and execution),
and `engine.py` (batch queues and gathered-DP orchestration). A new model is registered
with `ModelRegistry.register_model`; its TT generation class follows the
`LlamaForCausalLM` interface. Image+text models use the same contract with
`pixel_values` added to prefill. This pinned report supports only image+text among
multimodal inputs, so a generic multimodal claim would exceed the source.

### How the decision is tested

After offline single-request inference, run continuous batches with different prompt and
decode lengths, then exercise `--test_increasing_seq_lens`. Encode request/page identity
into a small cache test so reorder, freed blocks, and padding collisions are visible.
Compare traced fixed-shape decode with tracing disabled; output tokens and page updates
must match while trace reduces dispatch work. If capabilities advertise async decode,
submit with `read_from_device=False`, overlap another scheduler action, and read back in
request order. Also test prefix caching and device sampling only when their capability
flags are true. Finally send concurrent requests through the OpenAI-compatible server;
standalone and batched generations must agree within the model's sampling policy, with
no cache leakage between requests or data-parallel replicas.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/vLLM_integration.md):

- **Lifecycle adapter.** `TTModelLoader::load_model`, `initialize_vllm_model`, and
  `LlamaForCausalLM` connect vLLM construction to Tenstorrent weights, devices, and
  model state. Their ownership rules must keep cached tensors and mesh resources alive
  across requests.

- **Prefill/decode boundary.** `forward_prefill` and `paged_fill_cache` create prompt
  state; `forward_decode`, `paged_update_cache`, and
  `paged_scaled_dot_product_attention_decode` consume and extend it. Page tables, token
  positions, batch slots, and KV ownership must agree between the scheduler and device
  calls.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/vLLM_integration.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The task is to make a TT-backed model obey vLLM's scheduling and model-runner
    contracts: dynamic request batches, token positions, sampling inputs, KV-cache
    management, testing, and fallback modifications must agree across two runtimes.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Request identity, sequence position, KV-block ownership, batch slot, and
    returned-logit row must remain aligned through scheduling and execution. Reordering for
    performance is legal only if the inverse mapping restores vLLM's logical request
    order.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    vLLM admits and batches requests → the integration converts scheduler metadata and
    tokens to TT tensors → the TT model reads/updates the assigned KV-cache blocks and
    computes logits → results return to vLLM in request order → sampling selects tokens
    → updated sequence state enters the next scheduling step.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Concrete vLLM interfaces, TT model classes, cache managers,
    supported batching modes, patches, and test commands are version-specific on both
    sides.

    **Durable model.** Define a narrow backend contract, keep scheduler metadata and
    accelerator storage mapping explicit, test mixed-length and preemption cases,
    isolate vendor changes, and validate both numerical outputs and stateful multi-step
    behavior.

## Source and delta

- **Original source:** [`tech_reports/LLMs/vLLM_integration.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/vLLM_integration.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/LLMs/vLLM_integration.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
