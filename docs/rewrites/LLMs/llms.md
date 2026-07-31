<!-- rewrite-status: seed -->
# LLMs in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/llms.md"><code>tech_reports/LLMs/llms.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/LLMs/llms.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 1870 |
| Section headings | 70 |
| Fenced code examples | 79 |
| Markdown images | 3 |

### Section outline

- Contents
- 1. Overview
- 2. Modules
  - 2.1 Embedding
  - 2.2 RoPE
    - 2.2.1 Setting up inputs to RoPE
    - 2.2.2 Decode mode specifics
  - 2.3 Norm
    - 2.3.1 Implementations of Normalization Operations
    - 2.3.1.1 Non-Distributed Norm
    - 2.3.1.2 Distributed Norm
    - 2.3.1.3 References
  - 2.4 Attention
  - 2.4.1 Attention Prefill
  - 2.4.2 Attention Decode
  - 2.4.3 Miscellaneous Facts
  - 2.5 MLP
    - 2.5.1 Setup
    - 2.5.2 Inputs
    - 2.5.3 Setting Up Program Configurations For Matmuls
    - 2.5.4 FF1/FF3 Matmul
    - 2.5.5 FF1/FF3 Matmul With 2D Weight Fracturing
    - 2.5.6 Multiply + Fused SiLU Activation
    - 2.5.7 FF2 Matmul
- … 46 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/llms.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Source and delta

- **Original source:** [`tech_reports/LLMs/llms.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/llms.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/LLMs/llms.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
