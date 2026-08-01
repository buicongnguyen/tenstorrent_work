<!-- rewrite-status: improved-draft -->
# TT-Distributed: Multi-Host Runtime

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/MultiHostMeshRuntime.md"><code>tech_reports/TT-Distributed/MultiHostMeshRuntime.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to specify global mesh/rank identity,
one-controller-per-device ownership, local versus cross-host responsibilities, SPMD
workload epochs, host coordination, error propagation, and aggregate completion.

### How work and data move

The complete path is launcher/topology distribution through per-host rank
initialization, local `MeshDevice`/`MeshBuffer`/`MeshWorkload`, device command
submission, fabric communication, host rendezvous, global completion, and failure
cleanup.

### What must never break

The non-negotiable invariant is that all ranks agree on topology and epoch/workload
order, each physical device has one controlling process, and no rank advances beyond an
unpublished dependency or reports success when a peer failed.

### Where the report makes it concrete

The report makes the decision concrete by connecting the design to `MeshDevice`,
`MeshWorkload`, `MeshBuffer`, the proposed multiple-lockstep-controller model, and the
explicit host-coordination dependency in the source.

### How the decision is tested

The controlled procedure is to inject one delayed and one failed rank during a two-epoch
workload. **Expected observation:** delay appears as the global critical participant
and failure is propagated consistently without other ranks committing a later epoch.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/MultiHostMeshRuntime.md):

- **Local controller.** `MeshDevice`, `MeshBuffer`, and `MeshWorkload` represent one
  host's local mesh state and work. The proposed multiple lockstep controllers must
  agree on the same global mesh coordinates and workload phase before issuing dependent
  work.

- **Cross-host coordination.** The source leaves host coordination as an explicit
  dependency rather than hiding it inside a local queue. Define the transport, barrier,
  failure behavior, and completion evidence that make a remote controller's progress
  visible to its peers.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
