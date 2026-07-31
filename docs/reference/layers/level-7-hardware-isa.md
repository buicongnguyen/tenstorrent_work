# Level 7 — Reason from hardware constraints and ISA evidence

<p class="source-note">
<strong>Source class:</strong> Atlas architecture synthesis · architecture-qualified ·
<strong>Report set:</strong>
<a href="../report-catalog.md#level-7-hardware-isa">Level 7 catalog</a> ·
<strong>Use this page for:</strong> explaining a proven engine, format, or instruction-level limit
</p>

Level 7 is the last descent, not the default starting point. It connects TT-LLK
and kernel behavior to Tensix engine state, native shapes, data formats,
fidelity, special values, hazards, and generation-specific ISA semantics.

![Evidence-driven descent to hardware](../../assets/diagrams/layer7-hardware-descent.svg){ .atlas-diagram }

<small>[Open full-size diagram](../../assets/diagrams/layer7-hardware-descent.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/layer7-hardware-descent.mmd)</small>

## The architecture contract

Every Level 7 conclusion carries:

- architecture and revision (for example Wormhole B0 versus Blackhole);
- exact official ISA/LLK/source link and checked commit/date;
- visible state and instruction semantics separated from inferred physical
  microarchitecture;
- kernel/LLK call path that reaches the mechanism;
- accuracy, hazard, and synchronization invariants;
- measurement or simulator result that connects mechanism to the original
  symptom.

## Architecture reasoning loop

1. Arrive with a localized Level 4/5 symptom—engine busy/idle, format conversion,
   fidelity cost, special-value mismatch, or unexplained hazard.
2. Trace the supported API to TT-LLK and the architecture-specific instruction
   or configuration state.
3. Read official semantics; mark community/code-derived interpretations
   separately.
4. Build a minimal microbenchmark that isolates one mechanism.
5. Predict both result and relevant timing/counter behavior.
6. Compare architectures explicitly; never transfer encodings or hazards by
   analogy.
7. Return to the upper-level metric to show that the descent mattered.

## Worked problem — choose MatMul fidelity for a model layer

### Step 1: start from accuracy and format

Identify operand formats, accumulator/output format, value distribution, and
model-level error tolerance. Fidelity is not a standalone speed knob.

### Step 2: understand the hardware trade

Wormhole's matrix path uses narrow multiplier work across fidelity phases.
Additional phases consume more mantissa information but cost cycles and can
introduce intermediate rounding behavior. The exact mapping is
architecture-specific and must be checked against official material.

### Step 3: derive a performance hypothesis

If Matrix is the ceiling, fewer phases should reduce compute cycles. If Unpack,
Pack, DRAM, or NoC is already the ceiling, lower fidelity may barely change
end-to-end time. Predict the stage timeline before benchmarking.

### Step 4: test a matrix, not one value

Sweep representative shapes and value distributions, including zeros, large/
small magnitudes, NaN/Inf where semantics require them, and adversarial
cancellation. Record task/model accuracy as well as elementwise error.

### Step 5: publish a qualified choice

State architecture, formats, fidelity, kernel configuration, measured
performance, accuracy, and unsupported cases. The result is a policy for a
workload—not a universal claim that one fidelity is “best.”

## Tradeoffs an architect tracks

| Mechanism | Benefit | Cost or risk |
|---|---|---|
| Native Matrix shape | dense regular MAC datapath | blocking/edge composition in software |
| Narrow multipliers + phases | area/energy efficiency across formats | precision/throughput tradeoff |
| `SrcA`/`SrcB`/`Dst` local state | reuse near engines | explicit Unpack/Pack and finite capacity |
| SFPU/vector path | programmable fusion and nonlinear operations | separate ISA, hazards, and lane utilization |
| Config/replay/MOP state | amortized setup and high issue rate | hidden state becomes a correctness invariant |
| Simplified special values | cheaper/faster datapath | numerical behavior differs from full IEEE expectations |

## Questions and expert answers

### 1. When is an ISA-level optimization justified?

???+ note "Expert answer — reasoning"
    Only after upper-layer evidence localizes a meaningful engine or instruction
    limit, supported APIs cannot express the needed behavior efficiently, and
    the expected gain exceeds portability/maintenance cost. Build a minimal
    benchmark and a fallback. If the end-to-end bottleneck is dispatch or DRAM,
    hand-tuning an instruction sequence is the wrong layer.

### 2. Why can narrow multipliers plus fidelity phases be a good architecture choice?

???+ note "Expert answer — reasoning"
    Thousands of full-width multipliers consume large area and energy even when
    workloads use low precision. Narrow replicated units provide high low-
    precision throughput; multiple phases reconstruct more precision when
    needed. Software chooses the accuracy/performance point. The cost is
    variable latency, extra rounding behavior, and a more visible hardware
    contract.

### 3. Why must special values and data-format reconfiguration be tested together?

???+ note "Expert answer — reasoning"
    Reconfiguration changes how Unpack, Math/SFPU, `Dst`, and Pack interpret
    bits. NaN, infinity, denormal, saturation, and rounding behavior can differ
    at each boundary and across architectures. A value may survive one engine
    but change during conversion. Test the complete L1→Unpack→compute→Pack→L1
    path for each supported configuration.

### 4. How do you distinguish documented ISA behavior from microarchitectural inference?

???+ note "Expert answer — reasoning"
    ISA documentation specifies visible state transitions, encodings, hazards,
    and results. It rarely proves the physical circuit used internally. Timing
    patterns or instruction quirks may support a model—such as storage banking
    or port count—but label that model as inference and list alternatives. Use
    the visible contract for correctness; use inferred structure only to form
    experiments.

## Evidence checklist

- Architecture/revision and exact official source.
- Kernel API → TT-LLK → ISA/configuration call path.
- Minimal isolated benchmark with predicted outcome.
- Engine timeline/counters and end-to-end impact.
- Accuracy and special-value suite for selected formats/fidelity.
- Wormhole/Blackhole differences recorded separately.

## Continue

Use the [Matrix engine](../../rewrites/matrix_engine/matrix_engine.md), hardware
format, shared-exponent, special-value, and Blackhole bring-up reports. Then
follow the [official ISA route](../../resources/isa-reference.md) and the
[Corsix guided course](../../resources/corsix-reading-workbook.md), preserving
their different trust labels.
