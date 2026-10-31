---
name: negative-scan-coverage-attestation
description: "Verify a negative scan result actually covered the intended inputs before recording it as evidence. Use when a grep, PII or secrets scan, lint gate, or other banned-pattern check will report 'clean' in a delivery claim, when the scan command composes paths, globs, or shell expansions, or when the command is paired with a fallback such as `|| echo CLEAN` that prints a success-shaped message regardless of input coverage."
category: testing
date: 2026-10-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - negative-scan
  - coverage-attestation
  - vacuous-clean
  - evidence-discipline
  - grep
  - secrets-scan
  - pii-scan
  - gate-evidence
  - inconclusive-vs-clean
  - fallback-echo
  - stderr-interleave
---

# Negative-Scan Coverage Attestation

A negative scan result is evidence only if the scan covered the inputs you claim it
covered. A scan that reads zero or wrong inputs produces the same "no matches" output as a
genuine clean result. The two outcomes are indistinguishable from the scan output alone.

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-16 |
| **Objective** | Prevent false "clean" verdicts: before a negative result from a grep or gate command is cited in a delivery claim, attest what the scan actually read (which files, how many), refuse unconditional success fallbacks, and treat any scan-side error as INCONCLUSIVE, never as CLEAN. |
| **Outcome** | verified-local. In the triggering session a privacy scan `grep -nEi "$PATTERNS" "$MAIN" "$NOTES_PATH"` silently errored on a mis-expanded path (`$VAR.notes.md` parsed as `$VAR` + `.notes.md`), printed `CLEAN` through an `|| echo` fallback, and never scanned the companion file. The error line surfaced only in the trailing stderr of the merged tool output. The verdict was recorded only after a corrected re-run attested coverage of both files. |
| **Verification** | verified-local — the failure occurred in operation, was caught, corrected, and re-run with coverage attestation; the corrected scan was then cited in a published delivery claim. |

## When to Use

- Any scan, grep, linter, or banned-pattern check whose NEGATIVE result ("no matches",
  "clean", "0 issues") is about to be recorded as delivery evidence or to gate a
  publication, merge, or completion claim.
- The scan command composes its inputs from variables, expansions, command substitution,
  or globs — anywhere a path can silently mis-expand to nothing or to a wrong file.
- The command carries an unconditional fallback (`|| echo CLEAN`, `|| true`,
  `|| echo OK`) that converts ANY nonzero exit — including "input file does not exist" —
  into a success-shaped message.
- A gate's summary line will be cited without the coverage line that precedes it
  (for example citing "0 issues found" but not the "Linting: 2 files" line that proves
  the gate read anything).

## Verified Workflow

### Quick Reference

Attest coverage BEFORE the scan, keep the error channel visible, and separate
"genuinely clean" from "scan failed":

```bash
# WRONG — vacuous-clean: a mis-expanded input scans nothing; the fallback manufactures CLEAN
grep -nEi "$PATTERNS" "$MAIN" "$NOTES_PATH" || echo "CLEAN"

# RIGHT — assert every input exists and is non-empty BEFORE scanning
set -u
FILES=("$MAIN" "$NOTES_PATH")
for f in "${FILES[@]}"; do
  [[ -s $f ]] || { echo "INCONCLUSIVE: missing or empty input: $f" >&2; exit 2; }
done
echo "coverage: scanning ${#FILES[@]} files"   # recorded WITH the verdict

# No fallback echo: grep exit 1 = no match = CLEAN; any other nonzero = scanner error
if grep -nEi "$PATTERNS" "${FILES[@]}"; then
  echo "MATCHES FOUND — review above"
else
  rc=$?
  if [[ $rc -eq 1 ]]; then echo "CLEAN (coverage: ${#FILES[@]} files attested)"
  else echo "INCONCLUSIVE (scan error, exit $rc)" >&2; exit "$rc"; fi
fi
```

### Suggested Approach

1. **Attest coverage before trusting the negative.** Print or check the scan's input
   set: file list, file count, and non-emptiness. A scan over zero files proves nothing.
   For globbing gates, prefer the tool's own coverage line (for example the
   "Linting: 2 files" line a linter prints) or enumerate the inputs yourself
   (`git ls-files <dir> | grep -cE '<pattern>'` must be > 0).
