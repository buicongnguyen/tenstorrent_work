# Tenstorrent investigation routes: question to evidence

Tenstorrent questions cross several abstraction layers, but the strongest
evidence usually lives near the component that owns the disputed behavior. A
TT-NN model guide can establish operator semantics; it cannot prove an Unpacker
state transition. An ISA page can explain an instruction; it cannot prove that
host dispatch limits an application.

This page teaches how to select and combine the resources in this section. For
the general rules behind authority, version matching, and falsifiable claims,
read [Source trust and claim verification](../reference/provenance.md).

![How the official and community sources relate](../assets/diagrams/source-map.svg){ .atlas-diagram }

<small>[Open full-size diagram](../assets/diagrams/source-map.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/source-map.mmd)</small>

## Follow ownership downward and evidence upward

The downward path turns intention into mechanism:

`model semantics` → `TT-NN operation` → `TT-Metal program` →
`device kernels` → `TT-LLK` → `ISA unit/instruction`

The upward proof path reconnects a mechanism to the original problem:

`instruction or event observation` → `kernel effect` →
`operation result/timeline` → `model correctness or latency`

Do not stop after the downward path. A low-level fact is not yet an application
explanation. Do not skip the downward path either: an application symptom does
not identify a hardware mechanism on its own.

| Starting question | First route | Escalate only when | Technical output |
|---|---|---|---|
| Which operator or module first becomes wrong? | Pinned reports and model/operator learner pages | The first wrong operation is localized | Per-boundary golden comparison and exact failing configuration |
| Why is the first call or every launch slow? | DeepWiki discovery plus current runtime source | Host/runtime evidence rules out compilation, cache, queue, and trace effects | Cold/warm/replay timeline with a causal control-path explanation |
| Why does a device kernel stall? | Kernel/dataflow reports and profiler evidence | Reader, compute, or writer stage is localized | Tile ownership trace, circular-buffer state table, and stage timeline |
| What does an engine or instruction actually do? | Official generation-matched ISA documentation | A kernel-to-TT-LLK call path reaches that mechanism | API-to-ISA proof chain and isolated output/cycle prediction |
| What can independent Wormhole experiments teach? | Corsix guided course | The claim is restated as a hypothesis | Community observation paired with official confirmation or a marked disagreement |
| Why does multi-device scaling flatten? | Mesh, TT-Fabric, and distributed reports | Per-rank/link evidence identifies the limiting path | Global-to-physical map, bytes per link, and collective critical path |

## Route 1 — model result to the first violated contract

Use this route when a model has wrong outputs, unacceptable numerical drift, or
a failure that appears only for certain shapes.

1. Begin with the
   [pinned official report catalog](../reference/report-catalog.md) and choose the
   model/operator chapter that matches the workload. Record the exact source
   revision linked at the top of its learner edition.
2. Preserve a framework golden output at module boundaries. The useful boundary
   is the earliest place where the Tenstorrent path and the reference diverge,
   not merely the final model output.
3. Use TT-NN graph/operation tracing to record shape, layout, format, memory
   configuration, and operation identity at that boundary.
4. If values become wrong before device execution, remain at the model/runtime
   layer. If an operation receives correct inputs and emits wrong outputs, audit
   its physical tensor contract and kernel work split.
5. Descend to TT-LLK or ISA only after one kernel stage, format transition, or
   engine behavior is implicated.

**Why this route works:** each boundary preserves a known-good prefix. Editing a
kernel before finding the first wrong operation expands the hypothesis space and
can change timing without repairing the original semantic error.

**Evidence that closes the route:** the first incorrect boundary becomes correct
under one controlled change, later boundaries also recover, and the original
model metric passes.

## Route 2 — latency symptom to the limiting control or data path

Use the [DeepWiki optimization research course](deepwiki-research-guide.md) as a
code-discovery map, then verify every mechanism in current source and
measurement. Select the branch from the observed timeline:

