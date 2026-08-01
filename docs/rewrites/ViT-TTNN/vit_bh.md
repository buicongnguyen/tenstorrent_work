<!-- rewrite-status: improved-draft -->
# [skip ci] ViT in TT-NN for Blackhole

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md"><code>tech_reports/ViT-TTNN/vit_bh.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to list which ViT semantics remain
generation-independent and re-derive Blackhole-specific L1 footprint, core grid,
NoC/layout, transpose/multicast, compute config, and operation availability instead of
copying Wormhole tuning.

### How work and data move

The complete path is the same validated encoder flow as the Wormhole path while marking
every Blackhole-specific policy selection, buffer/layout transition, program
configuration, and fallback.

### What must never break

The non-negotiable invariant is that identical logical token/head/residual contracts and
checkpoint tolerances across generations; only physical layout, program, and scheduling
choices may differ.

### Where the report makes it concrete

The report makes the decision concrete by connecting the Blackhole plan to the source's
`WormholeComputeKernelConfig` comparison, `transpose_mcast=False/True`, `vit_layer()`,
`b × seqL × dim`, and generation-specific optimization/code sections.

### How the decision is tested

The controlled procedure is to run identical inputs/weights through the correctness
bootstrap and tuned Blackhole variants. **Expected observation:** checkpoint parity in
both, with gains attributable to measured Blackhole capacity/utilization or
communication changes.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md):

- **Generation boundary.** The source's `WormholeComputeKernelConfig` comparison marks a
  configuration inherited from another generation, not a guarantee of Blackhole
  equivalence. Re-establish grid, fidelity, accumulator, and memory assumptions on the
  Blackhole path.

- **Attention/matmul path.** `vit_layer()`, `b × seqL × dim`, and
  `transpose_mcast=False/True` connect model shape to operand distribution. Measure both
  orientations with their conversions and validate encoder output before claiming the
  Blackhole-specific choice is better.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The Blackhole report retargets and optimizes the ViT path for a new generation whose
    core, memory, and operation characteristics differ from the earlier implementation.
    The key task is separating portable model logic from hardware-specific program
    choices.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    For identical inputs and weights, the Blackhole path must preserve the same logical
    token sequence, attention/MLP computation, residual graph, and output interpretation
    as the validated reference, within an explicitly chosen numerical tolerance.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The image follows patch embedding and encoder stages → TT-NN selects
    Blackhole-specific layouts/program configurations for attention and MLP → sharded activations
    flow through residual boundaries → the classifier output is composed/read back →
    checkpoints compare with reference and prior-generation behavior.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Blackhole architecture differences, core grids, L1/NoC
    assumptions, operation availability, program configs, and benchmark results are
    generation-specific.

    **Durable model.** Retarget from a correctness baseline, isolate device-specific
    policy behind configuration, re-derive capacity and parallelism rather than copying
    numbers, and use identical checkpoint tests to distinguish architecture bugs from
    model bugs.

## Source and delta

- **Original source:** [`tech_reports/ViT-TTNN/vit_bh.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ViT-TTNN/vit_bh.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
