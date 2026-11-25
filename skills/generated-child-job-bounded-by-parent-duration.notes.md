# Generated Child Job Bounded by Parent Duration — Notes

## Evidence summary

A capacity-sharing control plane generated two scheduler jobs for one registration: a controller job and a child work job.

- The controller script rendered `--time` from the registration duration.
- The child job rendered placement and resource arguments but no `--time`.
- A two-hour registration produced a child job with a multi-day scheduler default.
- The child job stayed RUNNING after its registration ended.

The fix added the parsed duration to the child scheduler arguments and shared one walltime validator. A behavior test checks the child time from a two-hour duration. The controller test already existed.

## Verification commands

```bash
pytest -q <focused-controller-and-child-tests>
<linter> check <changed-paths>
<type-checker> check <changed-paths>
```

The required repository checks also passed.

## Compatibility boundary

A queued or running scheduler job keeps the script and arguments from its submission. The fix applies to new submissions. No running job is rewritten.

## Known boundary

A later duration change does not re-render the baked values. A shorter change can leave the original longer limit. The live-limit update or a refusal is a separate change.

## Privacy note

This note records the general pattern only. It omits project, repository, host, account, and issue identifiers.
