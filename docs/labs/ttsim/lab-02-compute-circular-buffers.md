# Lab 2 — Make circular-buffer ownership explicit

<p class="source-note">
<strong>Run this exact source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/add_2_integers_in_compute/add_2_integers_in_compute.cpp">host program</a>,
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/add_2_integers_in_compute/kernels/dataflow/reader_binary_1_tile.cpp">reader</a>,
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/add_2_integers_in_compute/kernels/compute/add_2_tiles.cpp">compute</a>, and
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/add_2_integers_in_compute/kernels/dataflow/writer_1_tile.cpp">writer</a>
at <code>tt-metal@5611c489</code>
</p>

**Learner references:** [NoC and circular-buffer ownership](../../rewrites/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md)
and [tensor layout](../../rewrites/tensor_layouts/tensor_layouts.md).

Lab 1 let one BRISC perform every stage. Real Tensix programs split work among
data-movement RISC-Vs and compute RISC-Vs so transfers and arithmetic can form a
pipeline. A circular buffer (CB) is the protocol boundary between them. Its page
storage is necessary, but the decisive information is its **published occupancy**:
which pages a producer owns, which are ready for a consumer, and which have been
returned for reuse.

## State the protocol before running it

For one input tile, the legal reader sequence is:

```text
reserve_back → obtain write pointer → issue NoC read
→ NoC read barrier → push_back
```

The legal compute-to-writer sequence is:

```text
wait_front(inputs) → acquire tile registers → unpack/compute
→ commit and wait tile registers → reserve output CB
→ pack output → release tile registers → pop input CBs → push output CB
→ writer wait_front → issue NoC write → write barrier → pop_front
```

Write a prediction for each invalid reorder: publishing an input before the NoC
read barrier, reading a CB before `wait_front`, packing without output capacity,
or popping output before the NoC write barrier. “It fails” is insufficient; name
the consumer that can observe a page too early or the producer that can overwrite
a page still in use.

## Run the baseline

```bash
cd ~/tt-metal
export TT_METAL_SIMULATOR=~/sim/1.9.7/wormhole/libttsim_wh.so
export TT_METAL_SLOW_DISPATCH_MODE=1
export TT_METAL_DISABLE_SFPLOADMACRO=1

./build/programming_examples/metal_example_add_2_integers_in_compute
```

Record the expected result reported by the example. Then use source search to
build an evidence table from the pinned files:

```bash
rg -n "cb_reserve_back|cb_push_back|cb_wait_front|cb_pop_front|noc_async_.*barrier|tile_regs" \
  tt_metal/programming_examples/add_2_integers_in_compute
```

| Resource | Producer | Publication event | Consumer | Return event |
|---|---|---|---|---|
| input CB 0 | reader RISC-V | `cb_push_back` | compute RISC-V | `cb_pop_front` |
| input CB 1 | reader RISC-V | `cb_push_back` | compute RISC-V | `cb_pop_front` |
| tile registers | compute unpack/math | commit/wait | pack stage | release |
| output CB | compute/pack | `cb_push_back` | writer RISC-V | `cb_pop_front` |

## Architecture walkthrough

The design separates three kinds of state that are easy to blur together.

First, a NoC transaction has completion state. `noc_async_read` creates an
outstanding transfer; its barrier proves that bytes have arrived in L1. Second,
a circular buffer has ownership state. `cb_push_back` says a complete page may be
consumed, while `cb_pop_front` says that storage may be reused. Third, tile
registers have execution state. Acquire/commit/wait/release coordinates unpack,
math, and pack pipelines inside the compute engine.

None of those protocols replaces another. If the reader pushes before the read
barrier, the CB says “ready” while the NoC says “in flight.” If compute retains
tile registers while waiting indefinitely for output space, it can prevent the
machine from making progress. If the writer pops before its write barrier, a
producer can reuse the L1 page while the NoC engine still reads it.

The architectural benefit is decoupling. Each stage can advance when its local
contract permits, which allows transfer, compute, and writeback to overlap. A
single global barrier would be easier to describe but would erase that overlap.
The cost is that backpressure and correctness are now expressed as a distributed
state machine. Good kernel design makes that state machine visible in source.

## Controlled experiment

Use a disposable branch and violate exactly one publication edge. In the reader,
temporarily move `cb_push_back` before its `noc_async_read_barrier`. Save the
original diff so the experiment is reversible.

```bash
cd ~/tt-metal
git switch -c lab/cb-publication
git diff -- tt_metal/programming_examples/add_2_integers_in_compute
cmake --build build --target metal_example_add_2_integers_in_compute -j2
timeout 30s ./build/programming_examples/metal_example_add_2_integers_in_compute
```

Depending on the modeled schedule, the observation can be incorrect data, a
contract error, or an execution that happens to pass. A pass does **not** legalize
the reorder: it means this schedule did not expose the race. Restore the source
immediately after recording the outcome:

```bash
git restore --source=HEAD -- \
  tt_metal/programming_examples/add_2_integers_in_compute/kernels/dataflow/reader_binary_1_tile.cpp
```

The reasoning result is deterministic even if the failure manifestation is not:
publication no longer implies initialized contents, so the consumer's invariant
has been removed.

## Questions and expert answers

### 1. Why is a circular buffer more than a ring of L1 addresses?

???+ note "Expert answer — reasoning"
    The addresses hold bytes, but reserve/push/wait/pop encode distributed
    ownership and backpressure. A producer may write only reserved capacity; a
    consumer may read only published pages; storage returns to the producer only
    after pop. That protocol lets independently scheduled RISC-Vs communicate
    without a global lock.

### 2. Why publish only after the NoC read barrier?

???+ note "Expert answer — reasoning"
    `push_back` is a promise to the consumer that the page is complete. The read
    barrier is the evidence needed to make that promise true. Publishing earlier
    exposes a buffer address whose transfer may still be modifying it, turning
    pipeline overlap into a data race.

### 3. Why can larger circular buffers help throughput but not fix a bad protocol?

???+ note "Expert answer — reasoning"
    More pages absorb producer/consumer rate variation and permit more work in
    flight. They do not create missing completion edges. With early publication
    or early reuse, a larger CB merely provides more locations on which the same
    race can occur and consumes more scarce L1 capacity.

## Completion gate

Submit a four-row ownership table, the baseline output, the controlled-change
diff and observation, and a causal explanation containing all three terms:
**NoC completion**, **CB publication**, and **tile-register lifetime**.

**Next:** [Lab 3 — SFPU fusion and exceptional values](lab-03-sfpu-special-values.md) ·
[Course index](index.md)
