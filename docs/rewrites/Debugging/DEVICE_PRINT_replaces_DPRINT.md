<!-- rewrite-status: improved-draft -->
# Deprecating `DPRINT` in favor of `DEVICE_PRINT`

<p class="source-note">
<strong>Original source:</strong>
<a href="https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md"><code>tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md</code> at <code>992f3ca</code></a>
· <strong>Status:</strong> source-grounded learner draft
</p>

## Architecture walkthrough

### Why the design is shaped this way

The legacy `DPRINT` interface coupled three concerns: device-resident format strings,
custom stream-style formatting, and type-specific serialization helpers. Its global
string sections were copied into RISC local data memory, so adding diagnostics increased
the scarce device footprint even when the interesting information was only needed on
the host. `DEVICE_PRINT` separates representation from rendering. Format strings live
in dedicated ELF sections that are not loaded onto the device; the device emits the
arguments needed by a host-side server/parser, which applies fmt-style formatting. The
result is a bounded, more predictable device cost, compile-time checking of
format/argument compatibility, and one extensible path for integers, floats, enums, and
tile slices.

The staged migration was also an architectural decision. During opt-in, both source APIs
existed but only one backend could be active because they shared the same L1 print
buffer. After at least a month of deprecation, `DEVICE_PRINT` became the sole backend
and `DPRINT` remained only as a function-style alias. This preserved a short spelling
without preserving two transports or the incompatible stream ABI.

### How work and data move

A call such as `DEVICE_PRINT("value = {:#010x}\n", value)` is compile-time checked. The
format string stays in the host-only ELF section; the device-side call serializes the
typed value through the common print infrastructure and the host parser combines it
with the retained format description. Enum values can be decoded to names through
DWARF when debug information is available; `{:#}` requests the fully qualified enum
type. `TSLICE(...)` produces a tile or tile-slice value that the same formatter can
render, including floating-point precision such as `{:.4f}`.

Call-site variants select the producer RISC, not a different host pipeline:
`DEVICE_PRINT_MATH`, `DEVICE_PRINT_PACK`, `DEVICE_PRINT_UNPACK`,
`DEVICE_PRINT_DATA0`, and `DEVICE_PRINT_DATA1` scope diagnostics to the corresponding
compute or data-movement role. That makes provenance part of the record at the point of
emission. The old transition flag `TT_METAL_DEVICE_PRINT=1` selected this backend while
legacy DPRINT was compiled out; at the pinned completed state, that flag has been
removed and no opt-in is required.

### What must never break

The format string and argument list must agree at compile time, and the selected macro
must identify the intended RISC. `TSLICE` parameters—CB id, tile index, range, CB kind,
read-pointer choice, coordinate printing, and tilized state—must describe the actual
buffer representation; a beautifully formatted wrong slice is still bad evidence. Only
one print implementation may own the shared L1 buffer. Finally, printing is observation,
not synchronization: it must not become an assumed CB, NoC, or producer-consumer
barrier. High print volume can perturb timing, so disappearance of a race while printing
does not establish correctness.

### Where the report makes it concrete

Migration is source-level, not just token substitution. `DEC()`, `HEX()`, `OCT()`,
`BIN()`, and `SETW()` become fmt specifiers such as `{0}`, `{0:#010x}`, `{0:o}`, and
`{0:b}`. Manual enum switch statements can become `DEVICE_PRINT("Mode: {}\n", mode)`.
Stream code such as `DPRINT << "value" << ENDL()` no longer compiles because the
remaining `DPRINT` macro forwards only function-style calls like
`DPRINT("value = {}\n", v)`. This compile failure is intentional: silently accepting
the old syntax would require retaining the old stream implementation and its footprint.

### How the decision is tested

Compile a small kernel that exercises an integer in decimal/hex, a float with precision,
an enum, and one known `TSLICE`, once with each RISC-specific macro. Deliberately mismatch
a format and argument to confirm compile-time rejection, and compile one legacy
stream-style statement to confirm the documented migration failure. Then compare device
memory footprint as print sites are added: the pinned design predicts that host-only
format strings do not scale RISC LDM consumption the way legacy DPRINT did. Run the
functional kernel with printing disabled and enabled, verifying identical output while
measuring perturbation. These tests separately establish type checking, provenance,
format correctness, footprint behavior, and observer overhead.

## Code connection

Review these concrete implementation boundaries against the
[pinned source](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md):

- **Compile-time surface.** The old `DPRINT << value << ENDL()` stream syntax and the
  replacement `DEVICE_PRINT` macros generate different device-side records. Use the
  include and invocation form that belongs to the pinned runtime; mixing the two
  surfaces can fail at compilation before any device output exists.

- **Runtime transport.** `TT_METAL_DEVICE_PRINT=1` selected the new backend only during
  the documented transition; the report says the flag was later removed when
  `DEVICE_PRINT` became the sole backend. For the pinned phase being studied, separate
  backend selection from core/thread filtering, device-buffer transport, and host drain.

## Verify your understanding

The answers below are derived from the
[pinned original report](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md). They make the report's
architecture reasoning explicit; generation-sensitive facts remain scoped to that source.

### 1. What concrete bottleneck, correctness constraint, or programming task is this report addressing?

???+ note "Expert answer — source-grounded reasoning"
    The programming task is migrating kernel diagnostics from `DPRINT` to `DEVICE_PRINT`
    while preserving useful device-side visibility and removing reliance on a deprecated
    interface. The constraint is that debugging output crosses a device/host boundary
    with limited buffering.

### 2. What is one invariant that must remain true?

???+ note "Expert answer — source-grounded reasoning"
    A print record must be emitted only from the intended core/RISC, remain well formed
    in the device debug buffer, and be drained before teardown. Adding a print must not
    be mistaken for synchronization or change the correctness contract of the kernel
    being observed.

### 3. Trace one unit of data or one control event from producer to consumer.

???+ note "Expert answer — source-grounded reasoning"
    A selected device thread reaches a diagnostic point → `DEVICE_PRINT` encodes text
    and values into the debug transport → runtime support drains the record → the host
    formats it on the console/log → the developer correlates it with the issuing core
    and program point.

### 4. Which claims are architecture-specific, and which form a durable mental model across Tenstorrent generations?

???+ note "Expert answer — source-grounded reasoning"
    **Snapshot-specific.** Macro syntax, enable flags, supported value types, buffer
    capacities, core-selection controls, and the deprecation timeline are
    revision-specific.

    **Durable model.** Keep instrumentation scoped, identify the producer, account for
    buffering and perturbation, flush before shutdown, and use printing to test a
    hypothesis rather than as a substitute for ownership or completion primitives.

## Source and delta

- **Original source:** [`tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md` at `992f3ca`](https://github.com/tenstorrent/tt-metal/blob/992f3ca634aac8733c70e48da395aab5361b4166/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md)
- **Local immutable baseline:** `upstream/tt-metal/tech_reports/Debugging/DEVICE_PRINT_replaces_DPRINT.md`
- **Current delta:** source-grounded architecture walkthrough, concrete
  implementation boundaries, and expert verification answers. Snapshot-specific claims
  remain scoped to the pinned commit.
