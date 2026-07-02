---
name: mojo-planning-verify-type-semantics-and-source-counts
description: "When planning Mojo code that DEPENDS on load-bearing type/data semantics (AnyTensor value-vs-reference copy semantics for a 'snapshot before mutation' pattern; `@fieldwise_init` constructor shape — positional vs keyword-only — for a factory that passes 80+ arguments; `Tuple[...]` return types mixing multiple struct types) OR that DEPENDS on a specific COUNT of fields/parameters in an existing file, do NOT infer these from analogy, from another skill's summary, or from CLAUDE.md prose. Verify them BY DIRECT PROBE: (1) run the exact grep the plan hinges on and paste the raw output into the plan, (2) build a 20-line throwaway `.mojo` file that exercises `var x = self.field` on the actual struct type and asserts value-copy semantics against later mutation, (3) build a throwaway that instantiates the target struct with the constructor shape the plan assumes (positional or kwargs), (4) build a throwaway that returns the actual mixed Tuple shape. When the task text disagrees with the code (e.g. issue says '~81 params', comment says '84', grep says '82'), the AUTHORITATIVE number is `git show HEAD:<path> | grep -cE '<pattern>'` — cite that command in the plan and stop rounding. Use when: (1) planning a Mojo forward-with-cache / snapshot-before-mutate pattern that assumes `var snap = self.tensor_field` is a value copy, (2) planning a factory that constructs a struct with 10+ fields via `@fieldwise_init` and needs to know positional vs keyword-only, (3) planning a function whose return type is a Tuple mixing AnyTensor with named struct types, (4) reconciling parameter/field counts across issue text + code comments + actual source, (5) any Mojo plan whose correctness rests on a semantics claim you sourced from CLAUDE.md, another skill, or a related struct rather than a compiler run."
category: architecture
date: 2026-07-02
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - planning
  - mojo
  - verify-before-planning
  - anytensor
  - snapshot-semantics
  - value-vs-reference
  - fieldwise-init
  - constructor-shape
  - tuple-return
  - parameter-count
  - grep-authoritative
  - throwaway-build
  - unverified
---

# Mojo Planning: Verify Type Semantics and Source Counts by Direct Probe

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-02 |
| **Objective** | When a Mojo plan depends on load-bearing type semantics (AnyTensor snapshot value-copy, `@fieldwise_init` constructor shape, Tuple return of mixed struct types) or on a specific count of fields in existing source, capture those facts by direct probe (grep + a throwaway `mojo build`) rather than by analogy, another skill's summary, or CLAUDE.md prose |
| **Outcome** | Plan authored for ProjectOdyssey issue #5514 (ResNet-18 forward activation caching + named velocity struct). NOT executed. Reviewer risk list surfaces 5 load-bearing assumptions the plan smuggled in without direct probes: AnyTensor snapshot copy semantics, `Movable` struct with 12–16 AnyTensor fields, 16-element mixed Tuple return type, `@fieldwise_init` 82-arg constructor shape, and trainable-parameter count (82 vs "~81" vs "84 comment") |
| **Verification** | unverified — planning learning only. The plan it came from was never built, no throwaway `.mojo` files were compiled, no `mojo test` (also removed in 1.0 per CLAUDE.md — itself unverified against Mojo release notes) was invoked. Only the `grep` for `^    var .*: AnyTensor` in `examples/resnet18_cifar10/model.mojo` was actually run and returned 82; every other claim (constructor shape, Tuple ergonomics, snapshot semantics) is INFERRED |
| **Category** | architecture / planning |
| **Related Issues** | ProjectOdyssey #5514 |

## When to Use This Skill

Use this skill when planning (not yet implementing) Mojo code and any of the following hold:

