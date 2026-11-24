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

## Privacy note

This note records the general pattern only. It omits project, repository, host, account, and issue identifiers.
