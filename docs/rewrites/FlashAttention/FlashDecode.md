<!-- rewrite-status: seed -->
# FlashDecode on Tenstorrent's Wormhole Architecture

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashDecode.md"><code>tech_reports/FlashAttention/FlashDecode.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/FlashAttention/FlashDecode.md</code>. This learner page
    establishes provenance, a reading map, and review prompts; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 186 |
| Section headings | 17 |
| Fenced code examples | 6 |
| Markdown images | 5 |

### Section outline

- 1 Introduction
  - 1.1 Common Terminology
  - 1.2 Group Query Attention (GQA)
- 2 Background
  - 2.1 What is KV Cache and How it Can Speed Up Decoding
  - 2.2 How to Smartly Utilize Tenstorrent's Tile-based Architecture for Attention Decoding
  - 2.3 FlashDecode
- 3 Implementation Details
  - 3.1 Parallelization
  - 3.2 Step-by-step Visualization of an Average Case
  - 3.3 Asynchronous Execution, NOC, Circular Buffers, and Semaphores
  - 3.4 Causal vs. Non-causal
- 4 Performance Analysis
  - 4.1 Generic Performance
  - 4.2 Long Context Length Performance on Llama 3.1 8B, Tensor Parallelism on 1,2,4,8 Devices
- 5 Future work
- References

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashDecode.md). During
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

- **Original source:** [`tech_reports/FlashAttention/FlashDecode.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashDecode.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/FlashAttention/FlashDecode.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and verification prompts. No new technical claims have been introduced yet.
