<!-- rewrite-status: seed -->
# Kernel Arguments as Function & Template Parameters

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/NamedKernelArgs/kernel_args_as_parameters.md"><code>tech_reports/NamedKernelArgs/kernel_args_as_parameters.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/NamedKernelArgs/kernel_args_as_parameters.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 89 |
| Section headings | 5 |
| Fenced code examples | 3 |
| Markdown images | 0 |

### Section outline

- Args in Metal 2.0 today
- Proposal
- C++ syntax carries the argument kinds
- Implementation
- Next phase

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/NamedKernelArgs/kernel_args_as_parameters.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/NamedKernelArgs/kernel_args_as_parameters.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The proposal replaces positional kernel-argument indexing with named C++ function
    and template parameters, so compile-time values, common runtime values, and per-core
    runtime values become visible in the kernel signature and tooling can check more of
    the ABI.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The host-generated binding and device-side signature must agree exactly on argument
    kind, type, order, scope, and compile-time/runtime lifetime. Renaming must not
    change which encoded slot a kernel consumes. This agreement is the kernel ABI, not
    an editor-only convenience.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Host code declares a kernel and its named arguments → program creation separates
    template/compile-time and runtime values → JIT generation creates the processor
    wrapper and signature → dispatch writes common/per-core runtime storage → kernel
    code reads the named parameter with its declared type.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** The proposed syntax, generator implementation, supported
    parameter types, migration tooling, and current Metal 2.0 argument APIs belong to
    the report's software snapshot.

    **Durable model.** Make binary interfaces explicit, attach names and types at the
    declaration boundary, generate both producer and consumer views from one schema, and
    retain a test that detects ABI drift.

## Source and delta

- **Original source:** [`tech_reports/NamedKernelArgs/kernel_args_as_parameters.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/NamedKernelArgs/kernel_args_as_parameters.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/NamedKernelArgs/kernel_args_as_parameters.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
