<!-- rewrite-status: improved-draft -->
# CCL Performance Tuning Tips for tt-metal

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md"><code>tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to classify collective cost into initialization/program
construction, dispatch, packet startup, per-link bytes/congestion, synchronization, and
buffer allocation before selecting trace, preallocation, packet size, or topology knobs.

### How work and data move

The complete path is one tensor shard through local read/packetization, selected CCL
algorithm/fabric route, intermediate reduce/relay steps, destination buffer, collective
completion, and dependent compute.

### What must never break

The non-negotiable invariant is that all ranks invoke the same compatible collective
order and shapes, buffers remain valid through completion/replay, and trace-captured
addresses/configuration remain stable across warm iterations.

### Where the report makes it concrete

The report makes the decision concrete by connecting tuning to `mesh_device`,
`FABRIC_1D`, `FABRIC_1D_RING`, `FABRIC_2D`, `FABRIC_2D_TORUS_X/Y/XY`, trace mode,
preallocated buffers, op parameters, and packet size.

### How the decision is tested

The controlled procedure is to sweep message and packet size in warm cached and trace
modes for one topology. **Expected observation:** trace removes launch gaps, while
packet/algorithm changes alter link utilization only in the matching latency or
bandwidth regime.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md):

- **Fabric selection.** `mesh_device` topology plus `FABRIC_1D`, `FABRIC_1D_RING`,
  `FABRIC_2D`, and torus variants select available routes and links. The collective
  algorithm and packetization should match that topology instead of assuming a ring or
  full wraparound exists.

- **Steady-state measurement.** Preallocate buffers, hold operation parameters and
  packet size constant, warm program caches, then use trace mode only when replay
  invariants hold. Compare payload bandwidth and link balance, not launch time hidden
  inside a single aggregate number.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
