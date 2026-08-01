<!-- rewrite-status: improved-draft -->
# Tensor Accessor (TA) Iterators 📚

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_accessor/tensor_accessor_iterator.md"><code>tech_reports/tensor_accessor/tensor_accessor_iterator.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

At the pinned snapshot, `TensorAccessor` already hides whether a tensor is interleaved
or sharded, but a kernel that repeatedly calls `TA.get_noc_addr(page_id)` pays the full
logical-page-to-bank mapping cost on every iteration. The iterator API separates two
use cases. `pages(start_page_id, end_page_id)` preserves a layout-independent page
order, while `shard_pages(shard_id, start_page_offset, end_page_offset)` deliberately
exposes one shard so an optimized kernel can process pages owned by its local bank.
This is a locality decision, not merely C++ syntax: for sharded tensors the iterator
retains mapping state across `operator++`, and a shard-local schedule can remove the
remote read that a naively even division of logical page IDs creates. The report's
reshard case records a **2x+** speedup for this local-read organization, depending on
the input and output sharding; that number belongs only to the linked experiment.

### How work and data move

In the generic reshard path, the host partitions the half-open logical range
`[start_page, end_page)` across cores. A reader constructs
`TensorAccessor(args_src, bank_base_address_src, page_size)`, reserves one slot with
`cb_reserve_back`, issues `noc_async_read(page.noc_addr(), cb_addr, page_size)`, waits
at `noc_async_read_barrier`, and publishes with `cb_push_back`. The writer owns the
destination mapping: it waits with `cb_wait_front`, writes to the destination
iterator's precomputed `page.noc_addr()`, waits at `noc_async_write_barrier`, and then
`cb_pop_front`s. Thus the CB transfers ownership between two kernels; advancing either
iterator before the corresponding CB action would pair the wrong source and destination
page.

The optimized sharded path changes work ownership. The host gives a core
`first_shard_id`, `num_cores`, and `num_shards`; shard IDs advance as
`first_shard_id + i * num_cores`, matching the report's round-robin bank mapping. The
device iterates `tensor_accessor_src.shard_pages(shard_id)`, asserts
`is_local_addr(page.noc_addr())`, and calls `noc_async_write_page(page.page_id(),
tensor_accessor_dst, page.noc_addr())`. Because the source is local, one kernel can
issue local-to-local or local-to-remote writes directly; the reader/writer CB pipeline
needed to avoid a remote-to-remote transaction is no longer necessary.

### What must never break

`pages()` must emit each **logical** page in the requested range exactly once and must
produce the same `(page_id, noc_addr)` mapping as direct `get_noc_addr`. For sharded
tensors it silently skips padded pages; therefore two shards can yield different
`shard_pages()` counts even when given identical offsets. Empty and out-of-range inputs
are also contractual: if `start_page_id >= end_page_id`, or the start is beyond
`dspec().tensor_volume()`, `begin() == end()`. Interleaved accessors cannot infer tensor
volume, so both bounds are mandatory. Finally, a stepped iterator accepts only a
positive stride. Violating any of these rules can produce an address-valid NoC transfer
that is logically wrong, which barriers cannot detect.

### Where the report makes it concrete

The cost boundary is explicit: `page.noc_addr()` returns an address already held by the
iterator, while the next address is calculated by `PagesAddressIterator::operator++`.
For interleaved tensors, the report says this performs identically to looping over IDs
and calling `get_noc_addr`; the retained-state benefit is specific to sharded mappings.
The 2-by-2 width-sharded example explains why: logical pages `0,2` are on one bank and
`1,3` on another, while an even logical split assigns `0,1` to one worker and `2,3` to
the other. `shard_pages()` realigns execution with physical ownership, accepting that
destination writes may still cross the NoC.

### How the decision is tested

First, for interleaved and each supported shard layout, record direct
`get_noc_addr(page_id)` and iterator results over empty, partial, full, strided, padded,
bank-wrap, and shard-wrap ranges; compare page IDs and addresses exactly. Second, run
the generic CB reshard and the shard-local single-kernel form on identical input/output
`TensorSpec`s, checking that every output page matches before timing. Instrument remote
source reads as well as cycles: the expected architectural observation is not simply a
faster loop, but that the shard-local form satisfies `is_local_addr` for every source
and eliminates the generic path's cross-bank reads. Re-test several shard shapes—the
pinned 2x+ result is evidence for the reported configurations, not a universal
iterator-speed guarantee.

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
