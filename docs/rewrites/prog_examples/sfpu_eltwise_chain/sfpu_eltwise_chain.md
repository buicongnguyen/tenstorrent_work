<!-- rewrite-status: improved-draft -->
# SFPU Eltwise Chain

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md"><code>tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to list the exact ordered elementwise chain and
intermediate consumers, then calculate pack/write/read/unpack bytes and launches
eliminated when the intermediate tile remains live in SFPU state.

### How work and data move

The complete path is input reader/CB publication, Unpack, ordered SFPU operations such
as exp/log/softplus composition, final Pack, output CB publication, writer, and host
comparison.

### What must never break

The non-negotiable invariant is that fused operation order, constants, approximation
mode, input/output formats, and final rounding implement the same function; the tile
remains compute-owned until all operations finish.

### Where the report makes it concrete

The report makes the decision concrete by connecting the plan to
`sfpu_eltwise_chain.cpp`, `softplus(x) = log(1 + exp(x))`, `ttnn::exp`, `ttnn::log`,
`float_to_bfloat16`, `bfloat16`, and its reader/compute/writer kernels.

### How the decision is tested

The controlled procedure is to compare fused and separate-kernel chains across
representative magnitudes. **Expected observation:** identical tolerated output with
fewer intermediate bytes/launch gaps unless register pressure or lost pipeline overlap
becomes limiting.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md):

- **Semantic chain.** `sfpu_eltwise_chain.cpp` implements `softplus(x) = log(1 +
  exp(x))` through `ttnn::exp` and `ttnn::log`. The reference must use the same input
  range and bfloat16 conversion when evaluating approximation and overflow behavior.

- **Kernel pipeline.** `float_to_bfloat16` creates stored inputs, reader/compute/writer
  kernels move tiles through circular buffers, and `bfloat16` output is compared after
  Pack. Match tile counts across all three kernels before attributing an error to SFPU
  math.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The example chains several elementwise SFPU operations while a tile remains in the
    compute pipeline, eliminating intermediate pack-to-memory, writer, reader, and
    unpack stages between operations. The saved traffic and launches are the intended
    performance gain.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The fused instruction order, constants, approximation modes, and final rounding must
    implement the intended mathematical chain. The tile must stay owned by the compute
    stage until the chain is complete and be published exactly once afterward.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A reader publishes an input tile → compute waits and unpacks it → SFPU applies the
    ordered elementwise operations to the live tile/register state → pack converts the
    final result → the output CB is published → a writer stores it for host comparison.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Available SFPU functions, approximation behavior,
    tile/register APIs, fidelity, CB identifiers, and cycle savings depend on the Tensix
    generation and low-level library.

    **Durable model.** Fuse producer-consumer chains when intermediates have no external
    users, preserve operation order and numerical policy, keep ownership local through
    the fusion, and measure eliminated movement against any register-pressure cost.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
