# Lab 4 — Distinguish L1 reuse from NoC multicast

<p class="source-note">
<strong>Run this exact source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/matmul/matmul_single_core/matmul_single_core.cpp">single-core matmul</a>,
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/matmul/matmul_multicore_reuse/matmul_multicore_reuse.cpp">multicore reuse</a>, and
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/matmul/matmul_multicore_reuse_mcast/matmul_multicore_reuse_mcast.cpp">multicore reuse plus multicast</a>
· <strong>Original report:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md">pinned technical report</a>
</p>

**Learner pair:** [architecture analysis](../../rewrites/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md)

Matrix multiplication exposes why “reduce data movement” is too vague to guide
an implementation. A tile can be reused **temporally** by keeping it in a core's
L1 across several products, or **spatially** by injecting it into the NoC once and
multicasting it to several cores. Those optimizations remove different traffic
and introduce different constraints.

## Write the traffic model first

For tiled `C = A × B`, output tile `C[m,n]` accumulates products over `k`:

```text
C[m,n] = Σk A[m,k] × B[k,n]
```

Suppose a block computes `R × C` output tiles for `K` reduction steps. Complete
this symbolic ledger from the pinned source's loop nest:

| Operand | Naive independent consumers | With local reuse | With multicast |
|---|---:|---:|---:|
| A tile reads/injections | `R × C × K` | depends on which output columns share A in one core | one source injection can feed a receiver set |
| B tile reads/injections | `R × C × K` | depends on which output rows share B in one core | one source injection can feed a receiver set |
| C writes | `R × C` | `R × C` | `R × C` |

Do not replace the symbolic terms with guessed hardware dimensions. Read `Mt`,
`Nt`, `Kt`, core-grid construction, block sizes, and sender/receiver roles from
the exact example, then instantiate the table for its compiled problem.

## Run the baseline

```bash
cd ~/tt-metal
export TT_METAL_SIMULATOR=~/sim/1.9.7/wormhole/libttsim_wh.so
export TT_METAL_SLOW_DISPATCH_MODE=1
export TT_METAL_DISABLE_SFPLOADMACRO=1

./build/programming_examples/metal_example_matmul_single_core
./build/programming_examples/metal_example_matmul_multicore_reuse
./build/programming_examples/metal_example_matmul_multicore_reuse_mcast
```

The multicast target at this revision is compiled with `TT_METAL_CI_MODE` to keep
its validation problem smaller. Record each program's own shape and correctness
result; do not compare raw wall-clock duration across unlike shapes.

Extract source evidence with:

```bash
rg -n "Mt|Nt|Kt|per_core|block|mcast|semaphore|noc_async_(read|write)" \
  tt_metal/programming_examples/matmul/matmul_single_core \
  tt_metal/programming_examples/matmul/matmul_multicore_reuse \
  tt_metal/programming_examples/matmul/matmul_multicore_reuse_mcast
```

## Architecture walkthrough

Local reuse asks: once a tile reaches a core, how many multiply-accumulate steps
can consume it before its L1 page is returned? Longer residence amortizes a DRAM
read but consumes L1 capacity and may delay the producer. Blocking is therefore
a balance among reuse distance, CB capacity, tile-register pressure, and enough
buffering to overlap the next transfer.

Multicast asks a different question: when several cores need identical bytes,
how many independent NoC injections should occur? A sender can distribute one
operand to a receiver rectangle, reducing source-side reads and injection load.
The receivers need agreed addresses, capacity, and a synchronization protocol so
no core consumes before delivery or reuses storage early. Multicast saves
redundant movement at the price of coordination and topology constraints.

The two mechanisms compose because they attack two axes. Multicast moves a tile
to many consumers once; local reuse lets each consumer use its received tile
multiple times. An architecture review should therefore ask both “how many
destinations?” and “how many uses per destination?”

The benefit is bandwidth amplification: more math is performed per DRAM byte and
per NoC injection. The failure mode is imbalance. A sender or slow receiver can
hold the cohort, an oversized block can exhaust L1, and a geometrically convenient
receiver set may not match the mathematical partition. Optimization is a mapping
problem with correctness invariants, not an API checkbox.

## Controlled experiment

This experiment is source-accounting rather than timing. For each executable,
record the following from the actual compiled constants and kernel loops:

```text
problem Mt × Nt × Kt:
worker cores:
A tiles fetched from DRAM:
B tiles fetched from DRAM:
unique source injections:
receiver deliveries:
output tiles written:
bytes = tile count × tile_size:
```

Then change one blocking constant in a disposable branch while keeping the
overall matrix shape valid and divisible. Rebuild only that target and predict
which counts change:

```bash
git switch -c lab/matmul-blocking
cmake --build build --target metal_example_matmul_multicore_reuse -j2
timeout 120s ./build/programming_examples/metal_example_matmul_multicore_reuse
```

If divisibility, CB capacity, or work partition assertions reject the edit, that
is architectural evidence: the blocked schedule is part of the program contract.
Restore the change after recording it. Do not report a speedup from simulator
wall time; `ttsim` explicitly does not model real-time device performance.

## Questions and expert answers

### 1. Why are reuse and multicast not synonyms?

???+ note "Expert answer — reasoning"
    Reuse reduces repeated fetches across time at one consumer; multicast reduces
    repeated injections across space for several consumers. A tile may be
    multicast once and still discarded after one local use, or fetched separately
    by every core and reused many times locally. Their traffic ledgers differ.

### 2. Why not maximize block size to maximize reuse?

???+ note "Expert answer — reasoning"
    A larger block increases live tiles and partial sums. That consumes L1 and
    registers, can reduce double-buffering, raises synchronization granularity,
    and may leave fewer independent blocks for load balance. The optimum is where
    saved movement still permits a full, overlapping pipeline.

### 3. Why is simulator elapsed time invalid performance evidence here?

???+ note "Expert answer — reasoning"
    The official simulator targets functional and architectural behavior; its
    host execution costs and modeled timing are not silicon cycle costs. It can
    prove that a mapped reuse/multicast program produces correct results and
    obeys supported contracts. Real throughput, contention, dispatch overhead,
    and power require counters and measurements on hardware.

## Completion gate

Provide correctness results for all three programs, an instantiated traffic
ledger with source locations, one controlled blocking observation, and a concise
explanation of temporal reuse versus spatial distribution.

**Next:** [Lab 5 — debugging synchronization](lab-05-debugging-synchronization.md) ·
[Course index](index.md)
