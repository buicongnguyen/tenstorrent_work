<!-- rewrite-status: seed -->
# Reconfiguring hardware for different DataFormats

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/reconfig_data_format.md"><code>tech_reports/data_formats/reconfig_data_format.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/data_formats/reconfig_data_format.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 65 |
| Section headings | 4 |
| Fenced code examples | 2 |
| Markdown images | 0 |

### Section outline

- `reconfig_data_format`
- `pack_reconfig_data_format`
- Usage guidelines
- Examples:

## Improvement plan

1. **Architecture pressure.** Specify which fused kernel consumes or produces multiple CB
   data formats and why a separate conversion kernel would add material traffic or dispatch.
   Name the exact safe points where Unpack or Pack state must change.

2. **Flow to make explicit.** Draw `producer CB format A → wait/ownership →
   reconfig_data_format(_srca/_srcb) → Unpack/compute → pack_reconfig_data_format →
   destination CB format B → publish`, including completion of work using the old
   configuration.

3. **Invariant to prove.** Prove that each tile's physical bytes agree with active
   Unpack/Pack interpretation and that reconfiguration occurs after prior-format work
   completes but before the next tile is consumed or published.

4. **TT-Metal evidence to connect.** Connect examples to `reconfig_data_format`,
   `reconfig_data_format_srca`, `reconfig_data_format_srcb`, and
   `pack_reconfig_data_format`, then trace the corresponding LLK/configuration path for the
   target Tensix generation.

5. **Experiment and expected observation.** Alternate two supported input/output formats in
   one controlled kernel and compare with fixed-format reference kernels; expected result:
   identical decoded values and fewer materialized conversion boundaries, with no corruption
   at the reconfiguration transition.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/reconfig_data_format.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

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
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
