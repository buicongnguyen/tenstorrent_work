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

1. **Architecture pressure.** Identify loops that traverse consecutive pages or shard pages
   and quantify address-generation cycles from repeated full mapping versus stateful
   iteration, including rank and shard-boundary frequency.

2. **Flow to make explicit.** Draw iterator construction from TensorAccessor/distribution
   state, first address, NoC read/write and CB ownership, incremented bank/shard/offset
   state, boundary transition, and `end_page_id` termination.

3. **Invariant to prove.** Prove the iterator emits exactly the same address sequence and
   logical page order as `TA.get_noc_addr(...)` for first, last, bank-wrap, shard-wrap,
   padded, and empty ranges.

4. **TT-Metal evidence to connect.** Connect the plan to `start_page_id`, `end_page_id`,
   `tensor_volume()`, page and shard-page iterator APIs, and the baseline
   `TA.get_noc_addr(...)` path.

5. **Experiment and expected observation.** Benchmark sequential and randomized page access
   with direct lookup and iterators; expected result: iteration reduces cycles for regular
   traversal while random access shows little benefit and both produce identical addresses.

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
