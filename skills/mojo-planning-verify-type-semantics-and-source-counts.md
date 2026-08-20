---
name: mojo-planning-verify-type-semantics-and-source-counts
description: "Verify load-bearing Mojo type semantics and source counts before planning. Use when correctness depends on tensor snapshot behavior, @fieldwise_init constructor shape, mixed Tuple feasibility, or a field/parameter count disputed by prose and code."
category: architecture
date: 2026-07-02
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: mojo-planning-verify-type-semantics-and-source-counts.history
tags:
  - mojo
  - planning
  - direct-probe
  - anytensor
  - fieldwise-init
  - tuple
  - source-count
  - verification
---

# Mojo Planning: Verify Semantics and Source Counts

## Overview

Do not base a Mojo plan on language folklore, another skill's summary, comments, or an analogous
type. Bind the toolchain and commit, run the exact source query that supports each count, and compile
a minimal probe against the actual types and syntax whenever semantics determine the design.

ProjectOdyssey issue #5514's R1 review directly inspected the pinned source and resolved the key
claims locally; the planned feature itself was not implemented or CI-verified. Case provenance is
in
[mojo-planning-verify-type-semantics-and-source-counts.notes.md](mojo-planning-verify-type-semantics-and-source-counts.notes.md),
and the complete prior version is in
[mojo-planning-verify-type-semantics-and-source-counts.history](mojo-planning-verify-type-semantics-and-source-counts.history).

## When to Use

- A plan snapshots a tensor field before a later mutation and assumes copy independence.
- A factory passes many named arguments to a `@fieldwise_init` struct.
- A proposed return type mixes tensors and named structs or contains many tuple elements.
- Issue text, comments, and source disagree about a parameter, field, or layer count.
- A statement about Mojo syntax or semantics came from prose rather than the pinned compiler.
- The plan says “matches existing behavior” without naming a source location or executable probe.

## Verified Workflow

### 1. Make a claim-to-probe ledger

For every load-bearing claim, record:

| Claim | Source inspection | Compiler probe | Decision if false |
| --- | --- | --- | --- |
| Tensor assignment is a safe snapshot | Actual type conformances/storage docs | Copy, mutate, assert old value | Explicit clone/copy path |
| Fieldwise constructor accepts keywords | Actual struct and call sites | Compile named arguments | Positional factory or explicit constructor |
| Return shape is supported and maintainable | Largest comparable shapes in tree | Compile exact signature | Named result struct |
| Count equals N | Immutable-source grep | Not normally needed | Use observed exact count |

Pin the repository SHA and toolchain version beside the ledger. A read from another branch or Mojo
version does not prove the target environment.

### 2. Derive counts from immutable source

Use the exact revision and pattern the plan will cite:

```bash
git show "$BASE_SHA:path/to/model.mojo" | grep -cE '^    var [A-Za-z_][A-Za-z0-9_]*: AnyTensor'
```

Paste raw output and explain inclusions/exclusions. Do not round `82` to “about 81,” or copy a
comment saying `84` if it counts two non-trainable running-stat tensors. If the plan later changes
the file, recompute from the implementation head.

### 3. Probe snapshot semantics on the actual type

First inspect conformances and storage documentation:

```bash
rg -n 'struct AnyTensor|Copyable|ImplicitlyCopyable|Movable|refcount|shared storage' src
```

Then compile and run a small disposable program using the actual construction and mutation APIs:

```mojo
fn main() raises:
    var original = make_test_tensor()
    var snapshot = original
    mutate_like_target_code(inout original)
    assert_equal(snapshot, expected_before_mutation())
```

“Refcounted” can mean assignment shares storage while replacement preserves the old allocation, or
that in-place mutation is visible through both values. The probe must use the exact mutation shape
the plan relies on. Keep the probe outside the product tree unless it becomes a maintained behavior
test.

### 4. Probe the generated constructor shape

Search a real fieldwise struct and its call sites, then compile the exact named-argument style:

```mojo
@fieldwise_init
struct Probe:
    var left: Int
    var right: Float64

fn main():
    var value = Probe(left=1, right=2.0)
```

Start with a small syntax probe, then build a probe using the target struct and pinned toolchain.
Constructor support does not prove an 80-field call is readable; a factory or named configuration
may still be the better interface.

### 5. Verify compound return shapes

Inventory comparable tuples in the codebase and compile the proposed signature. A codebase maximum
is design evidence, not a language limit. If a large mixed tuple has positional ambiguity or lacks
precedent, prefer a named fieldwise result struct even if a compiler probe succeeds.

```mojo
@fieldwise_init
struct ForwardCache:
    var output: AnyTensor
    var activation: AnyTensor
    var velocity: VelocityState
```

A named result improves ownership, evolution, and call-site clarity. Test construction, return, and
destructuring/access using the exact types.

### 6. Record provenance and residual risk

Mark each plan statement as one of:

- observed from immutable source;
- compiled/run against the pinned toolchain;
- inferred design choice;
- unresolved and requiring implementation-time verification.

Direct source reads can establish conformances, call syntax in existing code, and corpus counts.
Only execution establishes runtime mutation behavior. Do not upgrade the whole plan to verified
because several linchpin reads succeeded.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Trust an issue's approximate count | Prose and comments included different categories | Count immutable source with an explicit pattern |
| 2 | Infer AnyTensor behavior from another tensor type | Storage and mutation semantics can differ | Probe the actual type and mutation |
| 3 | Assume fieldwise constructors are positional-only | Existing pinned call sites used keywords | Read and compile the exact constructor form |
| 4 | Treat the largest observed tuple as a language maximum | Corpus precedent is not compiler specification | Compile exact shape, then apply maintainability judgment |
| 5 | Return a 16-element mixed tuple because syntax seems legal | Positional API is unsupported by local precedent and fragile | Use a named fieldwise result struct |
| 6 | Cite CLAUDE.md or another skill as semantic proof | Prose can lag toolchain and source | Record provenance and run a direct probe |

## Results & Parameters

- Source case parameter count: 82 trainable `AnyTensor` fields; the `84` comment included two
  non-trainable running statistics.
- Existing source showed keyword construction for `@fieldwise_init`.
- `AnyTensor` source declared refcounted shared storage plus `Copyable`, `ImplicitlyCopyable`, and
  `Movable`; this supported the replacement-style snapshot idiom inspected in R1.
- Largest comparable tuple observed in the pinned codebase: six elements; the plan replaced a
  proposed 16-element mixed tuple with a named result struct.
- Full feature build and CI remained pending, so verification stays `verified-local`.

## Evidence Boundary

The R1 source probes are local evidence tied to the recorded ProjectOdyssey revision. They do not
prove all mutation forms, later Mojo releases, or the unimplemented target feature. Re-run the
source queries and executable probes against the implementation head.
