# Notes: derive pytest node IDs from the current tree

Supporting evidence for
[`pytest-cache-nodeids-derive-from-source.md`](pytest-cache-nodeids-derive-from-source.md).
Keep rules in the main skill; this file holds the single recovery incident behind
the provenance of the rule. Repository names, paths, and identifiers are
intentionally generalized away.

## Recovery incident (2026-10-24)

**Context.** An orchestrator delegated a targeted pytest run of a short, fixed
list of node IDs. The list was assembled by searching the repository for prior
test names.

**Failure.** Every requested command exited during collection with

```text
ERROR: not found: <working-tree>/tests/test_module.py::test_name
(no match in any of [<Module test_module.py>])
... no tests ran ... exit code 4
```

zero tests executed, and no session start occurred.

**Root cause, verified.** The names matched only because a repository search
surfaced `.pytest_cache/v/cache/nodeids`, an untracked cache file written by an
older commit of the same repository. Repository-wide searches return cache
artifacts alongside real test modules, so the regex-style lookup validated text
existence, not test existence.

**Recovery.** The names were re-derived from the current module (the present
tests matched a different naming pattern), the invalid ID was replaced, and the
next command collected and ran as intended. Repository documentation for a
test-selection gate requires exact current node IDs; stale names waste one full
attempt each.

**Decision value.** The recovery introduces a reusable branch that neighboring
collection-diagnosis guidance does not: when the explicit input itself is stale,
the fix happens before pytest starts, in name derivation, not in configuration
or testpaths. A cache artifact is a trust-boundary violation when used as
command input.

## Unverified corners

- Only the two pytest cache keys `v/cache/nodeids` and `v/cache/lastfailed`
  were observed as a stale source; other runners with persistent state (for
  example JUnit-name inventories or timing files embedded in CI artifacts) show
  the same trust-boundary shape but did not fail in this incident.
- Pytest exit code 4 is observed here for a collection `not found` input. It
  also covers other usage errors; do not reverse-derive "stale names" from the
  exit code alone.
