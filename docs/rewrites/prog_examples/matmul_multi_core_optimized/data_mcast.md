<!-- rewrite-status: improved-draft -->
# Data Multicasting in [matmul_multicore_reuse_mcast]

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md"><code>tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

This pinned example is explicitly Grayskull-only and builds on the preceding
`matmul_multicore_reuse` kernel. Its optimization follows directly from output-tile
ownership. Cores in the same output row need the same `in0` row block but different
`in1` column blocks; cores in the same output column need the same `in1` block but
different `in0` blocks. If every core reads both operands from DRAM, shared blocks are
fetched once per consumer. The chosen mechanism assigns DRAM-reader/sender roles to the
left column and top row, then fans each resident block through the core grid. External
reads fall while on-chip multicast and synchronization increase—a good exchange only
when each block has enough fanout and reuse.

The design does not make a separate multicast-only compute graph. Every core still owns
a disjoint `per_core_M` by `per_core_N` region of C and uses the same partial-result
reload discipline as data reuse. Communication roles are overlaid on that output grid,
which avoids a separate set of relay-only cores but makes edge role selection and NoC
assignment part of correctness.

### How work and data move

The host derives the rectangle from `start_core`,
`bmm_op_utils::get_core_range(...)`, `num_cores_r`, and `num_cores_c`, then partitions
it into four roles: the top-left `in0_sender_in1_sender`; the remaining
`in0_sender_in1_receiver` cores in `left_column`; the remaining top-row
`in0_receiver_in1_sender` cores; and interior
`in0_receiver_in1_receiver` cores. `all_except_left_column` is also separated so writer
kernels can use a different default NoC from the left column. Circular buffers are
created over `CoreRangeSet({all_cores})`, giving every role the same local stream
interface even though its producer is DRAM on an edge or multicast in the interior.

Four dataflow kernels encode those roles. The top-left reader originates both operands.
A left-column reader receives its `in1` block from above while reading/originating its
row's `in0`; a top-row reader receives `in0` from the left while originating its
column's `in1`; an interior reader receives both. Runtime arguments contain the physical
multicast rectangle, sender coordinates, destination count, and the four semaphore IDs
created by `CreateSemaphore(program, all_cores, INVALID)`. The host obtains physical
endpoints with `device->worker_core_from_logical_core(...)`; logical output ownership
cannot be inserted directly into a NoC packet.

The source registers reader variants on `DataMovementProcessor::RISCV_1`, selecting
`NOC::RISCV_0_default` for left-edge roles and `NOC::RISCV_1_default` for top/interior
roles. Writers likewise split between `unary_writer_kernel_noc0_id` on
`all_except_left_column` and `unary_writer_kernel_noc1_id` on `left_column`. This is a
pinned routing choice intended to distribute traffic; it is not a generation-independent
rule about which RISC always reads or writes.

Once both input CB streams publish a K block, every core calls the fused compute kernel
`bmm_large_block_zm_fused_bias_activation.cpp`. `matmul_tiles` accumulates the core's
output subblocks. When accumulation must spill, the kernel reloads partials from its
intermediate CB; `enable_reload`, `spill`, `FUSE_BIAS`, and `PACKER_L1_ACC` decide that
path. On the final result, `add_tiles_bcast_rows` broadcasts bias rows across the output
subblock, and `SFPU_OP_FUNC_ACTIVATION` applies the selected in-place activation before
the writer stores the disjoint C region.

### What must never break

For every K iteration, each output core must see exactly one matching `in0` row block
and `in1` column block before compute begins. Receiver storage and receiver semaphore
state must be ready before the sender publishes; otherwise a fast edge core can
overwrite an unreserved CB page or an interior core can consume a previous iteration.
The destination count must equal the physical multicast rectangle excluding the sender
where specified. Logical-to-physical coordinate conversion, core-role range, runtime
arguments, semaphore IDs, and selected reader kernel must all describe the same grid.

Partial C ownership remains local and non-overlapping, all K blocks contribute once,
and bias/activation run only after the final accumulation state. Applying activation to
a spilled partial changes the math; skipping a required reload loses earlier K work.

### Where the report makes it concrete

The `mm_reader_args` tie output position to DRAM position: `Kt * per_core_M * core_idx_y`
selects the `in0` row region, while `per_core_N * core_idx_x` selects the `in1` column
region. The physical `right_core`, `left_core_plus_one`, `bottom_core`, and
`top_core_plus_one` coordinates bound the horizontal and vertical fanouts; their
`num_cores_c - 1` and `num_cores_r - 1` counts are the synchronization cardinalities.
That is the causal bridge between matrix partition, core role, and packet destination—not
merely boilerplate runtime arguments.

### How the decision is tested

First validate a small grid with uniquely encoded A rows and B columns so a swapped
sender range is visible in C, and compare every output tile with a host matmul including
bias and activation. Instrument semaphore waits and confirm no interior compute starts
before both operands arrive. Then compare the reuse-only and reuse-plus-multicast
executables at fixed dimensions while sweeping grid width and height. Count DRAM bytes
per operand separately: increasing columns should amortize each `in0` read, while
increasing rows should amortize each `in1` read. Also record NoC traffic and per-core
finish time. The expected benefit ends when multicast sender injection, a shared route,
or receiver skew costs more than the DRAM reads removed. Because the pinned report says
Grayskull-only, success there is not evidence that its exact kernel/NOC assignment is
valid on another architecture.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md):

- **Core-role partition.** `CoreRangeSet`, `all_cores`, `left_column`, and
  `all_except_left_column` separate DRAM readers/multicast senders from receivers. The
  host must generate runtime arguments and semaphore addresses that match each role's
  core set.

- **Multicast protocol.** Semaphore setup orders publication and reuse of multicast data
  before `bmm_large_block_zm_fused_bias_activation` consumes it. Verify receiver count,
  destination rectangle, sender exclusion, and reset value per block; one stale receiver
  can deadlock or reuse the wrong tile.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    This stage removes redundant DRAM reads by having designated cores fetch a shared
    matmul operand once and multicast it to receiver cores, while retaining block reuse
    and optionally fusing bias/activation in the compute path.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every receiver must reserve the correct CB page and advertise readiness before
    multicast; all destinations must observe the same tile before compute consumes it,
    and the sender must not reuse its source page until the multicast protocol permits.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A source core reads an operand block from DRAM into its CB → receiver semaphores
    prove destination space is ready → one NoC multicast distributes the block across a
    core range → receivers publish local CB pages → compute combines them with each
    core's private operand/output block → writers store results.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Multicast rectangle rules, logical/physical coordinates,
    semaphore APIs, CB depths, block sizes, core roles, and fused-kernel arguments are
    TT-Metal and topology specific.

    **Durable model.** Read shared data once, fan it out near consumers, separate
    readiness from arrival, retain private data where it is reused, and include
    synchronization/fanout cost in the bandwidth saving.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
