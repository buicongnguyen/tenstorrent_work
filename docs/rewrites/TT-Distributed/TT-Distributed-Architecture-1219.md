<!-- rewrite-status: improved-draft -->
# TT-Metalium Distributed

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md"><code>tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to define the lowering boundary between global TT-NN
intent and physical per-device programs: logical mesh identity, virtual queues, mesh
buffers/allocator, workload expansion, controller ownership, and completion aggregation.

### How work and data move

The complete path is a TT-NN distributed operation through `MeshDevice`, virtual command
queue, `MeshWorkload`, per-device program selection, `MeshBuffer` resolution, controller
enqueue, fabric/CCL movement, and logical completion.

### What must never break

The non-negotiable invariant is that each logical coordinate resolves to one owning
device for buffer/workload lifetime, every intended shard executes exactly once, and
logical completion includes all physical program and communication dependencies.

### Where the report makes it concrete

The report makes the decision concrete by connecting the plan to the report's
`MeshDevice`, virtual command queues, `MeshBuffer`, `MeshAllocator`, `MeshWorkload`,
controller, and virtualization sections rather than using a generic distributed diagram.

### How the decision is tested

The controlled procedure is to trace a small two-device operation with unique shard
markers through virtual and physical identities. **Expected observation:**
exactly-once local execution, correct composition, and no logical completion before both
device/fabric paths finish.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md):

- **Virtualized resources.** `MeshDevice`, virtual command queues, `MeshBuffer`, and
  `MeshAllocator` present global-looking objects over per-device resources. Review how
  mesh coordinates, buffer regions, and queue IDs translate at each local device.

- **Workload control.** `MeshWorkload` and the controller distribute programs and
  synchronization across the mesh. The virtualization contract is correct only if
  ownership, enqueue order, completion, and failure are preserved when one logical
  action becomes many physical actions.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The architecture virtualizes many devices behind TT-NN mesh
    abstractions—`MeshDevice`, virtual command queues, `MeshBuffer`/allocator, and
    `MeshWorkload`—so programs can scale without manually issuing every per-device
    operation. It coordinates logical intent with distributed physical ownership.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    A logical mesh coordinate must resolve to the same owning physical device throughout
    buffer and workload lifetimes. Queue dependencies, allocation views, and per-device
    programs must collectively implement the logical operation exactly once on every
    intended shard.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A TT-NN distributed operation targets a logical mesh tensor → a virtual command
    queue accepts the work → `MeshWorkload` expands or references per-device programs →
    mesh buffers resolve local allocations → owning controllers submit commands →
    fabric/CCL moves cross-device data → logical completion is reported.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Class names, virtual-CQ implementation, allocator metadata,
    workload APIs, host scaling model, mesh sizes, and fabric integration are tied to
    the dated architecture specification.

    **Durable model.** Virtualize placement behind stable logical identities, preserve
    explicit ownership and lifetimes, lower global work into local programs plus
    communication, and ensure logical completion aggregates every required physical
    dependency.

## Source and delta

- **Original source:** [`tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
