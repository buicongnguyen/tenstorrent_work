<!-- rewrite-status: improved-draft -->
# **Data Multicasting**

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md"><code>tech_reports/prog_examples/multicast/multicast.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned example isolates the minimum useful multicast contract: one 32x32 bfloat16
identity tile in DRAM, one coordinator at logical `{0,0}`, and three receivers at
`{1,0}` through `{3,0}`. The same tile is required by every receiver, so three
independent DRAM reads or three software-issued unicasts would repeat source traffic.
`noc_async_write_multicast` lets the NoC replicate one source payload over a rectangular
destination range. That bandwidth saving is only correct if every receiver has storage
before the fanout and no receiver consumes the destination before the data transaction
is ordered complete. The two-semaphore protocol exists to establish those conditions.

Logical and physical coordinates are kept separate because the host assigns portable
worker identities while the NoC packet addresses physical endpoints. The host uses
`worker_core_from_logical_core` for the sender and receiver range before placing
coordinates in kernel arguments. This is not administrative conversion: encoding the
logical rectangle in `get_noc_multicast_addr` could target the wrong workers after
harvesting or architecture-dependent placement.

### How work and data move

`multicast.cpp` writes the tilized identity matrix into a DRAM `MeshBuffer` and creates
one-page Float16_b circular buffers `c_0` and `c_16` on all four cores. `c_0` is the
inbound stream; `c_16` is only a placeholder for a later output path. `CreateSemaphore`
allocates identical local semaphore slots on the core range: `sender` is a readiness
counter and `receiver` is an arrival flag. The coordinator runs on
`DataMovementProcessor::RISCV_0`; `SetRuntimeArgs` supplies the physical destination
bounds, semaphore IDs, DRAM bank/address, tile byte count, and destination count.

The coordinator resolves the DRAM page with
`get_noc_addr_from_bank_id<true>(dram_bank_id, src0_dram)`, gets `c_0`'s write pointer,
issues `noc_async_read`, and waits at `noc_async_read_barrier()`. Each inbound kernel
first executes `cb_reserve_back(c_in0, 1)`, sets its local receiver semaphore to
`INVALID`, computes the coordinator semaphore address with `get_noc_addr`, and calls
`noc_semaphore_inc(..., 1)`. Only after `noc_semaphore_wait(sender_addr_ptr, num_dests)`
has observed all three increments does the coordinator reset its counter and begin
fanout.

The sender combines the physical rectangle and the common destination L1 address with
`get_noc_multicast_addr(start_x, start_y, end_x, end_y, tile_l1_addr)`, then calls
`noc_async_write_multicast(..., single_tile_size, num_dests)`. It writes `VALID` to its
local receiver semaphore value and multicasts that semaphore with
`noc_semaphore_set_multicast`. Receivers block in
`noc_semaphore_wait(receiver_addr_ptr, VALID)` and publish the now-arrived tile with
`cb_push_back(c_in0, 1)`. This protocol relies on the payload multicast being ordered
before the following semaphore multicast on the issuing NoC. The semaphore operation is
not, by itself, a payload-completion barrier; the report's final
`noc_async_write_barrier()` occurs after both sends and protects sender reuse/exit. Thus
the receiver flag is a valid release signal only under that documented same-NoC ordering
contract. In the pinned program, DPRINT `TileSlice` samples the CB write pointer before
push so validation does not alter stream ownership.

### What must never break

`num_dests`, receiver range, and number of readiness increments must agree; otherwise
the coordinator either waits forever or transmits before all buffers exist. Every
receiver must reserve the same-sized `c_0` page at the same L1-relative destination
before signaling readiness, because multicast carries one destination address for the
range. The arrival semaphore cannot be reused as readiness state, and it must be reset
for a subsequent iteration. Its transition to `VALID` must be ordered after payload
visibility at every receiver; if that ordering is not guaranteed by the selected NoC
API/path, an explicit completion/acknowledgment protocol is required before
`cb_push_back`. Source or destination storage cannot be reclaimed before the matching
NoC barrier/consumer action. Finally, all runtime coordinates sent to device code must
be physical even though kernel placement uses logical coordinates.

### Where the report makes it concrete

The example exposes the protocol's state rather than hiding it in a collective API:
sender semaphore values progress `0 -> 3 -> 0`, each receiver flag progresses
`INVALID -> VALID`, and CB ownership progresses free -> reserved/unpublished ->
published. `coordinator_kernel.cpp` owns DRAM and fanout; `inbound_kernel.cpp` owns local
reservation and publication. The void compute and outbound kernels are explicitly
exercises in the source, so this pinned report proves transport into `c_0`, not a
complete compute-and-writeback pipeline.

### How the decision is tested

Run the given identity tile first and verify the same sampled rows/columns on all three
receivers before their `cb_push_back`. Then encode receiver-visible sentinels and vary
one failure condition at a time in a debug build: delay one receiver before readiness,
use an incorrect `num_dests`, omit a reset, or repeatedly alternate payload bit patterns
to stress payload-versus-semaphore ordering. The correct program waits for the delayed
receiver and never shows a partial or prior-generation tile; mismatched cardinality
should expose a hang or protocol failure rather than silent success. For performance,
compare one multicast with three repeated unicasts and three independent DRAM reads
while sweeping payload size and fanout. Count source bytes, NoC transactions, sender
wait, and receiver skew. The pinned mechanism should win when payload reuse dominates
group synchronization; a slow receiver or sparse destination need can erase that
advantage.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md):

- **Host topology.** `multicast.cpp` assigns the `{0, 0}` coordinator, receiver core
  range, circular buffers, semaphores, and per-core runtime arguments. Coordinates used
  for NoC multicast must match the same physical/virtual coordinate convention on every
  participant.

- **Sender/receiver handshake.** `coordinator_kernel.cpp` reserves and publishes the
  payload, while `inbound_kernel.cpp` waits for the semaphore and consumes it. Check
  destination count, semaphore initialization/reset, write completion, and CB push/pop
  counts for every multicast round.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The example demonstrates one coordinator sending identical data to a group of
    receiver cores through a NoC multicast, replacing repeated point-to-point transfers
    while making receiver readiness and completion explicit. The optimization is valid
    only when all receivers need the same payload.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every target must reserve valid destination storage before the coordinator writes,
    and no receiver may publish the page before arrival. The sender may reuse its source
    only after the required completion/acknowledgement contract is satisfied.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The host creates coordinator/receiver kernels, CBs, ranges, and semaphores →
    receivers reserve pages and signal readiness → the coordinator issues one multicast
    to the physical destination rectangle → transport completes → receivers
    signal/publish arrival → local consumers process their copies.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** NoC multicast APIs, coordinate conversion, rectangular range
    restrictions, semaphore placement, alignment, and destination encoding depend on
    TT-Metal and the chip topology.

    **Durable model.** Use multicast for genuine one-to-many reuse, prove all
    destinations are ready, distinguish transport completion from local publication, and
    compare saved source traffic with synchronization and fanout cost.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/multicast/multicast.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/multicast/multicast.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
