# Notes: Negative-Scan Coverage Attestation

Supporting evidence for `negative-scan-coverage-attestation.md`, from the session of
2026-10-16. Repository names, paths, and workflow identifiers are omitted; the command
shapes are exact and generalized.

## The incident (near-miss, caught in session)

During pre-publication checks for a corpus amendment, the privacy scan was composed as:

```bash
grep -nEi "<banned-pattern-sets>" "$MAIN_FILE" "$VAR.notes.md" || echo "BOTH-FILES-CLEAN"
```

The intent was to scan the main skill file and its `<name>.notes.md` companion. The shell
expanded `$VAR.notes.md` as `$VAR` + the literal `.notes.md`, i.e. `<main-file>.md.notes.md`
— a path that does not exist. Consequences:

1. grep printed `grep: <main-file>.md.notes.md: No such file or directory` to stderr and
   exited nonzero.
2. The `|| echo "BOTH-FILES-CLEAN"` fallback executed — the same output the operator would
   see if both files had been scanned and found clean.
3. Only ONE of the two intended files was ever scanned. The companion file — the newer,
   less-reviewed file — got no coverage at all.
4. stdout and stderr were merged in the tool result; the error line appeared AFTER the
   printed `BOTH-FILES-CLEAN` line, under the next section header, where it was easy to
   misattribute to the following command.

The false verdict was caught because the full tool output was read to the end before the
classification was written into the delivery summary. The scan was re-run with explicit,
existence-checked paths covering both files; the corrected result (genuinely clean, 2
files) was the verdict recorded in the public delivery claim. The recorded claim carries
the coverage count.

## A second live instance during this skill's own delivery

While validating THIS skill's delivery, the notes-file write initially failed (a missing
tool parameter), and the first markdownlint pass printed `Linting: 1 file` where two
files were intended. Because the coverage line was read — per this skill's own rule — the
shortfall was caught and the gate re-run over both files. Same failure shape, second
surface: the coverage count is the evidence, not the verdict word.

## Why the fallback made it worse

`grep` exit codes: `0` = match found, `1` = no match, `2` = error. `|| echo CLEAN` fires
on `1` and `2` alike, so "input never read" and "input checked, no hits" print the same
message. Any unconditional success echo after a coverage-dependent scan converts scanner
errors into manufactured clean verdicts. The fix is not to remove negative-reporting —
branch on the exit code, or fail loudly.

## Corpus adjacency checked during disposition (2026-10-16)

- `plan-authoring-ci-justfile-fix-risk-surfacing` contains a buried failed-attempts row:
  "Assuming exit 0 means it linted something" — same concern, scoped to CI gate authoring;
  this skill's retrieval intent (interactive delivery-evidence gates) is distinct, and the
  two entries cross-link.
- `testing-non-vacuous-regression-guards-behavior-unchanged` and
  `testing-retired-lever-inertness-guard` cover vacuity in TEST CODE; this skill covers
  vacuity in EVIDENCE COMMANDS.
- `debugging-absence-of-evidence-verify-with-authority` covers event inference from
  missing artifacts; this skill covers property inference from negative scans.
- No open PR at the delivery revision touched this intent; disposition `create`.

## Validation executed for the delivery

Corpus fast tier, plugin validator, markdownlint on BOTH new files (Linting: 2 files —
see the second instance above), and the repository PII check all passed at the delivery
commit; exact counts are in the pull request.
