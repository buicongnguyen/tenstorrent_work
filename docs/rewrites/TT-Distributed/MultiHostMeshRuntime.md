<!-- rewrite-status: seed -->
# TT-Distributed: Multi-Host Runtime

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/MultiHostMeshRuntime.md"><code>tech_reports/TT-Distributed/MultiHostMeshRuntime.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/TT-Distributed/MultiHostMeshRuntime.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 310 |
| Section headings | 15 |
| Fenced code examples | 7 |
| Markdown images | 1 |

### Section outline

- Table of Contents
- Design Philosophy & Rationale
  - Core Principle: Global Definition vs. Local Execution
  - SPMD Execution Model
  - Coordination vs. Data Movement
  - Global View and Local Ownership
  - Underlying Fabric Assumption
  - Determinism
- **Proposed Design:** Multi-Host, Multi-Device (SPMD / Multiple Lockstep Controllers)
  - Visualization (4-Host Example: 16x8 Mesh / 8x4 Sub-Meshes)
  - Comparison with Other Architectures
    - 1. Single-Host, Single-Device
    - 2. Single-Host, Multi-Device (e.g., Galaxy)
    - 3. Multi-Host, Multi-Device (Single Controller, Multiple Executors)
- Host Coordination Dependency

## Improvement plan

1. **Architecture pressure.** Specify global mesh/rank identity, one-controller-per-device
   ownership, local versus cross-host responsibilities, SPMD workload epochs, host
   coordination, error propagation, and aggregate completion.

2. **Flow to make explicit.** Draw launcher/topology distribution through per-host rank
   initialization, local `MeshDevice`/`MeshBuffer`/`MeshWorkload`, device command
   submission, fabric communication, host rendezvous, global completion, and failure
   cleanup.

3. **Invariant to prove.** Prove all ranks agree on topology and epoch/workload order, each
   physical device has one controlling process, and no rank advances beyond an unpublished
   dependency or reports success when a peer failed.

4. **TT-Metal evidence to connect.** Connect the design to `MeshDevice`, `MeshWorkload`,
   `MeshBuffer`, the proposed multiple-lockstep-controller model, and the explicit
   host-coordination dependency in the source.

5. **Experiment and expected observation.** Inject one delayed and one failed rank during a
   two-epoch workload; expected result: delay appears as the global critical participant and
   failure is propagated consistently without other ranks committing a later epoch.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/MultiHostMeshRuntime.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/MultiHostMeshRuntime.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The design coordinates several host processes/controllers that collectively operate
    one logical multi-device mesh. It must preserve SPMD simplicity while assigning each
    local device to one controller and coordinating topology, workload order, and
    failures across hosts.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    All ranks must agree on the global mesh, rank mapping, workload/collective order,
    and synchronization epochs; each physical device must have exactly one controlling
    host process. A rank cannot advance past a dependency that another rank has not
    published.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A launcher establishes rank and topology metadata → each host process opens its
    local devices → matching mesh work is built or received → controllers submit local
    command streams → device fabric carries cross-host dependencies/data → host
    coordination provides barriers and propagates completion/errors.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** The proposed controller model, host-coordination dependency,
    process APIs, transport choice, mesh limits, and failure handling reflect a design
    snapshot.

    **Durable model.** Give resources single owners, represent the global topology
    identically everywhere, use epochs for distributed ordering, keep control-plane
    coordination separate from bulk device traffic, and make rank failures observable to
    all participants.

## Source and delta

- **Original source:** [`tech_reports/TT-Distributed/MultiHostMeshRuntime.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/MultiHostMeshRuntime.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/TT-Distributed/MultiHostMeshRuntime.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