- You are about to write `var snap = self.<tensor_field>` BEFORE a call that mutates that field, and the plan's correctness rests on `snap` being a value-independent copy rather than a live reference into shared storage.
- You are designing a `@fieldwise_init` struct with 10+ fields and planning a factory that constructs it — the plan needs to state whether the compiler-generated constructor is positional-only, keyword-supported, or both.
- The plan proposes a function whose return type is `Tuple[...]` with more than ~8 elements OR mixes `AnyTensor` with one or more named struct types.
- The task text, an inline code comment, and the actual source disagree about a COUNT (parameters, fields, layers, blocks). The plan is about to pick one.
- Your plan cites a Mojo-language claim ("`mojo test` was removed in 1.0", "`@fieldwise_init` generates a keyword constructor", "AnyTensor copies are cheap") sourced from CLAUDE.md, another skill's Overview, or a sibling struct's behavior, rather than from a throwaway build against the pinned toolchain.

**Triggers:**

- Plan contains the words "snapshot before", "capture BEFORE X mutates", or "read-before-write pattern" applied to a tensor field.
- Plan contains a factory function that constructs a struct by name with 20+ arguments.
- Plan contains a return type longer than three lines of text.
- Issue body or comment says "~N", "roughly N", "approximately N" for a count in code — this is a signal to grep.
- You caught yourself typing "matches existing behavior" or "same as ResNet18 struct" as justification without running a probe.

## Verified Workflow

