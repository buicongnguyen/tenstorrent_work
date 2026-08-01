<!-- rewrite-status: improved-draft -->
# Integrating TT Models into vLLM

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/vLLM_integration.md"><code>tech_reports/LLMs/vLLM_integration.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to define the exact boundary between vLLM scheduling
and the TT backend: request/batch identity, token position, prefill/decode dispatch, KV
block ownership, logits ordering, sampling interface, and supported preemption behavior.

### How work and data move

The complete path is a request from vLLM admission/batching through TT input
construction, `forward_prefill` or `forward_decode`, paged KV update/attention, logits
return in scheduler order, token sampling, and next-step state.

### What must never break

The non-negotiable invariant is that request identity, batch slot, token position, KV
block, and returned-logit row remain aligned under mixed lengths, reorder, cancellation,
and resume; performance reordering must have a correct inverse mapping.

### Where the report makes it concrete

The report makes the decision concrete by connecting the adapter to `paged_fill_cache`,
`paged_update_cache`, `paged_scaled_dot_product_attention_decode`, `forward_prefill`,
`forward_decode`, `LlamaForCausalLM`, `initialize_vllm_model`, and
`TTModelLoader::load_model`.

### How the decision is tested

The controlled procedure is to run interleaved requests with different prompt/decode
lengths and force scheduler reordering. **Expected observation:** each request
reproduces standalone tokens while persistent KV blocks avoid per-token host/device
reconstruction.

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
