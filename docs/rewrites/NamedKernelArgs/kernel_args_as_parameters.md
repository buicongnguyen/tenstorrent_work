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
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

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

1. **Architecture pressure.** Identify the positional ABI failures the proposal must
   eliminate: compile-time versus runtime kind, common versus per-core scope, type/order
   drift, and index shifts when a new argument is inserted.

2. **Flow to make explicit.** Draw one named value from host declaration through generated
   argument schema/wrapper, program compile/runtime storage, device kernel signature, and
   typed access at the consuming instruction path.

3. **Invariant to prove.** Prove host binding and kernel signature share one authoritative
   name, type, kind, order, and scope; generation or compilation must reject drift rather
   than silently read a neighboring slot.

4. **TT-Metal evidence to connect.** Connect the proposal to `kernel_args_generated.h`,
   `args::<name>`, `args::start_tile_id`, `get_arg(args::<name>)`, `constexpr` template
   parameters, and the generated `kernel_main()` wrapper.

5. **Experiment and expected observation.** Insert and reorder one argument in a test
   schema; expected result: regenerated host/device interfaces remain aligned or fail
   loudly, whereas an intentionally stale positional consumer is detected before runtime.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/NamedKernelArgs/kernel_args_as_parameters.md):

- **Generated ABI.** The host description generates `kernel_args_generated.h`, named
  indices such as `args::start_tile_id`, and the `kernel_main()` wrapper. Host
  serialization order and generated device declarations are one ABI; editing either side
  independently changes the meaning of every following argument.

- **Device access.** `get_arg(args::<name>)` retrieves runtime values, while `constexpr`
  template parameters specialize compile-time values. Review width, signedness, offset,
  and lifetime for each named field before replacing positional access; a name does not
  repair a mismatched representation.

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
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
