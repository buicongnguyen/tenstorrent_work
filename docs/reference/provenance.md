# Source trust and claim verification

Tenstorrent documentation spans technical reports, current source code,
architecture manuals, generated repository maps, and independent reverse
engineering. They are useful for different questions. This guide shows how to
turn those sources into a technical claim that is scoped, testable, and strong
enough to guide an implementation.

The learner editions on this site are grounded in the official TT-Metal
technical reports at commit
[`992f3ca634aac8733c70e48da395aab5361b4166`](https://github.com/tenstorrent/tt-metal/tree/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports).
The [report catalog](report-catalog.md) links every learner page to its exact
original report. A pinned report explains what that revision said; it does not
automatically prove that every detail remains true on current `main` or on a
different device generation.

## Evidence has two independent dimensions

People often rank a source with one word such as “official.” That is not enough.
Judge both **authority** and **version match**:

| Source class | What it can establish | What it cannot establish by itself |
|---|---|---|
| **Official · pinned** | Exact behavior, design intent, terminology, and examples for one known revision | Current behavior after later code or API changes |
| **Official · living** | Current public documentation and architecture manuals at the time you read them | What an older implementation did; a stable comparison unless you record a revision |
| **Current source and tests** | Implemented control flow, symbols, conditions, and expected behavior in a specific checkout | Hardware motivation or real performance without measurement |
| **DeepWiki map** | Fast discovery of subsystems, call paths, files, and related concepts | Final proof; generated explanations can lag or infer incorrectly |
| **Community · verify** | Hardware intuition, experiments, and hypotheses that official overview material may not expose | Guaranteed correctness, generation coverage, or support status |
| **Atlas synthesis** | A cross-source mental model and an explicit reasoning path | Official product behavior without the linked primary evidence |

A highly authoritative source with the wrong revision can be less useful than a
matching test in the actual checkout. Conversely, matching source code may show
*what* happens but not *why* the architecture chose it. Strong reasoning often
needs both.

## Classify the claim before looking for proof

Different claims require different evidence. Write the claim in a form that
could be false, then assign it to one of these classes:

| Claim type | Example | Minimum persuasive evidence |
|---|---|---|
| **API contract** | A runtime argument may change without creating a new cached program | Version-matched API/source path plus a focused test |
| **Correctness invariant** | A consumer cannot read a circular-buffer entry before the producer publishes it | Programming contract, matching implementation, and a boundary-case test |
| **Architecture mechanism** | Unpack transforms source data before matrix execution | Generation-matched official architecture/ISA material and the kernel-to-LLK path |
| **Performance mechanism** | Fast Dispatch removes a repeated host control-path cost | Code path plus a host/device timeline that isolates the removed interval |
| **Quantitative result** | A kernel reaches a stated bandwidth or FLOPS value | Exact device, clocks, formats, shapes, build, benchmark method, and raw measurement |
| **Design rationale** | Multicast is chosen to reduce repeated off-core reads | Source/report evidence, traffic model, rejected alternative, and measured trade-off |

This classification prevents a common mistake: using an architecture diagram to
prove a current API contract, or using one benchmark number to claim a universal
architectural limit.

## The verification chain

Use the shortest chain that can disprove the claim:

1. **State the claim precisely.** Include architecture, software revision,
   tensor shape/layout/format, and execution mode when they matter.
2. **Find the owning layer.** Use the
   [architecture dependency map](rewrite-roadmap.md) to identify which component
   owns the claimed invariant or resource.
3. **Locate primary evidence.** Follow the learner page’s pinned original link,
   then find the matching symbol, test, manual section, or report statement.
4. **Trace one concrete unit.** Follow one tensor, tile, command, event, packet,
   or instruction from producer to consumer. Name state transitions and owners.
5. **Separate durable from snapshot-specific facts.** Ownership and causal
   structure often survive generations; register layout, processor assignment,
   instruction encoding, and API names often do not.
6. **Predict an observation.** State what should change in a value, address,
   counter, or timeline if the claim is true—and what result would reject it.
7. **Reconnect to the original problem.** A local mechanism is useful only if it
   preserves correctness and changes the end-to-end workload metric.

The output is not “verified” or “unverified” in the abstract. It is a qualified
statement such as: “supported by the pinned report and reproduced on Wormhole
B0 at revision X for shape Y,” or “useful hypothesis from community analysis;
official generation-matched confirmation is still missing.”

## Worked example — evaluate a Fast Dispatch claim

Suppose the claim is: **Fast Dispatch makes this model faster.** It is too broad.
Fast Dispatch addresses repeated host-side command handling; it does not make a
matrix instruction execute faster or supply a starved reader kernel with data.

Refine the claim:

> For a warm workload containing many short launches, Fast Dispatch reduces
> host gaps between device command sequences without changing device-kernel
> duration or numerical output.

Then prove it:

1. Use the [Fast Dispatch lesson](../resources/deepwiki/fast-dispatch.md) to find
   the relevant control path, but treat DeepWiki as discovery rather than proof.
2. Confirm the path in the version-matched TT-Metal source and identify where
   slow and fast dispatch differ.
3. Capture host and device timelines for equivalent cold, warm, and steady-state
   executions. Do not compare a first compile with a cached run.
4. Predict that the host gap or submission interval shrinks while kernel regions
   remain approximately unchanged.
5. Compare outputs and the complete workload latency. If the host interval
   shrinks but end-to-end latency does not, dispatch was not on the critical path.

**Architectural conclusion:** Fast Dispatch is a control-plane optimization.
The durable idea is to move repeated scheduling work off the critical path. The
exact command structures and processors are revision- and architecture-specific.

## Worked example — decide whether program cache reuse is correct

The tempting claim is: **same operation means same cached program.** That can be
wrong because two calls with the same public operation name may require
different compiled structure, core grid, memory placement, data format, or
kernel specialization.

Use this reasoning:

1. Divide inputs into **structural identity** and **launch-specific values**.
   Structural choices affect generated resources or binaries; launch values can
   be patched safely only when the compiled structure remains valid.
2. Follow the [program-cache lesson](../resources/deepwiki/program-cache.md) to
   candidate key construction and runtime-argument override code.
3. Confirm every key field and override path in the actual revision. A generated
   repository map may omit a condition that changes identity.
4. Run calls that vary one property at a time: address, shape, layout, format,
   sharding, core grid, or compile-time option.
5. Predict cache-hit/miss behavior before running, then verify both cache evidence
   and output correctness.

**Invariant:** a cache hit is legal only if patchable launch state cannot violate
the assumptions embedded in the reused program. A high hit rate is not a success
if it aliases two structures that require different kernels or resources.

## Worked example — use Corsix for Wormhole low-level study

Corsix’s Wormhole articles can expose physical and microarchitectural questions
that are hard to see from a high-level API. Their best use is to generate a
traceable hypothesis, not to become an unofficial substitute for the ISA.

For a claim about the Unpack → Matrix/SFPU → Pack path:

1. Read the relevant [Corsix guided-course part](../resources/corsix-reading-workbook.md)
   and record the exact claim, experiment, and assumed Wormhole variant.
2. Check the [official ISA route](../resources/isa-reference.md), especially the
   generation-matched Tensix coprocessor and unpacker documentation.
3. Find the kernel and TT-LLK calls that configure or invoke the mechanism. Do
   not jump directly from a TT-NN operation name to an instruction conclusion.
4. Build the smallest kernel that changes only the suspected format, state, or
   instruction sequence.
5. Predict an output-bit pattern, counter change, or cycle difference. Include
   boundary values when data formats or special values are involved.

**Architecture rule:** keep community-derived intuition when official evidence
supports the mechanism; qualify it when only part of the claim is documented;
reject or isolate it when the device generation, stepping, or observed behavior
does not match.

## How to read numbers without learning the wrong lesson

A performance number is a property of an experiment, not merely a chip. Before
comparing a report value with a new measurement, reconstruct:

- device generation and count;
- clocks and power/thermal state;
- software commit and build mode;
- operation shape, batch, and sequence regime;
- tensor layout, memory layout, sharding, and data formats;
- warm-up, compilation, program-cache, and trace state;
- whether transfers and synchronization are included; and
- the numerator and denominator used for bandwidth, FLOPS, or latency.

If those conditions differ, preserve the old number as historical evidence and
compare the *mechanism* instead: traffic per output, achieved fraction of a
justified ceiling, occupancy, or the timeline region that dominates.

## A compact claim record

Use this template in notes, design reviews, or interviews:

| Field | What to record |
|---|---|
| Claim | One falsifiable sentence |
| Scope | Architecture, stepping, software revision, configuration, and workload |
| Owner | Layer/component whose contract decides the claim |
| Primary evidence | Pinned report, current source/test, or official manual section |
| Supporting evidence | DeepWiki map, Atlas explanation, community experiment |
| Concrete trace | One unit followed through named producers, state, and consumers |
| Prediction | Expected value, address, counter, or timeline change |
| Rejection condition | Observation that would make the claim false or narrower |
| Confidence | Confirmed for stated scope, partially supported, or hypothesis |

This is the important provenance skill for architecture work: not remembering
which page sounded authoritative, but preserving the chain from claim to scope,
primary evidence, causal mechanism, and observation.

## Source routes

- [Pinned official report catalog](report-catalog.md)
- [Architecture dependency map](rewrite-roadmap.md)
- [DeepWiki research method](../resources/deepwiki/research-method.md)
- [Official ISA route](../resources/isa-reference.md)
- [Corsix Wormhole guided course](../resources/corsix-reading-workbook.md)

This site is an unofficial educational companion and is not affiliated with or
endorsed by Tenstorrent. Tenstorrent, TT-Metalium, TT-NN, Tensix, Wormhole,
Blackhole, and other names may be trademarks of their respective owners.
