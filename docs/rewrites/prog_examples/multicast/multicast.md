<!-- rewrite-status: improved-draft -->
# **Data Multicasting**

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md"><code>tech_reports/prog_examples/multicast/multicast.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to state the exact one-to-many reuse: which coordinator
payload is identical for which receiver core rectangle, how often it is reused, and why
multicast saves more traffic than its group synchronization costs.

### How work and data move

The complete path is host setup in `multicast.cpp`, receiver reservation/readiness,
coordinator action in `coordinator_kernel.cpp`, NoC multicast, inbound handling in
`inbound_kernel.cpp`, arrival publication, local consumption, and acknowledgement/reuse.

### What must never break

The non-negotiable invariant is that all destinations are addressable and reserved
before send, no receiver publishes before transport completion, and source/destination
pages are not reclaimed while any required consumer still owns them.

### Where the report makes it concrete

The report makes the decision concrete by connecting core coordinates/ranges,
semaphores, CBs, and host runtime arguments to `multicast.cpp`,
`coordinator_kernel.cpp`, `inbound_kernel.cpp`, and the source's `{0, 0}` coordinator
example.

### How the decision is tested

The controlled procedure is to compare one multicast with repeated unicast/DRAM reads
for synchronized and deliberately skewed receivers. **Expected observation:**
multicast wins for aligned dense fanout but group wait can erase the benefit under skew.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md):

- **Host topology.** `multicast.cpp` assigns the `{0, 0}` coordinator, receiver core
  range, circular buffers, semaphores, and per-core runtime arguments. Coordinates used
  for NoC multicast must match the same physical/virtual coordinate convention on every
  participant.

- **Sender/receiver handshake.** `coordinator_kernel.cpp` reserves and publishes the
  payload, while `inbound_kernel.cpp` waits for the semaphore and consumes it. Check
  destination count, semaphore initialization/reset, write completion, and CB push/pop
  counts for every multicast round.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The example demonstrates one coordinator sending identical data to a group of
    receiver cores through a NoC multicast, replacing repeated point-to-point transfers
    while making receiver readiness and completion explicit. The optimization is valid
    only when all receivers need the same payload.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Every target must reserve valid destination storage before the coordinator writes,
    and no receiver may publish the page before arrival. The sender may reuse its source
    only after the required completion/acknowledgement contract is satisfied.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The host creates coordinator/receiver kernels, CBs, ranges, and semaphores →
    receivers reserve pages and signal readiness → the coordinator issues one multicast
    to the physical destination rectangle → transport completes → receivers
    signal/publish arrival → local consumers process their copies.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** NoC multicast APIs, coordinate conversion, rectangular range
    restrictions, semaphore placement, alignment, and destination encoding depend on
    TT-Metal and the chip topology.

    **Durable model.** Use multicast for genuine one-to-many reuse, prove all
    destinations are ready, distinguish transport completion from local publication, and
    compare saved source traffic with synchronization and fanout cost.

## Source and delta

- **Original source:** [`tech_reports/prog_examples/multicast/multicast.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/prog_examples/multicast/multicast.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
