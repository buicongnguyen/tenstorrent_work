<!-- rewrite-status: improved-draft -->
# TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md"><code>tech_reports/ttnn/ttnn.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned source is a 35-line stack index, not an implementation specification. Its
supported architectural claim is the layering itself: an ML-framework-facing interface
sits over a library of accelerated operations; OP Infra supplies common `Tensor` and
`Operation` primitives; TT-NN Runtime executes them and exposes graph tracing and
profiling. This boundary keeps framework ergonomics separate from reusable operation
contracts and from device execution machinery. It allows the op library to grow without
duplicating tensor ownership, registration, and debugging behavior in each frontend.
It also gives tracing and profiling a stable interception point below framework syntax
but above individual kernels.
Program factories, hashes, and cache callbacks are not named by this source and must be
learned from the linked operation-development documentation, not invented here.

### How work and data move

A supported walkthrough begins with a framework/user invoking an OP Library symbol.
OP Infra receives TT-NN `Tensor` objects and applies the shared operation contract;
runtime then schedules the operation on TT-Metal and returns TT-NN tensor state to the
caller. Graph tracing observes that runtime boundary, while the profiler supplies
performance evidence. The diagrams referenced by “ML Framework,” “OP Library,” “OP
Infra,” and “TT-NN Runtime” are the pinned source of this flow. Exact validation,
lowering, queue, and kernel steps depend on the chosen operation and are intentionally
outside this overview.
That separation helps diagnosis: a wrong public contract belongs at the framework/op
boundary, while a correct contract with a bad result must be followed into the chosen
operation implementation.

### What must never break

Each layer must preserve the operation's logical semantics and tensor identity while
making its own representation explicit. The frontend cannot assume a Torch tensor is a
device allocation; OP Library cannot bypass common Tensor lifetime rules; Runtime
completion cannot be equated with host visibility unless its API says so. Diagnostics
must attach to the same invocation that crosses these layers. Cache-key completeness is
a useful general runtime invariant, but it is not established by this short report and
therefore should not be attributed to it.

### Where the report makes it concrete

Concrete source links are the `Tensor` documentation, the “adding a new TT-NN
operation” guide, graph-tracing report, and profiler documentation. Use them as a
drill-down path: choose one public op, identify the Tensor metadata it accepts and
returns, find its registration/operation definition, then observe it at the runtime
with graph tracing and profiling. This respects the overview's function as a map while
avoiding unsupported claims about symbols absent from the pinned page.

### How the decision is tested

Select one documented accelerated operation and build a layer-evidence table: framework
call, OP Library name, OP Infra Tensor/Operation contract, runtime trace node, and
profiler row. Execute it with fixed inputs and compare the output to its golden test;
then inspect graph identity, allocation/lifetime events, and device timing. Repeat with
one tensor layout or shape change, but interpret cache behavior only if the operation's
own implementation documentation exposes it. The success criterion is a continuous,
source-backed causal chain across the four TT-NN layers—not a generic diagram decorated
with implementation details from another operation or revision.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
