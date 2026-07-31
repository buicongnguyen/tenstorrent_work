<!-- rewrite-status: seed -->
# TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md"><code>tech_reports/ttnn/ttnn.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn/ttnn.md</code>. This learner page
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 35 |
| Section headings | 6 |
| Fenced code examples | 0 |
| Markdown images | 5 |

### Section outline

- Roadmap
- High Level Structure Overview
- ML Framework
- OP Library
- OP Infra
- TT-NN Runtime

## Improvement plan

1. **Architecture pressure.** Turn the stack overview into one concrete operation lifecycle:
   public semantic contract, validation/registration, implementation selection,
   device-operation attributes, program creation/cache hit, runtime argument patching,
   dispatch, and output ownership.

2. **Flow to make explicit.** Draw a framework/user call through TT-NN operation
   library/infrastructure, tensor metadata validation, program hash/factory, TT-Metal
   command queue, reader/compute/writer kernels, and returned tensor.

3. **Invariant to prove.** Prove logical shape/dtype/layout/placement/ownership remain
   coherent across layers and that cached programs include every compile-time choice while
   only documented runtime state is patched.

4. **TT-Metal evidence to connect.** Connect the report's ML Framework, OP Library, OP
   Infra, TT-NN Runtime, and TT-Metal boundaries to one actual registered operation, its
   program factory/hash/cache-hit callback, tensor objects, and command queue.

5. **Experiment and expected observation.** Trace the same operation cold, warm, and with
   one shape/layout change; expected result: identical semantics, a cache hit only for
   compatible identity, and a timeline that separates construction from steady
   dispatch/device execution.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md):

- **Operation registration.** Trace one registered operation from ML framework call
  through OP Library and OP Infra to its program factory, validation, output-spec
  calculation, hash/cache key, and cache-hit runtime-argument callback.

- **Runtime execution.** The TT-NN Runtime owns tensor/device objects and enqueues the
  resulting program through TT-Metal command queues. Separate host operation completion
  from device execution and host-visible tensor readiness when explaining the stack
  boundary.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The overview explains TT-NN's layered path from ML-framework-facing tensor
    operations through the operation library and infrastructure to program generation,
    caching, dispatch, and TT-Metal device execution. Its programming task is defining
    clean contracts across those layers.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Across every layer, a tensor's logical shape, dtype, layout, placement, ownership,
    and dependency state must remain coherent. An operation may lower or transform
    representation, but its public result must satisfy the declared semantic contract.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A framework/user calls a TT-NN operation → validation and operation infrastructure
    select an implementation → a device operation computes program identity and creates
    or reuses a program → runtime arguments bind tensors → command queues dispatch
    kernels → output tensors return through TT-NN to the caller.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Class names, roadmap, registration mechanisms, program-cache
    hooks, runtime internals, supported frontends, and exact module boundaries evolve
    with TT-NN.

    **Durable model.** Layer semantic APIs over specialized kernels, validate contracts
    before lowering, cache specialization separately from runtime state, keep tensor
    metadata first-class, and expose profiling/debugging boundaries between layers.

## Source and delta

- **Original source:** [`tech_reports/ttnn/ttnn.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn/ttnn.md`
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
