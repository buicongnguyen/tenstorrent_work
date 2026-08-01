<!-- rewrite-status: improved-draft -->
# Reconfiguring hardware for different DataFormats

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/reconfig_data_format.md"><code>tech_reports/data_formats/reconfig_data_format.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Data format is active hardware state in the Unpack, Math, and Pack stages, not only
metadata attached to a circular buffer. A fused kernel that changes operand CBs can
therefore present valid bytes to the wrong decoder unless it reprograms the stage before
the next operation. The pinned API deliberately splits input-side reconfiguration from
output-side reconfiguration because they run on different compute RISCs:
`reconfig_data_format*` updates Unpack (`trisc0`) and Math (`trisc1`), whereas
`pack_reconfig_data_format` updates Pack (`trisc2`). Reconfiguring only the stage whose
operand changes avoids unnecessary state writes, but it makes stage ownership explicit
in the program.

The source also exposes two overload styles. Passing only a new operand is sufficient to
identify the target format; passing both old and new CB operands lets the implementation
use faster reconfiguration paths and perform dynamic eligibility checks. For that
reason, the report says programmers should always prefer the old-plus-new overload.

### How work and data move

Consider two consecutive operations in one compute kernel. After the first operation has
finished consuming its SrcA/SrcB tiles, call
`reconfig_data_format(srca_old_operand, srca_new_operand, srcb_old_operand,
srcb_new_operand)` if both sources change. If only one source changes, use
`reconfig_data_format_srca(old,new)` or `reconfig_data_format_srcb(old,new)`; changing
both globally would do needless work. The next CB tile can then be unpacked and consumed
under its own interpretation. If the result moves to an output CB with a different
format, trisc2 independently executes `pack_reconfig_data_format(old_operand,
new_operand)` before packing that result and publishing it to the destination CB.

The supported set in this snapshot is precise. Input-side FLOAT32, BFLOAT16,
BFLOAT8_B, and BFLOAT4_B may reconfigure among themselves. Crossing between that set
and UINT8 requires `to_from_int8=true` and `DST_ACCUM_MODE==true`. Pack supports the
same FLOAT/UINT8 transitions without those two requirements. This asymmetry is why one
combined "current format" variable is not an adequate model of the three-stage machine.

### What must never break

At every tile boundary, the CB's declared format, the active SrcA/SrcB decode state, the
Math mode, and the output Pack state must describe the same intended value path. All
uses of the old format must finish before state changes, and no new-format tile may be
unpacked or packed before its corresponding reconfiguration. FLOAT/UINT8 input
transitions additionally require destination accumulation mode. A missed input switch
corrupts source values before arithmetic; a missed Pack switch corrupts representation
after correct arithmetic. Both can produce finite, shape-correct numbers, making this a
dangerous silent failure rather than necessarily a hang.

### Where the report makes it concrete

Choose the narrow API by the state that actually changes: both source registers,
SrcA only, SrcB only, or Pack only. The template parameter belongs only to the
input-side APIs, reflecting the extra FLOAT/INT8 contract there. The old/new operand
pair is an architectural hint as well as a safety check: the report says it enables a
faster reconfiguration path and dynamic eligibility checks, but does not expose the
register-level mechanism. This report contains no worked example and does not specify
cycle counts or exact register writes;
those details must not be inferred from the signatures. Its defensible claim is the
stage boundary, supported transition table, and usage rule at commit `992f3ca`.

### How the decision is tested

Build a fused two-operation test whose first CB uses BFLOAT16 and second uses BFLOAT8_B,
then compare against two fixed-format reference kernels with a materialized boundary.
Exercise SrcA-only, SrcB-only, both-source, and Pack-only changes separately and use
old-plus-new overloads. Add a UINT8 crossing with `to_from_int8=true` and
`DST_ACCUM_MODE==true`, plus a negative configuration that should be rejected when those
conditions are absent. Use values near representational boundaries so a stale decoder
cannot pass by coincidence. Expected evidence is reference-equivalent decoded output at
every transition; performance claims require a separate measurement because the pinned
source supplies no latency numbers.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/reconfig_data_format.md):

- **Compute-side switch.** `reconfig_data_format`, `reconfig_data_format_srca`, and
  `reconfig_data_format_srcb` change how Unpack interprets the next source data. The
  producer must have published data in the format that the selected reconfiguration
  describes before compute consumes it.

- **Output-side switch.** `pack_reconfig_data_format` changes the destination encoding
  used by Pack. Trace both calls into the architecture-matched LLK/configuration path; a
  source-side reconfiguration alone cannot make a differently formatted destination
  buffer correct.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/reconfig_data_format.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The task is to let a long-running kernel consume or produce circular buffers with
    different data formats by reconfiguring unpacker and packer hardware at safe points,
    avoiding a separate kernel solely for a format boundary.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    When a tile is unpacked or packed, the hardware configuration must describe the
    format actually stored in that circular buffer. Reconfiguration must occur after
    prior work using the old format is complete and before any consumer interprets bytes
    using the new format.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A producer publishes a tile in its declared CB format → the compute kernel waits for
    ownership → `reconfig_data_format` selects the required input interpretation →
    unpack and math consume it → `pack_reconfig_data_format` selects the output encoding
    → pack writes the destination tile → the output CB is published.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Supported format pairs, reconfiguration instructions, CB
    identifiers, APIs, and unpacker/packer state are tied to the Tensix generation and
    the pinned low-level kernel interface.

    **Durable model.** Treat representation as part of a producer-consumer protocol.
    Change interpretation only at a quiescent boundary, make format metadata agree with
    physical bytes, and separate conversion cost from arithmetic cost.

## Source and delta

- **Original source:** [`tech_reports/data_formats/reconfig_data_format.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/reconfig_data_format.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/data_formats/reconfig_data_format.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