| Observation | First lesson | Architectural hypothesis | Evidence that would reject it |
|---|---|---|---|
| First call is slow; later calls are much faster | [Program-cache identity](deepwiki/program-cache.md) | compilation/program construction is amortized by compatible reuse | cache misses do not correlate with the slow interval |
| Host gaps separate short device launches | [Fast Dispatch](deepwiki/fast-dispatch.md) | repeated control-plane work is exposed | device work is continuous or host-gap reduction does not change latency |
| Independent transfers and compute remain serialized | [Queues and events](deepwiki/command-queues-events.md) | missing safe overlap leaves one engine idle | correct event overlap appears but critical-path duration is unchanged |
| Stable repeated sequence still has host replay cost | [Metal Trace](deepwiki/metal-trace.md) | capture can remove repeated submission work | shapes, addresses, or program choices are not replay-stable |
| Device is busy but throughput remains low | [Profiling investigation](deepwiki/profiling.md) | a memory, NoC, synchronization, load-balance, or compute resource limits execution | the predicted counter/timeline region does not respond to an isolated change |

The order matters. Fast Dispatch, cache, queues, trace, memory placement, and
kernel scheduling do not form a checklist of optimizations to enable. Each buys
time on a different path and introduces its own address, lifetime, capacity, or
ordering constraints.

**Evidence that closes the route:** the predicted timeline region changes, the
end-to-end latency or throughput improves, and output correctness remains within
the original acceptance criteria.

## Route 3 — kernel stall to tile ownership and backpressure

When device execution is the problem, stop reasoning from API call order. Trace
one output tile or block through the concurrent reader, compute, and writer
stages.

1. Assign each output tile exactly one owning core.
2. Derive the required input pages and reuse distance from that output.
3. Derive page addresses using layout, bank/shard mapping, base address, and
   boundary/tail rules.
4. Write circular-buffer transitions explicitly:
   `reserve → transfer → barrier → publish → wait → consume → release`.
5. Measure whether reader starvation, compute occupancy, writer backpressure,
   or an imbalanced core determines completion.

Use the pinned
[NoC tile-transfer report](../rewrites/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md)
for the basic transfer contract, then compare
[data reuse](../rewrites/prog_examples/matmul_multi_core_optimized/data_reuse.md)
and [multicast](../rewrites/prog_examples/matmul_multi_core_optimized/data_mcast.md).
Reuse reduces repeated off-core reads by retaining data; multicast reduces
repeated network injection by sharing data. Both consume more coordination or
local capacity than private rereads.

**Evidence that closes the route:** per-stage wait time changes in the predicted
direction, NoC/DRAM bytes agree with the data-reuse model, no circular-buffer
invariant is violated, and the complete operation improves.

## Route 4 — kernel API to TT-LLK and ISA

