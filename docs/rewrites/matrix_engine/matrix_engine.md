<!-- rewrite-status: improved-draft -->
# Matrix engine: work shape, fidelity, and throughput

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/matrix_engine/matrix_engine.md"><code>tech_reports/matrix_engine/matrix_engine.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> improved draft
</p>

Peak throughput is only meaningful when three things line up: the engine's
native work shape, enough useful rows to fill that shape, and the selected math
fidelity. This chapter separates those effects.

![Matrix engine data path and fidelity passes](../../assets/diagrams/matrix-engine-throughput.svg){ .atlas-diagram }

<small>[Open full-size diagram](../../assets/diagrams/matrix-engine-throughput.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/matrix-engine-throughput.mmd)</small>

!!! warning "Architecture scope"
    The pinned report says its numbers apply to Wormhole and Blackhole, while
    much of its wording names the Wormhole engine. Treat the numeric table as a
    pinned-report claim and verify generation-specific details in current
    official documentation before using it for capacity planning.

## Native matrix-multiply work

The documented single-cycle operation is:

```text
(8 × 16) × (16 × 16) → (8 × 16)
```

That is `8 × 16 × 16 = 2,048` multiply-accumulates, or `4,096` floating-point
operations when a multiply and add count separately. At 1 GHz, the report's
LoFi peak is therefore 4 TFLOPS per matrix engine.

The engine still executes the native `8 × 16` left-hand shape when fewer rows
are useful. A `1 × 16` left input consequently uses only one eighth of the
produced rows, reducing effective throughput to one eighth of peak even though
the hardware issue rate is unchanged.

## Separate three utilization factors

```text
effective work rate
  = documented peak
  × useful native-lane fraction
  ÷ fidelity passes
```

This is a reasoning model, not a full performance equation: unpack, pack,
NoC, synchronization, and instruction overhead can reduce the observed rate
further.

## Operation table from the pinned report

| Operation | Native work per cycle | LoFi metric at 1 GHz | Fidelity effect |
|---|---|---:|---|
| Matrix multiply | `8×16 × 16×16 → 8×16` | 4 TFLOPS | LoFi/HiFi2/HiFi3/HiFi4 divide by 1/2/3/4 |
| Reduce max/average/sum | `16×16` | 0.512 TFLOPS | max: none; average/sum: fidelity applies |
| Elementwise add/sub/mul | `8×16` | 0.128 TFLOPS | add/sub: none; multiply: fidelity applies |

### Matrix-multiply fidelity table

| Fidelity | Passes | Reported peak |
|---|---:|---:|
| LoFi | 1 | 4 TFLOPS |
| HiFi2 | 2 | 2 TFLOPS |
| HiFi3 | 3 | 1.33 TFLOPS |
| HiFi4 | 4 | 1 TFLOPS |

The Wormhole multiplier consumes 5 bits from SrcA and 7 bits from SrcB per
pass, including hidden bits as detailed in the source. Higher fidelity revisits
different mantissa portions so more input precision contributes to the result.

## Configuration knobs are not interchangeable

```cpp
struct WormholeComputeKernelConfig {
    MathFidelity math_fidelity = MathFidelity::LoFi;
    bool math_approx_mode = true;
    bool fp32_dest_acc_en = false;
    bool packer_l1_acc = false;
};
```

| Knob | Boundary it changes | Main trade-off from the report |
|---|---|---|
| `math_fidelity` | Matrix/selected arithmetic passes | More input precision versus proportional peak-rate reduction |
| `math_approx_mode` | Selected SFPU operations | Higher performance with lower precision for supported operations such as exp, GELU, and sqrt |
| `fp32_dest_acc_en` | Destination accumulation format | FP32 accumulation, but half as many destination tiles fit |
| `packer_l1_acc` | Pack-to-L1 behavior | Accumulate in L1 at higher precision, then perform a final lower-precision pack |

For the report's `DstSync::Half` example, Float16_b destination accumulation
fits eight tiles while FP32 fits four. The capacity change can alter blocking
and synchronization even if the arithmetic loop is otherwise identical.

## Code connection

- Configure these choices through `WormholeComputeKernelConfig` at the host
  kernel-creation boundary.
- Follow the official living ISA descriptions for the
  [matrix unit](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/MatrixUnit.md),
  [destination registers](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/Dst.md),
  [unpackers](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/Unpackers/README.md),
  and [packers](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/Packers/README.md).

The ISA pages explain units and state below the TT-LLK boundary; the TT-Metal
report remains the comparison source for the performance claims above.

## Verify your understanding

### 1. Why does `1×16 × 16×16` achieve only one eighth of the `8×16` useful-row throughput?

???+ note "Expert answer — utilization reasoning"
    The matrix engine still issues its native `(8×16) × (16×16)` work shape.
    Supplying one useful left-hand row does not create a smaller one-row engine
    operation; seven of the eight produced row lanes carry no useful model work.
    Useful-lane utilization is therefore `1/8`, so the effective useful FLOP rate
    is at most one eighth of the same-fidelity peak before movement, pack, or
    synchronization overhead.

    Batching or blocking several independent rows into the native eight-row
    shape recovers utilization if the operation's semantics permit it.

### 2. Starting from 4 TFLOPS LoFi, compute the report's HiFi3 peak.

???+ note "Expert answer — throughput calculation"
    HiFi3 uses three fidelity passes for work that LoFi issues in one pass, so:

    ```text
    4 TFLOPS ÷ 3 = 1.333... TFLOPS ≈ 1.33 TFLOPS
    ```

    This is a documented arithmetic ceiling, not a measured application rate.
    Useful-row fraction and all reader, unpack, pack, NoC, instruction, and
    synchronization costs can reduce observed throughput further.

### 3. Which elementwise operations ignore math fidelity, and which one uses it?

???+ note "Expert answer — operation semantics"
    In the pinned report's elementwise table, **add and subtract ignore math
    fidelity**, while **multiply uses it**. Fidelity controls how many mantissa
    portions contribute to multiplication; it is not a universal speed/accuracy
    knob applied identically to every arithmetic instruction.

    The same distinction appears in reductions: reduce-max does not use
    fidelity, whereas reduce-sum and reduce-average include addition/multiply
    behavior for which fidelity matters.

### 4. If FP32 destination accumulation halves destination tile capacity, what program-level blocking or synchronization assumptions must be revisited?

???+ note "Expert answer — capacity reasoning"
    A block designed to keep eight Float16_b destination tiles live may fit only
    four FP32 tiles. Recompute output sub-block size, destination acquire/release
    count, `DstSync` mode, pack cadence, intermediate-CB capacity, and the point
    at which partial K accumulations are spilled or repacked.

    If code still reserves or computes the old block, it can overrun destination
    state or wait for capacity that cannot exist. Smaller blocks can also change
    operand reuse and add synchronization/pack traffic, so accuracy gains must be
    evaluated with a newly measured schedule—not only a flipped config flag.

## Source and delta

- **Original:** [Matrix Engine at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/matrix_engine/matrix_engine.md)
- **Added here:** native-shape utilization, a fidelity/operation matrix, knob
  boundaries, an end-to-end engine flow, and ISA cross-links.
- **Review conclusion:** the arithmetic table remains explicitly scoped to the
  pinned report. The durable work-shape/utilization/fidelity reasoning transfers,
  but Wormhole and Blackhole capacities, state, encodings, and timing require
  their separate official ISA trees; this page does not claim equivalence.
