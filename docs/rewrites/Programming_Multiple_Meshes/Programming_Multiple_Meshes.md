<!-- rewrite-status: seed -->
# Programming Multiple Meshes

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md"><code>tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 693 |
| Section headings | 33 |
| Fenced code examples | 16 |
| Markdown images | 0 |

### Section outline

- Contents
- 1. Overview
  - 1.1 When to Use Multi-Mesh
  - 1.2 Multi-Mesh vs Big-Mesh
- 2. Physical Topologies
  - 2.1 Closetbox (16 Loudbox)
  - 2.2 WH Galaxy All-to-All System (5 Galaxies)
- 3. Mesh Graph Descriptors
  - 3.1 The Purpose of MGDs
  - 3.2 MGD Format Reference
  - 3.3 Example: Closetbox MGD
  - 3.4 Example: Exabox MGD
- 4. Rank Bindings and tt-run
  - 4.1 The Role of Rank Bindings
  - 4.2 Rank Binding Format
  - 4.3 Running with tt-run
- 5. Multi-Processing Support
  - 5.1 Virtualizing a Galaxy as Multiple Meshes
  - 5.2 TT_VISIBLE_DEVICES
  - 5.3 Generating Rank Bindings for Galaxy Systems
- 6. Fabric Configuration
  - 6.1 What is TT-Fabric?
  - 6.2 FabricConfig Options
  - 6.3 Setting Fabric Configuration
- … 9 additional headings in the original

## Improvement plan

1. **Architecture pressure.** Specify physical meshes, graph connectivity, host/rank
   ownership, process launch, fabric configuration, and failure/teardown domains so no
   process independently invents a conflicting global topology.

2. **Flow to make explicit.** Draw `.textproto` mesh graph loading through `tt-run`, rank
   binding, local mesh creation, fabric route setup, local SPMD work, cross-mesh
   communication, barrier/completion, and teardown.

3. **Invariant to prove.** Prove every physical device has one owner, all ranks interpret
   the identical mesh graph and collective/work order, and cross-mesh fabric is ready before
   dependent commands execute.

4. **TT-Metal evidence to connect.** Connect the plan to `.textproto`,
   `tt_metal/fabric/MGD_README.md`, `tt-run`, `mesh_id`, `TT_VISIBLE_DEVICES`, and
   `mesh_host_rank`.

5. **Experiment and expected observation.** Launch two ranks with a deliberately swapped
   binding and then the validated graph; expected result: validation rejects inconsistent
   ownership before execution, while the correct mapping produces identical graph hashes and
   expected cross-mesh traffic.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

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
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
