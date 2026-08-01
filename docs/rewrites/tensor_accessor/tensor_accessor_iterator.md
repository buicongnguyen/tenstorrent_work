<!-- rewrite-status: improved-draft -->
# Tensor Accessor (TA) Iterators 📚

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_accessor/tensor_accessor_iterator.md"><code>tech_reports/tensor_accessor/tensor_accessor_iterator.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to identify loops that traverse consecutive pages or
shard pages and quantify address-generation cycles from repeated full mapping versus
stateful iteration, including rank and shard-boundary frequency.

### How work and data move

The complete path is iterator construction from TensorAccessor/distribution state, first
address, NoC read/write and CB ownership, incremented bank/shard/offset state, boundary
transition, and `end_page_id` termination.

### What must never break

The non-negotiable invariant is that the iterator emits exactly the same address
sequence and logical page order as `TA.get_noc_addr(...)` for first, last, bank-wrap,
shard-wrap, padded, and empty ranges.

### Where the report makes it concrete

The report makes the decision concrete by connecting the plan to `start_page_id`,
`end_page_id`, `tensor_volume()`, page and shard-page iterator APIs, and the baseline
`TA.get_noc_addr(...)` path.

### How the decision is tested

The controlled procedure is to benchmark sequential and randomized page access with
direct lookup and iterators. **Expected observation:** iteration reduces cycles for
regular traversal while random access shows little benefit and both produce identical
addresses.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_accessor/tensor_accessor_iterator.md):

- **Traversal bounds.** `start_page_id`, `end_page_id`, and `tensor_volume()` define the
  half-open page interval. Direct `TA.get_noc_addr(...)` output is the correctness
  oracle for the same logical traversal before iterator performance is compared.

- **Cached iterator state.** Page and shard-page iterators cache bank, offset, shard,
  and coordinate progress between increments. Test transitions at bank and shard
  boundaries; a fast contiguous interior loop can still carry stale state when crossing
  either boundary.

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
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
