<!-- rewrite-status: seed -->
# Convolution Networks on Tenstorrent Chips

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md"><code>tech_reports/CNNs/ttcnn.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-linked learner seed
</p>

!!! info "What ‘seed’ means"
    The official report and its assets are preserved verbatim under
    <code>upstream/tt-metal/tech_reports/CNNs/ttcnn.md</code>. This learner page
    establishes provenance, a reading map, and review prompts; its technical
    explanation is still queued for a full visual rewrite.

## Original report map

| Signal | Pinned-source value |
|---|---:|
| Lines | 888 |
| Section headings | 14 |
| Fenced code examples | 4 |
| Markdown images | 0 |

### Section outline

- Abstract
- Convolution Operations in TTNN
  - `conv2d`
    - Python API
    - `Conv2dConfig`
    - Compute Config
    - Example Usage
  - `maxpool2d`
  - Halo implementation
    - Step 1 - Pad metadata
    - Step 2 - Op trace metadata
    - Step 3 - Shard boundaries
    - Step 4 - Tensor metadata
    - Step 5 - Kernel config tensors

## Improvement plan

1. **Architecture pressure.** Explain why convolution is lowered to blocked matrix
   multiplication on Tensix and why overlapping spatial windows make naive remote reads the
   dominant movement problem once activations no longer fit in one core's L1.

2. **Flow to make explicit.** Draw one activation stick from its source shard through
   sliding-window dependency analysis, local/remote halo configuration, halo transfer,
   activation-reader flattening, matrix accumulation, pack, and the destination output
   shard.

3. **Invariant to prove.** For every output coordinate, prove that stride, padding,
   dilation, groups, channel order, and shard-boundary haloing select exactly the same
   logical input window and filter values as reference convolution.

4. **TT-Metal evidence to connect.** Map the original `conv2d` input/weight/bias/output
   contracts and halo implementation sections to TT-NN convolution configuration,
   sliding-window analysis, reader CBs, compute blocks, and output post-processing rather
   than listing generic kernel roles.

5. **Experiment and expected observation.** Use distinctive boundary values and compare
   direct/reference convolution with haloed sharding for image edges and inter-core
   boundaries; expected result: identical outputs with fewer remote reads during the hot
   convolution phase after halo construction.

## Code connection

