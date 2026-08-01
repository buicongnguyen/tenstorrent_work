<!-- rewrite-status: improved-draft -->
# H2D / D2H PCIe Socket: Technical Report

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md"><code>tech_reports/TT-Distributed/HDSocketsModel.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to define socket direction, endpoint ownership,
transfer mode, ring depth, backing memory, producer/consumer rates, and host/device
failure/teardown semantics for the intended streaming workload.

### How work and data move

The complete path is slot reservation, payload fill/reference, publication, PCIe/DMA
transfer, remote availability, consumer read, completion, credit return, wraparound, and
endpoint close for both H2D and D2H.

### What must never break

The non-negotiable invariant is that a producer never overwrites an unread slot, a
consumer never reads an unpublished slot, credits/indices describe the same ring state,
and endpoints/buffers outlive every in-flight transfer.

### Where the report makes it concrete

The report makes the decision concrete by connecting the design to `H2DSocket`,
`D2HSocket`, `MeshSocket`, and `tt_metal/api/tt-metalium/experimental/sockets/`,
including the report's transfer-mode and flow-control APIs.

### How the decision is tested

The controlled procedure is to run producer faster than consumer and then reverse the
rates across multiple wraparounds. **Expected observation:** bounded backpressure
prevents corruption/underrun and steady-state throughput separates from
connection/fill/drain latency.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md):

- **Direction and ownership.** `H2DSocket` and `D2HSocket` make PCIe transfer direction
  explicit. `MeshSocket` is named only as the device-to-device contrast and is outside
  this report's scope; do not import its TT-Fabric behavior into the host/device socket
  model.

- **Flow control.** The APIs under `tt_metal/api/tt-metalium/experimental/sockets/`
  define connection, send/receive, and completion semantics. Match credits or
  acknowledgements with buffer reuse; host enqueue completion alone does not prove a
  remote consumer finished.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report designs high-throughput host-to-device and device-to-host PCIe sockets as
    long-lived streams rather than isolated tensor copies. Transfer modes, ring buffers,
    and flow control must support multiple hosts/devices without overwrite or
    starvation.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Producer and consumer indices/credits must describe the same ring state: a producer
    cannot overwrite an unread slot, a consumer cannot read an unpublished slot, and
    backing buffers plus socket endpoints must outlive all in-flight transfers.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A producer reserves a socket/ring slot → fills or points it at payload → publishes
    availability → PCIe/DMA moves data across the host-device boundary → the consumer
    waits on the matching state, reads the payload, and returns credit → the producer
    may reuse the slot.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Socket APIs, transfer modes, queue depths, buffer placement,
    PCIe topology, synchronization implementation, and reported bandwidth/latency are
    snapshot-specific.

    **Durable model.** Use bounded queues with explicit backpressure, separate
    reservation from publication and reclamation, preserve endpoint lifetime, batch
    transfers enough to amortize setup, and measure steady-state streaming independently
    from startup.

## Source and delta

- **Original source:** [`tech_reports/TT-Distributed/HDSocketsModel.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/TT-Distributed/HDSocketsModel.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
