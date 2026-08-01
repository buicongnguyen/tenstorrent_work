<!-- rewrite-status: improved-draft -->
# TT-Distributed: Multi-Host Runtime

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/MultiHostMeshRuntime.md"><code>tech_reports/TT-Distributed/MultiHostMeshRuntime.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The proposal targets one large uniform 2-D/3-D logical mesh and SPMD tensor/data
parallel workloads, explicitly not MPMD, pipeline/model parallel, or multiple meshes.
Its central trade is **replicated definition instead of serialized remote dispatch**:
one process (normally one MPI rank) per host runs the same application and constructs
the same global `MeshDevice`, `MeshBuffer`, and `MeshWorkload`. Each rank then owns only
its local sub-mesh and dispatches locally. This avoids a single controller's command
serialization and network bottleneck, but moves correctness onto determinism: every
rank must allocate, free, and define work in the same logical order.

### How work and data move

All ranks first establish the same global coordinate system. In the report's 16x8
example, four ranks each own an 8x4 region but all construct the 16x8 view. A global
`MeshWorkload` is submitted to the host-local `MeshCommandQueue`; its dispatch logic
filters commands by global coordinates and forwards only matching work to the 32 local
device `CommandQueue`s. Bulk collective/device traffic then traverses the unified
TT-Fabric without host relay. The host coordination layer—MPI for the proof of
concept—carries barriers, validation, broadcast/all-reduce metadata, and failures, not
model tensors.

This split makes ownership explicit: the virtual objects are identical specifications,
but only one rank controls a physical device and its CQ. A pluggable
`DistributedContext` is proposed so `barrier`, `allreduce`, `bcast`, and possibly
point-to-point coordination do not hard-wire MPI into single-host builds. Production
launch is associated in the source with `tt-run`; that launcher and the coordination
backend establish ranks, while the data plane remains TT-Fabric.

### What must never break

Every rank must generate byte-for-byte-equivalent resource/workload order before local
filtering. Rank-dependent branches, races, and unordered iteration that changes
`MeshWorkload` construction make behavior undefined. Python lifetime is a particular
hazard: garbage-collection timing cannot drive allocator mutations, so the proposal
requires explicit deterministic release—preferably a context manager, or `free()` at
the same logical point on every rank. Likewise Python hash randomization must not decide
operation order; use ordered structures or a controlled `PYTHONHASHSEED`. Global
coordinates must map to exactly one local owner, and host synchronization must never be
mistaken for completion of TT-Fabric data movement.

### Where the report makes it concrete

The layered boundary is `global MeshDevice/MeshBuffer/MeshWorkload -> MeshCQ -> local
dispatch -> per-Device CQ`. This makes a useful debugging property possible: global
definition can often run under `mpirun -np 1` because the application-visible objects
are rank symmetric up to submission. The source contrasts this with a single-controller
model: centralization prevents user-code divergence but needs command
serialization/deserialization, executor services, and a controller capable of feeding
all hosts. The SPMD choice is therefore justified for regular TP/DP scaling, not claimed
as a universal distributed runtime.

### How the decision is tested

Hash a canonical serialization of mesh shape, allocation sequence, program placement,
runtime arguments, and frees on every rank before each submission; all hashes must
match. Repeat with randomized Python GC, different process hash seeds, and intentionally
unordered construction to prove the validation catches divergence. For the 16x8 case,
stamp outputs with global coordinates and verify each is produced once by the rank that
owns its 8x4 region. Finally delay and terminate one rank at a coordination barrier:
healthy ranks must receive one defined failure rather than dispatching a later global
workload. Separately measure coordination bytes and TT-Fabric payload bytes; substantial
model traffic in MPI would violate the architectural separation even if results are
correct.

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
