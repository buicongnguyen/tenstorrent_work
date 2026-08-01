<!-- rewrite-status: improved-draft -->
# Reconfiguring hardware for different DataFormats

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/reconfig_data_format.md"><code>tech_reports/data_formats/reconfig_data_format.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to specify which fused kernel consumes or produces
multiple CB data formats and why a separate conversion kernel would add material traffic
or dispatch. Name the exact safe points where Unpack or Pack state must change.

### How work and data move

The complete path is `producer CB format A → wait/ownership →
reconfig_data_format(_srca/_srcb) → Unpack/compute → pack_reconfig_data_format →
destination CB format B → publish`, including completion of work using the old
configuration.

### What must never break

The non-negotiable invariant is that each tile's physical bytes agree with active
Unpack/Pack interpretation and that reconfiguration occurs after prior-format work
completes but before the next tile is consumed or published.

### Where the report makes it concrete

The report makes the decision concrete by connecting examples to `reconfig_data_format`,
`reconfig_data_format_srca`, `reconfig_data_format_srcb`, and
`pack_reconfig_data_format`, then trace the corresponding LLK/configuration path for the
target Tensix generation.

### How the decision is tested

The controlled procedure is to alternate two supported input/output formats in one
controlled kernel and compare with fixed-format reference kernels. **Expected observation:** identical decoded values and fewer materialized conversion boundaries,
with no corruption at the reconfiguration transition.

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
