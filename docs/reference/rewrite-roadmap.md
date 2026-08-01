# Tenstorrent architecture dependency map

This page is a diagnostic map for TT-NN and TT-Metalium. It answers a practical
question: **when an operation is wrong or slow, which layer owns the first
decision worth investigating?** It is not a project schedule or documentation
status page.

The map synthesizes the
[pinned TT-Metal technical-report snapshot](https://github.com/tenstorrent/tt-metal/tree/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports).
Use the [report catalog](report-catalog.md) to compare each learner edition with
its exact original source. Architecture-sensitive details must also be checked
against the current official code before implementation.

## The dependency rule

A higher layer states an intention; the next lower layer must preserve it while
choosing a physical realization. For example, a model asks for a mathematically
correct matmul, the runtime chooses a reusable program, the tensor layer assigns
formats and placement, and kernels turn that placement into tile movement and
compute. Hardware executes only the resulting stream; it cannot repair a wrong
shape, stale runtime argument, or mismatched circular-buffer contract.

| Level | Contract owned at this boundary | Why the boundary exists | First evidence to collect |
|---:|---|---|---|
| 0 · Stack | Assign one symptom to the layer that owns its first violated invariant | Prevents an API symptom from being mistaken for a hardware cause | One operator traced through objects, owners, and handoffs |
| 1 · Model/operator | Preserve mathematical semantics, shapes, and acceptable error | Lets a workload be decomposed without losing its reference behavior | Golden outputs and per-module shape/error checks |
| 2 · Runtime | Bind programs, arguments, queues, events, traces, and reusable state correctly | Separates stable executable structure from launch-specific state | Cold/warm/replay timelines plus queue dependencies |
| 3 · Tensor/memory | Map logical values to formats, tiles, pages, banks, cores, and addresses | Makes placement explicit enough for parallel movement | Byte counts and two boundary address derivations |
| 4 · Kernel/dataflow | Give each output one owner and transfer tile ownership in a safe order | Allows movement and compute engines to overlap without data races | Per-core work split, circular-buffer states, and NoC barriers |
| 5 · Measurement | Identify the resource or control path on the critical path | Stops plausible optimization stories from replacing evidence | A timeline/counter prediction followed by a one-variable test |
| 6 · Distributed | Preserve global tensor and session semantics across chips and hosts | Extends ownership and ordering beyond one device | Logical-to-physical map, bytes per link, and per-rank events |
| 7 · TT-LLK/ISA | Explain a localized engine, format, or instruction limit | Provides mechanism-level proof after the upper layers are ruled out | API-to-kernel-to-LLK call path and isolated microbenchmark |

The levels are dependencies, not a claim that every investigation must visit all
eight. Stop descending when the evidence explains both the symptom and the
end-to-end result.

## Trace A — bring up a model without hiding the first error

The architectural pressure is uncertainty: a whole model can fail because one
operator is unsupported, one reshape changes meaning, one data-format boundary
loses accuracy, or one kernel writes the wrong region. End-to-end comparison
alone tells you that *something* is wrong, but not which contract failed.

1. **Freeze Level 1 semantics.** Record production shapes, padding rules, and a
   framework golden output. Compare at module boundaries, not only at the final
   logits. The [model bring-up chapter](../rewrites/ttnn/TTNN-model-bringup.md)
   explains why progressive isolation is cheaper than debugging a complete
   graph.
2. **Use Level 2 observability before modifying kernels.** Operation and graph
   traces should show which call, shape, and configuration produced the first
   divergence. [Comparison mode](../rewrites/ttnn/comparison-mode.md) is useful
   here because it turns a distant output failure into a nearer operator
   boundary.
3. **Audit Level 3 representation.** Logical shape, tiled/row-major layout, data
   format, memory layout, and storage location are independent coordinates. A
   value can be mathematically correct yet physically misaddressed. Derive the
   tile/page count and the first and last valid address using the
   [tensor layout](../rewrites/tensor_layouts/tensor_layouts.md) and
   [TensorAccessor](../rewrites/tensor_accessor/tensor_accessor.md) chapters.
4. **Descend to Level 4 only after localization.** Trace one failing tile through
   reader, circular buffer, compute, and writer. The correctness invariant is:
   the producer reserves and publishes exactly the data the consumer waits for,
   and the consumer releases it only after the last use.

**Why this order is efficient.** Each step reduces the hypothesis space while
preserving a known-good boundary. Editing a low-level kernel first can change
timing and conceal an upper-layer shape or placement error; progressive checks
make the earliest divergence the primary fact.

## Trace B — diagnose latency before choosing an optimization

Fast Dispatch, program cache, non-blocking queues, traces, memory placement, and
kernel tuning solve different kinds of waiting. They are complementary only
when their costs occur on the same critical path.

### Separate control-plane time from device execution

Measure at least cold, warm, and steady-state runs:

- A large **cold-to-warm** difference suggests compilation, binary loading, or
  program-cache identity. Read
  [program-cache identity](../resources/deepwiki/program-cache.md) and verify
  which attributes belong to reusable structure versus runtime-patchable data.
- Repeated **host gaps before device work** point toward command generation,
  submission, or synchronization. Read
  [Fast Dispatch](../resources/deepwiki/fast-dispatch.md) and
  [queues and events](../resources/deepwiki/command-queues-events.md). The key
  invariant is that asynchronous execution may move a wait, but cannot remove a
  real producer-consumer dependency.
- A stable command sequence with avoidable host replay cost is a candidate for
  [Metal Trace](../resources/deepwiki/metal-trace.md). Replay is valuable only
  when launch structure and buffer lifetime remain valid.
- Continuous device work with poor throughput is no longer primarily a dispatch
  problem. Use the [Metal profiler](../rewrites/MetalProfiler/metal-profiler.md)
  and [performance counters](../rewrites/PerfCounters/perf-counters.md) to decide
  whether DRAM, NoC, circular-buffer stalls, or compute limits the schedule.

### Match the mechanism to the proved bottleneck

| Observation | Architectural interpretation | Useful response | Misleading response |
|---|---|---|---|
| Host is busy between short launches | Control-plane overhead is exposed | Reuse cached programs, reduce synchronization, batch or capture stable work | Rewrite matrix microcode before measuring device occupancy |
| Device timeline has reader starvation | Consumption outruns data arrival | Improve placement, access pattern, transfer size, reuse, or overlap | Add another command queue without changing data supply |
| Writer blocks while compute has work | Output path or buffer capacity applies backpressure | Inspect write bandwidth, circular-buffer depth, and ownership schedule | Fuse more compute and increase live data blindly |
| Matrix engine is continuously active near a justified ceiling | Compute is the limiting resource | Change algorithm, precision, tile schedule, or available parallelism | Optimize dispatch that is already hidden |

**Principal lesson.** An optimization is an architectural trade: it buys less
time on one path using memory capacity, code complexity, restricted dynamism, or
additional synchronization elsewhere. Accept it only when the before/after
timeline changes in the predicted region and numerical results remain valid.

## Trace C — design a kernel by ownership, not by API sequence

A TT-Metal program is easier to reason about when every output tile has one
owner and every transfer has an explicit ownership transition.

1. **Partition outputs.** For each core, write the exact output tile interval or
   shard it owns. Uneven work must have an explicit tail policy.
2. **Derive inputs from outputs.** Determine which input pages each output block
   requires. This exposes reuse: private rereads are simple but expensive;
   multicast or sharding reduces traffic but adds placement and coordination
   constraints.
3. **Budget local storage.** Circular-buffer capacity must cover the chosen
   overlap and reuse distance, not merely one convenient tile. Larger buffers
   can reduce stalls but consume L1 and may lower feasible parallelism.
4. **State transitions explicitly.** A reader reserves space, performs NoC
   transfers, waits for completion, then publishes. Compute waits, consumes,
   produces, and publishes. A writer waits for results, transfers them, waits
   for required completion, and releases the consumed entries.
5. **Prove the boundary cases.** Test the first tile, a bank/core transition,
   the last full block, and a partial tail. These cases disprove most address and
   work-split assumptions faster than a large throughput run.

The [NoC transfer](../rewrites/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md),
[data reuse](../rewrites/prog_examples/matmul_multi_core_optimized/data_reuse.md),
and [multicast](../rewrites/prog_examples/matmul_multi_core_optimized/data_mcast.md)
chapters show the three decisions separately. Combining them is justified when
the measured saving in off-core traffic exceeds the coordination and L1 cost.

## Trace D — extend one-device reasoning across a mesh

Multi-device software introduces new names for familiar architectural duties:
ownership, addressing, routing, flow control, completion, and lifetime. The
mistake is to treat a logical mesh shape as proof of an efficient physical
schedule.

Start with a global tensor and derive:

1. which device or rank owns every shard;
2. which collective or point-to-point dependency makes the next computation
   legal;
3. how many bytes cross each physical link and in which direction;
4. which sender, receiver, or buffer may apply backpressure;
5. which event proves that a buffer can be reused; and
6. whether one slow rank extends the collective critical path.

The [mesh programming](../rewrites/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md)
chapter owns logical placement, while the
[TT-Fabric architecture](../rewrites/TT-Fabric/TT-Fabric-Architecture.md) and
[distributed runtime](../rewrites/TT-Distributed/TT-Distributed-Architecture-1219.md)
chapters explain transport and session responsibilities. Keeping these
contracts separate lets the logical decomposition survive changes in topology
or transport implementation.

## When an ISA-level descent is justified

Do not descend merely because ISA detail is interesting. Descend when upper-level
evidence has localized the limitation to an engine, data format, register/state
transition, or instruction sequence and a source-level change cannot explain it.

Use this proof chain:

`TT-NN operation → TT-Metal program → device kernel → TT-LLK call → official ISA behavior → isolated measurement → end-to-end consequence`

At every arrow, name the concrete symbol and the state passed across the
boundary. If the chain breaks, the ISA claim is not yet an explanation of the
application symptom. Begin with the [matrix-engine report](../rewrites/matrix_engine/matrix_engine.md),
then use the [official ISA route](../resources/isa-reference.md). The
[Corsix Wormhole course](../resources/corsix-reading-workbook.md) is valuable
for intuition, but its community claims must be checked against official,
generation-matched documentation.

## A reusable architecture decision record

For any correctness or performance investigation, write these seven lines
before changing code:

1. **Symptom:** the smallest reproducible wrong value or lost time interval.
2. **First violated invariant:** the earliest contract that evidence disproves.
3. **Owner:** the layer and component allowed to repair that contract.
4. **Mechanism:** the proposed change and the resource or ordering it changes.
5. **Price:** extra memory, precision loss, restricted shapes, complexity, or
   synchronization introduced by the change.
6. **Prediction:** the exact counter, timeline region, address, or value that
   should change.
7. **End-to-end proof:** the original correctness and workload metric after the
   local observation improves.

This discipline is the durable lesson across Tenstorrent generations. API
names, processor details, and instruction encodings can change; locating the
owner of an invariant and proving a causal change remains valid.

## Continue at the owning layer

- [Level 0 — orientation and stack](layers/level-0-orientation.md)
- [Level 1 — models and operators](layers/level-1-models-operators.md)
- [Level 2 — TT-NN runtime](layers/level-2-runtime-observability.md)
- [Level 3 — tensor and memory](layers/level-3-tensor-memory.md)
- [Level 4 — kernels and dataflow](layers/level-4-kernels-dataflow.md)
- [Level 5 — performance and debugging](layers/level-5-performance-debugging.md)
- [Level 6 — multi-device systems](layers/level-6-distributed-systems.md)
- [Level 7 — hardware, TT-LLK, and ISA](layers/level-7-hardware-isa.md)

For document provenance and update rules, use
[Provenance and updates](provenance.md). Contributor workflow belongs in the
[rewrite playbook](../contributing/rewrite-playbook.md), outside this learning
guide.
