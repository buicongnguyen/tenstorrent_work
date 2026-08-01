<!-- rewrite-status: improved-draft -->
# New model bring-up in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md"><code>tech_reports/ttnn/TTNN-model-bringup.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to decompose model porting into its actual architecture
boundaries: preprocessing, each unsupported or converted operator, module composition,
end-to-end post-processing, numerical acceptance, and only then measured optimization
for the target model.

### How work and data move

The complete path is `reference input → TT preprocessing → per-op TT-NN tests → module
tests → composed TT-NN model → output post-processing → golden comparison →
profiler-driven optimization`, naming checkpoint tensors and layouts.

### What must never break

The non-negotiable invariant is that each checkpoint receives semantically identical
inputs and preserves shape/order/broadcast/padding with an agreed PCC or error
threshold; an optimization may change representation but not the model contract.

### Where the report makes it concrete

The report makes the decision concrete by connecting every model module to its concrete
TT-NN operations, golden implementation, device program/config, preprocessing utility,
test file, and profiler zone instead of leaving symbols deferred to a future rewrite.

### How the decision is tested

The controlled procedure is to introduce one module at a time and record the first
failing checkpoint, then optimize one measured boundary. **Expected observation:**
failures localize to one module and the accepted change improves end-to-end latency
without reducing model accuracy.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md):

- **Module checkpoint.** For every model module, name the TT-NN operations,
  preprocessing utility, tensor shape/layout/dtype, and golden implementation used by
  its unit test. This is the executable contract that localizes the first divergence.

- **Program and performance.** Connect each operation to its device program/config,
  cached-program identity, and profiler zone. Optimize only a measured boundary, then
  rerun the module and end-to-end accuracy checks so a faster representation change
  cannot bypass the model contract.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report gives a bottom-up model-porting workflow: implement TT-NN
    operations/modules, compare each against a reference, assemble end to end, then
    optimize only after correctness and obtain reliable performance measurements.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every module checkpoint must receive semantically identical inputs and produce the
    reference shape/order with an agreed error metric such as PCC. An optimization may
    change layout, sharding, or precision only if the model contract remains satisfied.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Reference inputs are preprocessed → individual TT-NN ops are unit-tested → ops form
    modules with checkpoint comparisons → modules assemble into the end-to-end model →
    output post-processing compares with the golden implementation → profiling
    identifies the next bottleneck → one optimization is applied.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Current TT-NN APIs, supported operators, program configs,
    data types, model utilities, profiler commands, and device performance are
    snapshot-specific.

    **Durable model.** Port bottom-up, keep an executable golden model, validate at
    narrowing checkpoints, separate correctness from performance phases, record
    shapes/layouts explicitly, and optimize one measured bottleneck at a time.

## Source and delta

- **Original source:** [`tech_reports/ttnn/TTNN-model-bringup.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn/TTNN-model-bringup.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
