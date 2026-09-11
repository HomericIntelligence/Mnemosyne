# Safety-Sensitive Wrapper Invocation Contract — Notes

## Evidence

A local repository-cleanup operation used a Python wrapper with this interface:

```text
wrapper dependency_checkout arguments ...
```

The first call supplied neither positional argument. The argument parser
returned status 2 and reported both arguments as missing. The wrapper stopped
before it validated the dependency or replaced itself with the downstream
process. No cleanup action started.

Source inspection showed this sequence:

1. Parse one dependency-checkout positional argument.
2. Collect the remaining arguments for the downstream command.
3. Validate a required revision in the dependency checkout.
4. Replace the wrapper process with the dependency-locked downstream command.

The operation contract prohibited a retry after a nonzero result. The operator
therefore stopped and preserved the repository state. This evidence verifies
the missing-argument failure and the safe stop. It does not verify a complete
cleanup operation.

## Privacy Review

This note omits repository names, paths, hostnames, user identifiers, issue
identifiers, credentials, and operational data. It keeps only the reusable
wrapper grammar and the observed failure result.
