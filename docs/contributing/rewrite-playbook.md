# Architecture claim review: from plausible prose to causal proof

A useful Tenstorrent explanation must do more than repeat a report accurately.
It must preserve the report’s scope, expose the ownership and dataflow that make
the design work, and name an observation that could prove the explanation wrong.
This chapter demonstrates that review as an engineering skill.

Use the [source trust guide](../reference/provenance.md) to classify evidence and
the [architecture dependency map](../reference/rewrite-roadmap.md) to locate the
layer that owns the claim.

## The four proofs an architecture explanation needs

| Proof | Reviewer asks | Failure when missing |
|---|---|---|
| **Scope** | Which device generation, software revision, shape, format, and execution mode does this claim cover? | A Wormhole or pinned-revision fact becomes a universal Tenstorrent claim |
| **Mechanism** | Which actors, state, and ownership transitions cause the result? | A feature list substitutes for an explanation |
| **Invariant** | What must remain true while the mechanism changes placement, timing, or representation? | Performance improves in the story while correctness becomes undefined |
| **Observation** | Which value, address, counter, or timeline region should change—and what rejects the claim? | The explanation cannot be separated from other plausible causes |

All four are necessary. A correctly cited claim can still be architecturally
weak if it never connects mechanism to outcome. A convincing mechanism can
still be unsafe if it omits the invariant.

## Review from the consumer backward

Start at the externally visible result and move backward until reaching the
component that owns the first disputed state:

`model result` ← `operation output` ← `writer/pack` ← `compute` ←
`reader/unpack` ← `NoC or DRAM` ← `runtime dispatch`

At every boundary record:

1. the object that crosses the boundary;
2. its producer and next consumer;
3. the state proving that the object is ready;
4. the state proving that its storage may be reused; and
5. the architecture/revision assumptions needed by the claim.

This backward method exposes missing links. For example, “the NoC write
completed” does not prove a circular-buffer page became consumer-visible;
publication is a separate ownership transition.

## Worked review — NoC tile transfer

Consider the claim: **a write barrier makes the destination tile safe to
consume.** It sounds plausible but is incomplete.

The pinned
[NoC tile-transfer report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/prog_examples/NoC_tile_transfer/NoC_tile_transfer.md)
contains a two-core, one-tile protocol. Review one tile from destination
ownership backward:

1. The destination writer may consume only after its local circular buffer has
   a front page.
2. The destination reader may publish that page only after the remote bytes have
   arrived.
3. The source signals arrival only after its asynchronous NoC write barrier.
4. The source may write only after the destination reserved the exact back page
   and signaled readiness.

The complete causal chain is:

`reserve destination` → `signal credit` → `remote write` → `write barrier` →
`signal arrival` → `publish page` → `consume` → `release`

### Review conclusion

The barrier proves completion of movement issued by the source RISC. The remote
arrival signal transfers that fact between cores. The destination’s
`cb_push_back` publishes local ownership to its consumer. Removing any one of
these three proof layers makes the original claim false or incomplete.

For multiple tiles, the review must additionally prove that credits and arrival
events cannot be confused between transactions. A one-bit signal is safe only
under serialization; pipelining requires sufficient buffer depth and a count or
sequence discipline.

## Worked review — matrix-engine throughput

Consider: **the matrix engine provides 4 TFLOPS.** A reviewer must reconstruct
the numerator, denominator, and scope before accepting it.

The pinned
[matrix-engine report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/matrix_engine/matrix_engine.md)
describes a native LoFi operation shaped as
`(8×16) × (16×16) → (8×16)`. That is 2,048 multiply-accumulates, conventionally
counted as 4,096 floating-point operations. At the report’s 1 GHz assumption,
the arithmetic ceiling is 4 TFLOPS per matrix engine.

The number does **not** establish application throughput. Review the factors
that can narrow it:

- fewer than eight useful output rows waste native row lanes;
- HiFi2/3/4 require additional fidelity passes;
- unpack, pack, NoC, circular-buffer, and instruction overhead consume time;
- destination format changes live capacity and therefore blocking; and
- a different architecture must use its matching official ISA description.

