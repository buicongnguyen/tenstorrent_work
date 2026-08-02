# Lab 1 — Trace host dispatch to one Baby RISC-V

<p class="source-note">
<strong>Run this exact source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/add_2_integers_in_riscv/add_2_integers_in_riscv.cpp">host program</a> and
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/programming_examples/add_2_integers_in_riscv/kernels/reader_writer_add_in_riscv.cpp">BRISC kernel</a>
at <code>tt-metal@5611c489</code> ·
<a href="https://github.com/tenstorrent/ttsim/blob/v1.9.7/docs/libttsim_api.md">simulator ABI at v1.9.7</a>
</p>

**Local prerequisite:** [course setup](setup-wsl2.md)

The integer addition is deliberately uninteresting. Its value is that almost all
of the machinery around the addition remains visible: a host process opens a
device, creates storage, installs a kernel on one Tensix core, sends addresses as
runtime arguments, submits work, and reads the result. The lab therefore answers
a more useful question than “can the simulator add?”: **which contracts must hold
before one RISC-V instruction can affect host-visible memory?**

## Predict the control and data path

Before running, copy this trace into your lab record and fill in the missing
ownership column:

| Phase | Object or event | Owner before | Owner after | Completion evidence |
|---|---|---|---|---|
| host construction | `MeshDevice`, workload, program | host | host | C++ calls return |
| input transfer | two `uint32_t` values | host | device DRAM | queued write completes in FIFO order |
| kernel read | DRAM addresses passed as runtime arguments | DRAM | BRISC-local L1 destination | NoC read barrier |
| arithmetic | `14 + 7` | BRISC | BRISC | RISC-V instruction retires |
| kernel write | result in L1 | BRISC/L1 | result DRAM buffer | RISC-V-to-L1 ordering plus NoC write barrier |
| readback | result buffer | device DRAM | host vector | blocking queue read |

The key architectural separation is between **naming** a buffer and **completing**
a transfer. A runtime argument can give BRISC the correct DRAM address while the
data at that address is not yet ready. Queue ordering, NoC barriers, and processor
memory ordering close different parts of that gap.

## Run the baseline

Use the environment established during setup:

```bash
cd ~/tt-metal
export TT_METAL_SIMULATOR=~/sim/1.9.7/wormhole/libttsim_wh.so
export TT_METAL_SLOW_DISPATCH_MODE=1
export TT_METAL_DISABLE_SFPLOADMACRO=1

./build/programming_examples/metal_example_add_2_integers_in_riscv
```

Expected terminal evidence:

```text
Success: Result is 21
```

Now read the two pinned source files from the source note. Locate these six host
actions in order: device creation, DRAM/L1 buffer creation, kernel creation,
runtime-argument assignment, workload enqueue, and blocking readback. Then locate
the kernel's DRAM-to-L1 reads, integer addition, ordering operation, and
L1-to-DRAM write. Record line links rather than paraphrasing the whole files.

## Architecture walkthrough

The host describes a program; it does not execute the device kernel one C++ call
at a time. `CreateKernel` associates compiled code and a processor placement with
a `Program`. Runtime arguments specialize that program instance with addresses.
Enqueueing the workload makes the previously described graph executable.

On the core, BRISC is both the data-movement processor and the arithmetic
processor for this intentionally small example. It issues asynchronous NoC reads,
then waits at the read barrier before dereferencing the L1 destination. That
barrier is not general ceremony: without it, the arithmetic could observe an old
L1 value while the network transaction is still outstanding.

After the RISC-V store writes the sum into L1, the kernel uses an ordering step
before asking the NoC engine to read that L1 location. This is a second dependency
at a different boundary. A NoC write barrier later establishes completion of the
outbound transfer before the kernel finishes. Finally, the host's blocking read
returns the DRAM result. Four memories or agents are involved even though only
one addition is visible in the algorithm.

This is why explicit dataflow can be fast: hardware can overlap independent
transactions because software says exactly where completion is required. The
same design is also unforgiving—an address, ownership transition, or barrier in
the wrong place violates correctness rather than merely losing performance.

## Controlled experiment

Make a disposable branch inside your WSL checkout, then change only the two host
input values and its expected result. Do not change runtime-argument order or
buffer placement yet.

```bash
cd ~/tt-metal
git switch -c lab/riscv-values
rg -n "14|7|21" tt_metal/programming_examples/add_2_integers_in_riscv
```

For example, use `40`, `2`, and expected result `42`. Rebuild and rerun:

```bash
cmake --build build --target metal_example_add_2_integers_in_riscv -j2
./build/programming_examples/metal_example_add_2_integers_in_riscv
```

Prediction: only payload values and final output change. Device placement,
runtime-argument roles, number of NoC transfers, and synchronization edges stay
constant. If any of those structural facts appears to change, your source edit
was wider than the experiment.

## Questions and expert answers

### 1. Why pass addresses as runtime arguments instead of compiling them into the kernel?

???+ note "Expert answer — reasoning"
    Code and placement can be reused while buffers vary between invocations.
    Compilation captures the stable mechanism; runtime arguments capture
    per-dispatch bindings. This reduces specialization cost and is a prerequisite
    for program reuse and caching. Correctness still requires the host and kernel
    to agree on argument index, address space, size, and lifetime.

### 2. Why are both a processor-ordering step and a NoC write barrier needed?

???+ note "Expert answer — reasoning"
    They order different producers. The first makes the RISC-V store visible to
    the L1/NoC consumer; the second waits until the network transfer reaches its
    completion point. A network barrier cannot retroactively guarantee that its
    source load saw the processor's newest store, and processor ordering does not
    prove that a packet reached DRAM.

### 3. What does `Success: Result is 21` actually prove?

???+ note "Expert answer — reasoning"
    For this execution it proves that device construction, kernel loading,
    argument binding, data movement, arithmetic, and readback composed to produce
    the expected value in the functional model. It does not measure dispatch
    latency, NoC bandwidth, overlap, power, or real-device firmware behavior.
    Those claims require separate evidence.

## Completion gate

Your record must contain the six host actions, the four completion/ordering
points, baseline output, changed-value output, and one paragraph distinguishing
an address binding from a completed transfer.

**Next:** [Lab 2 — compute kernels and circular-buffer ownership](lab-02-compute-circular-buffers.md) ·
[Course index](index.md)
