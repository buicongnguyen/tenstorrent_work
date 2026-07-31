<!-- rewrite-status: seed -->
# Purpose

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md"><code>tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md</code>. This learner page
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 217 |
| Section headings | 1 |
| Fenced code examples | 5 |
| Markdown images | 0 |

### Section outline

- Tips and Best Practices for Numerical Accuracy in TT-Metal Kernels

## Improvement plan

1. **Architecture pressure.** Partition numerical error into input encoding, Unpack, math
   fidelity/approximation, accumulation order/width, and Pack/output format for the specific
   kernel rather than adjusting one global tolerance.

2. **Flow to make explicit.** Draw reference input encoding through device format,
   reader/Unpack, matrix or SFPU operations, destination accumulation, Pack, output storage,
   host conversion, and each comparison metric.

3. **Invariant to prove.** Prove device and golden paths share shapes, broadcasting,
   padding, operation order, and exceptional-value policy; choose tolerance from the
   format/error budget rather than relaxing it after a failure.

4. **TT-Metal evidence to connect.** Connect tests to `comp_equal`/`assert_equal`,
   `comp_ulp`/`assert_with_ulp`, `comp_allclose`/`assert_allclose`, and relative-Frobenius
   helpers, selecting each for a stated failure model.

5. **Experiment and expected observation.** Sweep one precision boundary while holding the
   rest fixed on random and adversarial data; expected result: the selected metric changes
   at the responsible stage and model-level accuracy identifies the cheapest acceptable
   configuration.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md):

- **Comparator selection.** Use `comp_equal`/`assert_equal` for exact discrete results,
  `comp_ulp`/`assert_with_ulp` for representation-distance bounds,
  `comp_allclose`/`assert_allclose` for absolute/relative elementwise error, and
  relative-Frobenius helpers for aggregate tensor error.

- **Failure diagnosis.** Run the selected comparator on adversarial magnitudes, zeros,
  signs, and special values. Record both the accepted threshold and the first
  mismatching elements; a passing aggregate score can hide a localized indexing error,
  while exact equality can reject an expected low-precision rounding change.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report helps kernel authors diagnose numerical error introduced by input format,
    unpacking, math fidelity, approximate SFPU modes, accumulation width/order, and
    output packing, then spend precision only where it improves model-level correctness.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The device result and golden result must implement the same operation, shapes,
    broadcast rules, padding, and exceptional-value policy. Circular-buffer formats must
    match producer/consumer interpretation, and the chosen tolerance must be justified
    by the error budget.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Reference inputs are encoded into device format → unpackers create compute operands
    → matrix/SFPU work executes at selected fidelity and accumulation width → packers
    quantize the output → host comparison measures elementwise error/PCC → one precision
    boundary is changed for the next controlled experiment.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Available formats, fidelity modes, `fp32_dest_acc_en`,
    approximation behavior, packer options, and exact accuracy/performance trade-offs
    depend on hardware and kernel configuration.

    **Durable model.** Localize error by stage, use adversarial and realistic data,
    distinguish input quantization from accumulation and output quantization, change one
    precision knob at a time, and judge cost against end-to-end accuracy.

## Source and delta

- **Original source:** [`tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md`
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
