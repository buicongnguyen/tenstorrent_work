<!-- rewrite-status: improved-draft -->
# Purpose

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md"><code>tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

In the pinned report, numerical accuracy is a pipeline property, not a final-comparison
setting. A kernel can preserve its input and output data format yet still lose useful
bits while accumulating, reloading partials, reducing padded elements, or changing the
operation order. That matters because an error introduced by one operator can be
amplified by every downstream operator. The architectural decision is therefore to
identify *where rounding occurs* and spend precision at that boundary, instead of
loosening a model-wide PCC threshold after the fact.

The report deliberately provides several comparison metrics because they detect
different failures. `comp_equal()` catches bitwise/integer mistakes; `comp_ulp()` is
useful for short elementwise paths; `comp_allclose()` prevents a few large per-element
errors from hiding; relative Frobenius error measures aggregate energy; PCC preserves
correlation but can miss a global scale or bias. Metric selection is part of the
correctness contract: PCC alone could accept an output scaled by two, while a strict ULP
limit becomes hard to interpret after a long fused floating-point sequence.

### How work and data move

For an accumulating kernel, a tile travels from L1 circular-buffer storage through
Unpack, source or destination registers, repeated math, Pack, and eventually the host
comparison. `DeviceComputeKernelConfig.fp32_dest_acc_en` makes destination-register
accumulation FP32 on the Wormhole and Blackhole scope named by the report. If a partial
sum is spilled to a CB and later reloaded, that setting is not sufficient: the program
must also assign that CB `UnpackToDestMode::UnpackToDestFp32` in `ComputeConfig`.
`copy_tile_init(cb_id)` followed by `copy_tile()` can then unpack the partial directly
to destination registers without the TF32 truncation incurred by routing it through
srcA/srcB. This is a constrained fast path, not a universal higher-precision CB:
the same CB cannot then feed srcA/srcB operations such as `add_tiles()`; the result must
be copied to a compatible CB before those operations.

Reduction order creates another precision boundary. Supplying a `reduce_tile()` scalar
tile filled with `1/N` implements divide-then-sum and rounds the division once per
element. The pinned alternative supplies ones, accumulates the sum, and performs the
single final scaling on the SFPU with `mul_unary_tile(cb_mean, 1/N)`. This removes
`N-1` divisions and avoids flushing individually scaled small values to zero, at the
tradeoff of a larger running sum and therefore a greater overflow requirement.

Tile shape is part of that path. A last physical 32-wide tile may contain logical data
and unspecified out-of-bounds lanes. `reduce_tile()` processes the full tile, so those
lanes must be excluded by the operator-specific masking scheme, and dimension logic
must use `Tensor::logical_shape()` rather than `Tensor::padded_shape()`. For LayerNorm
and GroupNorm, Welford's method changes the dataflow further: mean and `M2` advance
together in one pass, reducing DRAM/NoC traffic and accumulating the smaller correction
`x_n - mean_(n-1)`. The pinned TT-NN entry points are `use_welford=True` in
`LayerNormDefaultProgramConfig` or `LayerNormShardedMultiCoreProgramConfig`, and the
`use_welford` argument of `ttnn.group_norm`. Precomputed tensors from
`ttnn.create_layer_norm_reciprocals` or `ttnn.create_group_norm_reciprocals` avoid
recomputing reciprocals in the hot path.

### What must never break

The logical reduction population must be exactly the reference population: padded lanes
are never observations, and every real element contributes once. A spilled FP32 partial
must return through an `UnpackToDestFp32` CB before further destination accumulation;
silently reloading through srcA/srcB changes the numerical algorithm. Welford state is a
coupled `(count, mean, M2)` recurrence, so combining or distributing it as three
independent reductions is invalid. Finally, the device and golden paths must agree on
shape, broadcast, operation order, output conversion, and treatment of exceptional
values. Breaking any of these invariants produces a correctness defect, not a reason to
relax tolerance.

### Where the report makes it concrete

Three pinned observations connect mechanism to symptom. Matmul accuracy deteriorates
with larger inner dimension when low-precision partial errors accumulate. LayerNorm
shows a discontinuity near the width at which its kernel switches to an intermediate
accumulator; configuring the reload path for FP32 removes that discontinuity. Width
sweeps also show periodic errors at non-tile-aligned shapes until logical extent and
partial-tile handling are corrected. The Welford experiment uses a skewed
`randn() + 100` FP32 distribution: subtracting the running mean keeps the recurrence's
working values better conditioned than summing a large offset repeatedly.

### How the decision is tested

Use paired experiments that change one boundary at a time: toggle
`fp32_dest_acc_en`; then independently toggle `UnpackToDestFp32`; compare
divide-then-sum with ones-plus-`mul_unary_tile`; and compare two-pass statistics with
Welford plus reciprocals. Sweep reduction width across multiples of 32 and across any
kernel-selection boundary, including partially filled last tiles. Include a hand-solvable
case, cancellation-heavy values, large offsets, very small values, and values near the
format's dynamic-range limit. Check per-element allclose or ULP *and* a global metric;
use PCC only as an additional model-level signal. The expected causal signature is
specific: FP32 reload removes a kernel-switch discontinuity, masking removes 32-lane
periodicity, sum-then-divide reduces division noise but may expose overflow, and Welford
improves the large-offset variance case while reducing the input to one pass.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
