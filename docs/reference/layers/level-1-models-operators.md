# Level 1 — Solve model and operator architecture problems

<p class="source-note">
<strong>Source class:</strong> Atlas architecture synthesis ·
<strong>Report set:</strong>
<a href="../report-catalog.md#level-1-models-operators">Level 1 catalog</a> ·
<strong>Use this page for:</strong> deciding what work the accelerator should execute
</p>

Level 1 converts a model requirement into an executable operator plan. The
expert question is not “does TT-NN have this operator?” It is “what partition
of the graph preserves accuracy while minimizing movement, synchronization,
and repeated work?”

![Model-to-operator decision flow](../../assets/diagrams/layer1-model-decisions.svg){ .atlas-diagram }

<small>[Open full-size diagram](../../assets/diagrams/layer1-model-decisions.svg) · [Diagram source](https://github.com/buicongnguyen/tenstorrent_work/blob/main/diagram_sources/layer1-model-decisions.mmd)</small>

## The architecture contract

Level 1 owns:

- graph semantics and required numerical behavior;
- workload shapes, dynamic dimensions, batch/sequence regimes, and reuse;
- operator partitioning, fusion opportunities, and fallback boundaries;
- end-to-end latency, throughput, and accuracy targets.

It does **not** own the physical NoC route or ISA sequence. It must express
enough intent—shape, layout, format, placement preference, and operation
configuration—for lower layers to make those decisions well.

## Architecture reasoning loop

1. **Characterize the workload distribution**, not only one example shape.
2. **Draw data dependencies and tensor lifetimes.** Movement often costs more
   than a small arithmetic operation.
3. **Choose graph partitions around reusable resident data.** Fuse when it
   removes a material boundary; split when specialization or reuse wins.
4. **Define an accuracy budget per transformation.** Precision choices are
   model decisions before they become hardware settings.
5. **Measure the complete request path.** A faster operator can lose to added
   conversions, queue gaps, or host fallback.
6. **Keep a correct reference path.** Optimization requires a stable semantic
   and accuracy oracle.

## Worked problem — bring up an attention block

**Goal:** support prefill and decode without treating them as the same
workload.

### Step 1: separate regimes

Prefill has large matrix dimensions and substantial parallelism. Decode often
has a small query dimension, persistent KV state, and tight per-token latency.
One kernel configuration is unlikely to be optimal for both.

### Step 2: identify expensive boundaries

- Host fallback creates device/host transfers and synchronization.
- Reformatting Q/K/V between operators can dominate small decode steps.
- Re-reading weights or KV state wastes bandwidth if they could remain device
  resident.
- Materializing a full attention matrix wastes memory when a tiled online
  algorithm can keep partial statistics.

### Step 3: choose the operator architecture

Use separate prefill/decode specializations behind one semantic interface.
Fuse only the boundaries that remove measured movement or launch cost. Preserve
an unfused reference path for validation and unusual shapes.

### Step 4: validate at three levels

1. compare values to the reference across representative shapes;
2. measure end-to-end token/prefill latency including conversions;
3. inspect lower levels only for the dominant remaining term.

## Tradeoffs an architect tracks

| Choice | Benefit | Cost | Decision evidence |
|---|---|---|---|
| Fuse adjacent operators | removes intermediate storage and launch gaps | larger specialization and harder debug | bytes/launches removed versus reuse lost |
| Separate shape regimes | better tile/core utilization | more compiled variants and cache pressure | production shape histogram |
| Keep tensors resident | avoids PCIe and repeated allocation | consumes device memory and complicates lifetime | reuse count and residency capacity |
| Lower precision | raises throughput and cuts traffic | accuracy and exceptional-value risk | model-level accuracy budget |
| Fallback to host | quick correctness coverage | transfers, synchronization, and deployment variance | frequency and end-to-end penalty |

## Report-by-report architecture decisions

### New model bring-up — why correctness is established bottom-up

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md) ·
[learner analysis](../../rewrites/ttnn/TTNN-model-bringup.md)

**Why this design exists.** An end-to-end mismatch has too many possible
causes: preprocessing, one operator, a branch ordering error, accumulated
numerical loss, or post-processing. Porting the whole graph before establishing
local contracts makes the first bad value hard to locate.

**Mechanism and benefit.** The report uses operation tests, then module tests,
then the complete TT-NN model, with PCC/reference checks at each narrowing
boundary. This converts one large attribution problem into a sequence of small
proofs and preserves a known-correct baseline for later performance work.

