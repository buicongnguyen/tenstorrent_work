<!-- rewrite-status: seed -->
# Tensor Padding (Multicore)

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md"><code>tech_reports/prog_examples/pad_multi_core/pad_multi_core.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 354 |
| Section headings | 5 |
| Fenced code examples | 17 |
| Markdown images | 0 |

### Section outline

- Building and Running the Example
- Device setup
- Initialize data
- Designate cores for utilization
- Configure and create DRAM buffers

## Improvement plan

1. **Architecture pressure.** Define logical padding, physical tile/page padding, output
   layout, pad value, and a disjoint output ownership partition so every produced coordinate
   has exactly one responsible core.

2. **Flow to make explicit.** Draw host `Device`/`CommandQueue`/`Program` setup,
   input/output buffer creation, output-range runtime arguments, per-core coordinate
   classification, input read or pad synthesis, writer commit, and host validation.

3. **Invariant to prove.** Prove each output coordinate is written once; in-range
   coordinates map to the correct input element and out-of-range coordinates receive the
   declared pad value, including partial rows/pages and every corner.

4. **TT-Metal evidence to connect.** Connect the plan to the example's `Device`,
   `CommandQueue`, `Program`, `bfloat16` buffers, designated core ranges, DRAM/L1 configs,
   reader/writer kernels, and runtime arguments.

5. **Experiment and expected observation.** Use distinctive interior/edge values and uneven
   padding that crosses page boundaries; expected result: exact output ownership/values with
   no overlap, and per-core timings reveal any padding-heavy imbalance.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The program parallelizes tensor padding: cores must produce a larger output
    containing both copied input coordinates and constant padding, without serializing
    address generation or creating overlapping writes. Boundary classification is the
    central correctness task.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Each physical output element must be written exactly once. Coordinates inside the
    original extent must map to the correct input element; coordinates outside it must
    receive the declared pad value, including tile/row padding required by the storage
    layout.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The host allocates input/output buffers and partitions output pages among cores →
    each reader classifies its assigned output coordinates → it reads the corresponding
    input page/element or synthesizes the pad value → a writer commits the
    non-overlapping output region → host validation checks edges and interior.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Page/tile layout, core range, runtime arguments, alignment,
    buffer placement, and vectorized fill/read implementation are example- and
    architecture-specific.

    **Durable model.** Partition by unique output ownership, derive source coordinates
    from the output, treat physical padding separately from logical padding, and
    emphasize boundaries/partial pages in tests.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/pad_multi_core/pad_multi_core.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
