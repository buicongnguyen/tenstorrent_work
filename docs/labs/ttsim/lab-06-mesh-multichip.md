# Lab 6 — Shard one tensor across a two-chip virtual mesh

<p class="source-note">
<strong>Official executable source:</strong>
<a href="https://docs.tenstorrent.com/tt-vscode-toolkit/lessons/ttsim-twenty-and-ten/#one-more-thing">ttsim N300 mesh lesson</a>,
<a href="https://github.com/tenstorrent/ttsim/releases/tag/v1.9.7"><code>ttsim v1.9.7</code> dual-Wormhole asset</a>, and the
<a href="https://github.com/tenstorrent/tt-umd/blob/ef7aa4b9dace8c75344f32886cfc7f31372cb2d1/tests/cluster_descriptor_examples/wormhole_N300.yaml">N300 cluster descriptor at TT-Metal's pinned UMD revision</a>
</p>

**Learner references:** [TT-NN mesh programming](../../rewrites/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md)
and [Ethernet multichip](../../rewrites/EthernetMultichip/BasicEthernetGuide.md).

A mesh introduces three independent descriptions that happen to align in a simple
N300 exercise: logical mesh coordinates, tensor shard placement, and physical
chip connectivity. Treating them as one concept works until a topology changes or
an operator needs a different distribution. This lab forces each description into
the record.

## Install the pinned two-chip model

```bash
mkdir -p ~/sim/1.9.7/wormhole-x2

curl -fL --retry 5 \
  https://github.com/tenstorrent/ttsim/releases/download/v1.9.7/libttsim_wh_x2.so \
  -o ~/sim/1.9.7/wormhole-x2/libttsim_wh_x2.so

echo "0fc0f3c6cbc488fc560d88c3d43d3fd979998c1d30e565a60389885c60dc583d  $HOME/sim/1.9.7/wormhole-x2/libttsim_wh_x2.so" \
  | sha256sum --check

cp ~/tt-metal/tt_metal/soc_descriptors/wormhole_b0_80_arch.yaml \
  ~/sim/1.9.7/wormhole-x2/soc_descriptor.yaml
```

Select the simulator and the matching cluster description:

```bash
source ~/tt-metal/python_env/bin/activate
export TT_METAL_HOME=~/tt-metal
export PYTHONPATH="$TT_METAL_HOME:${PYTHONPATH:-}"
export TT_METAL_SIMULATOR=~/sim/1.9.7/wormhole-x2/libttsim_wh_x2.so
export TT_METAL_MOCK_CLUSTER_DESC_PATH=\
$TT_METAL_HOME/tt_metal/third_party/umd/tests/cluster_descriptor_examples/wormhole_N300.yaml
export TT_METAL_SLOW_DISPATCH_MODE=1
export TT_METAL_DISABLE_SFPLOADMACRO=1
```

The SoC descriptor describes one Wormhole chip; the cluster descriptor says how
two such chips and host channels form the N300 system. The shared library supplies
the two modeled devices. All three must describe the same virtual system.

## Run the baseline

Create a self-contained script from the official lesson:

```bash
mkdir -p ~/ttsim-labs
cat > ~/ttsim-labs/lab6_mesh.py <<'PY'
import torch
import ttnn

torch.manual_seed(7)
mesh = ttnn.open_mesh_device(ttnn.MeshShape(1, 2))
print("opened:", mesh)

a = torch.randn(64, 64, dtype=torch.bfloat16)
b = torch.randn(64, 64, dtype=torch.bfloat16)

mapper = ttnn.ShardTensorToMesh(mesh, dim=0)
a_mesh = ttnn.from_torch(a, layout=ttnn.TILE_LAYOUT, device=mesh, mesh_mapper=mapper)
b_mesh = ttnn.from_torch(b, layout=ttnn.TILE_LAYOUT, device=mesh, mesh_mapper=mapper)

c_mesh = ttnn.add(a_mesh, b_mesh)
c = ttnn.to_torch(c_mesh, mesh_composer=ttnn.ConcatMeshToTensor(mesh, dim=0))
reference = a + b
max_error = (c - reference).abs().max().item()
print("output shape:", tuple(c.shape))
print("max error:", max_error)
assert c.shape == reference.shape
assert max_error <= 0.05
ttnn.close_mesh_device(mesh)
print("PASS: two-chip sharded add")
PY

python ~/ttsim-labs/lab6_mesh.py
```

