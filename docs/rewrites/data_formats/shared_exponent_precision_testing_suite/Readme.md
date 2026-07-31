<!-- rewrite-status: seed -->
# Shared Exponent Precision Testing Suite

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md"><code>tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md</code>. This learner page
    establishes provenance, a reading map, and review prompts; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 297 |
| Section headings | 52 |
| Fenced code examples | 17 |
| Markdown images | 0 |

### Section outline

- Overview
- Purpose
- Architecture
- Data Generation Strategy
  - Distribution Types (`generators.py`)
    - Basic Distributions
    - Outlier Distributions
    - Combined Distributions
    - Negative Variants
  - Pattern Types (`generators.py`)
    - **Column Gradient Pattern** (`column_magnitude_gradient`)
    - **Reverse Column Gradient Pattern** (`reverse_column_magnitude_gradient`)
    - **Row Gradient Pattern** (`row_magnitude_gradient`)
    - **Reverse Row Gradient Pattern** (`reverse_row_magnitude_gradient`)
    - **Row Uniform Pattern** (`row_uniform_column_varying`)
    - **Checkerboard Pattern** (`checkerboard_magnitudes`)
    - **Row Outliers Pattern** (`row_outliers`)
    - **Tile Boundaries Pattern** (`tile_boundaries`)
    - **Diagonal Gradient Pattern** (`diagonal_gradient`)
    - **Block Pattern** (`block_pattern`)
    - **FA_Rand Pattern** (`fa_rand_pattern`)
- Operations Tested
  - Reduction Operations
  - Matrix Operations
- … 28 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

Before rewriting this page, answer from the original:

1. What concrete bottleneck, correctness constraint, or programming task is
   this report addressing?
2. What is one invariant that must remain true?
3. Trace one unit of data or one control event from producer to consumer.
4. Which claims are architecture-specific, and which form a durable mental
   model across Tenstorrent generations?

## Source and delta

- **Original source:** [`tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
