# Level 6 — Solve multi-device and distributed problems

<p class="source-note">
<strong>Source class:</strong> Atlas architecture synthesis ·
<strong>Report set:</strong>
<a href="../report-catalog.md#level-6-distributed-systems">Level 6 catalog</a> ·
<strong>Use this page for:</strong> extending ownership, routing, and synchronization beyond one device
</p>

Level 6 adds failure domains, topology, links, hosts, and collective algorithms.
The central architecture problem is not simply moving bytes: it is maintaining
global meaning while every participant progresses with only local state.

![Distributed ownership and data flow](../../assets/diagrams/layer6-distributed-ownership.svg){ .atlas-diagram }

<small>[Open full-size diagram](../../assets/diagrams/layer6-distributed-ownership.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/layer6-distributed-ownership.mmd)</small>

## The architecture contract

For every distributed tensor or message, state:

- global shape and partition/replication rule;
- device, mesh, rank, host, and link ownership;
- route and collective algorithm;
- producer/consumer event and buffer lifetime;
- ordering, completion, retry/error, and teardown semantics;
- topology and software assumptions used by the performance claim.

A local device completion does not automatically imply global completion.

## Architecture reasoning loop

1. Define the global operation and correctness result.
2. Map logical partitions/ranks to the physical topology.
3. Calculate bytes per link and the critical communication path.
4. Choose routing/collective structure from topology, message size, and
   concurrency—not from algorithm name alone.
5. Place buffers and assign single-writer ownership for descriptors/events.
6. Schedule communication and compute with explicit dependency edges.
7. Measure per-device timelines and per-link utilization; look for stragglers,
   serialization, and congestion.

## Worked problem — adding devices slows an all-reduce workload

### Step 1: compute the scaling budget

Ideal compute per device shrinks with device count, but collective bytes and
latency do not shrink at the same rate. Estimate compute saved versus added
communication, synchronization, and launch overhead.

### Step 2: inspect topology mapping

Logical neighbors may map to non-neighbor links or cross a host boundary. A
ring that is balanced logically can overload one physical Ethernet path. Map
every step to actual links and count concurrent flows.

### Step 3: separate bandwidth and latency regimes

Small messages are dominated by startup, queueing, and synchronization; large
messages by link bandwidth and congestion. Chunk size/pipelining that helps one
regime can hurt the other.

### Step 4: expose overlap safely

Partition the tensor into chunks, start communication when a chunk is ready,
and let independent compute proceed. Each chunk needs a producer event, link
ownership, destination visibility, and a reclamation point. “Async” is not an
absence of ordering; it is explicit partial ordering.

### Step 5: diagnose the slowest rank

Global time follows the critical participant. Compare per-rank compute, send,
receive, and wait timelines. Fix imbalance, route congestion, or host service
time before adding more concurrency.

## Tradeoffs an architect tracks

| Choice | Gain | Cost |
|---|---|---|
| Replication | local reads and resilience | memory and update traffic |
| Sharding | aggregate capacity and compute | communication and ownership complexity |
| Ring collective | bandwidth-efficient regular flow | latency grows with steps and topology mismatch |
| Tree/hierarchical collective | fewer latency steps and host/rack locality | uneven link use and more complex scheduling |
| More chunks | overlap and pipeline utilization | per-message overhead and metadata pressure |
| Multiple meshes/hosts | scale and isolation | discovery, failure, ordering, and teardown domains |

## Questions and expert answers

### 1. Why can adding devices reduce throughput or increase latency?

???+ note "Expert answer — reasoning"
    Compute per device decreases, but partitioning, collective, synchronization,
    and host-control costs increase. Smaller local tiles may also reduce engine
    utilization. The break-even point occurs when saved compute exceeds added
    critical-path communication and overhead. Build that equation from measured
    bytes, link rates, message startup, and per-rank work rather than assuming
    linear scaling.

### 2. How should an architect choose a collective algorithm?

???+ note "Expert answer — reasoning"
    Match the algorithm to physical topology, message size, operation, and
    concurrency. Estimate steps, bytes per link, bottleneck-link load, temporary
    storage, and overlap opportunity. A ring may maximize bandwidth for large
    balanced messages; a tree or hierarchy may reduce latency or respect host/
    rack structure. Validate with per-link and per-rank measurements.

### 3. What does buffer ownership mean across asynchronous devices?

???+ note "Expert answer — reasoning"
    At any time, one producer owns mutation; consumers gain visibility only
    after a completion/event edge. Storage cannot be reused until every required
    consumer or transport operation completes. Host return, local queue
    completion, remote arrival, and collective completion are distinct states.
    Write them as a state machine before introducing overlap.

### 4. Why is topology part of the programming model even behind a mesh abstraction?

???+ note "Expert answer — reasoning"
    A mesh abstraction provides stable coordinates and APIs, but latency,
    bandwidth, route contention, host boundaries, and link failures are
    physical. Correctness can remain topology-independent while performance
    cannot. Good software separates semantic partitioning from a topology-aware
    placement/routing policy and records the mapping used by each measurement.

## Evidence checklist

- Global tensor/rank partition map and physical topology map.
- Bytes and messages per link for one collective/iteration.
- Per-rank timelines with compute, send, receive, and wait.
- Event/buffer ownership state machine including teardown.
- Scaling curve with a compute-versus-communication model.

## Continue

Use mesh programming, CCL tuning, Ethernet, TT-Fabric, distributed runtime,
multi-host, and socket reports as successive scopes. The
[Corsix Ethernet lesson](../../resources/corsix-parts/part4-ethernet.md) is a
useful substrate example, but maintained distributed reports define the
software architecture. Descend to [Level 7](level-7-hardware-isa.md) only when
link or engine behavior cannot be explained at the runtime/kernel boundary.
