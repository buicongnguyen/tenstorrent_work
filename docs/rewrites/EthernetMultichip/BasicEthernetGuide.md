<!-- rewrite-status: improved-draft -->
# Basic Ethernet Multichip

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md"><code>tech_reports/EthernetMultichip/BasicEthernetGuide.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned report marks itself **outdated**: current users no longer need to program
Ethernet cores directly because the fabric infrastructure manages them. Treat this page
as a mechanism-level explanation of the legacy direct-ERISC path, not as the recommended
application-facing API. Its handshakes, credits, buffer lifetimes, and measurements are
still useful for understanding what a fabric layer must make correct and efficient.

An on-chip `noc_async_write` has completion queries such as
`noc_async_writes_flushed()` and `noc_async_write_barrier()`. The pinned Ethernet model
does not give the sending ERISC an equivalent way to know, by itself, that a write left
source L1 or committed to destination L1. That missing observation forces reliability
into software: endpoint handshakes, acknowledgements, credits, stable source buffers,
and teardown are part of the data path. ERISC is also a finite routing resource on each
hop, unlike the NoC abstraction in which arbitrary unicasts eventually complete without
user allocation of every intermediate buffer. Static or dynamic routes must therefore
budget ERISC buffers and schedules as well as physical links.

The transaction layer is asynchronous. Two `tx_cmd_q` queues exist, although only queue
0 is available in this report and queue 1 is reserved. Commands are ordered within one
queue but not across queues; a busy queue cannot accept another command. This explains
both the opportunity—advance other work after `eth_txq_is_busy()`—and the hazard—never
reuse source L1 merely because a send was submitted.

### How work and data move

Before payload traffic, the two linked ERISCs establish a consistent startup handshake.
The source example reserves a 16-byte scratch region at
`eth_l1_mem::address_map::ERISC_L1_UNRESERVED_BASE`: the master calls
`eth_send_bytes(...,16)` then `eth_wait_for_receiver_done()`, while its peer calls
`eth_wait_for_bytes(16)` then `eth_receiver_channel_done(0)`. The guide recommends
channel 0 of `erisc_info` only for this bootstrap.

For a flow-controlled payload, the sender fills its channel buffer and an
`eth_channel_sync_t`. `bytes_sent` carries the nonzero payload byte count; the receiver
sets `receiver_ack` after receipt, and later clears both fields to advertise that the
buffer may be overwritten. Packing this 16-byte sync structure immediately after the
payload and sending both together avoids a command-queue gap in which payload submission
succeeds but the separate availability signal is back-pressured. The source further
recommends different receiver source addresses for acknowledgement and completion so
two completion meanings cannot race through the same word.

At kernel end, every sender channel waits until its receiver-done credit returns, calling
`run_routing()` periodically if required. This drains messages belonging to the current
kernel before a temporally later kernel reuses the same ERISC state.

### What must never break

Both endpoints must agree on link, channel, addresses, byte count, and the meaning of
each sync field. Source storage remains immutable from command submission until receiver
acknowledgement makes reuse safe. Dependent sends use one command queue unless software
adds an ordering protocol. Startup must complete before either endpoint writes payload
into remote L1, and teardown must receive all outstanding credits before kernel exit.
Otherwise a late credit from operation A can be interpreted as operation B's handshake,
or B can overwrite a buffer A still consumes. These are temporal ownership violations,
not physical-link corruption.

### Where the report makes it concrete

Host code acquires connected Ethernet cores and creates ERISC kernels with
`tt_metal::EthernetConfig{.noc=noc_id,.compile_args=...}`. The worked ring sends from a
master receiver over the local NoC to a sender, across Ethernet to the next chip's
receiver, then repeats. It performs one unmeasured round trip first to flush launch
skew. The pinned microbenchmarks report roughly 650 ns per hop in the newer merged-signal
ring formulation, about 5.2 microseconds for eight hops, and 530–620 ns one-way link-send
latency derived from round trip. Around 5 KB, serialization bandwidth begins to dominate
the fixed latency in that benchmark. Those numbers characterize this setup and snapshot;
they are not universal routing constants.

### How the decision is tested

First test startup/payload/teardown with one channel and a sequence number in every sync
record. Delay one chip's launch: the handshake must prevent early payload overwrite.
Then delay receiver consumption: the sender must not modify its buffer until the ack/
credit returns. Run a second kernel immediately afterward to detect stale-credit aliasing.
For performance, sweep packet size and channel count bidirectionally, checking
`eth_txq_is_busy()` rather than spin-submitting. The expected curve separates fixed
small-message latency from link serialization and eventually ERISC/queue contention.
If merging payload and sync removes gaps without changing sequence correctness, that is
evidence that command-queue backpressure—not computation—was the exposed bottleneck.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md):

- **Route establishment.** `run_routing()` prepares the host/runtime routing state
  before Ethernet kernels exchange packets. The route, channel assignment, peer
  coordinates, packet size, and packet count must agree at both endpoints before
  throughput or round-trip timing is meaningful.

- **Packet movement.** Ethernet kernels include `eth/dataflow_api.hpp`, while
  worker-side NoC movement uses `dataflow_api.hpp`; `eth_send_packet()` belongs to the
  Ethernet packet path. Keep those address spaces and completion rules separate when
  tracing a ring hop or round trip.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report explains how to move data between chips through active Ethernet cores and
    links, including topology discovery, packet/channel behavior, latency and bandwidth,
    and the extra coordination required when a NoC address is no longer enough.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    The sender may reuse storage only after the protocol says the receiver has accepted
    the data; both endpoints must agree on link peer, channel, packet size, destination,
    and flow-control state. A local NoC barrier alone cannot acknowledge remote
    consumption.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A worker or host prepares a source buffer → local NoC traffic reaches the sending
    Ethernet core → ERISC packetizes and transmits on the selected channel/link → the
    peer Ethernet core receives and validates flow-control state → remote NoC movement
    places bytes at the destination → a semaphore/message makes them visible to the
    consumer.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Ethernet-core types, channel count, packet-size curves, link
    bandwidth, physical topology, ERISC firmware, and measured latency are device- and
    snapshot-specific.

    **Durable model.** Separate local transport, link transport, routing, flow control,
    and application ownership; measure both small-message latency and sustained
    bandwidth; and design explicit end-to-end completion rather than assuming link
    delivery equals consumption.

## Source and delta

- **Original source:** [`tech_reports/EthernetMultichip/BasicEthernetGuide.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/EthernetMultichip/BasicEthernetGuide.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
