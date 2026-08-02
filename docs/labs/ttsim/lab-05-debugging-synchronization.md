# Lab 5 — Debug a synchronization chain, not a symptom

<p class="source-note">
<strong>Run this exact source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/NoC_tile_transfer/noc_tile_transfer.cpp">two-core host program</a>,
<a href="https://github.com/tenstorrent/tt-metal/tree/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/NoC_tile_transfer/kernels/dataflow">four dataflow kernels</a>, and the
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md">pinned original walkthrough</a>
</p>

**Learner references:** [NoC transfer analysis](../../rewrites/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md)
and [kernel debugging](../../rewrites/Debugging/Kernel_Debugging_Tips.md).

The program moves one tile through two cores:

```text
DRAM → core 0 L1 → NoC → core 1 L1 → DRAM
```

The difficult part is not the arrow diagram. Core 1 must first advertise
destination capacity; core 0 must wait for that advertisement; core 0 must not
announce arrival until the L1-to-L1 write completes; core 1 must not publish the
received CB page before that arrival; and the final writer must not release its
source page before the DRAM write completes. A useful debugger reconstructs this
causal chain instead of adding prints everywhere.

## Name the three kinds of evidence

| Mechanism | What it proves | What it does not prove |
|---|---|---|
| semaphore value | a named control event was signaled/observed | bytes associated with the event are complete unless protocol orders them |
| NoC barrier | the caller's qualifying NoC operations reached their completion point | another core published or consumed a CB page |
| CB push/pop | a page changed producer/consumer ownership | an earlier external transfer completed unless placed after its barrier |

Before running, turn the four kernel files into an event sequence. The minimum
expected order is:

```text
core 1 reserves destination
→ core 1 signals READY
→ core 0 observes READY
→ core 0 writes tile over NoC
→ core 0 waits for write completion
→ core 0 signals ARRIVED
→ core 1 observes ARRIVED and publishes its CB
→ core 1 writer waits, writes DRAM, waits, then pops
```

## Run the baseline

```bash
cd ~/tt-metal
export TT_METAL_SIMULATOR=~/sim/1.9.7/wormhole/libttsim_wh.so
export TT_METAL_SLOW_DISPATCH_MODE=1
export TT_METAL_DISABLE_SFPLOADMACRO=1
export TT_METAL_DPRINT_CORES="(0,0),(0,1)"

./build/programming_examples/metal_example_noc_tile_transfer
```

Expected payload evidence is `Result = 14 : Expected = 14`. Print order can be
affected by buffering and should not be promoted into a synchronization contract.
Use it to locate progress, then verify ordering in the kernel source.

```bash
rg -n "cb_|noc_semaphore|noc_async_write|noc_async_.*barrier|DPRINT|DEVICE_PRINT" \
  tt_metal/programming_examples/NoC_tile_transfer
```

## Architecture walkthrough

The destination-ready handshake prevents an overwrite. Core 1 reserves its CB
page before telling core 0 where it may send. That converts local capacity into a
remote permission. Core 0 waits for the permission, issues an asynchronous NoC
write, and executes a write barrier. Only then may its arrival notification mean
“the payload is safe to consume.”

This design uses a semaphore as a control message and the NoC as a data path. The
pair is analogous to a release/acquire protocol: payload completion precedes the
release signal; the receiver observes the signal before publishing the payload to
its next consumer. A semaphore operation alone is not a data barrier unless the
documented program orders the payload around it.

The CB adds a second layer of decoupling on core 1. Reader 1 owns the remote-arrival
protocol; writer 1 owns the DRAM egress. Publishing the CB page transfers local
ownership between those RISC-V roles. The final NoC write barrier precedes pop so
that producer reuse cannot alter bytes still being read by the egress engine.

Instrumentation is an observer. Device prints consume buffer space and change
execution timing. Watcher and stack triage expose different state. The robust
method is to form a hypothesis about the first violated edge, add the smallest
observation before and after that edge, and repeat without instrumentation. A race
that disappears when printed remains a race.

## Controlled experiment

In a disposable branch, edit only core 0's writer: move the arrival semaphore
increment before `noc_async_write_barrier`. Keep the actual NoC write before both.

```bash
cd ~/tt-metal
git switch -c lab/noc-arrival-order
git diff -- tt_metal/programming_examples/NoC_tile_transfer/kernels/dataflow/writer0.cpp
cmake --build build --target metal_example_noc_tile_transfer -j2
timeout 30s ./build/programming_examples/metal_example_noc_tile_transfer
```

Prediction: the receiver is permitted to proceed while the payload can still be
in flight. The run may fail, hang, produce incorrect data, or pass under a benign
schedule. In every case the protocol is incorrect because `ARRIVED` no longer
implies completed bytes. Record the outcome, then restore the file:

```bash
git restore --source=HEAD -- \
  tt_metal/programming_examples/NoC_tile_transfer/kernels/dataflow/writer0.cpp
```

If you instrument the experiment, compare four runs: correct/broken × printing
off/on. This small matrix reveals observer effects without confusing them with a
repair.

## Questions and expert answers

### 1. Why signal destination readiness before sending?

???+ note "Expert answer — reasoning"
    The sender cannot infer remote CB capacity from its own state. The receiver
    reserves a page, then converts that fact into a permission signal. This avoids
    overwriting remote L1 that is unallocated or still owned by a previous
    consumer.

### 2. Why must arrival follow the NoC write barrier?

???+ note "Expert answer — reasoning"
    Arrival is the receiver's authorization to treat bytes as initialized. An
    asynchronous write being issued is not completion. Placing the signal after
    the barrier gives the control event a precise meaning; moving it earlier
    severs the happens-before edge between payload and publication.

### 3. How do you locate a hang without treating the last print as the cause?

???+ note "Expert answer — reasoning"
    Map every wait to the peer event that can satisfy it, then inspect which peers
    reached their preceding waypoints or stack locations. The last print proves
    only that its producer reached that observation point. The cause can be an
    earlier missing publication, a wrong coordinate/address, or a peer that never
    received capacity.

## Completion gate

Provide the baseline result, an eight-event causal chain, the controlled diff and
four-run observation matrix, and one sentence each for semaphore meaning, NoC
completion, and CB ownership.

**Next:** [Lab 6 — a two-chip virtual mesh](lab-06-mesh-multichip.md) ·
[Course index](index.md)
