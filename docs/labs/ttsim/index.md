# Executable ttsim Labs: learn Tenstorrent by running the machine model

<p class="source-note">
<strong>Primary resources:</strong>
<a href="https://github.com/tenstorrent/ttsim"><code>tenstorrent/ttsim</code></a>,
<a href="https://github.com/tenstorrent/tt-metal"><code>tenstorrent/tt-metal</code></a>, and the
<a href="https://docs.tenstorrent.com/tt-vscode-toolkit/lessons/ttsim-twenty-and-ten/">official ttsim exercise collection</a>
· <strong>Course pin:</strong>
<a href="https://github.com/tenstorrent/tt-metal/tree/5611c4891b55eb883bd050fa197b3ee9bac80475"><code>tt-metal@5611c489</code></a>
+ <a href="https://github.com/tenstorrent/ttsim/releases/tag/v1.9.7"><code>ttsim v1.9.7</code></a>
· <strong>Checked:</strong> 2026-08-02
</p>

This course turns the Atlas from reading material into an executable architecture
workbook. The simulator is not used as a black box that merely prints `PASS`.
Each lab asks you to predict one ownership transition, run the smallest program
that exposes it, inspect the exact host and kernel sources, perturb one condition,
and explain the resulting observation.

The result is a tighter learning loop:

`read the contract → predict the flow → run it → perturb it → explain the evidence`

That loop is valuable because Tenstorrent performance and correctness emerge from
explicit choices—where a tile lives, which RISC owns a stage, when a circular
buffer page becomes visible, and which barrier establishes completion. A simulator
lets you exercise those choices before you own a card.

## Why this course uses `tenstorrent/ttsim`

Two similarly named projects exist:

| Project | Best use | Boundary |
|---|---|---|
| [`tenstorrent/ttsim`](https://github.com/tenstorrent/ttsim) | Run current TT-Metal, TT-NN, LLK, Wormhole, and Blackhole paths against Tenstorrent's official functional model | Slower than silicon; real-time performance is not modeled |
| [`mesham/tt-sim`](https://github.com/mesham/tt-sim) | Read and modify an approachable Python implementation derived from public ISA material; inspect instruction/state tracing | Community work in progress with a smaller modeled system; not the course execution target |

Use official `ttsim` for the labs. Read the community simulator later when you want
to study how somebody might implement a simulator from the published ISA.

## Reproducibility contract

The course does not follow two moving `main` branches blindly. At the checked
TT-Metal commit, the in-tree
[`ttsim-version`](https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/tt-llk/tests/ttsim-version)
file pins `ttsim` 1.9.7 and records these release hashes:

| Simulator | SHA-256 |
|---|---|
| `libttsim_wh.so` | `0ccad3b68be8f2340f5c0bfcebf8ceec7f3edbbb11f66dda01e43c35a05d92b7` |
| `libttsim_bh.so` | `4b69813eeb123b580474a6e4b48dfff2c4c684ac53935800d2a3025ed3fdda94` |

The latest simulator may be newer. Do not upgrade only one side in the middle of
the course. Finish the pinned labs first, then create a separate compatibility
experiment where you change the simulator version and record the difference.

## Course map

| Step | Executable question | Main mechanism | Evidence you must produce |
|---|---|---|---|
| [Setup](setup-wsl2.md) | Can WSL2 load the simulator through TT-Metal without a device driver? | `TT_METAL_SIMULATOR`, SoC descriptor, slow dispatch | version record, hash check, first successful BRISC result |
| [Lab 1](lab-01-riscv-dispatch.md) | What does the host construct before one Baby RISC-V can add two integers? | device/program/kernel/runtime arguments | host-to-BRISC control-flow trace |
| [Lab 2](lab-02-compute-circular-buffers.md) | How do reader, compute, and writer stages exchange ownership? | circular buffers, barriers, TRISC | page-state table and one predicted failure |
| [Lab 3](lab-03-sfpu-special-values.md) | What is preserved when SFPU operations are chained, and how are exceptional values observed? | tile registers, SFPU, pack/unpack, sticky status | numerical comparison plus observation-boundary explanation |
| [Lab 4](lab-04-matmul-reuse-noc.md) | Why do reuse and multicast reduce different traffic? | L1 residence, NoC injection, matmul work split | tile/byte accounting before and after reuse |
| [Lab 5](lab-05-debugging-synchronization.md) | Can you distinguish data completion, ownership publication, and instrumentation effects? | DPRINT, Watcher, NoC barriers, semaphores | causal event chain and corrected synchronization bug |
| [Lab 6](lab-06-mesh-multichip.md) | Which single-device assumptions break when the program becomes a mesh? | `MeshDevice`, sharding, cluster descriptor, Ethernet/fabric | logical-to-physical ownership map |
| [Limits](evidence-and-hardware-limits.md) | Which conclusions survive contact with real hardware? | functional fidelity versus timing | simulator-valid/hardware-required claim ledger |

Do the labs in order. Lab 4 assumes you can already state a circular-buffer
ownership invariant; Lab 6 assumes you can distinguish a tensor's logical shard
from the physical route used to move it.

## The lab record you should keep

Create one Markdown record per run. Do not record only the final terminal output.

```text
Lab and date:
TT-Metal commit:
ttsim version and SHA-256:
WSL distribution and uname -m:
Command:
Prediction:
Observed output:
First surprising event:
Invariant checked:
One controlled change:
Result of the change:
What the evidence proves:
What it does not prove:
```

This record is interview preparation as well as debugging discipline. It forces
you to separate an architectural contract from a plausible story.

## The three evidence planes

Every lab must close all three planes:

1. **Source plane:** point to the host program, device kernel, API or ISA page that
   defines the mechanism.
2. **Execution plane:** show the command and observation that prove the selected
   path actually ran.
3. **Reasoning plane:** state the ownership/completion invariant and explain why
   the observation follows from it.

A `PASS` message closes only part of the execution plane. Reading a source file
closes only part of the source plane. The architecture becomes useful when the
three agree.

## Start here

Continue to [WSL2 setup and reproducible environment](setup-wsl2.md). Do not move
to Lab 1 until the smoke test prints the expected result and your simulator hash
matches the course pin.
