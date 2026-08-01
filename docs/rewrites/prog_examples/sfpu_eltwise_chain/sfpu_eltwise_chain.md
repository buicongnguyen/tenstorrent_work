<!-- rewrite-status: improved-draft -->
# SFPU Eltwise Chain

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md"><code>tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned example implements `softplus(x) = log(1 + exp(x))` as one compute-kernel
lifetime. Calling separate tensor operators would materialize `exp(x)` and
`exp(x)+1`: each boundary requires a result Pack, circular-buffer/DRAM traffic, a later
Unpack, and another dispatch. Because all three functions are elementwise and the next
function consumes exactly the previous value at the same lane, there is no architectural
reason to expose either intermediate. The chosen mechanism keeps register 0 live across
`exp_tile`, `add_binary_tile`, and `log_tile`, paying one input read and one final output
write.

Fusion is not automatically beneficial for arbitrary chains. It increases the lifetime
of destination registers and fixes operation order, approximation behavior, and rounding
points inside one kernel. This one-tile example needs two live registers—input/result in
register 0 and a tile of ones in register 1—so the working set is explicit and small.

### How work and data move

The host creates one 32x32 bfloat16 tile, computes a CPU `golden_softplus`, and converts
the input with `tilize_nfaces`. Source and destination `MeshBuffer`s use a one-tile DRAM
page. On core `{0,0}`, CB `c_0` carries input, `c_1` carries the constant-one tile, and
`c_2` carries the final result; all three are `Float16_b` and one tile deep.

The reader reserves `c_0`, issues `noc_async_read_page(0, interleaved_accessor, ...)`,
waits at `noc_async_read_barrier`, and pushes the tile. It separately reserves `c_1`
and fills its L1 page through a `uint16_t*` with `float_to_bfloat16(1.0f)`, then pushes
that page. This synthesizes a constant locally rather than allocating and transferring a
second DRAM tensor.

The compute kernel calls `init_sfpu(src_cb_index, result_cb_index)` and
`tile_regs_acquire`, waits for both CB pages, and executes
`copy_tile(c_0, 0, 0)` plus `copy_tile(c_1, 0, 1)`. After `exp_tile_init`,
`exp_tile(0)` overwrites register 0 with `exp(x)`. `add_binary_tile_init` and
`add_binary_tile(0, 1, 0)` add the constant into that same register. `log_tile_init`
and `log_tile(0)` produce the final softplus value without an intervening Pack. Only
then does the kernel commit/wait tile registers, reserve `c_2`, and `pack_tile(0, c_2)`;
the complete implementation must publish the result so the writer's
`cb_wait_front(c_2, 1)` can issue `noc_async_write_page`, barrier, and pop it. The pinned
compute excerpt stops at `pack_tile`: it does **not** show `cb_push_back(c_2, 1)`, pops
for `c_0`/`c_1`, or `tile_regs_release()`. It therefore demonstrates the register-level
arithmetic chain, not a complete reusable reader/compute/writer lifecycle. Those
ownership-release steps must be verified in the linked implementation before treating
the sample as a runnable repeated-tile kernel. Host code then reads,
`untilize_nfaces`, and compares against the golden vector.

### What must never break

Register 0 must retain the same lane mapping and remain compute-owned from the first
copy through the final log. Register 1 must still contain exactly one in bfloat16 for
every lane when the binary add runs. Reordering log and add, packing after exp, changing
the constant format, or releasing destination registers between steps changes either
the function or its rounding. CB ownership remains conventional even though
intermediates do not: reader push precedes compute wait, compute publication precedes
writer wait, and writer barrier precedes pop. The host golden must compare untilized
logical order with device untilized logical order. Packing is not publication: without
the omitted result `cb_push_back`, the writer remains blocked; without input pops and
tile-register release, a repeated invocation eventually deadlocks or exhausts owned
state even if a one-tile arithmetic trace looks correct.

### Where the report makes it concrete

The eliminated boundary can be counted. A separate three-op formulation exposes two
full-tile intermediates and three operation dispatches. The chained kernel exposes zero
intermediate tiles and one compute dispatch, while retaining one input and one output
DRAM transfer. It still pays to create/copy the ones tile and to initialize three SFPU
operations. For a longer chain, saved memory traffic must therefore be balanced against
register pressure, extra constants, instruction count, and any loss of overlap between
independent kernels. This traffic comparison describes the intended full example; the
short compute listing in the pinned report is incomplete at the CB/register lifecycle
boundary and must not by itself be used as evidence that the writer can make progress.

### How the decision is tested

Run the pinned random `[0,1]` case to reproduce PCC above 0.999, but do not stop there:
PCC can hide scale and bias. Compare per element with allclose or ULP, and include large
positive values, large negative values, values near zero, and the region where `exp`
can overflow or underflow in the configured path. Compare chained and separate-kernel
versions with identical input/output formats and approximation settings. Measure kernel
launch gaps, DRAM/L1 bytes, Pack/Unpack activity, and cycles. The expected signature is
two missing materialization boundaries with numerically consistent final output; if
cycles grow despite fewer bytes, inspect SFPU latency, register pressure, and the locally
constructed constant rather than assuming fusion always wins. Also run more tiles than
the CB depths and repeat the program: this forces every result push, input pop, and tile
register release to execute, exposing lifecycle omissions that a single arithmetic
example can hide.

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