Use the [official ISA deep dive](isa-reference.md) only after the upper-level
investigation carries a precise question downward. Tenstorrent’s
[`tt-isa-documentation`](https://github.com/tenstorrent/tt-isa-documentation)
is the primary living source for generation-matched low-level behavior, while
[`tt-llk`](https://github.com/tenstorrent/tt-llk) connects kernel APIs to those
units.

For a Wormhole compute-path claim, follow:

1. device kernel call site;
2. matching TT-LLK wrapper and configuration;
3. [Tensix Coprocessor overview](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/README.md);
4. [Unpackers](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/Unpackers/README.md)
   and the relevant source-register/data-format state;
5. [Matrix Unit](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/MatrixUnit.md)
   or the selected SFPU instruction;
6. `Dst` state and
   [Packers](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/Packers/README.md);
7. isolated kernel measurement and upper-level consequence.

Wormhole B0 and Blackhole A0 must be separate proof chains. Similar component
names do not prove identical register layouts, instruction encodings,
capacities, or scheduling constraints.

**Evidence that closes the route:** the official generation-matched description,
kernel/TT-LLK call path, and isolated observation agree; changing the mechanism
also changes the localized kernel behavior predicted by the original symptom.

## Route 5 — use Corsix as hypothesis generation

The [Corsix Wormhole series](corsix-wormhole-series.md) is valuable because it
connects physical boards, PCIe windows, NoC experiments, Ethernet, Tensix tile
structure, SFPU, and matrix execution. It is independent analysis, so the
correct output of reading it is a better hypothesis—not automatic certainty.

Use the [Parts 1–7 guided course](corsix-reading-workbook.md) to keep three
columns for every important claim:

| Community observation or inference | Official comparison | Decision |
|---|---|---|
| Exact Corsix article, architecture assumption, and experiment | Generation-matched ISA page, pinned report, or current code | confirmed for scope, qualified, contradicted, or still open |

For example, a NoC latency trend can support a topology hypothesis without
proving every physical placement detail. A Matrix/SFPU experiment can reveal a
mechanism while leaving supported software dispatch relationships unresolved.
Preserve that distinction in the conclusion.

## Worked investigation — a warm matmul is still slow

Assume the first call is slow, warm calls reuse a cached program, host gaps are
small, and the device timeline shows the reader repeatedly waiting.

### Reasoning chain

1. Program-cache evidence rejects repeated compilation as the steady-state
   cause.
2. The absence of material host gaps weakens a Fast Dispatch or Metal Trace
   explanation for the remaining time.
3. Reader waits place the first limiting mechanism in the data-supply path, not
   the matrix engine.
4. Derive bytes read per output block and compare private rereads, retained
   reuse, and multicast. Include padding, sharding, and core distribution.
5. Predict the effect before changing code: fewer DRAM/NoC bytes and shorter
   reader waits; compute work per output should remain approximately constant.
6. Implement one change, then check traffic, stage timeline, operation latency,
   and numerical output.

### Architecture decision

Choose reuse when an operand fits the intended L1 lifetime and is consumed
multiple times locally. Choose multicast when several cores need the same data
and one injection can replace repeated transfers. Reject either when added L1
pressure or synchronization reduces feasible parallelism more than the traffic
saving buys.

The ISA route is unnecessary unless profiling later shows continuous data supply
and a matrix/SFPU mechanism becomes the localized limit. Stopping here is a sign
of disciplined abstraction, not incomplete research.

## Worked investigation — special values change through a kernel

Assume normal BF16 inputs match the reference, but infinities, NaNs, denormals,
or extreme magnitudes do not.

1. Freeze the exact input bit patterns and expected classification, not only a
   floating-point printout.
2. Use the pinned
   [special-values report](../rewrites/Handling_Special_Value/special_values.md)
   and [data-format report](../rewrites/data_formats/data_formats.md) to identify
   documented format and engine scope.
3. Locate the first stage whose output bits differ: input storage, Unpack/source
   state, Matrix/SFPU, `Dst`, Pack, or final storage.
4. Follow the generation-matched ISA and TT-LLK configuration only to that stage.
5. Test zeros, signs, normal controls, boundary exponents, repeated conversions,
   and the suspected special values.

**Architecture decision:** select a format/fidelity/conversion path only after
measuring both application accuracy and movement/compute cost. A path that
preserves one special case but silently changes ordinary precision is not a
correct fix; a high-fidelity path that violates the performance requirement may
need an algorithmic or boundary-handling alternative.

## Resolve disagreements without choosing a favorite source

When sources disagree, check in this order:

1. **Architecture and stepping:** Wormhole B0 and Blackhole A0 are different
   scopes.
2. **Revision:** a pinned report, current source, and DeepWiki page can describe
   different commits.
3. **Claim class:** a specification, implementation detail, observed result, and
   inferred rationale are not interchangeable.
4. **Configuration:** shape, format, layout, clocks, build, cache state, and
   execution mode can change the observation.
5. **Reproduction:** create the smallest test whose result separates the two
   explanations.

If the conflict remains, state both scoped claims and the missing experiment.
Uncertainty recorded precisely is more useful than false certainty.

## Enter the detailed courses

- [DeepWiki optimization research course](deepwiki-research-guide.md) — ten
  mechanism-focused lessons from code discovery through LLK/ISA escalation.
- [Performance optimization track](../start/optimization-path.md) — a
  symptom-driven route across runtime, memory, kernels, and measurement.
- [Corsix Wormhole guided course](corsix-reading-workbook.md) — Parts 1–7 with
  answered architecture reasoning and official comparison sources.
- [Official ISA deep dive](isa-reference.md) — direct Wormhole B0 and Blackhole
  A0 routes into Tensix units and representative instructions.
- [Source trust and claim verification](../reference/provenance.md) — how to
  qualify authority, revision, architecture scope, and confidence.
