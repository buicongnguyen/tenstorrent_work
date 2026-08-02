# Setup — TT-Metal plus ttsim on Windows WSL2 Ubuntu 22.04

<p class="source-note">
<strong>Official setup sources:</strong>
<a href="https://github.com/tenstorrent/ttsim/blob/v1.9.7/README.md">ttsim README at v1.9.7</a>,
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/INSTALLING.md">TT-Metal installation guide at the course commit</a>, and
<a href="https://github.com/tenstorrent/tt-metal/blob/5611c4891b55eb883bd050fa197b3ee9bac80475/tt_metal/tt-llk/tests/ttsim-version">official simulator version pin</a>
· <strong>Platform contract:</strong> Linux x86-64; WSL2 Ubuntu 22.04
</p>

The shortest reliable route is the direct shared-library path:

```text
Windows host
  → WSL2 Ubuntu process
  → TT-Metal host runtime
  → libttsim_wh.so
  → virtual Wormhole SoC
  → BRISC/TRISC/Tensix execution
```

This route does **not** emulate a PCI device and does not require `tt-kmd`,
firmware, `/dev/tenstorrent`, PCI passthrough, or a virtual IOMMU. Those belong
to real hardware or the separate, advanced QEMU bridge. Start with the direct
library because it removes the driver stack from the first learning experiment.

## 1. Verify the WSL boundary

In Windows PowerShell:

```powershell
wsl --update
wsl --list --verbose
```

The Ubuntu row must report version `2`. Then open Ubuntu and record:

```bash
cat /etc/os-release | grep -E '^(NAME|VERSION)='
uname -m
```

Use the ordinary release assets when `uname -m` is `x86_64`. On an ARM Windows
machine reporting `aarch64`, use simulator filenames with `_aarch64` before
`.so`. The simulator's ABI documentation lists Ubuntu 22.04 and 24.04 on both
architectures as continuously tested platforms.

Keep the source under `~/tt-metal`, not `/mnt/c/...`. The Linux filesystem avoids
the cross-filesystem metadata cost that can make a large C++ build unnecessarily
slow under WSL.

## 2. Clone the reproducible TT-Metal revision

```bash
sudo apt update
sudo apt install -y git git-lfs wget curl ca-certificates
git lfs install

git clone --recurse-submodules \
  https://github.com/tenstorrent/tt-metal.git \
  ~/tt-metal

cd ~/tt-metal
git checkout 5611c4891b55eb883bd050fa197b3ee9bac80475
git submodule update --init --recursive
git status --short
```

`git status --short` should be empty. Record the commit:

```bash
git rev-parse HEAD
```

Pinning matters because TT-Metal host APIs, firmware interfaces, examples, and
the simulator integration evolve together. “It worked on main” is not enough
information to reproduce a failure a week later.

## 3. Install dependencies and build

```bash
cd ~/tt-metal
sudo ./install_dependencies.sh
./build_metal.sh
```

The initial checkout is several gigabytes and the first build can take tens of
minutes. A later incremental build can use:

```bash
./build_metal.sh --enable-ccache
```

For the C++ labs, a successful Metal build is sufficient. For TT-NN Python work
and Lab 6, also create and activate the repository environment:

```bash
cd ~/tt-metal
./create_venv.sh
source python_env/bin/activate

export TT_METAL_HOME=~/tt-metal
export PYTHONPATH="$TT_METAL_HOME:${PYTHONPATH:-}"
```

Ubuntu 22.04 receives an automatic wheel pin from `create_venv.sh`; do not add a
second ad-hoc Python environment until the repository environment works.

## 4. Download the simulator and verify its identity

Use the version that TT-Metal pins, even if the ttsim release page shows a newer
tag:

```bash
mkdir -p ~/sim/1.9.7/wormhole

curl -fL --retry 5 \
  https://github.com/tenstorrent/ttsim/releases/download/v1.9.7/libttsim_wh.so \
  -o ~/sim/1.9.7/wormhole/libttsim_wh.so

echo "0ccad3b68be8f2340f5c0bfcebf8ceec7f3edbbb11f66dda01e43c35a05d92b7  $HOME/sim/1.9.7/wormhole/libttsim_wh.so" \
  | sha256sum --check

cp ~/tt-metal/tt_metal/soc_descriptors/wormhole_b0_80_arch.yaml \
  ~/sim/1.9.7/wormhole/soc_descriptor.yaml
```

