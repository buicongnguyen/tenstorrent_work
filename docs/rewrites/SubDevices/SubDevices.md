<!-- rewrite-status: improved-draft -->
# Sub-Devices

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md"><code>tech_reports/SubDevices/SubDevices.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

Without sub-devices, the pinned runtime treats allocation and completion as chip-wide
state. A sharded L1 allocation on one core reserves the same address globally, and a
read/write command waits for all prior programs so it cannot race any user. This is safe
but serializes unrelated work—for example, a persistent program on one core group blocks
host interaction with another group. A sub-device makes core membership, allocator
state, and dispatch completion independently trackable. The gain is overlap; the cost is
that the user now owns cross-sub-device dependency correctness and can create a deadlock
that global serialization previously prevented.

Global semaphores and global circular buffers are not alternative partitioning APIs.
They restore only the explicit communication edges that independent dispatch domains
need. A normal program semaphore/CB has a program-scoped address and pointer lifetime;
a global object reserves persistent L1 state so later or concurrent programs agree on
the same synchronization/data location.

### How work and data move

`ttnn.SubDevice([...CoreRangeSet...])` defines logical core membership by programmable
core type. `device.create_sub_device_manager([sub_device_0, sub_device_1], 3200)` builds
metadata and reserves a 3200-byte local-allocator region per Tensix-bearing sub-device,
but does not activate it. `device.load_sub_device_manager(id)` first waits for existing
programs and requires local allocators to be empty, then installs the configuration.
Each local allocator occupies the lower L1 address range in this pinned version; the
global allocator shrinks by the configured size. `CreateBuffer(..., sub_device_id_0)`
uses that local allocator, while an unspecified ID remains global. A zero local size
keeps all memory in the global allocator while still permitting independent execution
tracking.

Programs retain the ordinary host API. Dispatch infers which sub-device their cores
occupy and serializes only against prior programs on that sub-device. The pinned report
limits a program to one sub-device and says a program cannot be rerun under a different
manager configuration. Cross-domain host/device commands default to waiting on all
sub-devices for compatibility. `ttnn.set_sub_device_stall_group([...])` narrows that
default; `ttnn.synchronize_device(..., sub_device_ids=...)` waits on the host, while
`ttnn.record_event(..., sub_device_ids=...)` creates a device-side ordering point.
Excluding a persistent sub-device from the stall group is safe only if the command does
not consume its results.

For a scalar dependency, `ttnn.create_global_semaphore(device, cores, initial_value,
BufferType.L1)` allocates a persistent address on Tensix cores. Kernels can exchange
state through that address across program lifetimes; the host can inspect it with
`get_global_semaphore_address` and issue a new generation value with
`reset_global_semaphore_value`.

For streaming data, `ttnn.create_global_circular_buffer` allocates per-core L1 storage
from a sender-to-receiver mapping. A program binds it with
`CircularBufferConfig::remote_index`—the report uses remote index 31 and local index 0.
The remote interface handles cross-core flow control; an in-placed local CB feeds LLKs,
which cannot consume the remote configuration directly. A sender calls
`remote_cb_reserve_back` and
`remote_cb_push_back_and_write_pages(...)`; receivers call `remote_cb_wait_front` and
`remote_cb_pop_front`. Page-size changes use the paired resize APIs followed by
`align_local_cbs_to_remote_cb` for in-placed locals. Because hot execution caches
read/write pointers in a struct, exactly one RISC per core must call
`update_remote_cb_config_in_l1(remote_cb_index)` at program end so a later program resumes
at the correct persistent position.

### What must never break

Sub-device core sets and local allocator ownership must match the active manager. No
local buffers may exist while loading/clearing a manager, and the active manager cannot
be removed. A program cannot span sub-devices in the pinned feature set. Narrowing a
stall group must never omit a producer on which the command depends; circular waits
between a long-running program and a host/event wait cause a hang.

Global state needs generation discipline. Semaphore reset cannot race a producer still
using the previous value. For a remote CB, sender reserve precedes every write/push,
receiver wait precedes consumption, and pop is the acknowledgement that releases
capacity. Local and remote CB index ranges cannot overlap; the maximum local index must
remain below the minimum remote index. Resizing requires all linked interfaces to agree,
and one owner writes final cached pointers back to L1. Losing that writeback makes the
next program replay old pointer state and can overwrite unconsumed data.

### Where the report makes it concrete

The allocator split is a space/overlap tradeoff: a larger local range enables more
independent L1 allocation but removes that range from global allocation. In the pinned
report, global semaphores use the global allocator and Tensix L1, while TT-NN tensors do
not yet accept sub-device allocation. The feature is marked under active development;
planned Ethernet-core changes are not durable API promises.

Remote CB indices conventionally start high and local indices low for dispatch
performance; non-overlap is mandatory. `UpdateDynamicCircularBufferAddress` may retarget
a bound CB only when the new global object contains every configured core.

### How the decision is tested

Create two disjoint worker sub-devices and run a long persistent program on one while
dispatching a finite program/read on the other. Compare the default all-domain stall
group with a correctly narrowed group; the second command should overlap only when it has
no dependency on the persistent work. Record per-sub-device events and confirm that
waiting on one ID does not wait on the other. Exercise manager load/clear with live local
buffers and require the runtime to reject the invalid lifecycle.

Then add one producer-consumer edge. For a global semaphore, tag successive generations
and verify no stale wakeup. For a global CB, send more pages than its capacity so reserve,
wait, push, and pop all execute; split the transfer across two programs and verify the
second resumes from the L1-persisted pointer. Deliberately omit final pointer writeback
in a diagnostic build to show why it is required. Measure overlap, CB full/empty waits,
and serialized edges. The architecture succeeds when unrelated work overlaps and only
the declared global object/event imposes ordering—not when global stalls are merely
removed.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md):

- **Manager lifecycle.** `device.load_sub_device_manager`,
  `clear_loaded_sub_device_manager`, and `remove_sub_device_manager` change the
  partition state used by later allocations and queues. Handles and sub-device IDs are
  valid only within the manager lifetime that created them.

- **Scoped progress.** `CreateBuffer(..., sub_device_id)` binds storage, while
  `set_sub_device_stall_group`, `Synchronize`, and `EnqueueRecordEvent` scope ordering
  or observation. Confirm which sub-devices each call waits for; a global-looking host
  sequence need not imply global device synchronization.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    Sub-devices partition one chip's cores and dispatch resources so independent
    workloads can be launched and synchronized at a narrower scope. Global semaphores
    and circular buffers then provide deliberate coordination across those partitions
    when isolation alone is insufficient.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Sub-device core ranges and owned resources must not overlap illegally; commands
    targeted to one sub-device must not consume another's local resources.
    Cross-sub-device state becomes visible only through an explicitly shared object and matching
    synchronization protocol.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    The host defines disjoint core sets → the runtime creates sub-device managers/queues
    → a command is targeted to one partition → its kernels use local CBs and cores → a
    global semaphore or global CB carries the required cross-partition dependency →
    completion can be waited at sub-device or device scope.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Sub-device APIs, dispatch-core allocation, permitted core
    ranges, global-object implementation, and synchronization capabilities depend on
    device and runtime version.

    **Durable model.** Partition resources to reduce interference and synchronization
    scope, make ownership exclusive by default, share only named channels, and match
    every cross-partition data transfer with a happens-before edge.

## Source and delta

- **Original source:** [`tech_reports/SubDevices/SubDevices.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/SubDevices/SubDevices.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