**Price and rejected shortcut.** The method costs fixtures, intermediate tensor
capture, and duplicated reference execution. The tempting shortcut—judge only
the final model score—can hide offsetting errors and makes every optimization a
full-graph debugging exercise.

**Architect's evidence test.** Require a checkpoint map showing input contract,
shape/layout/dtype, golden implementation, tolerance, and first failing module.
Do not start layout, sharding, or fidelity tuning until that map is green for the
production shape distribution.

### Convolution networks — why convolution is lowered and haloed

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md) ·
[learner analysis](../../rewrites/CNNs/ttcnn.md)

**Why this design exists.** Sliding convolution has heavy reuse but irregular
neighborhood access, while Tensix provides an efficient regular matrix path and
limited per-core L1. Reading every overlapping window remotely would spend NoC
bandwidth reproducing data that neighboring outputs share.

**Mechanism and benefit.** Windows and filters are lowered to matrix blocks;
outputs are partitioned first, then each core's required input dependency set is
derived. A halo phase copies boundary sticks so the hot convolution phase reads
mostly local, regular data. Blocking keeps the live activation, weight, and
output set within L1 and reuses it before eviction.

**Price and rejected shortcut.** Halo construction duplicates edge data,
consumes L1, and adds a synchronization phase. Direct remote window reads look
simpler but repeat traffic inside the innermost loop and expose compute to
network latency.

**Architect's evidence test.** Prove every output window at image and shard
boundaries, then compare remote bytes and matrix idle time with and without
haloing. The choice is justified only when saved repeated reads exceed halo
construction and storage cost.

### CNN optimization — why layout is chosen from the next consumer

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/cnn_optimizations.md) ·
[learner analysis](../../rewrites/CNNs/cnn_optimizations.md)

**Why this design exists.** CNN graphs contain long runs of convolution,
residual, pooling, and reshaping operations. Optimizing each operator in
isolation often inserts reshard or untilize/tilize boundaries that cost more
than the local kernel improvement.

**Mechanism and benefit.** The architecture treats a sequence of operations as
the unit of layout policy. Activations remain device-resident and sharded in a
form useful to the next expensive consumer; shape-specific convolution configs
are selected after correctness bring-up. The purchased benefit is fewer
representation changes and higher reuse across the subgraph.

**Price and rejected shortcut.** Consumer-driven layouts increase coupling and
program variants, and may make a small producer slower. Selecting the fastest
layout for each individual operator rejects the real objective: minimum
critical-path cost across boundaries.

**Architect's evidence test.** Produce a subgraph table of input/output layouts,
conversion bytes, L1 lifetime, and warm latency. Accept a locally slower operator
when it removes a larger downstream conversion and improves the complete request.

### LLMs — why prefill and decode are different architectures

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/llms.md) ·
[learner analysis](../../rewrites/LLMs/llms.md)

**Why this design exists.** Prefill presents large matrix dimensions and ample
parallel work; decode presents one or a few queries, a growing persistent KV
cache, and a strict per-token latency target. One schedule cannot simultaneously
optimize matrix utilization and long-cache bandwidth.

**Mechanism and benefit.** The report organizes transformer modules with
regime-specific configurations while keeping weights and KV state resident.
Prefill favors throughput and block parallelism; decode favors low launch cost,
careful cache ownership, and bandwidth-aware attention. This matches physical
work to the dominant constraint instead of hiding both behind an average.

**Price and rejected shortcut.** Two paths increase cache entries, testing, and
state management. A single general path reduces code count but commonly
under-fills compute during decode or compromises prefill throughput.

**Architect's evidence test.** Report time-to-first-token and steady token
latency separately, along with KV bytes read/written, cache address/lifetime,
and module checkpoints. A throughput gain that worsens the deployed decode
distribution is not an LLM improvement.

### vLLM integration — why scheduler metadata is part of the accelerator contract

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/vLLM_integration.md) ·
[learner analysis](../../rewrites/LLMs/vLLM_integration.md)

**Why this design exists.** vLLM continuously batches, reorders, and advances
requests. A model backend that accepts only dense static batches cannot preserve
which token position owns which KV-cache blocks when requests have different
lifetimes.

**Mechanism and benefit.** The integration translates scheduler state—request
identity, positions, batch slots, and cache-block mapping—into TT tensors and
persistent device state, then restores logits to scheduler order. This allows
continuous batching without surrendering accelerator residency.

