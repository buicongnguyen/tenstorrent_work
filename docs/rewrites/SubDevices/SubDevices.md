<!-- rewrite-status: improved-draft -->
# Sub-Devices

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md"><code>tech_reports/SubDevices/SubDevices.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to define which cores, dispatch resources, buffers,
queues, and synchronization scope each independent workload owns and which rare
dependencies genuinely require global semaphores or circular buffers.

### How work and data move

The complete path is sub-device manager creation/loading, targeted buffer/program
enqueue, local completion, optional global object publication, cross-sub-device
wait/consume, stall-group synchronization, and manager teardown.

### What must never break

The non-negotiable invariant is that core/resource sets are disjoint by default,
commands cannot consume another sub-device's local resources, and shared storage becomes
visible and reusable only through explicit cross-owner dependencies.

### Where the report makes it concrete

The report makes the decision concrete by connecting the lifecycle to
`device.load_sub_device_manager`, `clear_loaded_sub_device_manager`,
`remove_sub_device_manager`, `CreateBuffer(..., sub_device_id)`,
`set_sub_device_stall_group`, `Synchronize`, and `EnqueueRecordEvent`.

### How the decision is tested

The controlled procedure is to run two independent sub-device programs with and without
a global barrier, then add one shared buffer/event. **Expected observation:**
independent work overlaps, while only the declared producer-consumer edge serializes
shared use.

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
