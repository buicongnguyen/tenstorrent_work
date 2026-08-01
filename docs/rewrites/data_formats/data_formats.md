<!-- rewrite-status: improved-draft -->
# Data formats: shared exponents and rounding

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/data_formats.md"><code>tech_reports/data_formats/data_formats.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> improved draft
</p>

The key difference between an ordinary floating-point value and a block-float
group is **where the exponent lives**. A normal value carries its own exponent;
block-float values share one exponent across a group of 16 numbers. That saves
bits, but it couples the precision of every value in the group to the largest
exponent selected for that group.

![Block-float conversion pipeline](../../assets/diagrams/data-format-conversion.svg){ .atlas-diagram }

<small>[Open full-size diagram](../../assets/diagrams/data-format-conversion.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/data-format-conversion.mmd)</small>

## The conversion in one pass

1. Inspect the 16-value block and select the shared exponent.
2. Shift or normalize each mantissa relative to that exponent.
3. Keep the mantissa bits supported by the destination format.
4. Round the discarded portion to nearest, with ties going to an even retained
   mantissa.
5. If rounding overflows the retained mantissa, clamp it to all ones. The
   pinned report explicitly says not to recompute the block exponent and
   renormalize all 16 values.

That final rule matters: conversion is local and deterministic after the shared
exponent is chosen, but a value at the upper edge may saturate its mantissa.

## Round to nearest, ties to even

Suppose a high-precision mantissa is divided into retained and discarded bits:

```text
retained bits | discarded bits
        ...b0 | r sssss...
```

- If the discarded value is below half, keep the retained value.
- If it is above half, increment the retained value.
- If it is exactly half, choose the result whose retained least-significant bit
  is even.

For the report's bfloat8 example, the stored mantissa has seven bits including
an explicitly stored hidden bit. Six fraction bits are therefore retained from
the original float32 mantissa before the hidden bit is added.

Ties-to-even avoids a persistent upward bias when many halfway values are
converted. It does **not** remove quantization error; it makes the direction of
that error less systematically biased.

## What changes across block-float widths

| Choice | What remains the same | What changes |
|---|---|---|
| Block-float-8 | Shared exponent, normalization, ties-to-even rule | More mantissa information retained |
| Block-float-4 | Same pipeline | Fewer retained bits, larger quantization steps |
| Block-float-2 | Same pipeline | Least mantissa detail and greatest sensitivity to the shared exponent |

The pinned report does not define every bit layout in prose, so use its figures
and the current implementation before encoding exact packing assumptions.

## Invariants and failure modes

- All 16 values in a block must be interpreted with the same shared exponent.
- Normalization must happen before mantissa rounding when an individual value's
  exponent differs from the shared exponent.
- A rounding carry cannot silently change the shared exponent under the rule
  documented here; the mantissa clamps instead.
- Repeated format conversion can accumulate error even when each conversion is
  correctly rounded.
- Values with much smaller magnitude than the block maximum lose more useful
  mantissa information after alignment to the shared exponent.

## Code connection

The original page describes host-side conversion rather than naming one stable
API symbol. For the hardware boundary, compare the official living ISA pages
for the [unpackers](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/Unpackers/README.md)
and [packers](https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/TensixCoprocessor/Packers/README.md).

Use this division of responsibility when reading code:

```text
stored page → unpack / interpret format → compute representation
             → pack / convert format → stored output page
```

The ISA repository is an **official living source**; this learner page remains
pinned to the TT-Metal report commit above.

## Verify your understanding

### 1. Why can two values with equal mantissas quantize differently when placed in blocks with different maximum exponents?

???+ note "Expert answer — numerical reasoning"
    In block floating point, a mantissa is not interpreted independently: all
    16 values align to the block's selected exponent. If another value raises
    that maximum exponent, the value under study must shift farther before its
    retained mantissa bits are chosen. More low-order information is discarded,
    so its quantization step grows even though its original mantissa bits match
    the value in the other block.

    The correct unit of analysis is therefore the entire exponent-sharing
    group. Per-value error can change when only a neighboring value changes.

### 2. For a halfway discarded value, what property of the retained result decides whether to increment?

???+ note "Expert answer — rounding reasoning"
    Round-to-nearest, ties-to-even examines the least-significant **retained**
    bit. At an exact half-way case, increment if the unincremented retained
    mantissa is odd; keep it if it is already even. Both candidates are equally
    distant, so this rule selects the candidate with an even low bit and avoids
    a systematic upward bias over many ties.

    Bits below the round bit must all be zero for the case to be an exact tie;
    any lower one makes the discarded part greater than half.

### 3. What happens when rounding would overflow the retained mantissa?

???+ note "Expert answer — format-boundary reasoning"
    Under the rule documented by the pinned report, the retained mantissa clamps
    to all ones. The converter does **not** increase the shared exponent and
    renormalize all 16 values, because that would change every member of a block
    after the exponent-selection phase.

    A reference model that propagates the carry into a recomputed block exponent
    therefore implements a different quantizer and can disagree even when both
    appear reasonable in ordinary floating-point terms.

### 4. Design a 16-value test block with one large outlier. Compare its error with the same small values placed in a block without that outlier.

???+ note "Expert answer — experiment design"
    Use fifteen small, non-power-of-two values near a rounding boundary—for
    example variations around `1.0`—and one value with a much larger exponent,
    such as `256.0`. Encode this block, then encode the same fifteen small values
    in a second block whose sixteenth value is also near `1.0`.

    The outlier selects a larger shared exponent in the first block. The small
    values shift farther, retain fewer useful low bits, and show larger absolute
    or relative error; some narrow formats may collapse several distinct small
    inputs to the same code. Record encoded bits as well as error so the causal
    boundary is visible.

## Source and delta

- **Original:** [Data Formats at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/data_formats.md)
- **Added here:** an end-to-end conversion flow, explicit rounding decisions,
  invariants, failure modes, and unpack/pack study links.
- **Review conclusion:** rounding, exponent-sharing, and bit-layout statements
  above are claims of the pinned report. The living Unpacker/Packer links are
  mechanism references, not evidence that Wormhole encodings transfer to
  Blackhole. No cross-generation bit-layout equivalence is claimed.