2. **Never pair a coverage-dependent scan with an unconditional success fallback.**
   `|| echo CLEAN` executes on exit 1 (no match) AND on exit 2 (missing file, bad
   argument) alike. Either branch explicitly on the exit code, or drop the fallback and
   read the real status.
3. **Treat scan-side errors as INCONCLUSIVE, not CLEAN.** A missing file, a failed glob,
   or a tool error means the property was not checked at all. Publication evidence that
   says "clean" while the command errored is false assurance.
4. **Keep stderr visible and read the whole tool result.** In merged stdout/stderr output
   an error line can trail after your own `echo CLEAN`; read to the end before you
   classify the run. (The triggering incident's error line appeared only in the trailing
   stderr of the tool result.)
5. **Record the coverage attestation WITH the verdict.** Write "privacy scan clean
   (2 files attested)", not "privacy scan clean". A later reader — or you, one hour
   later — must be able to distinguish an attested negative from a vacuous one.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Privacy-scan two files with `grep -nEi "$PATTERNS" "$MAIN" "$VAR.notes.md" \|\| echo "CLEAN"` | Composed the companion path from a variable plus a literal suffix | The shell parsed the input as `<VAR-value>.notes.md`, a path that does not exist; grep errored on it AND the fallback still printed CLEAN; one of the two files was never scanned. The error appeared only in trailing stderr of the merged output and was easy to miss | Assert every input exists before scanning; never mask a scan behind an unconditional `&&`/`||` echo; read the FULL tool output including trailing stderr before classifying |
| Record the verdict as "clean" without the coverage line | Wrote the bare negative into the delivery summary (caught during the same session before publication) | A bare "clean" is indistinguishable from a vacuous-clean for any later reader, including the author's future self; the attestation is the evidence, not the verdict word | Write the coverage count with the verdict ("clean, N files attested"); if you cannot name N, the verdict is not yet evidence |

## Results & Parameters

- The attestation primitive is cheap: an existence loop plus a count, or the tool's own
  coverage line. It adds seconds; it can prevent a false publication-evidence claim.
- Exit-code policy for POSIX scan tools: `0` = matches found, `1` = no match (CLEAN),
  `2` = error (INCONCLUSIVE). Only `1` may become a recorded clean verdict.
- **ASSUMPTION:** the scan tool reports input errors on stderr and with a distinct
  nonzero exit. True for grep and the session's other gates; verify for any new tool by
  feeding it one deliberately missing path during setup.
- **UNVERIFIED:** repository-level pre-commit/CI compositions of these scans were not
  re-audited; the rule was exercised at the interactive delivery gate where the incident
  occurred.

### Related skills

- `debugging-absence-of-evidence-verify-with-authority` — do not infer that an EVENT
  happened or did not happen from a missing artifact; verify with authority. THIS skill:
  do not infer that a PROPERTY holds from a negative SCAN result whose coverage is
  unattested.
- `testing-non-vacuous-regression-guards-behavior-unchanged` — test-CODE vacuity: an
  assertion that passes under any plausible change gates nothing. THIS skill: operational
  evidence-command vacuity: a scan that covers nothing proves nothing.
- `testing-retired-lever-inertness-guard` — pair rejection-only guards with an acceptance
  contrast so the rejection is attributed to the intended branch; same anti-vacuity
  family applied to guard design.
- `plan-authoring-ci-justfile-fix-risk-surfacing` — its "exit 0 ≠ the linter ran"
  audit row shares the coverage concern for CI gate AUTHORING; this skill is the
  interactive delivery-evidence complement.
- `verify-issue-premise-against-code-before-planning` (v1.3.0) — full-fidelity evidence
  capture for test suites (never truncate failure lists); this skill applies the same
  fidelity discipline to negative scan results at delivery gates.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| `<agent knowledge-corpus delivery workflow>` | Pre-publication privacy gate for a corpus amendment PR | verified-local — mis-expanded input path + `\|\| echo CLEAN` fallback produced a false CLEAN; caught via trailing stderr; corrected re-run attested coverage (2 files) and only then was the verdict recorded in the public delivery claim |
