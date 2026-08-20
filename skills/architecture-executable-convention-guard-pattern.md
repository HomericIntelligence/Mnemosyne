---
name: architecture-executable-convention-guard-pattern
description: >-
  Turn a prose-only invariant into a reusable, blocking check without changing the
  signal it observes. Use for absence/marker checks, mirror parity, scoped membership,
  commit trailers, install/package smoke tests, canonical CI checks, release-pipeline
  validation, and documentation catalogs whose completeness must be enforced.
category: architecture
date: 2026-07-17
version: "2.0.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
history: architecture-executable-convention-guard-pattern.history
tags: [executable-convention, invariant-guard, fail-safe, read-only-verification, ci-gate, bidirectional-invariant, scoped-membership, negative-branch-test, docs-catalog-completeness]
---

# Architecture: Executable Convention Guard Pattern

**Supporting cases:** [notes](./architecture-executable-convention-guard-pattern.notes.md)

**Superseded content:** [history](./architecture-executable-convention-guard-pattern.history)

## Overview

An executable convention converts a documented claim into one predicate, one stable
machine-readable result, and one blocking integration point. Prefer a small importable
library plus a thin CLI. The checker must observe its inputs read-only, exercise its own
failure branches, and guard the exact population and direction promised by the issue.

This skill is `verified-local`: several patterns were executed locally, while the release
validator, scoped population, and some catalog/table variants remain explicitly proposed.
Consult the notes before treating a project case as CI-proven.

## When to Use

- A marker, log line, artifact, trailer, table row, package, or tracked file is required,
  but the requirement lives only in prose.
- A mirror/parity check asserts only `A - B` and may miss the reverse `B - A` defect.
- A checker iterates a population whose siblings are only partially compliant; the issue
  names a narrower target set.
- Absence is meaningful and a resolver or setup path might create the missing artifact.
- A canonical `install`, `package`, or `release` check must perform real work rather than
  publish a fabricated green status.
- A tag-only publisher needs PR/main validation without publishing or rebuilding twice.
- A human-facing catalog claims to enumerate tracked files and needs a completeness test.

## Verified Workflow

1. **State the invariant in set or verdict form.** Name both sides, the population, allowed
   exceptions, and whether enforcement is membership-only or also validates metadata.
2. **Inventory existing enforcement.** Search workflows, pre-commit, tests, scripts, and
   console entry points. Extend the repository's existing altitude instead of creating a
   parallel framework or a CI step that never runs.
3. **Resolve inputs read-only.** A verification path must not `mkdir`, touch, repair, or
   infer the evidence it is checking. Separate preparation from observation.
4. **Implement a reusable predicate.** Return structured findings or a small verdict enum;
   keep process exit, JSON/text formatting, and argument parsing in the CLI adapter.
5. **Choose a collision-free contract.** Inspect sibling CLIs before selecting an exit code.
   Keep `2` for usage errors. A common contract is `0=proved`, `3=not proved`, while
   execution faults use another documented code.
6. **Anchor evidence structurally.** Match a log marker at the start of a line, a Markdown
   catalog entry by backticked relative path, and a commit trailer in the trailer block.
   Do not use a free substring that user-controlled text can spoof.
7. **Test positive and negative branches.** Mutate a throwaway input to remove or corrupt
   the signal. An always-on self-test prevents a permanently green checker.
8. **Wire the same checker everywhere.** Unit tests, CLI, pre-commit, and CI should call the
   same implementation. Emit the check before making its status required.
9. **Run the shipped-tree acceptance test.** The new guard must pass the current repository
   for the issue's intended scope and fail on a synthetic defect.

### Core contract

```python
from enum import Enum
from pathlib import Path

class Verdict(Enum):
    OK = "OK"
    RAN_WITH_ERRORS = "RAN_WITH_ERRORS"
    NOT_RUN = "NOT_RUN"

def classify(log_path: Path) -> Verdict:
    # Read only: never create log_path or its parent here.
    lines = log_path.read_text(errors="replace").splitlines()
    if any(line.startswith("HANDLER_OK:") for line in lines):
        return Verdict.OK
    if any(line.startswith("HANDLER_ERROR:") for line in lines):
        return Verdict.RAN_WITH_ERRORS
    return Verdict.NOT_RUN
```