Record the mesh print, output shape, maximum error, and pass line. The official
lesson reports the same 1×2 mesh pattern and concatenates shards along dimension
zero; follow its current result if its tested tolerance changes.

## Architecture walkthrough

`MeshShape(1, 2)` requests two logical device coordinates. The cluster descriptor
maps discovered chip identities and connectivity into that system. Neither choice
yet says how a tensor is divided.

`ShardTensorToMesh(mesh, dim=0)` supplies that missing data-placement policy. For
a 64×64 tensor, the first 32 rows belong to one device and the second 32 to the
other. `ttnn.add` is shard-local because aligned shards of `a` and `b` contain all
operands needed for each output element. No cross-chip reduction is mathematically
required. `ConcatMeshToTensor(..., dim=0)` defines the inverse host reconstruction.

The main invariant is alignment: corresponding shards of both operands must use
the same logical mapping, and the composer must invert that mapping. If `a` is
sharded by rows while `b` is replicated or sharded by columns, `add` requires a
different distribution contract. A mesh API cannot infer mathematical intent
from shape alone.

This distinction prepares you for expensive operators. A row-sharded elementwise
add is embarrassingly local. Matmul may need one operand replicated, multicast,
or communicated; an all-reduce deliberately combines partial results. Physical
Ethernet routes then affect performance, but the logical tensor contract must be
correct before route optimization matters.

## Controlled experiment

First test configuration causality without changing data. In the same terminal:

```bash
unset TT_METAL_MOCK_CLUSTER_DESC_PATH
timeout 30s python ~/ttsim-labs/lab6_mesh.py
```

Prediction: mesh discovery/configuration fails or cannot construct the requested
1×2 system; it should not silently become a valid two-chip computation. Restore
the exact descriptor variable and rerun to recover.

Then change tensor height from 64 to an intentionally awkward value for tiling or
even sharding. Record whether rejection occurs at tilization, shard mapping, or
operator execution. The lesson is not “all dimensions must be 64”; it is to find
the first layer whose divisibility/alignment contract rejects the shape.

## Questions and expert answers

### 1. Why is mesh shape not enough to define tensor parallelism?

???+ note "Expert answer — reasoning"
    Mesh shape names available logical devices. Tensor parallelism additionally
    needs a mapping from tensor dimensions/regions to those coordinates, plus a
    rule for composing results. The same 1×2 mesh can implement row sharding,
    column sharding, replication, or pipeline stages.

### 2. Why does this add need no cross-chip reduction?

???+ note "Expert answer — reasoning"
    Each output element depends only on the matching elements of `a` and `b`.
    Aligned row shards place both inputs for a row on the same device, so each
    shard computes a complete region of the result. Concatenation gathers disjoint
    completed regions; it does not combine partial values.

### 3. What does the dual-chip simulator prove about Ethernet performance?

???+ note "Expert answer — reasoning"
    It can exercise supported functional topology, discovery, mesh placement, and
    communication protocols. It does not establish link bandwidth, contention,
    synchronization latency, thermal limits, or overlap on a physical N300. Those
    claims require hardware counters and controlled measurements.

## Completion gate

Provide the dual-library checksum, baseline output, a 1×2 ownership map naming
row ranges, the missing-descriptor observation, and separate statements for
logical mapping, tensor placement, and physical connectivity.

**Next:** [Evidence and hardware limits](evidence-and-hardware-limits.md) ·
[Course index](index.md)
