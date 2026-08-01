<!-- rewrite-status: improved-draft -->
# Shared Exponent Precision Testing Suite

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md"><code>tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

`bfloat8_b` shares exponent information, so precision depends on which magnitudes occur
together, not merely on the marginal distribution of individual values. The pinned
suite therefore crosses *statistical distributions* with *spatial patterns*. A standard
normal baseline cannot reveal whether a large value in one row, column, block, or tile
changes the error of nearby small values. The generators deliberately add gradients
from `10^-3` to `10^3`, 1000x row outliers, checkerboards, tile-boundary magnitudes, and
8x8 blocks spanning `1e-3` through `1e4`. Comparing a pattern with its reverse tests
directional sensitivity instead of assuming that equal histograms imply equal encoded
behavior.

The report describes the representation as particularly relevant to column-based shared
exponents but does not specify the exact sharing-group width or bit-level encoding.
Consequently, this learner page treats grouping details as an experimental question;
it does not infer a fixed block size from the datatype name.

### How work and data move

`main.py` orchestrates a Cartesian test matrix. `generators.py` creates a named pattern
and distribution for a shape; `runner.py` executes a BFLOAT16 reference and the
BFLOAT8_B path for `sum`, `mean`, `max`, `softmax`, `matmul`, or `matmul_tt`.
Reductions are exercised on axis 0 and axis 1, while `matmul_tt` also varies tile width
16/32 and transpose state. The shape dimension is causal evidence too: `32x32` isolates
one tile, `512x512` spans a 16x16 tile grid, and `32x128`, `128x32`, and `64x256`
separate orientation from element count.

`postprocessing.py` then records PCC, allclose at `1e-2` and `1e-3`, absolute and
relative error, ULP mean/max/percentiles, and input min/max/mean/standard deviation.
`raw_results.json` preserves machine-readable cases; `worst_cases_analysis.md` ranks the
top ten per metric; `pattern_impact_analysis.md` aggregates distributions by pattern.
This pipeline keeps case identity—shape, pattern, distribution, operation, axis/config—
attached to every measurement so an aggregate score can be traced back to a causal
input arrangement.

### What must never break

The BFLOAT16 and BFLOAT8_B executions must receive the same generated logical input and
operation parameters; only the precision path may differ. Axis numbering, transpose
choice, tile width, shape, and output alignment must match before metrics are computed.
PCC alone is insufficient: constant or nearly constant outputs can make correlation
misleading, large outputs can hide relative problems in absolute error, and one outlier
can disappear inside a mean. A conclusion should therefore agree across relevant
allclose, absolute/relative, ULP, and distribution statistics. Negative variants must
also preserve the intended sign transform. A generator bug or mismatched operation
config invalidates the comparison even if the report format looks complete.

### Where the report makes it concrete

The most diagnostic comparisons change one spatial cause at a time. Column versus row
gradients ask whether orientation relative to shared-exponent grouping matters;
forward versus reverse gradients test direction; `tile_boundaries` asks whether an
error resets or changes at 32x32 boundaries; `row_outliers` and `fa_rand_aggressive`
measure sparse large-value contamination. Operation choice then reveals propagation:
`max` selects a value, `sum`/`mean` accumulate quantization error, `softmax` amplifies
relative logit differences, and matmul repeatedly accumulates products. The suite is a
precision-characterization architecture, not proof that one datatype is globally safe
or unsafe.

### How the decision is tested

Start with `constant` and `normal_0_1` on `32x32`, then add one causal factor:
`column_magnitude_gradient`, its reverse, the corresponding row pair, and
`tile_boundaries`. Run both reduction axes and compare the complete metric vector.
Repeat on `512x512` to determine whether the effect is local or accumulates across
tiles. Then introduce `normal_with_outliers` and `row_outliers`, inspecting
`worst_cases_analysis.md` rather than only averages. A credible result is a reproducible
error signature tied to pattern orientation, boundary, operation, and axis. If forward
and reversed cases differ, that is evidence of directional sensitivity; discovering the
exact exponent-sharing group responsible requires additional format-level evidence not
provided by this pinned report.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md):

- **Input generator.** `generators.py` creates controlled exponent-sharing blocks
  through `constant`, `normal_0_1`, `normal_skewed_mean`, `normal_high_var_10`,
  `normal_high_var_100`, `normal_with_outliers`, and `fa_rand_default`. Each
  distribution targets a different loss mechanism rather than providing interchangeable
  random data.

- **Oracle boundary.** Review the encoded and decoded values per shared-exponent block,
  not only one aggregate error. High-variance and outlier cases should reveal whether a
  large exponent suppresses smaller mantissas while constant or narrow distributions
  establish the no-stress baseline.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The suite tests how shared-exponent formats lose precision across data generation,
    conversion, arithmetic operations, and comparison. Its real target is corner-case
    coverage—outliers, ties, cancellation, overflow, and magnitude mixtures—not merely
    average random-input accuracy.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The oracle and device path must use the same block grouping, shared-exponent
    selection, rounding rule, operation semantics, and output interpretation. Seeds,
    tolerances, and error metrics must be recorded so a regression is reproducible.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A controlled 16-value block is generated → a reference encoder chooses the shared
    exponent and quantizes mantissas → the corresponding device format enters the
    operation under test → the result is unpacked → elementwise and aggregate error
    metrics compare it with the high-precision/reference path.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** The exact BFP encodings, 16-value grouping, supported
    operations, pack/unpack behavior, and accepted tolerances reflect the documented
    formats and hardware/software revision.

    **Durable model.** Build numerical tests from the quantizer's decision boundaries,
    include adversarial distributions as well as random data, compare against an
    independent oracle, and diagnose error by stage rather than hiding it in one
    end-to-end threshold.

## Source and delta

- **Original source:** [`tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
