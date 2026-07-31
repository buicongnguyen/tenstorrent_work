<!-- rewrite-status: seed -->
# CCL Performance Tuning Tips for tt-metal

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md"><code>tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 124 |
| Section headings | 5 |
| Fenced code examples | 6 |
| Markdown images | 0 |

### Section outline

- 0. Proper Initialization
- 1. Use Trace Mode
- 2. Op-Specific Parameters
- 3. Pre-Allocated Buffers
- 4. Custom Packet Size

## Improvement plan

1. **Architecture pressure.** Classify collective cost into initialization/program
   construction, dispatch, packet startup, per-link bytes/congestion, synchronization, and
   buffer allocation before selecting trace, preallocation, packet size, or topology knobs.

2. **Flow to make explicit.** Draw one tensor shard through local read/packetization,
   selected CCL algorithm/fabric route, intermediate reduce/relay steps, destination buffer,
   collective completion, and dependent compute.

3. **Invariant to prove.** Prove all ranks invoke the same compatible collective order and
   shapes, buffers remain valid through completion/replay, and trace-captured
   addresses/configuration remain stable across warm iterations.

4. **TT-Metal evidence to connect.** Connect tuning to `mesh_device`, `FABRIC_1D`,
   `FABRIC_1D_RING`, `FABRIC_2D`, `FABRIC_2D_TORUS_X/Y/XY`, trace mode, preallocated
   buffers, op parameters, and packet size.

5. **Experiment and expected observation.** Sweep message and packet size in warm cached and
   trace modes for one topology; expected result: trace removes launch gaps, while
   packet/algorithm changes alter link utilization only in the matching latency or bandwidth
   regime.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report tunes collective communication by removing avoidable setup/dispatch
    overhead and matching packetization, buffers, topology, and operation-specific
    parameters to the message, so links and fabric routers remain supplied.
    Optimization begins only after collective correctness is established across ranks.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every rank must invoke compatible collectives in the same logical order with
    matching tensor counts/shapes, and source/output buffers must remain valid until
    completion. Trace replay or pre-allocation may optimize execution only while
    captured addresses and lifetimes stay valid.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A tensor shard is read from each participant → the CCL operation packetizes it →
    fabric/links forward packets along the collective topology → intermediate nodes
    reduce, gather, or relay → final shards land in destination buffers → completion
    makes the collective result visible to subsequent compute.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Trace APIs, CCL algorithms, packet-size knobs, buffer counts,
    link topology, queue behavior, and best parameter values depend on the collective,
    message size, chip generation, and TT-Metal revision.

    **Durable model.** Initialize once, reuse storage, separate launch overhead from
    wire time, choose an algorithm/topology from traffic volume, keep enough packets in
    flight, overlap only with explicit dependencies, and validate all ranks under the
    same schedule.

## Source and delta

- **Original source:** [`tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
