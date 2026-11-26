# Generated Child Explicit Args Not Environment — Notes

## Evidence summary

A rendered scheduler job exported two per-run values for its fixed payload command. A repository environment-surface check rejected both new literals. The change replaced the exports with two quoted positional arguments, updated the help text and task guide, and removed all allowlist rows for the retired names.

The source module regenerated the script. A test asserted the payload command received the two values in order. The changed tests, type check, surface check, and required CI checks passed.

## Verification commands

Use the repository's own test and validation entry points. The generic sequence is:

```bash
pytest -q <focused-child-job-tests>
<linter> check <changed-paths>
<type-checker> check <changed-paths>
python3 <environment-surface-check> --repository-root .
```

A surface check that scans literals fails in both directions:

- a new occurrence without an allowlist row fails;
- a row whose occurrence is gone fails as stale.

Remove all rows for a retired name and path pair in the same change. Then run the check.

## Compatibility boundary

The rendered artifact text is the contract for an in-flight job. This change affects only a new render. An older artifact that is already queued or running keeps its exported values and its old behavior. No live artifact is rewritten or stopped to force the new interface.

## Cross-release child context

A rendered launcher probes a child command from a different release. The first
implementation passed the launcher's absolute registry path. Each supported
older release refused it: a release reads only the registry that it packages.

The corrected launcher passes a stable context name. The child interpreter
resolves its own package data root and joins the name. The launcher refuses an
empty or missing result before it starts the probe. This keeps the parent from
assuming the child's install layout and gives one actionable failure.

The first peer test supplied a synthetic path. It proved option parsing and
missed the production failure. The corrected test resolves the packaged file
from each peer's own tree, then asserts that the command reaches a later
refusal. A service-start test is not necessary for this contract.

## Privacy note

This note records the general pattern only. It omits project, repository, host, account, and issue identifiers.