> **Warning (Proposed Workflow):** This workflow has NOT been validated end-to-end. Treat it as a hypothesis until CI confirms. Verification level: `unverified` — the plan it came from (ProjectOdyssey #5514) was never built. Only the one grep that returned 82 was run; every other claim (throwaway builds, constructor shape, snapshot semantics) is a PRESCRIPTION, not a confirmed result.

### Step 1 — For every load-bearing semantics claim, list the probe that would prove it

Before writing the plan section that relies on the claim, write a two-line block:

```text
CLAIM:  var snap = self.bn1_running_mean   is a value copy, so a later
        self.bn1_running_mean = new_val    does not mutate snap.
PROBE:  20-line throwaway that instantiates the actual struct, snapshots the
        field, mutates it, and asserts snap != new value. Build with the
        pinned toolchain: `pixi run mojo build /tmp/probe.mojo`.
```

If the probe is not run, mark the claim `UNVERIFIED` in the plan's risk section. Do not silently promote a probe target into a plan assumption.

### Step 2 — For counts, the grep IS the source of truth; cite it

When the issue text, an inline comment, and the source disagree, the answer is the grep against `HEAD`, not the arithmetic in your head:

```bash
# ProjectOdyssey #5514 said "~81 trainable params, NOT the 84 in the comment"
# Authoritative count for `AnyTensor`-typed leaf var declarations in ResNet18:
git show HEAD:examples/resnet18_cifar10/model.mojo \
  | grep -cE '^    var (.*kernel|.*bias|.*gamma|.*beta|fc_weights|fc_bias): AnyTensor'
# → 82
```

Rules:

1. Paste the exact command AND the exact numeric output into the plan.
2. If the number contradicts the issue's "~N", the plan states the discrepancy explicitly and picks the grep result.
3. Do not round "82" back to "~81" to match the issue. The issue was imprecise; the file is not.
4. Beware regex gotchas: exclude BN `running_mean`/`running_var` (not trainable), fold in the FC layer's `weights`/`bias`, and remember that a residual stage with N blocks has PROJECTION layers only where the input channels change (typically 3 projections for ResNet-18 stages 2/3/4, not 4 — check by grepping `projection_kernel` explicitly).

### Step 3 — Snapshot-before-mutate: verify VALUE-copy semantics with a probe, not by analogy

`AnyTensor` may be implemented as a value type, a reference-counted handle over shared storage, or an owning wrapper around an `UnsafePointer`. A "snapshot before BN mutates" pattern is only correct if plain assignment produces an independent value:

```mojo
# /tmp/probe_anytensor_snapshot.mojo — throwaway
from projectodyssey.core.any_tensor import AnyTensor, zeros

fn main() raises:
    var t = zeros[DType.float32]((4,))
    # ... set t[0] = 1.0 via whatever the real API is ...
    var snap = t                     # the pattern the plan relies on
    # ... set t[0] = 2.0 ...
    # PROBE ASSERTION: snap[0] must still equal 1.0
    print(snap[0])                   # expected: 1.0
    print(t[0])                      # expected: 2.0
```

Build with `pixi run mojo build /tmp/probe_anytensor_snapshot.mojo`. If `snap[0]` prints `2.0`, the snapshot pattern in the plan is BROKEN and needs an explicit deep-copy call (or a shape-(C,) tensor materialization) before it can be relied on.

Do NOT substitute reading `src/projectodyssey/core/any_tensor.mojo`'s copy constructor and reasoning about it. A probe is cheaper than an argument.

### Step 4 — `@fieldwise_init` constructor shape: build a 5-field probe, then extrapolate

Before writing `ResNet18Velocities(bn1_gamma=..., bn1_beta=..., ...)` with 82 kwargs, verify the constructor accepts kwargs at all — and confirm error messages if you accidentally omit one:

```mojo
# /tmp/probe_fieldwise_init.mojo — throwaway
from projectodyssey.core.any_tensor import AnyTensor, zeros

@fieldwise_init
struct ProbeStruct(Movable):
    var a: AnyTensor
    var b: AnyTensor
    var c: AnyTensor
    var d: AnyTensor
    var e: AnyTensor

fn main() raises:
    # (A) positional — must work
    var p1 = ProbeStruct(
        zeros[DType.float32]((1,)),
        zeros[DType.float32]((1,)),
        zeros[DType.float32]((1,)),
        zeros[DType.float32]((1,)),
        zeros[DType.float32]((1,)),
    )
    # (B) keyword — MAY OR MAY NOT WORK; the probe tells you
    var p2 = ProbeStruct(
        a=zeros[DType.float32]((1,)),
        b=zeros[DType.float32]((1,)),
        c=zeros[DType.float32]((1,)),
        d=zeros[DType.float32]((1,)),
        e=zeros[DType.float32]((1,)),
    )
```

Interpretation:

- If (B) fails to compile → `@fieldwise_init` is positional-only in the pinned Mojo. Plan an 82-arg POSITIONAL constructor and add a numbered comment above each argument OR introduce a `Builder` pattern. Do not paper over a keyword-only assumption.
- If (A) fails to compile → the struct needs an explicit constructor; `@fieldwise_init` alone is not enough for `Movable` + `AnyTensor` fields. This changes the plan materially.
- If both work → the plan can use kwargs, but STILL prefer positional if the field list is stable, because 82 misordered kwargs are silently valid whereas 82 misordered positionals fail at the type-mismatch site.

### Step 5 — Mixed Tuple returns: probe the actual shape, don't extrapolate from a 3-element example

The plan proposed:

```mojo
fn forward_with_cache(mut self, x: AnyTensor) raises ->
    Tuple[AnyTensor, IdentityCache, IdentityCache, ProjectionCache, IdentityCache,
          ProjectionCache, IdentityCache, ProjectionCache, IdentityCache,
          AnyTensor, AnyTensor, AnyTensor, ...]:
```

Verify that Mojo 1.0 accepts this. A 5-line probe:

```mojo
# /tmp/probe_tuple_return.mojo
from projectodyssey.core.any_tensor import AnyTensor, zeros

@fieldwise_init
struct IdentityCache(Movable):
    var pre: AnyTensor

fn probe() raises -> Tuple[AnyTensor, IdentityCache, AnyTensor]:
    return (zeros[DType.float32]((1,)),
            IdentityCache(zeros[DType.float32]((1,))),
            zeros[DType.float32]((1,)))

fn main() raises:
    var (a, ic, b) = probe()
```

If this fails, the plan's return type is wrong and needs to become a dedicated `ResNet18ForwardCache` struct (which is likely the better design anyway — a named struct beats a 16-tuple for callsite readability).

### Step 6 — When you cite a Mojo-language fact from CLAUDE.md or a skill, mark its provenance

Every Mojo-language claim in the plan gets one of three provenance tags:

- `[PROBE:file.mojo]` — verified by a throwaway build against the pinned toolchain
- `[GREP:cmd]` — verified by a grep against `HEAD` (paste the command)
- `[UNVERIFIED-DOC:source]` — sourced from CLAUDE.md, a sibling skill, or another struct, NOT independently probed

Example:

- "`mojo test` was removed in Mojo 1.0" — `[UNVERIFIED-DOC:CLAUDE.md /.claude/shared/mojo-guidelines.md]`. If the plan's test file MUST run under a specific runner, this claim moves from doc-provenance to probe-provenance before the plan is final.
- "`@fieldwise_init` accepts keyword constructor args" — `[PROBE:probe_fieldwise_init.mojo]` once run; `[UNVERIFIED-DOC:mojo-type-api-migration-and-import-patterns]` until then.

### Quick Reference

```text
1. List every load-bearing semantics claim; for each, name the throwaway probe that proves it.
2. When issue-text ≠ comment ≠ code on a COUNT, grep HEAD and cite the exact command.
3. AnyTensor snapshot pattern: 20-line probe that snapshots, mutates original, asserts snap unchanged.
4. @fieldwise_init factory: 5-field probe testing BOTH positional and kwargs constructors.
5. Mixed Tuple return: 5-line probe that actually returns the shape and destructures it.
6. Tag every Mojo-language claim [PROBE:...], [GREP:...], or [UNVERIFIED-DOC:...] — never bare.
```

```bash
# Authoritative count grep (adapt regex to the real field naming convention):
git show HEAD:examples/resnet18_cifar10/model.mojo \
  | grep -cE '^    var (.*kernel|.*bias|.*gamma|.*beta|fc_weights|fc_bias): AnyTensor'
```

```mojo
# Snapshot-semantics probe skeleton:
var t = zeros[DType.float32]((C,))
var snap = t
# ... mutate t via the ACTUAL API the plan uses (batch_norm2d result assignment) ...
# assert snap has the ORIGINAL value
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust CLAUDE.md's "AnyTensor is Movable, ResNet18 uses AnyTensor fields, therefore ResNet18Velocities with AnyTensor fields is Movable" | Inferred that a 12–16-field `Movable` struct with `AnyTensor` fields will compile because ResNet18 itself compiles with 100+ such fields | Cross-file `Movable` conformance can fail for reasons that do not apply to the reference struct (implicit destructor generation, missing move-init on a field type, `@fieldwise_init` interaction with `Movable`). Analogy is not proof. | Build a 5-field throwaway with the actual field types and the `Movable` trait; only then commit to the design in the plan |
| Assume `@fieldwise_init` generates a keyword-only constructor because that is the pattern in a related skill's Overview | Wrote a factory `initialize_velocities(model)` that constructs `ResNet18Velocities(bn1_gamma=..., ...)` with 82 kwargs | Never probed whether the compiler-generated constructor is positional-only, keyword-optional, or both. A positional-only reality would require rewriting the factory as 82 ordered positional args, which is error-prone and MUST be a plan decision, not a discovery at implementation time. | Write a 5-field probe that instantiates the struct BOTH positionally and by keyword; make the constructor-shape decision explicit in the plan |
| Round the parameter count from the source (82) back to "~81" to match the issue text | Task said "~81, NOT the 84 in comments"; grep gave 82; picked 82 in the plan but wavered on whether to reconcile with the issue | The issue was imprecise; the file is authoritative. Every un-cited "~N" in a plan is a place a reviewer can and will push back on. | Cite the exact grep + numeric result in the plan. State the discrepancy with the issue text openly. Do not average, do not round to match prose |
| Assume `forward_with_cache` returning a 16-element `Tuple` mixing `AnyTensor`/`IdentityCache`/`ProjectionCache` compiles cleanly, without probing | Wrote the return type as `Tuple[..., ..., ..., ...]` across 16 elements and 3 distinct types | Never verified that Mojo 1.0's `Tuple` handles this size and mixed-struct composition ergonomically. If it doesn't compile, the plan's caller signature is invalid; if it does but destructuring is painful at 8 callsites, the ergonomics are still bad. | Probe the exact Tuple shape (or 1/3 of it) in a 5-line throwaway; if painful, propose a dedicated `ResNet18ForwardCache` struct in the plan itself |
| Take "snapshot BEFORE BN mutates" for granted based on `AnyTensor`'s pure-functional signature | Wrote `var bn1_rm_snap = self.bn1_running_mean` before the `batch_norm2d(...)` call; assumed value-copy semantics because the API looks functional | The API being functional does not tell you whether `var x = y` on the underlying struct is a value copy or a reference-count bump into shared storage. A snapshot that shares storage with the mutated field is a subtle data-race / read-your-writes bug that will not be caught by bit-identity tests on the OUTPUT (logits), because the SNAPSHOT is not compared. | Probe: snapshot, mutate original, assert snap unchanged element-wise. This is the linchpin of the whole caching design — a probe is mandatory, not optional |
| Cite "`mojo test` was removed in Mojo 1.0" from CLAUDE.md as a plan invariant without checking Mojo release notes | Plan mandated `mojo run` for the test file instead of `mojo test`, sourced from CLAUDE.md | CLAUDE.md is a project convention doc, not upstream release notes. If it is stale (drift after a Mojo point release), the test-runner choice ripples through the plan. Same class of error as any other "docs told me so" plan claim. | Tag every Mojo-language claim with its provenance: `[PROBE:...]`, `[GREP:...]`, or `[UNVERIFIED-DOC:...]`. Doc-sourced claims that gate the plan's runnability get promoted to `[PROBE]` before the plan is final |

## Results & Parameters

### What the plan produced (design intent — unverified)

- Per-block `IdentityCache` / `ProjectionCache` structs (`@fieldwise_init(Movable)`) capturing per-block intermediate activations.
- A `forward_with_cache(mut self, x)` method on `ResNet18` returning a mixed `Tuple[AnyTensor, IdentityCache, ..., ProjectionCache, ..., AnyTensor]`.
- BN "snapshot BEFORE mutation" pattern: `var bn_rm_snap = self.<...>_running_mean` on the line BEFORE the `batch_norm2d(...)` call, with the result's new running stats written back to `self` afterward.
- A `@fieldwise_init` `ResNet18Velocities(Movable)` struct with one named `AnyTensor` field per trainable parameter, plus an `initialize_velocities(model)` zero-fill factory.
- All changes in `examples/resnet18_cifar10/model.mojo`, growing from 1661 to ~2150 lines (under the 3000-line SRP-split threshold).
- Test file uses `mojo run` (not `mojo test`, which is claimed removed in 1.0 — `[UNVERIFIED-DOC:CLAUDE.md]`).
- Bit-equality test between `forward` and `forward_with_cache` logits via `_data.bitcast[Float32]()` element-wise comparison.

### Most uncertain assumptions / reviewer risks (verify before relying on these)

1. **AnyTensor `var snap = self.field` is a VALUE COPY, not a reference-counted alias.** This is the linchpin of the entire snapshot-before-BN-mutation design. Never probed. If false, the cached BN running stats are silently mutated by the caller's `self.<...>_running_mean = new_val` assignment on the following line, and the "cache is faithful to the forward pass at time-of-forward" invariant is broken. Reviewer action: build the 20-line probe in Step 3.
2. **`struct ResNet18Velocities(Movable)` with 12–16 (per-block) or 82 (flat) `AnyTensor` fields compiles.** Inferred from ResNet18 itself being `Movable`. Cross-struct conformance is not transitive across `@fieldwise_init` and different field-type mixes. Reviewer action: 5-field throwaway with `Movable` + `AnyTensor` fields.
3. **`Tuple[AnyTensor, IdentityCache, IdentityCache, ProjectionCache, IdentityCache, ProjectionCache, IdentityCache, ProjectionCache, IdentityCache, AnyTensor, AnyTensor, AnyTensor, ...]` (16 elements, 3 distinct types) compiles AND destructures cleanly at 8 callsites.** Never verified Mojo 1.0's `Tuple` size limits or ergonomics for mixed-struct composition. Reviewer action: probe with a 3-element `Tuple[AnyTensor, IdentityCache, AnyTensor]` returning function; if that is painful, elevate to a dedicated `ResNet18ForwardCache` struct in the plan.
4. **`initialize_velocities` can construct `ResNet18Velocities(...)` with 82 KEYWORD arguments.** Not verified that `@fieldwise_init` generates a keyword-supporting constructor in the pinned Mojo. A positional-only reality would silently require ordered positional args, and 82 misordered positionals are a class of bug reviewers cannot spot at review time. Reviewer action: 5-field probe with both call shapes.
5. **Trainable-parameter count is 82.** Task text said "~81"; existing comment said "84" (which folds in BN `running_mean`/`running_var`, not trainable). The single grep `^    var (.*kernel|.*bias|.*gamma|.*beta|fc_weights|fc_bias): AnyTensor` returned 82. Off-by-one is credible — could be miscounted projection layers (typically 3 projections at s2b1/s3b1/s4b1, not 4). Reviewer action: rerun the exact grep against `HEAD` and independently count projection layers.
6. **`mojo test` really was removed in Mojo 1.0.** Sourced from CLAUDE.md, not from upstream release notes. If the runner naming changed but the subcommand still exists, the plan's `mojo run tests/...` prescription is not wrong but is not the most idiomatic choice either.

### Generalizable lessons (the durable takeaway)

1. When a plan's correctness rests on a load-bearing Mojo type-semantics claim (value-copy vs. reference-share, constructor shape, trait conformance across struct compositions), a 20-line throwaway `mojo build` is cheaper than an argument from analogy.
2. When issue text, comment, and code disagree on a COUNT, `git show HEAD:<path> | grep -c<pattern>` is the source of truth. Cite the exact command in the plan and stop rounding to match prose.
3. `@fieldwise_init` constructor shape (positional vs keyword) is a plan decision, not a discovery. 80+ kwargs vs 80+ positionals is materially different for correctness and reviewability. Probe before choosing.
4. A Tuple return type longer than three lines of text is a design smell. Probe or promote to a named struct.
5. Every Mojo-language claim in a plan gets a provenance tag: `[PROBE:...]`, `[GREP:...]`, `[UNVERIFIED-DOC:...]`. Bare claims are a bug.
6. The "snapshot before mutation" pattern is only sound if the snapshot is a VALUE. The functionality of the mutating API (its signature, its purity) is orthogonal to that. Prove the snapshot semantics separately.
7. Bit-identical-logits tests do NOT catch snapshot-vs-reference bugs, because the snapshot itself is never compared. Add an explicit snap-vs-post-mutation-original assertion to the test plan when a snapshot pattern is load-bearing.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | Issue #5514 planning | Planning-only; unverified — plan never executed, no throwaway `.mojo` probes were compiled, no `pixi run mojo build` was invoked. Only the `grep` for `^    var .*: AnyTensor` in `examples/resnet18_cifar10/model.mojo` was actually run and returned 82. Every semantics claim (AnyTensor snapshot copy, `@fieldwise_init` kwargs, mixed-Tuple return, `Movable` cross-field conformance) is a PRESCRIPTION for a reviewer to probe, not a confirmed fact |