Expected checksum output:

```text
/home/<user>/sim/1.9.7/wormhole/libttsim_wh.so: OK
```

The descriptor must be named `soc_descriptor.yaml` and live beside the `.so`.
The runtime derives the descriptor location from the simulator-library path;
putting the correct file elsewhere does not satisfy that contract.

## 5. Select the virtual device

```bash
source ~/tt-metal/python_env/bin/activate 2>/dev/null || true

export TT_METAL_HOME=~/tt-metal
export PYTHONPATH="$TT_METAL_HOME:${PYTHONPATH:-}"
export TT_METAL_SIMULATOR=~/sim/1.9.7/wormhole/libttsim_wh.so
export TT_METAL_SLOW_DISPATCH_MODE=1
export TT_METAL_DISABLE_SFPLOADMACRO=1
```

These variables make three distinct decisions:

| Variable | Decision | Why the course fixes it |
|---|---|---|
| `TT_METAL_SIMULATOR` | route UMD/Metal device access to the shared library | selects virtual silicon rather than `/dev/tenstorrent` |
| `TT_METAL_SLOW_DISPATCH_MODE=1` | use the direct, easier-to-reason-about dispatch path | current simulator Fast Dispatch is not sufficiently characterized for a baseline |
| `TT_METAL_DISABLE_SFPLOADMACRO=1` | avoid an unsupported SFPU macro path | prevents a known simulator limitation from masquerading as a lab bug |

## 6. Run the smoke test

```bash
cd ~/tt-metal
./build/programming_examples/metal_example_add_2_integers_in_riscv
```

Expected result:

```text
Success: Result is 21
```

Do not treat this as merely “the simulator installed.” The result establishes a
chain: the host opened a virtual device, constructed a program, loaded a BRISC
kernel, passed runtime arguments, advanced the virtual machine, and read back the
kernel's effect.

## Troubleshooting by boundary

| Symptom | Boundary to inspect | First check |
|---|---|---|
| `.so: cannot open shared object file` | WSL filesystem/path | `test -f "$TT_METAL_SIMULATOR"` and `uname -m` |
| missing `soc_descriptor.yaml` | simulator configuration | `ls -l "$(dirname "$TT_METAL_SIMULATOR")"` |
| checksum mismatch | downloaded artifact | delete only that `.so`, download again, and do not continue |
| executable missing | TT-Metal build | confirm commit, submodules, and successful `build_metal.sh` |
| `UnimplementedFunctionality` | simulator feature coverage | read the complete category/message before changing the kernel |
| process exits instead of throwing | simulator contract | `libttsim` reports fatal contract violations with process termination; isolate experiments |

## Questions and expert answers

### 1. Why is the SoC descriptor part of correctness rather than convenience?

???+ note "Expert answer — reasoning"
    The library models execution units, memories, coordinates, and routing, while
    TT-Metal needs a matching topology description to construct addresses and
    programs. If the descriptor names a different architecture or grid, host-side
    placement and simulator-side interpretation disagree. A successfully loaded
    `.so` does not repair that split contract.

### 2. Why begin with Slow Dispatch if Fast Dispatch is an important optimization?

???+ note "Expert answer — reasoning"
    Slow Dispatch removes device-side command-queue machinery from the first
    proof. That leaves a shorter causal path from the host call to kernel
    execution. After functional invariants are understood, Fast Dispatch can be
    a separate experiment. Mixing it into setup makes a dispatch problem look
    like a kernel or installation problem and cannot teach real silicon timing.

### 3. What does a matching checksum prove—and what does it not prove?

???+ note "Expert answer — reasoning"
    It proves that the downloaded bytes match the artifact TT-Metal's regression
    pin identifies. It does not prove the host build is at the intended commit,
    that the descriptor matches, or that a selected example is implemented. The
    complete reproducibility tuple is TT-Metal commit, submodule state, simulator
    version/hash, descriptor, environment, and command.

## Completion gate

Record all of the following before continuing:

- WSL version and `uname -m`;
- TT-Metal commit `5611c489...`;
- simulator checksum `0ccad3b...`;
- the exact smoke-test command;
- `Success: Result is 21`;
- one sentence explaining why no Tenstorrent kernel driver was involved.

**Next:** [Lab 1 — host to Baby RISC-V dispatch](lab-01-riscv-dispatch.md) ·
[Course index](index.md)
