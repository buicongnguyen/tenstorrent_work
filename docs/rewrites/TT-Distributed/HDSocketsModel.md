<!-- rewrite-status: improved-draft -->
# H2D / D2H PCIe Socket: Technical Report

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md"><code>tech_reports/TT-Distributed/HDSocketsModel.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

At the pinned Blackhole snapshot, a PCIe “socket” is a hardware streaming FIFO, not a
POSIX socket. `H2DSocket` and `D2HSocket` hide TLB mapping, PCIe/NoC address encoding,
and credits behind host `write()`/`read()` plus `barrier()`, while device kernels use
`SocketReceiverInterface` or `SocketSenderInterface`. The architecture is shaped by
who can drive the bulk transfer efficiently. D2H and H2D `DEVICE_PULL` put the ring in
vIOMMU-mapped pinned host memory; H2D `HOST_PUSH` puts it in Tensix L1 so posted host
writes land directly on device. Even `HOST_PUSH` still requires vIOMMU host buffers for
credits and barrier pages. Page size and FIFO depth are therefore protocol parameters:
Blackhole's cited 64-byte NoC word width makes 64 B the minimum practical page in the
benchmark, while the cited 1464 KB L1/core limits device-side buffering.

### How work and data move

All modes use monotonically advancing `bytes_sent` and `bytes_acked`; available space is
`fifo_size - (bytes_sent - bytes_acked)`. In `HOST_PUSH`, host `write()` checks credits,
posts the page into the L1 FIFO through a TLB window, then updates `bytes_sent` in L1.
The kernel `socket_wait_for_pages`, copies the already resident page from
`receiver_socket.read_ptr` to its destination with `noc_async_write`, barriers, then
`socket_pop_pages` and `socket_notify_sender` publish consumption.

In `DEVICE_PULL`, the host instead copies locally into pinned RAM and performs only the
notification TLB write. The receiver calculates
`pcie_data_addr + read_ptr - fifo_addr`, issues chunked `noc_read_with_state` requests
up to `max_noc_burst_bytes`, waits for PCIe completions at
`noc_async_read_barrier`, then copies the filled L1 FIFO slot onward. This permits
multiple device-initiated reads to be in flight. D2H reverses ownership: the sender
`socket_reserve_pages`, builds a 64-bit host address from `data_addr_hi`,
`downstream_fifo_addr`, and `write_ptr`, calls `noc_write_page_chunked`, barriers before
`socket_push_pages`, and notifies host. Host `read()` polls the host-local `bytes_sent`,
copies from pinned RAM, and acknowledges the freed slot.

### What must never break

The sender may publish a page only after its payload is visible, and may reuse its slot
only after the receiver advances `bytes_acked`. Host `set_page_size(page_size)` must
match device `set_receiver_socket_page_size` or `set_sender_socket_page_size`, because
both sides derive ring pointers at that granularity. A device write must retire before
`socket_push_pages`; a device pull must complete before consuming the L1 data. Finally,
`update_socket_config` must preserve the cached `read_ptr`/`write_ptr` and counters
across kernel invocations. An incorrect barrier location can produce valid counter
progress with stale payload, the most dangerous failure mode in this protocol.

### Where the report makes it concrete

Host setup constructs the socket, sets page size, creates a `MeshBuffer`, passes
`get_config_buffer_address()` as a kernel compile-time argument, then calls
`EnqueueMeshWorkload(..., false)` before its page loop and `barrier()` afterward.
Device initialization uses `create_receiver_socket_interface(socket_config_addr)` or
`create_sender_socket_interface`. This makes completion precise: host enqueue is not
remote consumption; socket `barrier()` waits until sent bytes are acknowledged. The
source also separates `MeshSocket` over TT-Fabric as a different device-to-device
transport. Its semantics must not be imported into these PCIe rings.

### How the decision is tested

Run the pinned benchmark families (`BM_D2HSocketThroughput`, latency/ping and multi-chip
variants, plus the H2D equivalents) across page and FIFO sizes, separating startup from
steady state. Add payload sequence numbers and deliberately stall each endpoint through
multiple ring wraps; verify `0 <= bytes_sent - bytes_acked <= fifo_size` and exact data
order. Compare `HOST_PUSH` and `DEVICE_PULL` on the same high-bandwidth and
low-bandwidth chip classes while recording CPU load and link width. The expected
mechanism is that larger pages/FIFOs amortize signaling and that pipelined device pulls
can outpace CPU-driven writes for substantial pages; the report's Gen4/Gen5 and
per-chip measurements are snapshot-specific, so reproduce them before using them as a
capacity promise.

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
