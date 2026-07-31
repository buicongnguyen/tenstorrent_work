# Level 4 — Solve kernel and dataflow problems

<p class="source-note">
<strong>Source class:</strong> Atlas architecture synthesis ·
<strong>Report set:</strong>
<a href="../report-catalog.md#level-4-kernels-dataflow">Level 4 catalog</a> ·
<strong>Use this page for:</strong> designing reader–compute–writer pipelines that stay busy and correct
</p>

Level 4 converts the tensor contract into concurrent device programs. The
architecture problem is a bounded pipeline: readers produce tiles, compute
consumes/produces them, writers drain results, and circular buffers carry both
data and synchronization.

![Kernel pipeline reasoning flow](../../assets/diagrams/layer4-kernel-dataflow.svg){ .atlas-diagram }

<small>[Open full-size diagram](../../assets/diagrams/layer4-kernel-dataflow.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/layer4-kernel-dataflow.mmd)</small>

## The architecture contract

For each circular buffer or communication channel, state:

- producer, consumers, and ownership-transfer operation;
- page/tile format and order;
- capacity and double-buffer requirement;
- wait/reserve/push/pop sequence;
- NoC source/destination and completion requirement;
- termination count shared by every participant.

Most kernel hangs are violated protocols, not mysterious hardware behavior.

## Architecture reasoning loop

1. Partition output work into disjoint core ownership.
2. For one output block, list required input tiles and their reuse counts.
3. Decide which data is read, multicast, retained, or recomputed.
4. Draw reader, compute, and writer timelines with every circular-buffer state
   transition.
5. Size buffers to cover latency and burstiness without starving L1.
6. Prove loop counts and edge handling before optimizing overlap.
7. Profile per-stage active/wait time and change the limiting stage only.

## Worked problem — multicore MatMul stalls intermittently

### Step 1: establish the protocol

For each K block, the reader must make A/B tiles available, compute must wait
for both, and output space must be reserved before accumulation is committed.
The writer can reclaim output slots only after writes complete as required.

### Step 2: localize the wait

- Compute waiting on input: reader/NoC/layout or input CB capacity.
- Reader waiting on space: compute consumption or buffer too small.
- Compute waiting on output space: writer/NoC or output CB capacity.
- All cores waiting at different iterations: loop-count or multicast receiver
  mismatch.

### Step 3: check reuse before adding bandwidth

If the same A block feeds several output columns, multicast or retain it rather
than reread it. But multicast helps only when receivers are synchronized enough
and the sender does not become a serialization point.

### Step 4: tune the bounded pipeline

Increase capacity only when the measured producer/consumer skew exceeds the
current slack and L1 permits it. More buffering cannot fix a wrong count or a
permanently slower writer; it only delays the eventual stall.

## Tradeoffs an architect tracks

| Choice | Gain | Cost |
|---|---|---|
| More cores | more parallel work | smaller shards, edge imbalance, more coordination |
| Larger circular buffers | hide latency and absorb bursts | L1 capacity and longer lifetime |
| Multicast | one NoC transfer serves many consumers | receiver protocol and sender/fabric contention |
| Data reuse | fewer DRAM/NoC bytes | resident state and more complex loop nesting |
| Kernel fusion | removes intermediate traffic and barriers | code size, register/L1 pressure, reduced modularity |
| Compile-time arguments | specialization and simpler device code | more program variants/cache identity |

## Questions and expert answers

### 1. How do you reason about a kernel hang without adding random delays?

???+ note "Expert answer — reasoning"
    1. Record each actor's last completed iteration and blocking primitive.
    2. For the blocked buffer/channel, identify who must perform the matching
       transition.
    3. Compare producer/consumer loop counts, including edge cores and multicast
       participants.
    4. Verify that NoC completion and buffer reclamation ordering match the API
       contract.
    5. A delay may hide a race but cannot prove ownership; repair the protocol
       and test many schedules.

### 2. How should circular-buffer capacity be chosen?

???+ note "Expert answer — reasoning"
    Capacity must hold the maximum in-flight difference between producer and
    consumer plus the transfer/compute granularity. Start with double buffering
    when stages can overlap, then use timelines to estimate burst and latency
    slack. Increase only if wait time falls enough to justify L1 cost. Capacity
    is a performance parameter after correctness counts are proven.

### 3. When is multicast better than repeated unicast or DRAM reads?

???+ note "Expert answer — reasoning"
    Multicast wins when many cores need identical data at roughly the same
    phase and the network can distribute it cheaper than repeated sources.
    Include sender injection, receiver synchronization, route contention, and
    the cost of holding the shared tile. If consumers are sparse or badly
    skewed, independent reads may produce better overlap despite more bytes.

### 4. Why can fusing reader, compute, and writer logic reduce performance?

???+ note "Expert answer — reasoning"
    Fusion removes queues and intermediate traffic but can serialize formerly
    independent stages, enlarge code/instruction state, raise register/L1
    pressure, and reduce the ability to overlap NoC with compute. Compare the
    pipeline critical path before and after. Fuse a boundary only when the
    removed movement/synchronization exceeds lost concurrency.

## Evidence checklist

- Per-core work assignment including edge cores.
- Circular-buffer producer/consumer protocol and loop counts.
- Reader/compute/writer timeline with waits and NoC completion.
- Bytes loaded versus bytes reused or multicast.
- L1 footprint for all buffers and resident state.

## Continue

Use the improved [NoC transfer](../../rewrites/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md)
and [kernel code-indexing](../../rewrites/code-indexing/kernel-code-indexing.md)
guides, then MatMul reuse/multicast and SFPU examples. Continue to
[Level 5 — performance reasoning](level-5-performance-debugging.md) when the
pipeline is correct but its limiting stage is uncertain.