The current official ISA repository has separate
[Wormhole B0](https://github.com/tenstorrent/tt-isa-documentation/tree/main/WormholeB0/TensixTile/TensixCoprocessor)
and
[Blackhole A0](https://github.com/tenstorrent/tt-isa-documentation/tree/main/BlackholeA0/TensixTile/TensixCoprocessor)
coprocessor trees. Similar unit names are not proof of identical capacity,
encoding, or timing.

### Review conclusion

“4 TFLOPS” is accepted only as the pinned report’s LoFi arithmetic ceiling
under its stated work shape and clock convention. A measured claim must record
hardware, clocks, fidelity, useful-lane fraction, shape, formats, and whether
movement is included.

## Worked review — TensorAccessor cost

Consider: **static rank makes TensorAccessor construction free and address cost
is linear in rank.** This overreaches.

The pinned
[TensorAccessor report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/tensor_accessor/tensor_accessor.md)
supports the qualitative mechanism: compile-time rank allows specialization and
removes runtime rank metadata; iterators can retain traversal state instead of
reconstructing a mapping for every page. It does not create a universal cycle
law across architectures, layouts, compiler versions, and access patterns.

### Review conclusion

State the durable trade-off: static structure permits more compile-time
specialization, while runtime rank buys flexibility with additional carried
state and work. Measure direct lookup versus iterator traversal for the exact
rank, layout, sharding, compiler, and device. “Zero cost” and a fixed cycle
formula require disassembly or benchmark evidence that the report does not
provide.

## Detect architectural overclaiming

Use these transformations during review:

| Weak statement | Stronger reviewed statement |
|---|---|
| “L1 is faster.” | “For this access pattern, keeping pages in the consuming core’s L1 removes the measured DRAM/NoC interval; allocation and reshard cost are included.” |
| “Fast Dispatch speeds up kernels.” | “Fast Dispatch reduces the observed host submission gaps; device-kernel duration remains approximately unchanged.” |
| “Multicast is optimal.” | “For N consumers of the same block, multicast reduces repeated injection bytes enough to offset added synchronization and L1 pressure.” |
| “The barrier synchronizes everything.” | “This barrier proves completion of the issuing engine’s outstanding movement; separate events and buffer publication establish cross-core ordering and ownership.” |
| “Blackhole works the same.” | “The durable pipeline model transfers; capacities, state, and instruction behavior are checked in the Blackhole A0 source.” |

The stronger version identifies scope, mechanism, price, and a falsifiable
observation.

## Numeric-claim review

For every number, reconstruct:

1. **Meaning:** capacity, peak, measured result, latency, count, or example value.
2. **Unit:** bytes versus pages, MACs versus FLOPs, cycles versus time.
3. **Scope:** architecture, revision, clocks, formats, shapes, and execution mode.
4. **Derivation:** copied specification, arithmetic from documented primitives,
   or measurement.
5. **Use:** whether the explanation depends on the exact value or only the
   underlying trade-off.

If the value is not supported, remove it or label it as an example. If the
reasoning survives after the number changes, state that durable principle
separately.

## Symbol and source review

A named symbol is useful only when it closes a reasoning edge. For each symbol:

- link the commit-pinned report or source file that contains it;
- state whether it creates state, moves bytes, orders events, or exposes
  measurement;
- avoid treating a current `main` symbol as evidence for an older snapshot;
- distinguish public contract from implementation detail; and
- verify that a renamed symbol does not silently change semantics.

DeepWiki can discover the file, but the official source or test must establish
the claim. Community analysis can motivate a hypothesis, but generation-matched
official material and observation decide its scope.

## Review questions and expert answers

### 1. A page matches every sentence in its pinned report. Is the explanation complete?

???+ note "Expert answer — reasoning"
    No. Textual fidelity proves provenance, not understanding. The learner still
    needs the causal mechanism: actors, movement, ownership, ordering, invariant,
    trade-off, and a falsifying observation. Otherwise the page is an accurate
    paraphrase rather than an architecture explanation.

### 2. When should a review descend to ISA documentation?

???+ note "Expert answer — reasoning"
    Descend only when upper-level evidence localizes the question to an engine,
    format, state transition, or instruction. Carry a concrete kernel and TT-LLK
    call path downward, then reconnect the low-level observation to operation or
    workload behavior. ISA detail without that chain is interesting but not
    causal proof.

### 3. Why can a current-source check disagree with a pinned report without either being wrong?

???+ note "Expert answer — reasoning"
    They may describe different revisions, architectures, APIs, or execution
    modes. First align those scopes. Preserve the pinned claim as historical
    evidence, describe the current behavior separately, and identify the code or
    document change that explains the difference.

### 4. What result should prevent a documentation-only review from claiming hardware verification?

???+ note "Expert answer — reasoning"
    Absence of a reproduced architecture-sensitive observation is sufficient.
    Source review can establish internal consistency and revision scope, but it
    cannot prove cycle cost, throughput, numerical edge behavior, or silicon
    timing. Keep those claims qualified until a matching simulator or hardware
    experiment supplies the evidence.

## The transferable review habit

The durable habit is simple: narrow the claim until one component owns it,
follow one concrete unit across every relevant boundary, state the invariant,
and predict the observation that would reject the explanation. This method
transfers to other NPU systems even when their APIs, engines, and interconnects
have different names.
