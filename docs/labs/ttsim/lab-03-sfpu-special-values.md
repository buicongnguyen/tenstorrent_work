# Lab 3 — SFPU fusion, register lifetime, and special values

<p class="source-note">
<strong>Run this exact source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/eltwise_sfpu/eltwise_sfpu.cpp">single-operation host</a>,
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/eltwise_sfpu/kernels/compute/eltwise_sfpu.cpp">single-operation compute kernel</a>,
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.cpp">chained host</a>, and
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/sfpu_eltwise_chain/kernels/compute/compute.cpp">chained compute kernel</a>
</p>

**Learner reference:** [special values and sticky status](../../rewrites/Handling_Special_Value/special_values.md)

The SFPU path is where “one operator” stops being a complete architectural unit.
An implementation can unpack a tile, keep it in destination registers, apply
several elementwise transforms, and pack once. That removes intermediate
circular-buffer traffic, but it also changes where rounding and exceptional
values can be observed. This lab studies both sides of that choice.

## Build the register-lifetime hypothesis

The chained example implements a softplus-shaped expression:

```text
input tile → exp → add a tile of ones → log → output tile
```

Read the pinned compute kernel before running. Mark the first tile-register
acquire and the final release. Then answer: how many times is the evolving value
packed to a CB between `exp`, add, and `log`? Your prediction should be zero. The
intermediate value remains in the compute register domain.

The optimization is not “three instructions are faster than three operators.”
It is elimination of two materialization boundaries. A non-fused design could
pack after `exp`, publish an output CB, let another stage consume it, and repeat
after add. Fusion avoids those ownership changes, L1 pages, and pack/unpack work.

## Run the baseline

```bash
cd ~/tt-metal
export TT_METAL_SIMULATOR=~/sim/1.9.7/wormhole/libttsim_wh.so
export TT_METAL_SLOW_DISPATCH_MODE=1
export TT_METAL_DISABLE_SFPLOADMACRO=1

./build/programming_examples/metal_example_eltwise_sfpu
./build/programming_examples/metal_example_sfpu_eltwise_chain
```

Record both correctness reports. Then collect the source evidence:

```bash
rg -n "tile_regs|exp_tile|add_tiles|log_tile|pack_tile|cb_(wait|push|pop|reserve)" \
  tt_metal/programming_examples/eltwise_sfpu \
  tt_metal/programming_examples/sfpu_eltwise_chain
```

Create a register-lifetime diagram with an acquire at the left, release at the
right, and every SFPU/math operation between them. Add separate markers for
input-pop and output-push. This makes clear that register lifetime and CB
ownership are related but not identical.

## Architecture walkthrough

Unpack translates a tile from its L1 representation into the compute engine's
working register form. Math and SFPU operations transform that register state.
Pack converts the final state into the selected output data format and writes an
L1-backed CB page. Each crossing has synchronization and often conversion cost.

Keeping a chain inside one acquire/commit/wait/release interval therefore improves
locality and removes intermediate producer-consumer protocols. It can also expose
a larger live range, increase register pressure, and make a long dependency chain
harder to overlap. Fusion is a resource trade, not a universal commandment.

Numerical behavior needs a separate argument. The direct expression
`log(exp(x) + 1)` is mathematically softplus, but a large positive `x` can make
the intermediate `exp(x)` overflow in finite precision even when the final
mathematical result is close to `x`. A numerically stable formulation changes
the algorithm around that range. Avoiding an intermediate pack removes one
rounding boundary; it does not by itself make an unstable formula stable.

Exceptional-status reporting has yet another lifetime. The status described in
the learner reference is sticky across qualifying SFPU work until software clears
or reports it at the appropriate epoch boundary. That is useful because lanes can
execute in parallel and a single per-value trap would serialize the design. The
program must therefore define the observation epoch: clear before the region,
run the region, read/report after its completion, then attribute the flag to that
region—not to an individual lane without more evidence.

## Controlled experiment

Use a disposable branch and extend the chained example's input set with a few
classes rather than random values:

| Input class | Example intent | Prediction for direct `log(exp(x)+1)` |
|---|---|---|
| moderate negative | well below zero | small positive output |
| near zero | transition region | near `log(2)` |
| moderate positive | linear-looking region | near input |
| very large positive | stress intermediate range | possible overflow/Inf or tolerance failure |

Locate the host initializer and golden comparison instead of copying an offset
from an unpinned tutorial:

```bash
cd ~/tt-metal
git switch -c lab/sfpu-ranges
rg -n "input|golden|allclose|softplus|exp|log" \
  tt_metal/programming_examples/sfpu_eltwise_chain
cmake --build build --target metal_example_sfpu_eltwise_chain -j2
./build/programming_examples/metal_example_sfpu_eltwise_chain
```

Record exact values, output classification (`finite`, `Inf`, or `NaN`), and the
comparison tolerance. Do not infer a sticky-status bit solely from a floating
result; result classification and architectural status are two evidence channels.

## Questions and expert answers

### 1. Why can fusion improve performance without changing the number of mathematical operations?

???+ note "Expert answer — reasoning"
    It removes storage-domain transitions around the operations. Intermediate
    packs, L1 CB pages, publications, waits, pops, and unpacks disappear when the
    value remains in registers. The arithmetic count is unchanged, but data
    movement, synchronization, and scarce L1 consumption decrease.

### 2. Why does fusion not guarantee better numerical behavior?

???+ note "Expert answer — reasoning"
    Fewer packs can mean fewer format-conversion roundings, but the fused formula
    still creates its mathematical intermediates. `exp(x)` can overflow before
    `log` reduces the magnitude. Stability requires a range-aware formulation;
    it is independent from whether the operations share one kernel.

### 3. Why should exceptional status use a defined observation epoch?

???+ note "Expert answer — reasoning"
    A sticky flag accumulates evidence. If it is not cleared before the region or
    read only after the region completes, an old operation or an unfinished one
    can be blamed incorrectly. Clear–execute–synchronize–read turns a persistent
    bit into evidence attributable to one chosen interval.

## Completion gate

Provide the two baseline results, a register-lifetime diagram, the range-test
table with observed classifications, and separate conclusions for fusion cost,
floating-point output, and sticky-status evidence.

**Next:** [Lab 4 — matmul reuse and NoC multicast](lab-04-matmul-reuse-noc.md) ·
[Course index](index.md)