The blocking condition is `NOT_RUN`; `RAN_WITH_ERRORS` proves invocation but may be handled
by a separate execution-success policy. Keep those claims distinct.

### Bidirectional parity and allowlists

For mirrored sets `source` and `target`, calculate both differences:

- `source - target`: required target entries are missing.
- `target - source`: target contains ghosts or intentional exceptions.

Do not delete reverse-only entries automatically. Classify them, then encode intentional
exceptions in a narrow allowlist with an owner and rationale. Fail if an allowlisted item no
longer needs its exception so the allowlist cannot become a permanent junk drawer.

For mixed doc tables, guard only the verifiable invariant. If symbol membership comes from
`__all__` but an "Added" version is historical inference, compare membership in both
directions and leave the inferred column out of the executable claim.

### Scope the population

When the issue names specific targets, pass those targets explicitly to the checker and
scope workflow/pre-commit path filters to the same set. Expanding to every sibling can make
the guard fail on pre-existing noncompliance and violate the issue boundary. A repository-
wide invariant requires either a clean baseline or a separately reviewed migration.

### Specialized variants

- **Commit trailers:** parse the final trailer block, normalize case according to the
  repository policy, and test malformed, duplicate, missing, and body-lookalike cases.
- **Install/package smoke:** build/install into a temporary prefix, inspect the installed
  layout, and compile or import a minimal downstream consumer. Run a negative self-test
  against a mutated copy so the failure branch executes on every CI run.
- **Canonical CI name:** the job must perform the ecosystem operation implied by its name.
  If no product surface exists, document N/A; if quick-start installation is a real surface,
  test it. Verify the dashboard derives names from check-runs on the default branch.
- **Tag-only release:** validate tag gating, OIDC permission, environment, immutable action
  pins, and distribution filename/version consistency against the already-built artifact.
  Never publish, republish, or fabricate a no-op pass on PR/main.
- **Tracked-file catalog:** derive the population with `git ls-files <dir>`, not a filesystem
  glob. Match entries by backticked directory-relative path and derive descriptions from
  file headers. Avoid adding fenced commands where a README-command validator executes them.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Let verification create a missing directory or marker | Let verification create a missing directory or marker | It fabricates the signal whose absence should fail | Resolve and read inputs without mutation |
| Scan logs or trailers with a free substring | Scan logs or trailers with a free substring | User-controlled text or message bodies can spoof success | Anchor line prefixes and parse the trailer block |
| Check only one parity direction | Check only one parity direction | Reverse-only ghosts and omissions survive | Compute both set differences and classify exceptions |
| Apply a new guard to every sibling | Apply a new guard to every sibling | Pre-existing unrelated noncompliance breaks the shipped tree | Scope to named targets or plan a baseline migration |
| Add a green no-op for a canonical check name | Add a green no-op for a canonical check name | It asserts work that never happened | Perform real install/package validation or document N/A |
| Use a filesystem glob for a tracked-file catalog | Use a filesystem glob for a tracked-file catalog | Scratch and ignored files change the claimed population | Use `git ls-files` as the source of truth |
| Assert inferred table metadata | Assert inferred table metadata | The guard upgrades best-effort history into false certainty | Enforce only verifiable membership |

## Results & Parameters

| Parameter | Default / rule |
| --- | --- |
| Observation | Read-only; preparation is a separate phase |
| Success | `0`, stable text/JSON verdict |
| Usage error | `2` reserved for the argument parser |
| Convention failure | Repository-chosen nonzero code, checked against siblings |
| Population | Exact issue-named targets unless a clean repo-wide baseline is proven |
| Mirror comparison | Both `A - B` and `B - A` |
| Exceptions | Narrow allowlist with owner, rationale, and stale-entry failure |
| Negative coverage | At least one mutated-input test for every failure class |
| CI rollout | Emit check first; require it only after it exists on the target branch |
| Catalog authority | Git tracked set, using directory-relative backticked keys |

Successful adoption leaves one callable checker, explicit evidence semantics, deterministic
negative tests, and no prose-only copy of the invariant. Project-specific paths, issue/PR
records, and verification boundaries are indexed in the notes; complete older content is in
the history snapshot.
