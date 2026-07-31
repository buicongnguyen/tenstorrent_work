<!-- rewrite-status: seed -->
# New model bring-up in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md"><code>tech_reports/ttnn/TTNN-model-bringup.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ttnn/TTNN-model-bringup.md</code>. This learner page
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 182 |
| Section headings | 17 |
| Fenced code examples | 7 |
| Markdown images | 11 |

### Section outline

- 1. Overview
- 2. New model bringup flow in TTNN
  - 2.1 Recommended steps for model bringup
  - 2.2 Create a model Card
  - 2.3 Using the reference model in Torch
  - 2.4 Create the torch model graph
  - 2.5 Extract the model summary
  - 2.6 Create issues for potential bugs or missing TTNN ops
- 3. End to end model in TTNN
- 3.1 Create TTNN unit tests per module and per op
- 3.2 PCC
- 3.3 Optimization
- 4.  End to end model performance
  - 4.1 Performance Sheet
  - 4.2 Visualizer
  - 4.3 Trace and 2cq
- 5. Conclusion

## Improvement plan

1. **Architecture pressure.** Decompose model porting into its actual architecture
   boundaries: preprocessing, each unsupported or converted operator, module composition,
   end-to-end post-processing, numerical acceptance, and only then measured optimization for
   the target model.

2. **Flow to make explicit.** Draw `reference input → TT preprocessing → per-op TT-NN tests
   → module tests → composed TT-NN model → output post-processing → golden comparison →
   profiler-driven optimization`, naming checkpoint tensors and layouts.

3. **Invariant to prove.** Prove each checkpoint receives semantically identical inputs and
   preserves shape/order/broadcast/padding with an agreed PCC or error threshold; an
   optimization may change representation but not the model contract.

4. **TT-Metal evidence to connect.** Connect every model module to its concrete TT-NN
   operations, golden implementation, device program/config, preprocessing utility, test
   file, and profiler zone instead of leaving symbols deferred to a future rewrite.

5. **Experiment and expected observation.** Introduce one module at a time and record the
   first failing checkpoint, then optimize one measured boundary; expected result: failures
   localize to one module and the accepted change improves end-to-end latency without
   reducing model accuracy.

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
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