**Price and rejected shortcut.** The adapter becomes stateful and must handle
preemption, mixed lengths, and version changes on both sides. Copying every
request through a stateless host boundary is simpler but destroys KV locality
and forces synchronization each token.

**Architect's evidence test.** Stress reordered, mixed-length, cancelled, and
resumed requests. Trace one request's token and KV block through scheduling,
device execution, returned logit row, and next iteration; identity errors can
pass single-request accuracy tests.

### FlashAttention — why online softmax replaces score materialization

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md) ·
[learner analysis](../../rewrites/FlashAttention/FlashAttention.md)

**Why this design exists.** Standard attention materializes an `S × S` score
matrix between QKᵀ and softmax/value multiplication. At useful sequence lengths,
those intermediate bytes overwhelm limited L1 and cause avoidable DRAM traffic.

**Mechanism and benefit.** Query blocks stay local while K/V blocks stream
through. A running maximum, normalization sum, and weighted-value accumulator
are rescaled as each block arrives, preserving exact softmax semantics without
storing the full score matrix. The main benefit is IO complexity: intermediate
scores are consumed where produced.

**Price and rejected shortcut.** The recurrence couples stages, adds reduction
state, and makes causal masks and numerical stability correctness-critical.
Materialization is easier to inspect but pays quadratic storage/movement.

**Architect's evidence test.** Validate the online recurrence against reference
attention for adversarial logits and masks, then measure external score bytes
and inter-stage gaps. Faster matmul alone does not prove the algorithmic choice.

### FlashDecode — why the KV dimension becomes the parallel dimension

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashDecode.md) ·
[learner analysis](../../rewrites/FlashAttention/FlashDecode.md)

**Why this design exists.** During decode, query length is too small to occupy a
large core grid, but the cached K/V sequence is long and bandwidth-heavy.
Parallelizing the query dimension therefore leaves hardware idle.

**Mechanism and benefit.** Workers take disjoint K/V ranges, compute partial
online-softmax state, then combine `(max, sum, weighted value)` with the required
rescaling. The design exposes parallel reads along the large dimension while
preserving exact global normalization.

**Price and rejected shortcut.** It adds a cross-worker reduction and can lose
to its synchronization cost for short contexts. Assigning one decode query to
one worker avoids reduction but serializes the dominant cache scan.

**Architect's evidence test.** Sweep context length and worker count. The
expected signature is increased aggregate KV bandwidth followed by a reduction
floor; verify partial-state recombination at uneven partitions and causal edges.

### Integral image — why prefix state is fed across tile boundaries

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md) ·
[learner analysis](../../rewrites/ttnn_operators/intimg.md)

**Why this design exists.** A summed-area table is a two-dimensional prefix
dependency, not an embarrassingly parallel elementwise operator. Independent
tile scans are wrong unless each tile receives the completed horizontal and
vertical state from predecessor tiles.

**Mechanism and benefit.** Reader, compute, and writer roles carry both payload
tiles and boundary context. Local scans exploit tile/SFPU parallelism; feedback
of edge state creates the minimal dependency needed for the next tile or core.
The architecture parallelizes work without discarding the mathematical scan.

**Price and rejected shortcut.** Wavefront ordering and state buffers constrain
parallel scheduling. A fully sequential scan is simple but wastes cores; fully
independent tiles are fast but mathematically incomplete.

**Architect's evidence test.** Use small hand-computable inputs with distinct
values and inspect every tile boundary. Prove the carried state equation before
profiling, then measure whether dependency waits or local scan compute sets the
critical path.

### ViT — why attention and MLP boundaries drive layout policy

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md) ·
[learner analysis](../../rewrites/ViT-TTNN/vit.md)

**Why this design exists.** ViT alternates reshapes/head transforms, attention,
projections, residuals, and MLPs. These stages prefer different access patterns;
blindly returning to a canonical layout at every boundary spends bandwidth on
representation rather than model work.

**Mechanism and benefit.** The implementation keeps token/head meaning explicit
while selecting sharding and TT-NN operations across encoder subgraphs. Layout
is preserved or converted where the next dominant consumer benefits, and
residual checkpoints guard semantic equivalence.

**Price and rejected shortcut.** Cross-operator layout policy couples modules
and creates shape-specific choices. Canonicalizing after every operation
improves modularity but adds conversions and loses L1 residency.

**Architect's evidence test.** Record attention/MLP/residual boundary layouts,
bytes converted, and module PCC. A chosen shard is justified only if it reduces
the encoder-layer critical path without breaking token order or residual pairing.

