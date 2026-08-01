<!-- rewrite-status: improved-draft -->
# TT-NN Comparison Mode

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md"><code>tech_reports/ttnn/comparison-mode.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Comparison mode is intentionally inserted at the operation boundary because a final
model mismatch does not identify the first divergent operator. At the pinned snapshot,
it compares each operation's output with the corresponding reference-operation output
using Pearson correlation coefficient (PCC). This localizes failures; it does not prove
bitwise correctness. PCC is insensitive to some affine changes, and its useful threshold
depends on the numerical contract. The mode requires fast runtime to be disabled, so
`enable_fast_runtime_mode` must be false. That trade exchanges production
dispatch behavior and performance for per-operation observability. Because the
comparison is attached at each boundary, developers can localize a long forward pass
without first rewriting it as manually isolated subgraphs.

### How work and data move

Configuration is established before TT-NN initialization through
`TTNN_CONFIG_OVERRIDES`. With `enable_comparison_mode=true`, an operation executes and
the runtime obtains the corresponding reference output, computes PCC between the two
outputs, and checks `comparison_mode_pcc` (the source example uses `0.999`). The report
does not say how device/reference representations are adapted before PCC, so that step
must be checked in the implementation for padded or non-host layouts. If it fails,
`comparison_mode_should_raise_exception=true` stops at that invocation; false reports
the mismatch and lets the sequence continue. The former preserves the first failing
boundary, while the latter can reveal a failure cascade but makes later mismatches
dependent on already-corrupted inputs.

### What must never break

The reference and device paths must represent the same operation, parameters, logical
shape, and input values. The comparison must exclude physical padding or normalize it
consistently. An operation without a valid golden implementation cannot silently count
as passed, and a multi-output operation must compare every semantically relevant
output. Most importantly, comparison mode changes runtime configuration and adds
reference execution and transfers; its wall time is not evidence about normal fast
runtime performance. A PCC above threshold is only the configured acceptance result,
not evidence that maximum error or downstream task accuracy is acceptable.

### Where the report makes it concrete

The pinned report is only 24 lines and documents four controls: fast mode defaults true,
comparison defaults false, raise-on-failure defaults false, and
`comparison_mode_pcc` selects sensitivity. It does not specify reference conversion,
unsupported-operation policy, NaN behavior, tuple handling, or the exact report schema.
Those must therefore be verified in the pinned implementation before making stronger
claims. This source limitation is itself architectural guidance: use the mode to find a
candidate boundary, then reproduce that operator with an explicit unit-test oracle and
metrics suited to its dtype and function.
For reductions, softmax, or classifier outputs, that follow-up may need absolute or
relative error, row-sum invariants, or task accuracy in addition to PCC.

### How the decision is tested

Build a three-operation chain with a supported golden path and perturb only the second
device result. Run at thresholds just below and above the measured PCC, in both
exception policies; verify the raised case names/stops at operation two and the report
case distinguishes the primary mismatch from downstream effects. Add constant tensors,
NaNs, multiple outputs, broadcast/padded shapes, and an operation lacking a golden path
to characterize undefined cases rather than guess. Finally rerun without comparison and
with fast mode restored to confirm identical unperturbed results. Performance data from
the instrumented run must be discarded.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md):

- **Runtime selection.** `TTNN_CONFIG_OVERRIDES` sets `enable_fast_runtime_mode`,
  `enable_comparison_mode`, and `comparison_mode_should_raise_exception`. Confirm the
  effective configuration at process start; changing an environment string after
  initialization may not alter the active runtime.

- **Golden comparison.** Each operation's registered golden function receives converted
  inputs and produces the reference used for comparison. Shape, dtype conversion,
  tolerance, and exception policy decide what a mismatch means; an operation without a
  compatible golden path cannot be validated by the mode.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    Comparison mode automatically runs or obtains a golden implementation for TT-NN
    operations and reports numerical differences, shortening the search from an
    incorrect model output to the first operation whose contract diverges.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Golden and device executions must see the same logical inputs, parameters,
    broadcasting, shape semantics, and operation order. The configured tolerance/PCC
    threshold must reflect the expected numerical format rather than being loosened
    until a failure disappears.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A TT-NN operation call is intercepted → comparison infrastructure records its
    inputs/configuration → a golden path computes the reference → the device operation
    executes → outputs are converted to comparable form → error/PCC is reported with
    operation identity → the first divergence guides debugging.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Enablement APIs, golden-function coverage, report format,
    supported operations, conversion behavior, and default thresholds depend on the
    TT-NN release.

    **Durable model.** Use differential testing close to operation boundaries, keep
    inputs identical, select justified metrics, preserve the first failing context, and
    treat automatic comparison as localization evidence rather than proof of root cause.

## Source and delta

- **Original source:** [`tech_reports/ttnn/comparison-mode.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ttnn/comparison-mode.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
