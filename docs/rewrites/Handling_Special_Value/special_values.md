<!-- rewrite-status: improved-draft -->
# Handling Infinity, NaN and denormal numbers in Tensix compute

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Handling_Special_Value/special_values.md"><code>tech_reports/Handling_Special_Value/special_values.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The design is shaped by the need to specify expected NaN, ±Inf, denormal, saturation,
and approximate-mode behavior at stored format, Unpack, Math/SFPU, destination, and Pack
boundaries for the architecture/configuration being studied.

### How work and data move

The complete path is explicit input bit patterns through L1 storage, format
interpretation, compute operation, destination accumulation, output conversion, stored
result, and host/device classification observation.

### What must never break

The non-negotiable invariant is that classification is performed on the representation
that actually reaches each stage and distinguish documented
propagation/canonicalization/flush behavior from host IEEE-754 assumptions.

### Where the report makes it concrete

The report makes the decision concrete by connecting the report's `NaN` and `+/-Inf`
representation/detection rules to the architecture-matched Unpacker, Math/SFPU, Dst, and
Packer ISA/LLK paths used by a minimal kernel.

### How the decision is tested

The controlled procedure is to inject normal, subnormal, ±0, ±Inf, quiet/signaling NaN
patterns through one operation and format conversion. **Expected observation:** each
boundary matches the documented class/bit behavior and localizes any change.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Handling_Special_Value/special_values.md):

- **Representation boundary.** The report's NaN and ±Inf bit rules describe stored
  formats and architecture-specific conversion behavior. Test exact input patterns at
  L1, after Unpack, in Math/SFPU or `Dst`, and after Pack so a classification change is
  assigned to the unit that caused it.

- **ISA/LLK boundary.** Follow the minimal kernel through the architecture-matched
  Unpacker, Math/SFPU, destination-state, and Packer documentation. Host IEEE-754
  behavior is a reference observation, not proof that Tensix canonicalization,
  approximation, or flush behavior is identical.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Handling_Special_Value/special_values.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The report asks how infinity, NaN, and denormal values are represented, detected,
    transformed, and debugged across Tensix unpack, compute, and pack paths, where
    behavior may differ from a host CPU's full IEEE-754 expectations.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    Classification must be performed on the representation that actually reaches the
    relevant stage. A value changed by input format conversion, flush-to-zero,
    approximate math, or output packing cannot be diagnosed correctly from its original
    host bits alone.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    Host-created special-value bits enter a stored tensor → unpackers convert them to
    the internal compute representation → math units propagate, clamp, flush, or
    generate special values according to mode → packers encode the result → host
    readback or device diagnostics inspect the final bits/classification.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Supported encodings, denormal policy, approximate-mode
    behavior, detection idioms, and pack/unpack treatment depend on data format, Tensix
    generation, and compute configuration.

    **Durable model.** Document floating-point behavior at every representation
    boundary, test classes rather than only ordinary values, distinguish payload bits
    from semantic class, and verify special-value propagation with small targeted
    kernels.

## Source and delta

- **Original source:** [`tech_reports/Handling_Special_Value/special_values.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Handling_Special_Value/special_values.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Handling_Special_Value/special_values.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
