# Evidence ledger — what ttsim can teach and what requires hardware

<p class="source-note">
<strong>Primary resources:</strong>
<a href="https://github.com/tenstorrent/ttsim/blob/v1.9.7/README.md">official v1.9.7 capability and known-issues record</a>,
<a href="https://github.com/tenstorrent/ttsim/blob/v1.9.7/docs/libttsim_api.md">v1.9.7 library ABI</a>, and
<a href="https://docs.tenstorrent.com/tt-vscode-toolkit/lessons/ttsim-twenty-and-ten/">official executable exercise collection</a>
· <strong>Comparison discipline:</strong> conclusions below are scoped to the checked simulator/repository revisions
</p>

`ttsim` is useful when the question is architectural and observable in functional
state: which kernel ran, which address was used, whether a CB protocol completed,
whether a supported ISA path produced the expected bits, or whether a mesh mapping
composed correctly. It is the wrong instrument when the claim depends on physical
time, analog behavior, power, or an insufficiently modeled runtime path.

## Claim ledger

| Claim | Simulator evidence | Hardware evidence still required |
|---|---|---|
| host/runtime can construct a supported program | successful open, compile/load, dispatch, and readback | driver/firmware compatibility on the target system |
| kernel mapping and arguments are functionally coherent | known input, expected output, source trace | generation-specific edge cases not covered by the model |
| CB/NoC protocol has the intended explicit ordering | source invariants plus controlled reordering experiments | stress across real timing variation and firmware scheduling |
| SFPU/LLK/ISA operation is functionally modeled | bit/classification comparison for selected ranges | undocumented silicon behavior and generation errata |
| mesh sharding composes correctly | per-shard ownership plus gathered reference comparison | physical link routing, failures, and scale behavior |
| optimization reduces modeled traffic | tile/byte/injection accounting | achieved bandwidth, cycles, overlap, congestion, and power |
| Fast Dispatch is faster than Slow Dispatch | **not established by the course baseline** | real-device side-by-side benchmark with warmup and cache control |
| program cache reduces launch preparation | cache hit/miss control-flow study may be possible | real launch latency and invalidation costs |
| kernel meets a throughput target | **not established** | profiler counters and end-to-end measurement on target hardware |

The important habit is to attach an instrument to every verb. “Correct” needs a
reference and tolerance. “Faster” needs comparable work and a silicon clock or
wall-time protocol. “Less traffic” needs a counted source/receiver ledger. “Scales”
needs device counts, topology, and efficiency definition.

## Simulator-safe learning loop

Use this sequence for every new TT-Metal mechanism:

1. Freeze TT-Metal commit, submodules, simulator artifact/hash, descriptor, and
   environment.
2. Choose the smallest official example that exposes one ownership boundary.
3. Read host and kernel sources; state producer, consumer, address space,
   publication, and completion events.
4. Predict output and the first consequence of one controlled perturbation.
5. Run baseline and perturbation with a timeout; retain commands and complete
   category/message for errors.
6. Decide what the observation proves and explicitly list claims it cannot prove.
7. Convert the smallest case into a regression test before studying a larger op.

This is stronger than using the simulator as a tutorial launcher. It makes every
run a falsifiable architecture experiment.

## Error taxonomy

| Observation | First interpretation | Next action |
|---|---|---|
| build or kernel compile failure | source/API/ISA mismatch before simulation | confirm pin, submodules, generated headers, and full compiler diagnostic |
| simulator configuration error | `.so`, architecture, or descriptor contract | verify paths, filename, hashes, and single/dual topology |
| `UnimplementedFunctionality` | modeled-feature boundary | preserve full category/message; reduce and compare with official supported paths |
| contract termination | invalid API/state transition or unsupported fatal condition | isolate in its own process; record last completed boundary |
| hang/timeout | missing producer, publication, completion, or wrong address/coordinate | map every wait to the peer event that satisfies it; use scoped observation |
| wrong finite value | layout, format, address, arithmetic, or ordering | compare at the earliest producer/consumer boundary |
| `NaN`/`Inf` | possible valid input behavior, overflow, invalid operation, or stale data | classify inputs/intermediates and inspect status epoch separately |
| pass only with printing | observer perturbed a race | keep the original protocol suspect; use lower-impact evidence |

## What not to benchmark in ttsim

Do not use simulator wall time to rank kernels, report dispatch speedups, select a
multicast shape, or predict model tokens per second. The official project describes
performance counters and timers as divergent from hardware and recommends Slow
Dispatch for the supported baseline. Simulation speed also includes host-model
implementation cost, which is not a physical Tensix/NoC cycle model.

You can still prepare a sound hardware benchmark in simulation. Validate output,
freeze shapes and data types, enumerate bytes and operations, decide cache warmup,
name profiler counters, and define a failure threshold. Then move the unchanged
case to silicon and measure.

## Hardware handoff worksheet

For each promising optimization, complete this before using a card:

```text
Functional case and reference:
TT-Metal commit / firmware / driver:
Device and topology:
Warmup iterations:
Measured iterations:
Program-cache state:
Dispatch mode:
Input/output bytes and math operations:
Profiler zones/counters:
Correctness tolerance:
Simulator-proven invariants:
Hardware-only hypotheses:
Regression/failure threshold:
```

Fast Dispatch is a good example. First learn Slow Dispatch so kernel invariants
are isolated. On hardware, run warmed cached and uncached cases with identical
work, then separate host enqueue cost, device dispatch cost, and kernel execution.
Only that experiment can support a speedup claim. The simulator can help ensure
the kernel beneath the comparison is functionally unchanged.

## Questions and expert answers

### 1. Is a bit-correct simulator run proof that the kernel is race-free?

???+ note "Expert answer — reasoning"
    No. One modeled schedule can avoid an illegal early publication. Race freedom
    comes from the protocol: every consumer observation must be ordered after
    producer completion, and reuse after consumer completion. Perturbations and
    stress add evidence, but do not replace an ownership proof.

### 2. Why is traffic accounting useful when timing is not faithful?

???+ note "Expert answer — reasoning"
    Tile/byte/injection counts are consequences of the mapping and source loops,
    not simulator execution speed. They reveal whether an optimization removes
    redundant movement. Hardware is still required to learn how that reduction
    converts into cycles under contention, overlap, and finite bandwidth.

### 3. What is the best first hardware experiment after this course?

???+ note "Expert answer — reasoning"
    Re-run one already-correct lab unchanged, then compare Slow and Fast Dispatch
    with program-cache state controlled and profiler regions separating launch
    from kernel execution. This isolates the new hardware/runtime mechanism while
    keeping the dataflow proof and reference output fixed.

## Completion gate

Select one conclusion from each prior lab and place it in the claim ledger. For
each, name its source evidence, execution evidence, reasoning invariant, and one
hardware-only question. The course is complete when no performance claim relies
on simulator elapsed time.

**Back:** [Course index](index.md) ·
**Continue studying:** [optimization path](../../start/optimization-path.md)
