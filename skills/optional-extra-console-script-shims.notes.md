# Notes: optional-extra-console-script-shims

Supporting evidence for the main skill. This file is not part of normal retrieval.

## Source

- Session date: 2026-10-28.
- Trigger: a bug report showed that a base install of a published Python CLI
  distribution crashed on six automation console scripts with a raw
  `ModuleNotFoundError: No module named 'pydantic'` on every invocation,
  including `--version`.
- Root cause: an earlier refactor had moved `pydantic` from base dependencies
  into an optional extra, while the console-script entry points for the product
  layer stayed in base `[project.scripts]`.
- Regression history method: install each published release into a clean
  virtual environment and run one gated command. The last release before the
  dependency move passed; every release after it failed. This bound the defect
  to the dependency move without bisecting source commits.

## Verification evidence

Fix verified in four layers:

1. Unit tests (18 parametrized cases): missing extra produces the
   configuration-error exit code and a recovery line; present extra delegates
   to the mapped module's `main()` unchanged; `SystemExit` keeps its code.
2. Boundary and import-surface regression suites stayed green: the shim module
   imports nothing from the product layer at module load.
3. Built-wheel matrix in clean virtual environments: base install — all six
   commands exit with the configuration code and print the two-line error, no
   traceback; extra install — all six commands return their real version and
   help output. A command that needs no extra stayed unchanged.
4. Published-artifact matrix from the package registry: same result on the
   released version, base install and extra install.

## Parameters observed

- Exit code: the package's configuration-error class produced exit code `4`.
- Stderr: exactly two lines (error line, recovery line).
- Extra module check list: three modules (the extra's direct runtime
  dependencies). Checking all of them caught a partial-install case during
  review.
- Delegation: shim passed `argv=None` through; the real parser reads `sys.argv`.

## Failure signature (for diagnosis)

```text
Traceback (most recent call last):
  ...
  from pkg.product.module import main
ModuleNotFoundError: No module named 'module_a'
```

The traceback names the target module import, not the user's command logic. A
`--version` invocation that fails this way is the discriminator: argument
parsing never ran, so the failure is at import time.

## Limits

- The wheel smoke test must run from a neutral working directory. From the
  source checkout, `sys.path` resolves the local source tree first and masks
  the installed wheel.
- Python packaging has no supported way to declare a console script that is
  conditional on an extra. If that changes upstream, revisit the shim rule.
