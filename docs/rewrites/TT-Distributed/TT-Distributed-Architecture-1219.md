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
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

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

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Source and delta

- **Original source:** [`tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
