<!-- rewrite-status: improved-draft -->
# Kernel Arguments as Function & Template Parameters

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/NamedKernelArgs/kernel_args_as_parameters.md"><code>tech_reports/NamedKernelArgs/kernel_args_as_parameters.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Metal 2.0 already gives arguments names and kinds: the host registers compile-time
arguments (CTA), per-core runtime arguments (RTA), and common runtime arguments (CRTA);
JIT emits `kernel_args_generated.h`; and kernels read `get_arg(args::<name>)`. The
remaining failure surface is duplicated entry boilerplate: every kernel hand-writes
`kernel_main()` and a fetch for each name. The proposal makes an ordinary C++ signature
the consumer interface and generates the adapter. Template parameters carry the one
semantic distinction the body needs—true compile-time constants usable in `if
constexpr` and array bounds—while function parameters carry runtime values. Whether a
runtime value is common or per-core stays in the host schema because the body should not
change when storage scope changes.

This is an ABI simplification, not dynamic reflection on device. Generation still
happens before JIT compile and resolves every name to the existing typed accessor layer.

### How work and data move

The user marks one typed function with `TT_KERNEL`, defined in
`experimental/kernel_args.h`. In phase 1 the marker expands to `FORCE_INLINE`, so no
runtime call boundary remains. `genfiles` strips comments, strings, and preprocessor
content, finds the lone real marker, matches the optional `template<...>` and function
`(...)` lists, splits only top-level commas, and extracts each trailing identifier.

It then emits a `kernel_main()` after both `kernel_args_generated.h` and user source are
in scope. CTA names appear as template actuals—`my_kernel<get_arg(args::Ht),...>`—and
RTA/CRTA names as function actuals—`get_arg(args::start_tile_id)`,
`get_arg(args::scaler)`. The `args::<name>` accessor, generated from the host schema,
selects compile-time, per-core runtime, or common runtime storage. Thus a value travels
`host schema -> generated named accessor -> generated shim -> typed user parameter`,
with no positional index repeated in handwritten kernel code.

### What must never break

There must be exactly one `TT_KERNEL` entry, and every extracted parameter name must
exist in the generated `args` schema with a compatible kind. Template parameters must
resolve to compile-time accessors; function parameters may resolve to RTA or CRTA without
body-visible distinction. Phase 1 restricts parameters to `uint32_t`, because the manual
parser is a name extractor, not a complete C++ parser. Comments, strings, macros, nested
templates, or decoy marker text must not become false entries. A mismatch should fail
generation or compilation rather than shift an index and silently read an adjacent
argument—the central correctness benefit over legacy positional calls.

### Where the report makes it concrete

The legacy example manually binds CTA indices 0–2, RTA indices 0–2, and CRTA index 0.
The proposed function instead names `Ht`, `Wt`, `untilize`, `start_tile_id`,
`num_tiles`, `start_row`, and `scaler` once in its signature. A synthetic 8.49 MB source
containing thousands of functions and decoy markers parses in about 37 ms (roughly
227 MB/s) in the pinned experiment, negligible beside JIT for real kernels of a few KB.
That number supports the phase-1 tokenizer's engineering cost, not arbitrary C++
correctness. Planned `uint64_t` and `std::array` support needs multi-word accessors; if
type spellings defeat trailing-identifier extraction, libclang/Clang AST tooling can
replace parsing behind the same shim interface. Those wider types and AST parser are
future work.

### How the decision is tested

Generate a kernel containing CTAs, per-core RTAs, and a CRTA, then run different values
on multiple cores to prove that scope resolution comes from the accessor schema. Insert
and reorder signature parameters, regenerate, and verify identical named binding. Add
negative cases: an unknown name, CTA/function-kind mismatch, duplicate or absent
`TT_KERNEL`, unsupported non-`uint32_t` type, and marker text inside comments, strings,
and preprocessor lines. Finally compare generated assembly or runtime timing with the
legacy kernel to confirm `FORCE_INLINE` removes call indirection. The acceptance result
is either correct values or a loud build-time error—never a successful build that reads
the neighboring positional slot.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
