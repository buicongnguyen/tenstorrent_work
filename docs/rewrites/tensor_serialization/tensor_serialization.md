<!-- rewrite-status: improved-draft -->
# Tensor Serialization

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_serialization/tensor_serialization.md"><code>tech_reports/tensor_serialization/tensor_serialization.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The persistent boundary must carry enough information to reconstruct a TT-NN tensor
without persisting process-local allocation state. At the pinned snapshot, the
`.tensorbin` format therefore separates structured FlatBuffer metadata—whose schema is
`ttnn/core/tensor/flatbuffer/tensor.fbs`—from raw tensor buffers. The metadata includes
tensor specifications, mesh shape, and distributed shard information; the payload
contains the stored elements. `ttnn.dump_tensor` and `ttnn.load_tensor` expose explicit
persistence, while `ttnn.as_tensor(..., cache_file_name=...)` uses the same format as a
materialization cache. This design lets a file survive process and device lifetimes and
lets `load_tensor(..., device=mesh_device)` choose placement at load time rather than
mistaking an old device address for durable identity.

### How work and data move

A writer emits an 8-byte `uint64_t header_size`, followed by `header_size` bytes of
FlatBuffer metadata and then the data buffers. Both the metadata boundary and data
region are aligned to 8 bytes; individual buffers observe their element alignment.
That layout allows the loader to read the small size word, validate/interpret the
FlatBuffer, and map the payload at a naturally aligned file offset. The report connects
this directly to memory-mapped loading: host access can refer to mapped file pages
instead of first copying the complete payload into another RAM buffer.

For a distributed tensor, one `.tensorbin` describes the global tensor. Only one host
writes the file; shard records retain their mesh coordinates. On load, those coordinates
drive reconstruction and optional placement onto a `MeshDevice`. With
`ttnn.as_tensor`, the control flow starts with the derived name
`{cache_file_name}_dtype_{dtype}_layout_{layout}.tensorbin`: an existing compatible
artifact supplies the tensor, while a miss converts the supplied PyTorch tensor and
creates the cache. The source explicitly warns by example that the input value is
ignored on a hit, so the file name is part of correctness ownership, not just storage
organization.

### What must never break

The size word, FlatBuffer tensor specification, shard coordinates, buffer lengths, and
payload bytes must describe one tensor. The data start must remain 8-byte aligned for
the promised mapped access. In multi-host execution exactly one writer must publish the
global artifact, and no reader may interpret a partial file as complete. Cache reuse
also requires semantic identity: the generated name distinguishes dtype and layout,
but the report lists shape mismatch and corrupted/incomplete files as misses too.
Consequently callers must not deliberately reuse a base `cache_file_name` for different
weights that happen to share shape, dtype, and layout; the cached input is authoritative
once the hit occurs.

### Where the report makes it concrete

The public APIs live in `ttnn/ttnn/operations/core.py`. `ttnn.dump_tensor` requires the
`.tensorbin` extension; `ttnn.load_tensor` can return a host tensor or place it directly
on a supplied device; and `ttnn.as_tensor` combines conversion, placement parameters
such as `memory_config=ttnn.L1_MEMORY_CONFIG`, and disk caching. The report's file tree
separates immutable weights from regenerable activations and dataset-specific inputs.
That organization is architectural metadata for humans: filenames include purpose,
dtype, and, for random artifacts, a `seed_42`-style seed so two byte-valid caches are
not confused semantically.

### How the decision is tested

Round-trip representative row-major, tile-layout, and distributed tensors through
`dump_tensor`/`load_tensor`; compare shape, dtype, layout, shard-to-mesh-coordinate
mapping, and values after a fresh process loads them. Inspect the file offset computed
from `8 + header_size` and verify the promised alignment. For caching, run
`as_tensor` twice with the same semantic input and then vary shape, dtype, and layout
one at a time; the first call should materialize, the identical call should reuse, and
an incompatible request must not silently reinterpret bytes. Finally truncate the
metadata and payload independently and simulate two concurrent host writers. A safe
integration must reject incomplete/corrupt artifacts and enforce one publication
owner; the pinned report describes the format and single-writer rule but does not claim
an atomic-publication protocol, so that property must be verified in the consuming
system rather than assumed.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_serialization/tensor_serialization.md):

- **Materialization and cache.** `ttnn.as_tensor` converts host data and may use
  `cache_file_name` to reuse a `.tensorbin`. The key must include every property that
  changes stored bytes or interpretation: shape, dtype, layout, padding, and relevant
  memory/preprocessing configuration.

- **Explicit persistence.** `ttnn.dump_tensor` writes and `ttnn.load_tensor`
  reconstructs the serialized representation implemented in
  `ttnn/ttnn/operations/core.py`. Validate metadata and a round-trip golden comparison
  before treating file existence as a cache hit.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_serialization/tensor_serialization.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report defines how to persist TT-NN tensors—including enough metadata to
    reconstruct them—and how multi-host use and cache hits/misses affect reliable reuse
    across processes and runs. The file must be portable without pretending device
    allocation is serialized.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Serialized payload and metadata must agree on logical shape, dtype, layout, padding,
    version, and byte count. A reader must never interpret a partial, stale, or
    incompatible file as a valid cache hit, and participating hosts must agree on
    ownership/path semantics.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A tensor is materialized in a serializable representation → metadata/header and
    payload are written to a stable file → cache lookup validates identity and
    compatibility → deserialization reconstructs the tensor → requested device/memory
    placement is applied → consumers use the restored value.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** API names, on-disk format, cache-key fields, multi-host file
    rules, supported layouts, and compatibility guarantees belong to the TT-NN revision.

    **Durable model.** Version persistent formats, validate metadata before payload use,
    publish files atomically, make cache identity explicit, separate logical
    serialization from device placement, and test cross-process plus
    backward-compatibility cases.

## Source and delta

- **Original source:** [`tech_reports/tensor_serialization/tensor_serialization.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_serialization/tensor_serialization.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/tensor_serialization/tensor_serialization.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
