<!-- rewrite-status: improved-draft -->
# Shared Exponent Precision Testing Suite

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md"><code>tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to organize the precision investigation around
shared-exponent decision boundaries—maximum exponent selection, alignment, rounding
ties, carry/saturation, cancellation, and outliers—rather than around a large
undifferentiated random corpus.

### How work and data move

The complete path is `generator → 16-value exponent-sharing block → independent
encoder/oracle → TT format conversion → operation under test → decode → elementwise and
aggregate error report`, recording seeds and encoded bits.

### What must never break

The non-negotiable invariant requires oracle and device paths to agree on block
grouping, shared exponent, rounding, operation semantics, and output interpretation
while keeping the oracle implementation independent enough to expose device bugs.

### Where the report makes it concrete

The report makes the decision concrete by connecting cases to `generators.py` and the
named distributions `constant`, `normal_0_1`, `normal_skewed_mean`,
`normal_high_var_10/100`, `normal_with_outliers`, and `fa_rand_default`.

### How the decision is tested

The controlled procedure is to compare fifteen small values with and without one large
outlier in the same block. **Expected observation:** the outlier raises the shared
exponent and increases error or code collisions for the small values, matching the
reference encoder.

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
