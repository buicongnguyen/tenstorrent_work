<!-- rewrite-status: improved-draft -->
# Tensor Padding (Multicore)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md"><code>tech_reports/prog_examples/pad_multi_core/pad_multi_core.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned program pads row-major `(64,32)` bfloat16 data to `(64,64)` on four cores.
Padding is expressed as data movement rather than compute because every output value is
either copied from one input coordinate or synthesized from a constant. The first
dimension partitions evenly—16 rows per core—so cores can own disjoint source and
destination intervals without communicating. This avoids a compute-kernel launch and
keeps the reader responsible for classifying coordinates while the writer remains a
simple ordered drain.

The physical stream is not one CB page per logical bfloat16. Two bfloat16 values are
packed in a `uint32_t`, but the TTNN-v2 row-major reader uses a 64-byte aligned L1 slot
per stick in this example. That decouples external payload size (`stick_size_bytes = 4`)
from circular-buffer stride (`stick_size_padded_aligned = 64`). The extra space supports
the generic padding/alignment kernel; it must not be mistaken for 64 bytes of output per
logical stick.

### How work and data move

The host packs input values 1..2048 and the pad value 2 into `uint32_t` words, then
creates replicated DRAM `MeshBuffer`s with 4-byte pages. Three `UInt32` CB interfaces
are configured on cores `{0,0}` to `{0,3}`: `c_0` is the padded row stream, `c_1` holds
the padding pattern interface, and `c_2` is alignment scratch. `c_0` has
`num_packed_row_dst` pages, enough for one output row; its page size is 64 bytes while
`c_2`'s page is 4 bytes.

Compile-time arguments describe N/H/C source and padded extents, alignment, front/end
padding, `packed_pad_value`, and `TensorAccessorArgs(*src_buffer)`. The source chooses
`pad_reader_dims_rm_interleaved.cpp` on `RISCV_0` and
`pad_writer_dims_rm_interleaved.cpp` on `RISCV_1`, using their respective default NoCs.
Per-core runtime arguments assign `start_src_idx`, `start_dst_idx`, total output sticks,
and one row (`num_packed_row_dst`) per barrier. After each core is configured, the host
advances source by `num_packed_row_src * 16` and destination by
`num_packed_row_dst * 16`, which is the ownership proof for non-overlapping rows.

For each row-sized batch, the reader calls `cb_reserve_back(c_0, ...)` and walks padded
N/H/C coordinates. It seeds the first word of every 64-byte L1 slot with
`packed_pad_value`. If the coordinate is in the logical `(64,32)` input, a
`TensorAccessor` NoC address supplies the 4-byte source word and overwrites that seed;
otherwise the seed remains the output. The front-padding and unaligned branches stage
through `c_2`; the latter contains an explicit read barrier to prevent the next read
from overwriting scratch while a loop-back read still sources it. After all reads in a
row complete, `cb_push_back` transfers ownership to the writer. The writer waits on
`c_0`, emits only 4 bytes from each 64-byte slot through the destination
`TensorAccessor`, calls `noc_async_write_barrier`, then pops the row.

### What must never break

Each of the 64 output rows has exactly one core owner; each row contains 16 copied packed
words followed by 16 packed pad words. `start_src_idx` advances only for logical source
sticks, while `start_dst_idx` advances across every output stick. The writer's 4-byte
payload step and 64-byte L1 stride must stay distinct. It cannot pop a row before its
write barrier, and the reader cannot publish before every asynchronous read in that row
completes. In alignment branches, `c_2` cannot be reused across an outstanding read.
Changing `src_N`, `dst_N`, packing ratio, or core count without recomputing page counts
and per-core starts breaks address ownership even if the program still runs.

### Where the report makes it concrete

For the pinned constants, `src_N / packing_ratio = 16` and
`dst_N / packing_ratio = 32`; four cores therefore process 16 rows each, not two. The
report's later prose saying “it is 2” is inconsistent with its code and preceding
partition and should not be used as an architectural fact. Similarly, some inline
comments label the 64-byte `stick_size_padded` as 32 B. The assigned values and kernel
arguments are the reliable pinned evidence: 4-byte external words in 64-byte L1 slots,
32 output sticks per row.

### How the decision is tested

Validate all 4096 bfloat16 outputs, not only shape: columns 0..31 must equal the original
row and columns 32..63 must equal 2. Encode row and column into input values so a swapped
`start_src_idx` is obvious, and place canaries around destination ranges to detect
overrun. Instrument each core's first/last source and destination word; expected ranges
must be adjacent and non-overlapping. Then test the generic kernel paths with front and
unaligned padding in a separate configuration, checking scratch barriers under stress.
For performance, measure reader CB-full waits, writer CB-empty waits, and per-core finish
time. Since all four owners have equal rows and padding, persistent skew points to bank,
NoC, or address-placement effects rather than intended workload imbalance.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md):

- **Host partition.** `Device`, `CommandQueue`, and `Program` setup allocate bfloat16
  DRAM/L1 buffers and divide output regions across the designated core ranges. Runtime
  arguments must give each core a disjoint output interval plus the correct source
  bounds and pad value.

- **Reader/writer contract.** Reader kernels distinguish copied input from synthesized
  padding; writer kernels place both into the declared layout. Validate edge, corner,
  and uneven final-core work so no core reads outside the logical tensor or overwrites
  another core's output.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The program parallelizes tensor padding: cores must produce a larger output
    containing both copied input coordinates and constant padding, without serializing
    address generation or creating overlapping writes. Boundary classification is the
    central correctness task.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Each physical output element must be written exactly once. Coordinates inside the
    original extent must map to the correct input element; coordinates outside it must
    receive the declared pad value, including tile/row padding required by the storage
    layout.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The host allocates input/output buffers and partitions output pages among cores →
    each reader classifies its assigned output coordinates → it reads the corresponding
    input page/element or synthesizes the pad value → a writer commits the
    non-overlapping output region → host validation checks edges and interior.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Page/tile layout, core range, runtime arguments, alignment,
    buffer placement, and vectorized fill/read implementation are example- and
    architecture-specific.

    **Durable model.** Partition by unique output ownership, derive source coordinates
    from the output, treat physical padding separately from logical padding, and
    emphasize boundaries/partial pages in tests.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/pad_multi_core/pad_multi_core.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
