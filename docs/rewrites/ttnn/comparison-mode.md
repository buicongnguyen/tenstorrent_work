<!-- rewrite-status: improved-draft -->
# TT-NN Comparison Mode

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md"><code>tech_reports/ttnn/comparison-mode.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to define which TT-NN operations have valid golden
functions, what tensor conversions comparison requires, which metric/tolerance each
format warrants, and how failures should preserve invocation context.

### How work and data move

The complete path is an intercepted operation through input/config capture, golden
execution, device operation, comparable output conversion, PCC/error calculation,
report/exception, and continuation or stop policy.

### What must never break

The non-negotiable invariant is that golden and device paths see the same logical
inputs, parameters, broadcast/padding, and order; tolerances must come from the
numerical contract and comparison must not be used for performance timing.

### Where the report makes it concrete

The report makes the decision concrete by connecting configuration to
`TTNN_CONFIG_OVERRIDES`, `enable_fast_runtime_mode`, `enable_comparison_mode`,
`comparison_mode_should_raise_exception`, and the operation's registered golden
function.

### How the decision is tested

The controlled procedure is to inject one known numerical error in a supported op and
run raise/report modes. **Expected observation:** comparison identifies the first
exact invocation and metric while normal execution returns after the configured policy.

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
