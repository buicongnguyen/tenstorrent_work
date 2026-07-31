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

1. Why can two values with equal mantissas quantize differently when placed in
   blocks with different maximum exponents?
2. For a halfway discarded value, what property of the retained result decides
   whether to increment?
3. What happens when rounding would overflow the retained mantissa?
4. Design a 16-value test block with one large outlier. Compare its error with
   the same small values placed in a block without that outlier.

Expected observation for question 4: the outlier can force a larger shared
exponent, leaving fewer effective low-order bits for the smaller values.

## Source and delta

- **Original:** [Data Formats at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/data_formats.md)
- **Added here:** an end-to-end conversion flow, explicit rounding decisions,
  invariants, failure modes, and unpack/pack study links.
- **Still to review:** exact bit layouts and architecture-dependent pack/unpack
  behavior against a hardware practitioner and current implementation.
