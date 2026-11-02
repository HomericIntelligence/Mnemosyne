# Notes: typed-boundary-cause-diagnostic-on-exit

Supporting evidence for the main entry. Privacy screened: no repository,
organization, issue, path, or credential identifiers.

## Source session evidence

- A CI script catches `ValueError`, `OSError`, `KeyError`, `TypeError`, and
  `subprocess.SubprocessError` at one entry point. Before the change it printed
  one fixed sentence and returned `1`. Every distinct cause produced identical
  output, so a failing job could not be attributed.
- The change adds `as error` and one stderr line with `type(error).__name__` and
  `error`. The first line, the exit code, and every output file are unchanged.
- Four workflow consumers of the script read exit codes and `--output` artifact
  files. None parse the sentence. The extra line cannot break a parser.
- Before the change, a structured record field was rejected. The record
  validation fails closed on unknown keys, so an additive field would have
  created a new failure. Diagnostics stayed on stderr.
- Verification: a missing input printed
  `Why: FileNotFoundError: [Errno 2] No such file or directory: '...'` and
  exited `1`. The focused suite passed 45 tests. Lint and format checks were
  clean. The required CI check had not run at review time, so the review gave a
  verdict without a gate label.

## Why the main entry is separate from two related entries

- `preserve-primary-failure-diagnostics.md` keeps the primary failure evidence
  when a follow-up probe also fails, and it keeps the result blocked. Its
  decision is about a causal chain of two failures. The other order matters
  there: capture the initial failure before the probe runs. This entry has one
  failure and no probe.
- `parse-boundary-error-context-safe-access.md` keeps a typed error from
  becoming a bare `KeyError` inside the error path. Its decision is safe mapping
  access before the completeness proof. This entry keeps the message stable and
  exposes the exception class; it does not change how the error is built.
- A reader who asks "why did this boundary fail?" can act on both entries. Each
  entry gives a different ordering of work. Do not merge them without a distinct
  trigger for each branch.

## Corpus entries inspected for duplication

- `preserve-primary-failure-diagnostics` — different trigger (probe failure).
- `parse-boundary-error-context-safe-access` — different trigger (strict index in
  the error path).
- `python-logging-and-silent-error-patterns` — documents silent `ValueError`
  swallowing. It recommends propagation, not a bounded cause line.
- `logging-subprocess-context-tracking`, `bash-stderr-jq-separation`,
  `tooling-cli-batch-terminal-outcome-contracts` — handle stream separation and
  terminal outcomes, not a fixed-sentence cause line.
- `verify-pr-ready` — covers gate evidence, not boundary diagnostics.