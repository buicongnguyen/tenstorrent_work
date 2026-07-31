<!-- rewrite-status: seed -->
# Tensor Accessor (TA) Iterators 📚

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_accessor/tensor_accessor_iterator.md"><code>tech_reports/tensor_accessor/tensor_accessor_iterator.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/tensor_accessor/tensor_accessor_iterator.md</code>. This learner page
    establishes provenance, a reading map, and an improvement plan; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 302 |
| Section headings | 18 |
| Fenced code examples | 10 |
| Markdown images | 0 |

### Section outline

- Pages Iterator 📄
  - Usage
  - Performance Considerations 🚀
  - Creation ⚙️
  - Examples of Using the Pages Iterator 💡
  - Note on NOC Address Computation ⚠️
  - Note on Padding ⚠️
  - Advanced Usage 🔧
- Shard Pages Iterator 🧩
  - Usage
  - Performance Considerations 🚀
  - Examples of Using the Shard Pages Iterator 💡
  - Note on Padding ⚠️
  - Advanced Usage 🔧
- When Should You Use Each Iterator? 🤔
  - Reshard Op Example 📋
    - Pages Iterator
  - Shard Pages Iterator

## Improvement plan

The learner edition should make these parts explicit before it can move beyond
`seed`:

1. State the problem and the hardware/software boundary involved.
2. Draw the data or control flow, including ownership and synchronization.
3. Extract correctness invariants and architecture-specific assumptions.
4. Connect the concepts to concrete TT-Metal symbols or examples.
5. Add a small verification exercise with an expected observation.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_accessor/tensor_accessor_iterator.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_accessor/tensor_accessor_iterator.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report introduces page and shard-page iterators that retain mapping state while
    traversing a tensor, avoiding repeated full logical-page-to-bank calculations in
    regular loops. The targeted bottleneck is address-generation overhead inside a
    data-movement loop.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The iterator's sequence of `(bank, offset)` results must exactly match the tensor's
    `DistributionSpec`, including shard boundaries, orientation, page count, and end
    condition. Cached state may improve cost but cannot change logical iteration order.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Kernel code constructs an iterator from the accessor/distribution state →
    dereference yields the current NoC address → a NoC API moves the page into or out of
    owned L1 storage → increment updates bank/shard offsets with cached strides → the
    loop stops after the declared page range.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Iterator classes, compile/runtime argument layout, state
    representation, sharded fast paths, and per-rank cycle costs depend on the TT-Metal
    implementation.

    **Durable model.** Use stateful traversal when adjacent addresses share structure,
    define iteration order as part of the interface, keep movement and ownership
    separate from address generation, and test transitions at bank/shard boundaries.

## Source and delta

- **Original source:** [`tech_reports/tensor_accessor/tensor_accessor_iterator.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_accessor/tensor_accessor_iterator.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/tensor_accessor/tensor_accessor_iterator.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and source-grounded verification answers. Generation-sensitive claims remain
  scoped to the pinned source snapshot.
