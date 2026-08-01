<!-- rewrite-status: improved-draft -->
# PCIe Bandwidth Measurement

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md"><code>tech_reports/PCIe_bandwidth/PCIe_bandwidth.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to separate host memory/API overhead, PCIe DMA, device
DRAM/L1 placement, and on-device NoC redistribution for both H2D and D2H; declare which
path each reported GB/s number actually measures.

### How work and data move

The complete path is payload movement from pinned/host buffer through `WriteShard` or
`ReadShard`, PCIe, device buffer, optional `noc_async_read/write`, completion/barrier,
and final data validation.

### What must never break

The non-negotiable invariant is that timed bytes, direction, buffer lifetime, placement,
and synchronization are identical across comparisons and that the timer stops only after
transfer completion, not asynchronous enqueue.

### Where the report makes it concrete

The report makes the decision concrete by connecting tests to `distributed::WriteShard`,
`distributed::ReadShard`, `std::chrono`, `noc_async_read`, `noc_async_write`, and device
zones such as `DeviceZoneScopedN("RISCV0")`.

### How the decision is tested

The controlled procedure is to sweep transfer size in both directions and compare direct
host path with device NoC redistribution. **Expected observation:** small sizes expose
startup/API cost, large sizes approach the negotiated-link or device-path ceiling.

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
