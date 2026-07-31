<!-- rewrite-status: seed -->
# ViT in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md"><code>tech_reports/ViT-TTNN/vit.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/ViT-TTNN/vit.md</code>. This learner page
    establishes provenance, a reading map, and review prompts; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 712 |
| Section headings | 30 |
| Fenced code examples | 21 |
| Markdown images | 17 |

### Section outline

- Contents
- 1. Overview
- 2. ViT TT-NN Optimization Techniques
  - 2.1 Sharding on all relevant OPs
  - 2.2 Matmul sharding variants in ViT
    - 2.2.1 Matmul Reuse (BMM)
    - 2.2.2 Matmul Reuse Mcast (2D)
    - 2.2.3 Matmul Reuse Mcast (1D)
  - 2.3 Transformer optimizations
- 3. ViT TT-NN Code Structure
  - 3.1 Top-level modules
  - 3.2 Embeddings module
  - 3.3 Encoder module
  - 3.4 Encoder One Layer module
- 4. ViT Encoder Layer TT-NN Deep Dive
  - 4.1 Input
  - 4.2 Sharding parametrization
  - 4.3 Layer Normalization (Layernorm)
  - 4.4 Multi-Head Self-Attention
    - 4.4.1 Q,K,V Generation using the Fused Linear OP
    - 4.4.2 Splitting into Q-K-V
    - 4.4.3 Attention Mechanism
    - 4.4.4 Matmul with Value
    - 4.4.5 Concatenating Heads and Self-Output Linear OP
- … 6 additional headings in the original

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md). During
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

- **Original source:** [`tech_reports/ViT-TTNN/vit.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/ViT-TTNN/vit.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
