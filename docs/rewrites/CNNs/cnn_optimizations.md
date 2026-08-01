<!-- rewrite-status: improved-draft -->
# CNN Bring-up & Optimization in TT-NN

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/cnn_optimizations.md"><code>tech_reports/CNNs/cnn_optimizations.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The pinned report optimizes an encoder-decoder workload, where downblocks create
residual activations and upblocks later upsample and concatenate them. The architectural
problem is not simply convolution FLOPs: the same forward pass also changes layout,
reshards tensors, keeps long-lived skip tensors in L1, and moves large inputs and
outputs. TT-NN sliding-window operators use channels-last ordering and expect flattened
`[1, 1, NHW, C]` activations, while the PyTorch boundary normally starts in NCHW. The
report therefore performs one NCHW-to-NHWC transformation near entry and one fused
return transformation near exit, instead of paying conversions around every operator.

Grouped convolution attacks a different bottleneck. The report says `conv2d` and
`maxpool2d` are bound by tall shard size for this model. Folding batch into channels,
`B x H x W x C -> 1 x H x W x BC`, and setting `groups=B` converts independent batch
items into wider channel groups. That shortens the shard-height work and gives the
reported linear speedup in the sliding-window operations, at the cost of more delicate
residual concatenation and greater L1 pressure.

### How work and data move

At model entry, `preprocess_unet_input_tensor` pads channels to at least 16 when needed,
uses `ttnn.permute(..., (0, 2, 3, 1))`, and reshapes NHWC to `[1, 1, NHW, C]`. A
downblock runs convolutions, retains `residual = x`, and sends the main path through
pooling. In an upblock, the main activation is reshaped back to `(B,H,W,C)`, assigned a
height-sharded memory configuration with `ttnn.create_sharded_memory_config_`, moved by
`ttnn.reshard`, doubled spatially by `ttnn.upsample`, and flattened again.

Grouped layout changes the residual join. Non-grouped batches are vertically stacked;
after folding batch into channels, logical pairs are interleaved across channel groups.
The required result is equivalent to splitting `a` and `b` into per-batch channel
chunks and producing `concat(a0,b0,a1,b1,...)`. The `groups` parameter of `ttnn.concat`
fuses that rearrangement. Once the concat owns the required values, the old main-path
and residual tensors are explicitly released with `ttnn.deallocate`; this is what makes
room for larger groups and convolution buffers rather than an incidental cleanup step.

### What must never break

Batch identity must survive the batch-to-channel fold: group `g` may consume only input
channels and residual channels belonging to batch item `g`. Channel padding must remain
zero and must not become a real model channel. Every reshape must preserve the same
linear NHWC order, and `ttnn.upsample` must see the intended `(B,H,W,C)` dimensions.
Finally, deallocation can happen only after `ttnn.concat` has consumed both branches.
Typical failures are numerically plausible cross-batch mixing, an apparently correct
shape with wrong channel order, L1 allocation failure from residual lifetime or double
buffers, and a speedup erased by added reshards.

### Where the report makes it concrete

The L1/performance controls expose a capacity tradeoff. `act_block_w_div` controls
activation blocking; choosing a configuration with a larger output activation block
uses more L1 and can improve performance. Enabling
`enable_weights_double_buffer` or `enable_act_double_buffer` can overlap supply with
compute but consumes more L1. The report recommends iterative tuning rather than a
universal setting. `ttnn-visualizer` is the named tool for inspecting fragmentation and
residency. Above the operator level, tracing records the static operation sequence into
device DRAM for replay, reducing op-to-op dispatch latency. For its UNet case, one
command queue owns operation launches while another owns input/output transfers, so I/O
can overlap execution. Across chips, `ShardTensorToMesh(dim=0)` partitions inputs,
`ReplicateTensorToMesh` copies weights, and `ConcatMeshToTensor(dim=0)` restores host
batch order: data parallelism avoids collectives inside the model but replicates weight
storage. The pinned `Optimizing data transfers`, `Performance Analysis`, and
`Troubleshooting` sections are all `Coming soon!`; the report supports these mechanisms
and qualitative choices, but it does not supply an end-to-end speedup or tuning table.

### How the decision is tested

Test in causal layers. First compare ordinary batching with the `groups=B` transform and
grouped `ttnn.concat`, checking each batch item independently against the reference; a
single aggregate PCC can conceal cross-batch swaps. Next sweep group size and the three
buffer/block controls while recording L1 use and end-to-end latency, rejecting any
configuration that spills or adds reshards. Then compare one-CQ, two-CQ, traced, and
traced-plus-two-CQ execution after warmup. The expected signature is lower dispatch gap
from trace and transfer/compute overlap from the CQ split, not a change in device-op
arithmetic. Finally, scale identical per-device batches with replicated weights and
verify that output reconstruction on dimension zero preserves original request order.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/cnn_optimizations.md):

- **Operator boundary.** `ttnn.conv2d`, `ttnn.maxpool2d`, and `ttnn.concat` are the
  semantic checkpoints. Record their input/output shapes, dtype, layout, memory config,
  and golden comparison before changing sharding or folding batch into channels.

- **Representation boundary.** The `B×H×W×C → 1×H×W×BC` transform and sharded memory
  configurations purchase locality only if every downstream module interprets the new
  axes consistently. The model's module tests are therefore part of the optimization
  contract, not optional validation after tuning.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/cnn_optimizations.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report addresses the full CNN path from numerical bring-up to throughput: map
    convolution-heavy modules into TT-NN, then remove layout conversions, DRAM traffic,
    under-filled core grids, and poorly chosen sharding or convolution configurations
    without losing model accuracy.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    At every optimization checkpoint, the TT-NN module must implement the same logical
    tensor transform as the reference model: shapes, padding, stride, channel order,
    residual branches, and output interpretation must agree within the chosen numerical
    tolerance.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    One activation enters preprocessing → is converted to the required TT-NN
    dtype/layout → is distributed or sharded to the cores that run convolution →
    intermediate activations remain in a consumer-friendly layout where possible → later
    modules consume them → post-processing restores the host-visible
    detection/classification result for comparison.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Concrete convolution configs, core grids, shard shapes, data
    types, program-cache behavior, and measured device numbers depend on the TT-Metal
    revision and target chip.

    **Durable model.** Bring up bottom-up against a golden model, profile before tuning,
    follow the next consumer when selecting layout, keep reusable data local, fuse
    avoidable boundaries, and re-check correctness after every performance change.

## Source and delta

- **Original source:** [`tech_reports/CNNs/cnn_optimizations.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/cnn_optimizations.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/CNNs/cnn_optimizations.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
