---
name: persistence-backing-store-test-harness-driven-choice
description: "Plan durable backing for an existing C++ in-memory store by choosing technology from the real test harness and de-risking dependency, warning, path, error, and restore contracts. Use when embedded versus networked storage, Conan versus fetched C code, per-target -Werror, silent writes, or partial restart reconstruction are unresolved."
category: architecture
date: 2026-06-20
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: unverified
history: persistence-backing-store-test-harness-driven-choice.history
tags: [persistence, backing-store, sqlite, test-harness, conan, cmake, durability, planning]
---

# Persistence Backing-Store Choice from the Test Harness

## Overview

Let existing deterministic test infrastructure constrain the backing store. A network service is a
poor unit-test dependency when today’s suite runs without it. Then de-risk the selected embedded
store against the repository’s actual dependency mechanism, per-target compiler/static-analysis
gates, durable path, complete restore surface, and observable acceptance criteria.

This skill remains unverified. Planning cases are indexed in
[`persistence-backing-store-test-harness-driven-choice.notes.md`](persistence-backing-store-test-harness-driven-choice.notes.md),
and the complete prior source is in
[`persistence-backing-store-test-harness-driven-choice.history`](persistence-backing-store-test-harness-driven-choice.history).

## When to Use

- Adding durable backing behind an in-memory C++ repository/store.
- Choosing embedded SQLite versus networked JetStream/KV or similar infrastructure.
- Introducing a C/C++ dependency through package manager or handwritten fetch/build.
- Raw C API code must pass `-Werror`, clang-tidy, and cppcheck.
- Tests must run without a live server and use isolated storage.
- Review finds ignored storage errors, incomplete load reconstruction, or cwd-relative data files.

## Verified Workflow

> Status: proposed and unverified. Run every verify-first gate and build/test step before claiming the
> design works.

### 1. Inventory the actual harness and ownership model

Read how unit/integration tests construct the service, whether they start a network dependency, how
server absence is handled, and whether multiple service instances share one store file. Do not let a
generic “multi-writer” concern drive the design until code proves shared ownership.

Decision rule:

```text
suite runs without network service -> prefer an in-process embedded store
network service already deterministic prerequisite -> networked store may be defensible
```

A stream configured for file storage proves stream durability, not persistence of separate in-memory
maps. Match the durability target exactly.

### 2. Use the repository’s proven dependency mechanism

Inspect Conan/vcpkg/manifest and generated CMake target conventions. Prefer a pinned package-manager
recipe and imported target over a guessed archive URL and self-compiled amalgamation. Before writing
the plan as fact, run dependency resolution and read the generated config to confirm the available
recipe version and exact target name.

```bash
just deps
# or the repository's conan/vcpkg install command
rg -n 'add_library|IMPORTED|SQLite' <generated-config-root>
```

Keep unresolved version/target names explicitly marked placeholders. A prebuilt dependency also keeps
third-party source out of the project’s own `-Werror` compilation.

### 3. Separate compiler warnings from static analysis

Two independent gates need different remedies:

```text
compiler -Wxxx/-Werror -> code/casts or scoped -Wno-xxx compile options
clang-tidy/cppcheck    -> code change or targeted NOLINT/inline suppression
```

`NOLINT` does not suppress compiler errors. Inspect which CMake target compiles each new source;
warning policy is per target. Isolate unavoidable raw-C-API noise in a dedicated store library that
mirrors an existing narrow suppression precedent and links into service plus tests. Do not relax the
strict main library or assume the precedent covers warnings not yet observed.

### 4. Define durability failures as operation failures

Check and propagate every prepare, bind, step, finalize, transaction, and close result with backend
diagnostics. Mutate the in-memory cache only when the durable operation succeeds or define a rollback
that restores consistency. Silent success on disk-full/locked storage voids the audit guarantee.

Open one native handle for object lifetime, initialize schema/WAL deliberately, load on construction,
and persist every mutation while holding the existing store lock. Do not batch the only save at clean
shutdown; crashes happen before shutdown.

### 5. Preserve API and deterministic tests

Use a defaulted path constructor so existing `Store store;` call sites still compile, while tests pass
an isolated `:memory:` or temporary file path. Restart tests must exercise the real persistence path:
create/mutate, destroy, reopen the same file, and assert entities plus all statistics/state.

Clean database, WAL, and shared-memory sidecars per test. Cite the current API response shape instead
of guessing nested JSON identifiers.

### 6. Make restore total over the read API

Enumerate every value exposed after restart—pending, active, completed, or domain equivalents. Persist
the source row/status required to reconstruct them and recompute derived counters from rows. A load
path that maps only some states silently corrupts the public read model.

Create a state-to-counter table and tests for every row. Do not trust stored aggregate counters that
can drift from source entities.

### 7. Use a stable absolute default path

Resolve under a location such as `$XDG_STATE_HOME` with a documented user-state fallback, create the
parent with `std::filesystem::create_directories`, and return an absolute path. A bare relative DB
name opens a different empty store after a cwd change. Avoid string-interpolated `system("mkdir")`;
it adds shell injection and portability risks.

### 8. Map every acceptance criterion to evidence

Include commands for dependency resolution, compile, static analysis, ctest, restart survival, every
counter, write-error injection, cwd change, and absence of forbidden recovery actions. An acceptance
criterion about “no manual apply-all” needs an observable assertion that the restart path makes no
such call.

If two independently versioned repositories require similar store adapters, acknowledge intentional
duplication rather than coupling them through an unjustified shared build location.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Reuse network stack | Chose JetStream because it existed | Unit suite had no live server; stream did not store maps | Harness and data target choose store |
| Guessed fetch URL | Added handwritten amalgamation archive | Availability/build were unverified | Use existing package manager |
| Self-built dependency | Compiled third-party C under project gates | `-Werror` applied to vendor code | Prefer imported binary target |
| NOLINT for `-Werror` | Used static-analysis comment for compiler warning | Mechanisms are independent | Use casts/scoped compiler options |
| Repo-wide warning assumption | Ignored per-target CMake policy | Source compiled under different flags | Inspect and isolate exact target |
| Ignored return codes | Updated cache after failed durable write | Reported success without audit trail | Check every backend result |
| Partial restore | Recomputed pending/completed only | Active state silently changed | Make load total over public reads |
| Relative DB path | Used `service.db` | Restart from new cwd appeared to lose data | Use stable absolute state path |
| Save at shutdown | Deferred all persistence | Crash lost every mutation | Save incrementally inside lock |
| Claimed placeholder target | Assumed recipe/target spelling | Dependency resolution was never run | Verify generated package config first |

## Results & Parameters

```text
current test harness and live-service requirements
store ownership/multi-writer evidence
backing-store decision and rejected alternative
package manager, proposed recipe, verified imported target
CMake source target and compiler/static-analysis gates
scoped warning dispositions from actual tool output
backend result checks and cache/durable ordering
schema/status mapping and total restore table
constructor/default absolute path/test override
restart, sidecar cleanup, error injection, cwd-change tests
acceptance criterion to command/assertion mapping
```

## Verified On

- Odysseus issue #71 planning and two review revisions.
- Repository configuration was read, but no dependency resolution, compilation, lint, or tests ran.
- Overall verification remains `unverified`.
