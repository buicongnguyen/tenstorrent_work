<!-- rewrite-status: seed -->
# Programming Mesh of Devices with TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md"><code>tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 1086 |
| Section headings | 41 |
| Fenced code examples | 36 |
| Markdown images | 2 |

### Section outline

- Contents
- 1. Overview
- 2. MeshDevice
  - 2.1 System Topology
    - 2.1.1 SystemMesh Visualization
  - 2.2 MeshDevice Management
    - 2.2.1 MeshDevice Initialization/Close
    - 2.2.1 MeshDevice Visualization
  - 2.3 Controlling Device Visibility
    - Usage Examples
    - Running Concurrent Processes On A Single Host
  - 2.4 Distributed Process Launch with tt-run
    - 2.4.1 Overview and Design Philosophy
    - 2.4.2 Configuration and Usage
    - 2.4.3 Usage Patterns
- 3. Distributing Tensor to MeshDevice
  - 3.1 Distribution Strategies
  - 3.2 Programming Example: Sharding
- 4. Single-Program Multiple Device
  - 4.1 Execution Model
  - 4.2 Single Device to Multiple Device Execution
    - 4.2.1 Single Device Execution
    - 4.2.2 Mesh Device Execution
- 5. MeshDevice and Collective Communication Library (CCL)
- … 17 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Source and delta

- **Original source:** [`tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
