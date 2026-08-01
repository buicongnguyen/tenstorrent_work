<!-- rewrite-status: improved-draft -->
# Programming Multiple Meshes

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md"><code>tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to specify physical meshes, graph connectivity,
host/rank ownership, process launch, fabric configuration, and failure/teardown domains
so no process independently invents a conflicting global topology.

### How work and data move

The complete path is `.textproto` mesh graph loading through `tt-run`, rank binding,
local mesh creation, fabric route setup, local SPMD work, cross-mesh communication,
barrier/completion, and teardown.

### What must never break

The non-negotiable invariant is that every physical device has one owner, all ranks
interpret the identical mesh graph and collective/work order, and cross-mesh fabric is
ready before dependent commands execute.

### Where the report makes it concrete

The report makes the decision concrete by connecting the plan to `.textproto`,
`tt_metal/fabric/MGD_README.md`, `tt-run`, `mesh_id`, `TT_VISIBLE_DEVICES`, and
`mesh_host_rank`.

### How the decision is tested

The controlled procedure is to launch two ranks with a deliberately swapped binding and
then the validated graph. **Expected observation:** validation rejects inconsistent
ownership before execution, while the correct mapping produces identical graph hashes
and expected cross-mesh traffic.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md):

- **Deployment description.** The `.textproto` and `tt_metal/fabric/MGD_README.md`
  define mesh groups, hosts, and fabric connectivity consumed by `tt-run`. Validate that
  every physical device appears in the intended mesh exactly once.

- **Process identity.** `mesh_id`, `mesh_host_rank`, and `TT_VISIBLE_DEVICES` connect a
  launched process to its local portion of a logical mesh. A mismatch can produce a
  valid local open on the wrong global rank, so log these values before collective
  traffic begins.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report extends programming from one mesh to several meshes and hosts by
    describing physical topologies, mesh-graph descriptors, rank bindings, launch,
    multiprocessing, and fabric configuration. The central difficulty is consistent
    global identity across independent controllers.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every physical device must have one unambiguous owner/rank, every process must
    interpret the same mesh graph and bindings, and cross-mesh communication must be
    configured before dependent work is submitted. Conflicting ownership or collective
    order can hang the system.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A mesh-graph descriptor defines logical meshes and connectivity → `tt-run`/the
    launcher binds ranks and processes to local devices → each process opens its mesh →
    fabric links and routes are configured → local SPMD work executes → cross-mesh
    operations synchronize through the shared topology.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Descriptor schema, rank-launch syntax, process model,
    supported topologies, fabric modes, and resource limits are current-runtime details.

    **Durable model.** Keep topology and rank assignment declarative, enforce single
    ownership, separate launch/control-plane coordination from data-plane traffic,
    validate the graph on every process, and make distributed failure diagnostics rank
    aware.

## Source and delta

- **Original source:** [`tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
