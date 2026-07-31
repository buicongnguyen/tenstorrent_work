<!-- rewrite-status: seed -->
# TT-Metalium Distributed

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md"><code>tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md</code>. This learner page
    establishes provenance, a reading map, a report-specific architecture plan,
    concrete code boundaries, and answered reasoning checks; a full visual rewrite
    remains queued.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 2370 |
| Section headings | 89 |
| Fenced code examples | 42 |
| Markdown images | 43 |

### Section outline

- Architecture Specification
- 2.1 Virtualization through TTNN <a id="virtualization-through-ttnn"></a>
- 2.2 Project Motivation and Design <a id="motivation"></a>
- 2.3 Dependencies with External Efforts <a id="dependencies"></a>
- 3.1 MeshDevice: Overview and Associated Data-Structures <a id="meshdevice"></a>
  - 3.1.1 Terminology: <a id="meshdevice-terminology"></a>
  - 3.1.2 Constraints and Properties of a Virtual Mesh <a id="meshdevice-constraints"></a>
  - 3.1.3 MeshDevice Abstraction <a id="meshdevice-abstraction"></a>
  - 3.1.3 Data Structures <a id="meshdevice-data-structures"></a>
  - 3.1.3 Lightweight and Consistent APIs <a id="meshdevice-lightweight-and-consistent-apis"></a>
- 3.2 Virtual Command Queues <a id="virtual-command-queues"></a>
  - 3.2.1 Overview
  - 3.2.2 API Interface
- 3.3 Memory Management: MeshBuffer and MeshAllocator <a id="meshbuffer"></a>
  - 3.3.1 Background: Device Buffer and Single-Device Allocator
  - 3.3.2 MeshBuffer and Allocator: Overview
  - 3.3.3 MeshBuffer: Data Structure
  - 3.3.4 SubDevice Integration
  - 3.3.5 MeshBuffer: Host APIs
- 3.4 MeshWorkload: Overview, Data-Structures and APIs <a id="meshworkload"></a>
  - 3.4.1 Differences with the Existing Program Class
  - 3.4.2 Minimal Functional Specification of MeshWorkload
  - 3.4.3 User Facing APIs for MeshWorkload
  - 3.4.4 Usage Examples
- … 65 additional headings in the original

## Improvement plan

1. **Architecture pressure.** Define the lowering boundary between global TT-NN intent and
   physical per-device programs: logical mesh identity, virtual queues, mesh
   buffers/allocator, workload expansion, controller ownership, and completion aggregation.

2. **Flow to make explicit.** Draw a TT-NN distributed operation through `MeshDevice`,
   virtual command queue, `MeshWorkload`, per-device program selection, `MeshBuffer`
   resolution, controller enqueue, fabric/CCL movement, and logical completion.

3. **Invariant to prove.** Prove each logical coordinate resolves to one owning device for
   buffer/workload lifetime, every intended shard executes exactly once, and logical
   completion includes all physical program and communication dependencies.

4. **TT-Metal evidence to connect.** Connect the plan to the report's `MeshDevice`, virtual
   command queues, `MeshBuffer`, `MeshAllocator`, `MeshWorkload`, controller, and
   virtualization sections rather than using a generic distributed diagram.

5. **Experiment and expected observation.** Trace a small two-device operation with unique
   shard markers through virtual and physical identities; expected result: exactly-once
   local execution, correct composition, and no logical completion before both device/fabric
   paths finish.

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
- **Current delta:** provenance, source metrics, outline, report-specific architecture
  plan, two source-linked implementation-boundary reviews, and answered reasoning
  checks. Generation-sensitive claims remain scoped to the pinned source snapshot.