### ViT for Blackhole — why porting means re-deriving, not copying

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md) ·
[learner analysis](../../rewrites/ViT-TTNN/vit_bh.md)

**Why this design exists.** The model graph is portable, but L1 budgets, core
topology, NoC behavior, supported programs, and profitable block sizes are not.
A Wormhole configuration can remain numerically correct on Blackhole while
leaving the new machine badly utilized.

**Mechanism and benefit.** The Blackhole path retains the validated ViT semantic
checkpoints and isolates generation-specific program/layout policy. Capacity,
parallelism, and operation selection are re-derived for Blackhole instead of
treated as copied constants.

**Price and rejected shortcut.** Generation policy adds configuration and
benchmark matrices. Copying the old path is a useful correctness bootstrap, but
it is not a performance architecture.

**Architect's evidence test.** Hold model inputs, weights, and checkpoint
tolerances fixed; compare per-stage shapes, L1 footprints, active cores, and
timelines. Attribute gains to a named Blackhole mechanism rather than the device
label alone.

### YOLOv4 — why multi-scale branch identity must remain explicit

[Pinned original](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md) ·
[learner analysis](../../rewrites/YoloV4-TTNN/yolov4.md)

**Why this design exists.** YOLOv4 repeatedly routes, shortcuts, upsamples, and
concatenates feature maps before three scale-specific heads. A shape-compatible
layout or branch swap can still attach the wrong semantic feature to a head.

**Mechanism and benefit.** The port treats each backbone/neck/head boundary as a
named tensor contract and selects convolution/sharding policy with its next
route or concatenation in view. This protects branch meaning while minimizing
avoidable conversion around multi-scale fusion.

**Price and rejected shortcut.** Keeping branch identity and layouts explicit
adds metadata and checkpoint tests. Validating only decoded detections can hide
raw-head errors and makes neck failures difficult to localize.

**Architect's evidence test.** Verify shapes, channel order, route source, and
raw values at every downsample, neck merge, and head before host decoding. Then
profile conversion and convolution time around the three scale paths separately.

## Questions and expert answers

### 1. Why can an individually faster fused operator make the model slower?

???+ note "Expert answer — reasoning"
    1. Fusion may prevent reuse of an intermediate or force a less favorable
       layout for the next consumer.
    2. It may create more compiled variants, program-cache misses, or a larger
       working set.
    3. The fused kernel may improve arithmetic time while worsening movement or
       occupancy.
    4. Compare the original and fused **subgraph** including conversions,
       allocation, dispatch, and downstream layout. Optimize the boundary, not
       the kernel name.

### 2. How should an architect choose between one general operator and several specialized variants?

???+ note "Expert answer — reasoning"
    Build a cost model over the real shape distribution. Specialize when a
    common regime has a different bottleneck or dataflow and the saved steady-
    state cost exceeds compilation, cache, testing, and maintenance costs.
    Keep a general fallback for rare shapes. This is an expected-value decision,
    not a contest for the fastest single benchmark.

### 3. Where should the accuracy budget be decided?

???+ note "Expert answer — reasoning"
    The model layer owns acceptable task-level error; lower layers expose
    format and fidelity choices. Start from the model metric, allocate
    tolerances to sensitive operations, then test the selected formats across
    representative inputs. Hardware peak throughput never defines acceptable
    accuracy. Conversely, demanding maximum precision everywhere can waste
    bandwidth and compute without improving the model result.

### 4. What is the correct reasoning order for a host fallback?

???+ note "Expert answer — reasoning"
    First establish semantic coverage: which shapes/dtypes require fallback?
    Then quantify frequency in the target workload. Next measure transfers,
    synchronization, and queue disruption around it. Finally compare three
    choices: implement on device, restructure the graph to avoid it, or accept
    it as a rare path. Replacing fallback is justified by end-to-end impact,
    not by the mere existence of a CPU operation.

## Evidence checklist

- Workload shape histogram, not only a canonical benchmark.
- Correct reference outputs and model-level accuracy thresholds.
- Tensor lifetime/residency diagram across the candidate subgraph.
- End-to-end timing including layout conversion and fallback.
- Separate cold, warm, prefill, and decode measurements where applicable.

## Report path and continuation

Start with [model bring-up](../../rewrites/ttnn/TTNN-model-bringup.md), then use
CNN, LLM, FlashAttention/FlashDecode, ViT, and YOLO reports as different
constraint cases. Continue to [Level 2 — runtime reasoning](level-2-runtime-observability.md)
when operator semantics are clear but execution behavior is not.
