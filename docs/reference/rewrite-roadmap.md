# Rewrite roadmap

The source snapshot is complete; the teaching layer is intentionally iterative.
Every report has a one-to-one learner URL and exact original-source link, but a
`seed` is not presented as an improved technical explanation.

## Coverage now

| Status | Count | Meaning |
|---|---:|---|
| `improved-draft` | 8 | Substantive explanation, diagram, code connection, and verification prompts; practitioner review remains |
| `seed` | 49 | Provenance, source outline, report-specific architecture plan, and answered reasoning checks exist; full visual rewrite is queued |
| **Total** | **57** | One learner page for every pinned official report |

The [report catalog](report-catalog.md) is the authoritative per-document status
table. Regenerate it after every promotion.

## Phase 1 — foundational mental models

- [x] [Tensor and memory layouts](../rewrites/tensor_layouts/tensor_layouts.md)
- [x] [Data formats](../rewrites/data_formats/data_formats.md)
- [x] [Matrix engine](../rewrites/matrix_engine/matrix_engine.md)
- [x] [TensorAccessor](../rewrites/tensor_accessor/tensor_accessor.md)
- [x] [Device allocator](../rewrites/memory/allocator.md)
- [x] [NoC tile transfer](../rewrites/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md)
- [x] [Kernel code indexing](../rewrites/code-indexing/kernel-code-indexing.md)

## Phase 2 — kernel programming primitives

Improve these next because later performance and model reports depend on them:

1. [Data-format reconfiguration](../rewrites/data_formats/reconfig_data_format.md)
2. [TensorAccessor iterators](../rewrites/tensor_accessor/tensor_accessor_iterator.md)
3. [Tensor serialization](../rewrites/tensor_serialization/tensor_serialization.md)
4. [Tensor sharding](../rewrites/tensor_sharding/tensor_sharding.md)
5. [Multicast](../rewrites/prog_examples/multicast/multicast.md)
6. [Matmul data reuse](../rewrites/prog_examples/matmul_multi_core_optimized/data_reuse.md)
7. [Matmul data multicast](../rewrites/prog_examples/matmul_multi_core_optimized/data_mcast.md)
8. [Multi-core sharded data](../rewrites/prog_examples/shard_data_rm/shard_data_rm.md)
9. [SFPU elementwise chains](../rewrites/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md)
10. [Multi-core padding](../rewrites/prog_examples/pad_multi_core/pad_multi_core.md)

## Phase 3 — measurement and optimization

After the primitives, promote the reports on DRAM/PCIe bandwidth, GEMM FLOPS,
profilers, performance counters, numerical accuracy, and advanced optimization.
Each rewrite should distinguish a theoretical ceiling from measured utilization
and identify the counter or trace that tests the suspected bottleneck.

- [x] [Advanced runtime and model optimizations](../rewrites/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md)
- [x] [Cross-layer optimization learning track](../start/optimization-path.md)
- [x] [DeepWiki research guide](../resources/deepwiki-research-guide.md)

## Phase 4 — operators, models, and scale-out

Then tackle TT-NN tracing/bring-up, CNN/ViT/YOLO/LLM reports, mesh programming,
TT-Fabric, and TT-Distributed. These pages should reuse—not redefine—the
foundational vocabulary established in Phases 1–3.

## Promotion rule

A page moves from `seed` to `improved-draft` only when it has:

- a problem statement and stack placement;
- at least one structure, flow, order, ownership, or trade-off diagram when a
  diagram materially clarifies the concept;
- explicit correctness invariants and architecture scope;
- concrete code symbols or examples;
- verification prompts with an expected observation;
- a delta section and exact pinned original-source link.

`improved` remains reserved for a page that has passed the full
[rewrite playbook](../contributing/rewrite-playbook.md), including technical
review against the pinned source and current architecture-sensitive behavior.
