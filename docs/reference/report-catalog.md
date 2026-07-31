# Upstream report catalog

This index covers all **57** Markdown reports in the pinned 
[official snapshot](https://github.com/tenstorrent/tt-metal/tree/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports).
The snapshot also includes each report's images, media, and helper scripts.

Every source has a one-to-one learner page. Status is intentionally
conservative: `seed` means provenance and a reading map exist, while
`improved-draft` means a substantive rewrite still awaits final review.

## Read from high level to low level

Levels 0–4 form the main descent from stack vocabulary to device-kernel
dataflow. Levels 5 and 6 are advanced branches for measurement and scale.
Level 7 is the lowest layer and should be architecture-qualified.

| Level | Abstraction | Main question | Reports |
|---:|---|---|---:|
| [0](#level-0-orientation) | Whole stack | Vocabulary, boundaries, and the TT-NN to hardware mental model. | 1 |
| [1](#level-1-models-operators) | Highest | See how complete workloads and operators use TT-NN. | 11 |
| [2](#level-2-ttnn-runtime) | High | Devices, tracing, comparison, serialization, and runtime behavior. | 5 |
| [3](#level-3-tensor-memory) | Middle | Tiles, formats, layouts, sharding, allocation, and addressing. | 8 |
| [4](#level-4-kernels-dataflow) | Low | Host programs, reader/compute/writer kernels, NoC, and multicore flows. | 8 |
| [5](#level-5-performance-debugging) | Advanced cross-layer | Measure bottlenecks, debug kernels, and optimize with evidence. | 10 |
| [6](#level-6-distributed-systems) | Advanced system scale | Meshes, Ethernet, collectives, fabric, and multi-host execution. | 9 |
| [7](#level-7-hardware-isa) | Lowest | Tensix engines, formats at the hardware boundary, and architecture-specific details. | 5 |

## Level 0 — Orientation and stack { #level-0-orientation }

Vocabulary, boundaries, and the TT-NN to hardware mental model.

**Start this level when:** you are new to Tenstorrent or cannot yet place TT-NN, TT-Metalium, kernels, and Tensix on one diagram.

| Step | Report | Upstream original | Learner edition | Status |
|---:|---|---|---|---|
| 1 | TT-NN | [`ttnn/ttnn.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/ttnn.md) | [Open learner page](../rewrites/ttnn/ttnn.md) | `seed` |

## Level 1 — Models and operators { #level-1-models-operators }

See how complete workloads and operators use TT-NN.

**Start this level when:** you can name the major stack layers and want an application-level reason for the lower-level machinery.

| Step | Report | Upstream original | Learner edition | Status |
|---:|---|---|---|---|
| 2 | New model bring-up in TT-NN | [`ttnn/TTNN-model-bringup.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/TTNN-model-bringup.md) | [Open learner page](../rewrites/ttnn/TTNN-model-bringup.md) | `seed` |
| 3 | Convolution Networks on Tenstorrent Chips | [`CNNs/ttcnn.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/ttcnn.md) | [Open learner page](../rewrites/CNNs/ttcnn.md) | `seed` |
| 4 | CNN Bring-up & Optimization in TT-NN | [`CNNs/cnn_optimizations.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/CNNs/cnn_optimizations.md) | [Open learner page](../rewrites/CNNs/cnn_optimizations.md) | `seed` |
| 5 | LLMs in TT-NN | [`LLMs/llms.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/llms.md) | [Open learner page](../rewrites/LLMs/llms.md) | `seed` |
| 6 | Integrating TT Models into vLLM | [`LLMs/vLLM_integration.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/LLMs/vLLM_integration.md) | [Open learner page](../rewrites/LLMs/vLLM_integration.md) | `seed` |
| 7 | FlashAttention on Tenstorrent’s Wormhole Architecture | [`FlashAttention/FlashAttention.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashAttention.md) | [Open learner page](../rewrites/FlashAttention/FlashAttention.md) | `seed` |
| 8 | FlashDecode on Tenstorrent's Wormhole Architecture | [`FlashAttention/FlashDecode.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/FlashAttention/FlashDecode.md) | [Open learner page](../rewrites/FlashAttention/FlashDecode.md) | `seed` |
| 9 | Tenstorrent `tt-metal`: Integral Image (Summed-Area Table) Kernels — High-Level Guide (Axis Spec: **[B, W, H, C]**) | [`ttnn_operators/intimg.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn_operators/intimg.md) | [Open learner page](../rewrites/ttnn_operators/intimg.md) | `seed` |
| 10 | ViT in TT-NN | [`ViT-TTNN/vit.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit.md) | [Open learner page](../rewrites/ViT-TTNN/vit.md) | `seed` |
| 11 | [skip ci] ViT in TT-NN for Blackhole | [`ViT-TTNN/vit_bh.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ViT-TTNN/vit_bh.md) | [Open learner page](../rewrites/ViT-TTNN/vit_bh.md) | `seed` |
| 12 | YOLOv4 in TT-NN | [`YoloV4-TTNN/yolov4.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/YoloV4-TTNN/yolov4.md) | [Open learner page](../rewrites/YoloV4-TTNN/yolov4.md) | `seed` |

## Level 2 — TT-NN runtime and observability { #level-2-ttnn-runtime }

Devices, tracing, comparison, serialization, and runtime behavior.

**Start this level when:** you understand what an operator does and now need to see how TT-NN schedules, records, and checks it.

| Step | Report | Upstream original | Learner edition | Status |
|---:|---|---|---|---|
| 13 | Sub-Devices | [`SubDevices/SubDevices.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/SubDevices/SubDevices.md) | [Open learner page](../rewrites/SubDevices/SubDevices.md) | `seed` |
| 14 | Tensor Serialization | [`tensor_serialization/tensor_serialization.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_serialization/tensor_serialization.md) | [Open learner page](../rewrites/tensor_serialization/tensor_serialization.md) | `seed` |
| 15 | TT-NN Graph Tracing | [`ttnn/graph-tracing.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/graph-tracing.md) | [Open learner page](../rewrites/ttnn/graph-tracing.md) | `seed` |
| 16 | TTNN Operation Parameter Tracing | [`ttnn/operation-tracing.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/operation-tracing.md) | [Open learner page](../rewrites/ttnn/operation-tracing.md) | `seed` |
| 17 | TT-NN Comparison Mode | [`ttnn/comparison-mode.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/ttnn/comparison-mode.md) | [Open learner page](../rewrites/ttnn/comparison-mode.md) | `seed` |

## Level 3 — Tensor representation and memory { #level-3-tensor-memory }

Tiles, formats, layouts, sharding, allocation, and addressing.

**Start this level when:** you can follow an operator call but cannot yet predict where its bytes live or how a kernel addresses them.

| Step | Report | Upstream original | Learner edition | Status |
|---:|---|---|---|---|
| 18 | Tensor and Memory Layouts | [`tensor_layouts/tensor_layouts.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_layouts/tensor_layouts.md) | [Open learner page](../rewrites/tensor_layouts/tensor_layouts.md) | `improved-draft` |
| 19 | Data Formats | [`data_formats/data_formats.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/data_formats.md) | [Open learner page](../rewrites/data_formats/data_formats.md) | `improved-draft` |
| 20 | Tensor Sharding | [`tensor_sharding/tensor_sharding.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_sharding/tensor_sharding.md) | [Open learner page](../rewrites/tensor_sharding/tensor_sharding.md) | `seed` |
| 21 | Allocator | [`memory/allocator.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/memory/allocator.md) | [Open learner page](../rewrites/memory/allocator.md) | `improved-draft` |
| 22 | Tensor Accessor Guide | [`tensor_accessor/tensor_accessor.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_accessor/tensor_accessor.md) | [Open learner page](../rewrites/tensor_accessor/tensor_accessor.md) | `improved-draft` |
| 23 | Tensor Accessor (TA) Iterators 📚 | [`tensor_accessor/tensor_accessor_iterator.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_accessor/tensor_accessor_iterator.md) | [Open learner page](../rewrites/tensor_accessor/tensor_accessor_iterator.md) | `seed` |
| 24 | Tensor Padding (Multicore) | [`prog_examples/pad_multi_core/pad_multi_core.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/pad_multi_core/pad_multi_core.md) | [Open learner page](../rewrites/prog_examples/pad_multi_core/pad_multi_core.md) | `seed` |
| 25 | Data Sharding (Multicore) | [`prog_examples/shard_data_rm/shard_data_rm.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/shard_data_rm/shard_data_rm.md) | [Open learner page](../rewrites/prog_examples/shard_data_rm/shard_data_rm.md) | `seed` |

## Level 4 — TT-Metal kernels and dataflow { #level-4-kernels-dataflow }

Host programs, reader/compute/writer kernels, NoC, and multicore flows.

**Start this level when:** you understand tensor storage and want to trace pages and tiles through actual device kernels.

| Step | Report | Upstream original | Learner edition | Status |
|---:|---|---|---|---|
| 26 | NoC Tile Transfer | [`prog_examples/NoC_tile_transfer/NoC_tile_transfer.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md) | [Open learner page](../rewrites/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md) | `improved-draft` |
| 27 | **Data Multicasting** | [`prog_examples/multicast/multicast.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/multicast/multicast.md) | [Open learner page](../rewrites/prog_examples/multicast/multicast.md) | `seed` |
| 28 | Data Reuse in [matmul_multicore_reuse] | [`prog_examples/matmul_multi_core_optimized/data_reuse.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_reuse.md) | [Open learner page](../rewrites/prog_examples/matmul_multi_core_optimized/data_reuse.md) | `seed` |
| 29 | Data Multicasting in [matmul_multicore_reuse_mcast] | [`prog_examples/matmul_multi_core_optimized/data_mcast.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/data_mcast.md) | [Open learner page](../rewrites/prog_examples/matmul_multi_core_optimized/data_mcast.md) | `seed` |
| 30 | Matmul (Multi Core Optimized) | [`prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md) | [Open learner page](../rewrites/prog_examples/matmul_multi_core_optimized/matmul_multi_core_optimized.md) | `seed` |
| 31 | SFPU Eltwise Chain | [`prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md) | [Open learner page](../rewrites/prog_examples/sfpu_eltwise_chain/sfpu_eltwise_chain.md) | `seed` |
| 32 | Kernel Arguments as Function & Template Parameters | [`NamedKernelArgs/kernel_args_as_parameters.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/NamedKernelArgs/kernel_args_as_parameters.md) | [Open learner page](../rewrites/NamedKernelArgs/kernel_args_as_parameters.md) | `seed` |
| 33 | Kernel code indexing | [`code-indexing/kernel-code-indexing.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/code-indexing/kernel-code-indexing.md) | [Open learner page](../rewrites/code-indexing/kernel-code-indexing.md) | `improved-draft` |

## Level 5 — Performance and debugging { #level-5-performance-debugging }

Measure bottlenecks, debug kernels, and optimize with evidence.

**Start this level when:** a program is correct and you need to explain its latency, bandwidth, utilization, or failure mode.

| Step | Report | Upstream original | Learner edition | Status |
|---:|---|---|---|---|
| 34 | Kernel Debugging Tips | [`Debugging/Kernel_Debugging_Tips.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/Kernel_Debugging_Tips.md) | [Open learner page](../rewrites/Debugging/Kernel_Debugging_Tips.md) | `seed` |
| 35 | Deprecating `DPRINT` in favor of `DEVICE_PRINT` | [`Debugging/DEVICE_PRINT_replaces_DPRINT.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md) | [Open learner page](../rewrites/Debugging/DEVICE_PRINT_replaces_DPRINT.md) | `seed` |
| 36 | Purpose | [`op_kernel_dev/accuracy_tips/accuracy_tips.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/op_kernel_dev/accuracy_tips/accuracy_tips.md) | [Open learner page](../rewrites/op_kernel_dev/accuracy_tips/accuracy_tips.md) | `seed` |
| 37 | Metal Profiler | [`MetalProfiler/metal-profiler.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/MetalProfiler/metal-profiler.md) | [Open learner page](../rewrites/MetalProfiler/metal-profiler.md) | `seed` |
| 38 | Real-time profiler — getting started | [`real_time_profiler/getting-started.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/real_time_profiler/getting-started.md) | [Open learner page](../rewrites/real_time_profiler/getting-started.md) | `seed` |
| 39 | Hardware Performance Counters | [`PerfCounters/perf-counters.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PerfCounters/perf-counters.md) | [Open learner page](../rewrites/PerfCounters/perf-counters.md) | `seed` |
| 40 | PCIe Bandwidth Measurement | [`PCIe_bandwidth/PCIe_bandwidth.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/PCIe_bandwidth/PCIe_bandwidth.md) | [Open learner page](../rewrites/PCIe_bandwidth/PCIe_bandwidth.md) | `seed` |
| 41 | Saturating DRAM bandwidth | [`Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md) | [Open learner page](../rewrites/Saturating_DRAM_bandwidth/Saturating_DRAM_bandwidth.md) | `seed` |
| 42 | Matrix Multiply FLOPS | [`GEMM_FLOPS/GEMM_FLOPS.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/GEMM_FLOPS/GEMM_FLOPS.md) | [Open learner page](../rewrites/GEMM_FLOPS/GEMM_FLOPS.md) | `seed` |
| 43 | Advanced Performance Optimizations for Models | [`AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md) | [Open learner page](../rewrites/AdvancedPerformanceOptimizationsForModels/AdvancedPerformanceOptimizationsForModels.md) | `improved-draft` |

## Level 6 — Multi-device and distributed systems { #level-6-distributed-systems }

Meshes, Ethernet, collectives, fabric, and multi-host execution.

**Start this level when:** you can reason about one device and are ready to extend ownership, routing, and synchronization across devices or hosts.

| Step | Report | Upstream original | Learner edition | Status |
|---:|---|---|---|---|
| 44 | Programming Mesh of Devices with TT-NN | [`Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md) | [Open learner page](../rewrites/Programming_Mesh_of_Devices/Programming_Mesh_of_Devices_with_TT-NN.md) | `seed` |
| 45 | CCL Performance Tuning Tips for tt-metal | [`Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md) | [Open learner page](../rewrites/Programming_Mesh_of_Devices/CCL_Performance_Best_Practices.md) | `seed` |
| 46 | Programming Multiple Meshes | [`Programming_Multiple_Meshes/Programming_Multiple_Meshes.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md) | [Open learner page](../rewrites/Programming_Multiple_Meshes/Programming_Multiple_Meshes.md) | `seed` |
| 47 | Basic Ethernet Multichip | [`EthernetMultichip/BasicEthernetGuide.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/EthernetMultichip/BasicEthernetGuide.md) | [Open learner page](../rewrites/EthernetMultichip/BasicEthernetGuide.md) | `seed` |
| 48 | TT-Fabric Architecture Specification | [`TT-Fabric/TT-Fabric-Architecture.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Fabric/TT-Fabric-Architecture.md) | [Open learner page](../rewrites/TT-Fabric/TT-Fabric-Architecture.md) | `seed` |
| 49 | TT-Metalium Distributed | [`TT-Distributed/TT-Distributed-Architecture-1219.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TT-Distributed-Architecture-1219.md) | [Open learner page](../rewrites/TT-Distributed/TT-Distributed-Architecture-1219.md) | `seed` |
| 50 | TT-Distributed: Multi-Host Runtime | [`TT-Distributed/MultiHostMeshRuntime.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/MultiHostMeshRuntime.md) | [Open learner page](../rewrites/TT-Distributed/MultiHostMeshRuntime.md) | `seed` |
| 51 | H2D / D2H PCIe Socket: Technical Report | [`TT-Distributed/HDSocketsModel.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/HDSocketsModel.md) | [Open learner page](../rewrites/TT-Distributed/HDSocketsModel.md) | `seed` |
| 52 | TTNN Device to MeshDevice Migration Guide | [`TT-Distributed/TTMeshMigrationGuide.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/TT-Distributed/TTMeshMigrationGuide.md) | [Open learner page](../rewrites/TT-Distributed/TTMeshMigrationGuide.md) | `seed` |

## Level 7 — Hardware, TT-LLK, and ISA { #level-7-hardware-isa }

Tensix engines, formats at the hardware boundary, and architecture-specific details.

**Start this level when:** kernel-level behavior is no longer enough and you need to explain an engine, register, instruction, or architecture constraint.

| Step | Report | Upstream original | Learner edition | Status |
|---:|---|---|---|---|
| 53 | Matrix Engine | [`matrix_engine/matrix_engine.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/matrix_engine/matrix_engine.md) | [Open learner page](../rewrites/matrix_engine/matrix_engine.md) | `improved-draft` |
| 54 | Reconfiguring hardware for different DataFormats | [`data_formats/reconfig_data_format.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/reconfig_data_format.md) | [Open learner page](../rewrites/data_formats/reconfig_data_format.md) | `seed` |
| 55 | Shared Exponent Precision Testing Suite | [`data_formats/shared_exponent_precision_testing_suite/Readme.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/data_formats/shared_exponent_precision_testing_suite/Readme.md) | [Open learner page](../rewrites/data_formats/shared_exponent_precision_testing_suite/Readme.md) | `seed` |
| 56 | Handling Infinity, NaN and denormal numbers in Tensix compute | [`Handling_Special_Value/special_values.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Handling_Special_Value/special_values.md) | [Open learner page](../rewrites/Handling_Special_Value/special_values.md) | `seed` |
| 57 | Blackhole Bring-Up Programming Guide | [`Blackhole/BlackholeBringUpProgrammingGuide.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Blackhole/BlackholeBringUpProgrammingGuide.md) | [Open learner page](../rewrites/Blackhole/BlackholeBringUpProgrammingGuide.md) | `seed` |

Continue below the report set with the [official TT-LLK and ISA guide](../resources/isa-reference.md) and the [Corsix Wormhole field notes](../resources/corsix-wormhole-series.md).

## Additional foundation document

- [`METALIUM_GUIDE.md`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/METALIUM_GUIDE.md)

## Regenerate this page

```console
python scripts/build_catalog.py
python scripts/check_docs.py
```
