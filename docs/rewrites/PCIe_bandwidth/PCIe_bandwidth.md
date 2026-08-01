<!-- rewrite-status: improved-draft -->
# PCIe Bandwidth Measurement

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md"><code>tech_reports/PCIe_bandwidth/PCIe_bandwidth.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned report intentionally measures two different systems that happen to traverse
PCIe. Tests 606/607 time `distributed::WriteShard` and `distributed::ReadShard` from the
host. Those numbers include command-queue serialization, the runtime's dispatch path,
DMA setup, and the transfer itself. Tests 604/605 instead run a tight data-movement
kernel on Tensix core `{0, 0}` and issue raw `noc_async_write` or `noc_async_read`
transactions to the PCIe core. Mixing these results would attribute software launch
cost to the link, or report an internal microbenchmark as application-visible
throughput. The architecture is shaped around preserving that boundary.

The two sweeps also answer different optimization questions. Host tests vary total
buffer size from 4 KB to 16 MB with a fixed 4 KB page to reveal when dispatch and DMA
startup are amortized. Device tests vary transaction size at fixed repeated work to
reveal the NoC/PCIe packet-size knee. The pinned architecture-specific ranges begin at
one flit—32 B on Wormhole and 64 B on Blackhole—and end at 8 KB and 16 KB respectively.

### How work and data move

On the host path, a caller supplies a shard and invokes `distributed::WriteShard` for
H2D or `distributed::ReadShard` for D2H. The command is serialized into the mesh command
queue, consumed by the dispatch machinery, and completed by DMA. `std::chrono` surrounds
that full operation, so the measured owner is the host API, not a kernel. Buffer size is
the numerator and host elapsed time is the denominator.

On the device path, the host first resolves the translated coordinates of the PCIe core
from the SoC descriptor. The test targets an offset 50 MB into the PCIe BAR so that the
benchmark does not collide with runtime-reserved regions. Coordinates, local addresses,
transaction bytes, count, and clock are compile-time arguments; this keeps runtime
argument loading out of the measured loop. The kernel constructs
`NOC_XY_PCIE_ENCODING(pcie_x_coord, pcie_y_coord) | pcie_l1_local_addr`, then issues
`num_of_transactions` operations between that address and a local L1 address. A read
uses `noc_async_read(noc_addr, l1_local_addr, bytes_per_transaction)`; a write reverses
the data direction with `noc_async_write`. The matching
`noc_async_read_barrier()`/write barrier establishes completion ownership before the
zone ends.

`DeviceZoneScopedN("RISCV0")` records cycle duration. The byte count is
`num_transactions * transaction_size`; division by cycles gives bytes/cycle. The host
queries `device->get_clock_rate_mhz()` and the kernel emits it with
`DeviceTimestampedData("Clock frequency MHz", ...)`, allowing the Python stats collector
to convert to GB/s using the observed clock instead of an assumed nominal value. The
`bandwidth_unit` in `test_information.yaml` controls whether reporting remains in
bytes/cycle or is converted.

### What must never break

Direction, numerator, and completion boundary must describe the same transaction. For
D2H, request/response traffic and read completion belong to the measurement; for posted
H2D writes, enqueue completion alone is not transfer completion. Source and destination
ranges must remain live, non-overlapping with runtime state, aligned for the selected
test, and large enough for every transaction. Changing core, NoC, dispatch mode, BAR
offset, page size, or clock conversion while comparing only the headline GB/s breaks the
experiment. Host and device measurements must retain separate labels because neither is
a correction factor for the other.

### Where the report makes it concrete

The transaction sweep explains the expected curve. A 32/64-byte transfer pays fixed
issue, routing, and protocol overhead for little payload, so sustained bandwidth is low.
Larger transactions amortize that cost until some link, DMA, NoC, or endpoint resource
sets the plateau. Reads may trail writes because a PCIe read requires a request and
returning completion data, whereas a write can be posted. On the host sweep, the same
amortization applies at a coarser level; very large buffers can plateau or regress when
dispatch chunking or allocation behavior becomes relevant. Those are hypotheses to
separate with the two tests, not conclusions to infer from one curve.

### How the decision is tested

Run the report's filters independently: `*PCIeHost*` for tests 606/607 and
`*PCIeBandwidthSweep*` for 604/605; use `dmtest ... --plot` for device profiler plots.
For every point, record direction, total bytes, transaction/page size, transaction
count, core, NoC, fast-dispatch state, measured clock, cycles, and validation result.
First sweep the pinned powers of two, then repeat enough times to report distribution,
not one best sample. A sound result shows a small-transfer overhead region followed by
a stable plateau; host API bandwidth should generally remain below the raw-kernel path
because it includes more work. If a curve changes without a corresponding change in
cycles or byte accounting, audit barriers and units before claiming a hardware effect.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md):

- **Host-transfer measurement.** `distributed::WriteShard` and `distributed::ReadShard`
  measure host/device transfer paths; `std::chrono` must bracket only the intended
  operation with required synchronization. Allocation, compilation, and warm-up belong
  outside the steady-state interval.

- **Device-transfer measurement.** `noc_async_read` and `noc_async_write` exercise
  device movement, while `DeviceZoneScopedN("RISCV0")` supplies a device timeline
  boundary. Convert bytes and duration using the actual payload and direction, then
  compare host PCIe and device NoC results as different paths.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report measures host-to-device and device-to-host PCIe throughput through both
    host-side shard APIs and device-side NoC kernels, separating PCIe limits from
    on-device placement and transfer overhead. It therefore requires controlled direction,
    size, synchronization, and placement.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The timed interval must move a known byte count in one declared direction, all
    asynchronous work must complete before the timer stops, source and destination
    buffers must remain valid, and readback must verify that the expected bytes arrived.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    For a write, a pinned host buffer feeds the runtime transfer → PCIe carries data to
    device DRAM/L1 shards → optional device NoC movement distributes it → a completion
    boundary makes it consumable. The read path reverses those stages before host
    validation.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** PCIe generation/width, host platform, DMA granularity, device
    bank topology, sharding API, transfer size, and measured GB/s are machine- and
    snapshot-specific.

    **Durable model.** Report payload bytes and direction, warm and synchronize
    consistently, sweep transfer sizes, separate link throughput from device
    redistribution, validate data, and compare against the negotiated-link ceiling
    rather than a marketing maximum.

## Source and delta

- **Original source:** [`tech_reports/PCIe_bandwidth/PCIe_bandwidth.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