Code references remain in the [pinned official report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md). During
the full rewrite, each important symbol will be mapped to its role in the
host → data-movement → compute → data-movement path.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md).
They explain the architecture reasoning rather than only restating its section
headings.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — architecture reasoning"
    The programming task is to implement `conv2d` efficiently on Tensix even
    though the hardware does not provide a dedicated convolution instruction.
    The report first lowers each sliding-window dot product to matrix
    multiplication: one flattened activation window becomes a matrix row and
    one filter becomes a matrix column.

    The main bottleneck is then **data movement under limited local L1
    capacity**. A complete activation, output, and weight set usually cannot all
    reside in one core's L1. A naive implementation would repeatedly fetch
    overlapping windows from DRAM or remote cores, wasting bandwidth while the
    matrix engine waits.

    The architectural response has three connected parts:

    1. block the transformed activation, weights, and output so the live working
       set fits in L1;
    2. reuse a resident activation or weight block across several output blocks
       before replacing it;
    3. shard work across cores and construct **haloed shards** so every core has
       the padding, local sticks, and neighboring sticks needed for its assigned
       outputs before convolution begins.

    This converts irregular cross-core sliding-window reads into a preparation
    phase followed by mostly local, regular matrix work. The expected proof is
    not merely correct output: the convolution phase should show reduced remote
    access and greater reuse of data already in L1. See the original sections
    [Convolution as Matrix Multiplication](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md#convolution-as-matrix-multiplication),
    [Parallelization](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md#parallelization-of-convolution-operation),
    and [Haloing](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md#haloing).

### 2. What is one invariant that must remain true?

???+ note "Expert answer — architecture reasoning"
    For every output coordinate and output channel, the compute core must consume
    **exactly the logical input window selected by kernel size, stride, padding,
    dilation, groups, and channel order**, paired with the corresponding filter
    values. Sharding and haloing may relocate or duplicate sticks, but they must
    not change that mathematical dependency.

    Derive the invariant from the consumer: first assign an output range to a
    core; then enumerate the padded input indices required by every output in
    that range. The halo configuration must classify each required stick as
    padding, local, or remote and place its value at the offset expected by the
    activation reader. Only after this mapping is complete may the reader flatten
    windows into rows for matrix multiplication.

    This invariant catches several subtle failures:

    - a missing neighbor stick corrupts boundary outputs;
    - an incorrect padding classification substitutes real data or the wrong
      padding value;
    - a wrong local/remote offset silently feeds another spatial position;
    - channel padding may participate physically, but padded lanes must not alter
      logical output channels;
    - output post-processing must remove padded channels and restore the promised
      layout.

    A strong test therefore emphasizes shard boundaries, image edges, stride or
    dilation greater than one, groups, and distinctive non-constant inputs. A
    uniform tensor can hide an indexing mistake because several wrong sticks may
    contain the same value.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — architecture reasoning"
    Trace one activation **stick**—all channel values at one `(N, H, W)`
    position—that belongs to a convolution window assigned to a neighboring
    core.

    1. The stick initially resides in the source core's sharded input buffer.
    2. Host-side sliding-window analysis starts from each destination core's
       output range and determines that this remote stick is part of one or more
       required windows.
    3. That dependency is encoded in the remote halo configuration with source
       core coordinates, source-local index, destination halo offset, and chunk
       length.
    4. The halo kernel executes the configured transfer. In the default model
       the source pushes its local data to the remote destination; with
       `remote_read`, the consumer pulls it instead.
    5. After halo completion, the destination core owns a local haloed shard
       containing padding, original local sticks, and copied neighbor sticks.
    6. The activation reader selects this stick using the window's starting
       position and offsets, then writes the flattened window row into a circular
       buffer.
    7. The compute kernel consumes that row together with a filter column and
       accumulates the dot product for one output position/channel.
    8. Pack and writer stages materialize the result in the destination core's
       output shard; later post-processing removes channel padding and restores
       the requested tensor shape/layout.

    The critical control edge is **halo completion before the activation reader
    publishes the window**. Without it, the compute consumer can observe an
    uninitialized or stale remote stick. The original
    [Halo implementation](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md#halo-implementation)
    and [worked implementation](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md#implementation)
    provide the source details for this path.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — architecture reasoning"
    **Architecture- or snapshot-specific claims** include the quoted Grayskull
    and Wormhole L1 capacities, the 32×32 tile assumptions, the stated limit on
    output tiles processed together, particular TT-NN configuration fields,
    reserved L1 configuration storage, and compute options such as
    `fp32_dest_acc_en` or `packer_l1_acc`. Core counts, NoC behavior, supported
    sharding choices, optimal block sizes, and the exact halo implementation must
    be rechecked for the target architecture and software commit.

    **Durable mental models** are the reasoning patterns underneath those
    numbers:

    - lower convolution to a regular dot-product/matrix engine when that is the
      efficient compute primitive;
    - choose blocking from local-memory capacity and maximize reuse before
      eviction;
    - partition outputs first, then derive each worker's input dependency set;
    - exchange or duplicate boundary data in a halo phase so the hot compute
      phase can remain local;
    - treat layout, sharding, padding, and ownership as part of the physical
      tensor contract;
    - balance parallel work and measure total movement, rather than assuming
      more cores or local placement automatically improves throughput.

    On another Tenstorrent generation, keep these questions but recompute every
    numeric answer and inspect the architecture-matched APIs. That separation is
    what makes the report useful beyond the exact snapshot it documented.

## Source and delta

- **Original source:** [`tech_reports/CNNs/ttcnn.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/CNNs/ttcnn.md`
- **Current delta:** provenance, source metrics, outline, improvement checklist,
  and four source-grounded expert answers covering the bottleneck, invariants,
  producer-to-consumer flow, and architecture boundaries. A full visual rewrite
  of the report remains pending.
