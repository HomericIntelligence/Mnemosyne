---
name: planning-follow-up-issue-line-number-drift
license: BSD-3-Clause
description: "Plan and repair externally filed documentation issues (audit findings, doc nits, follow-ups): resolve stale citations by current content, distinguish partial fixes, source documented commands from the live task runner, and manage the flag set of a printed command by the inputs its operation reads. Use when: (1) an issue cites line numbers or a code range that may have moved, (2) an issue claims a documented command is wrong and the file may be partially fixed, (3) a page documents a printed command and a later fix corrected the printed message but not the page, (4) a repair must choose flags for a documented command that the parser accepts but the selected operation ignores."
category: documentation
date: 2026-06-19
version: "1.2.0"
user-invocable: false
verification: verified-local
tags:
  - follow-up-issue
  - line-number-drift
  - docstring
  - planning
  - stale-line-numbers
  - git-log
  - module-docstring
  - doc-audit
  - partial-fix
  - justfile
  - command-reference
  - documented-command-drift
  - printed-message-parity
  - args-consumption-parity
  - ignored-flag
  - operation-scoped-input
  - docs-only-repair
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/planning-follow-up-issue-line-number-drift.history"
history-cleanup-date: "2026-09-20"
---

# Planning: Follow-Up Issue Line Number Drift

**History:** [changelog](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/planning-follow-up-issue-line-number-drift.history)

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-13 |
| **Objective** | Correctly locate the real documentation gap when a follow-up issue's cited line numbers have shifted due to intervening PR merges |
| **Outcome** | Successful — plan correctly identified that the function docstring was already fixed by PR #1303, but the module-level `FAILS LOUDLY` block still omitted the marker-excluded fallback case |
| **Verification** | verified-local |

The same discipline applies to a documented command, not only to cited line numbers. A printed
command is correct only when its flag set equals the inputs the selected operation reads. A flag
that the parser accepts and the operation ignores is a defect in the text, even when the command
runs without error.

When a follow-up issue is filed during or after a sibling PR's review process, the cited file
state often lags behind `main`. The function-level fix the issue targets may have already landed,
while a subtler module-level gap remains unfixed. This skill documents how to detect that situation
and find the actual remaining gap.

> **v1.1.0 (2026-06-19) — unverified additions.** The original docstring line-number-drift workflow
> is `verified-local`. The v1.1.0 generalization below (the **partial-fix per-claim re-verification**
> step and the **justfile command-sourcing** step, drawn from Odysseus issue #182) is **planning-stage
> and `unverified`** — no CI/code was executed to validate the fix end-to-end. Treat those additions as
> a hypothesis until CI confirms. They are marked inline where they appear.

## When to Use

- Planning any issue whose body cites specific line numbers (follow-up issues, refinement issues, audit findings)
- Issue body references a PR as "pending" but that PR is now merged on `main`
- Issue text says "After PR #N this is false" but you haven't confirmed whether #N has merged
- Docstring fix issues targeting a specific function — the function may be fixed but the module docstring may still be stale
- Any issue filed from within another PR's review thread (high likelihood of pre-merge line number references)
- **(v1.1.0, unverified)** Any doc-audit issue that claims "lines X–Y use the wrong/phantom command" — the file may have been **partially fixed** since filing, so one of the cited lines may already be correct
- **(v1.1.0, unverified)** Issues about phantom/stale `just` recipes or command references in onboarding/getting-started docs — source each command from the live justfile before editing
- **(v1.2.0)** An issue says a documented command carries a flag that the operation ignores, or that a page still shows a command after a sibling fix corrected the message that prints it
- **(v1.2.0)** You must choose the flag set for a documented command whose parser accepts more flags than the selected operation reads

## Verified Workflow

### Quick Reference

```bash
# 1. Check git log for the most recent commit(s) touching the cited file
git log --oneline -10 -- scripts/check_license_compatibility.py

# 2. See exactly what the most recent relevant commit changed
git show <sha> -- scripts/check_license_compatibility.py | grep -A 20 "def scan"

# 3. Grep BOTH the module docstring AND function docstrings separately
#    (the issue may only mention one; the other may still be stale)
grep -n "FAILS LOUDLY\|marker.*exclud\|FALLBACK" scripts/check_license_compatibility.py | head -30

# 4. Verify current line numbers for issue-cited line ranges
#    (the issue may cite e.g. lines 248-251, but those may now be 257-262)
grep -n "def scan" scripts/check_license_compatibility.py

# 5. Check module-level docstring separately (lines 1-30 typically)
head -30 scripts/check_license_compatibility.py

# --- v1.1.0 (UNVERIFIED) — doc-audit / command-reference re-verification ---
# 6. Re-verify EACH per-line claim, not just the line numbers. A doc-audit issue may say
#    "lines 232-234 use phantom recipes X and Y" — but the file may have been PARTIALLY fixed.
#    Grep the exact cited lines and check each one independently:
sed -n '232,234p' docs/onboarding.md          # ground-truth the cited range
grep -n 'agamemnon-start\|nestor-start\|start-agamemnon\|start-nestor' docs/onboarding.md

# 7. For command/recipe references, SOURCE every documented command from the live justfile
#    BEFORE planning the edit. The justfile may mix MULTIPLE live naming conventions
#    (e.g. verb-first `start-nestor` AND prefix-first `hermes-start`) — you cannot infer the
#    correct name from one convention; grep each candidate.
grep -nE '^[a-z]' justfile                      # list every real recipe name
grep -nE '^(start-|[a-z-]+-start)' justfile     # both naming conventions

# --- v1.2.0 — documented command flag set vs operation inputs ---
# 8. Find the printed reference: the program that emits the follow-up command.
grep -rn '<operation-name>' scripts/                 # the hint the page must match
# 9. Read which inputs the selected operation actually consumes.
sed -n '<parser-range>p;<operation-branch-range>p' <module>.py
# 10. Delegate the flag choice to the parser after the edit; it reports required inputs.
python3 -m <module> --operation <name> --release-manifest M   # run in a scratch dir
```

### Detailed Steps

#### Step 1: Identify the most recent commit touching the file

Before reading the issue's cited line numbers, run `git log --oneline -10 -- <file>` to
find the SHA of the most recent commit. This tells you which PR last touched the file
and whether the issue's claimed "current state" is actually `main`'s current state.

```bash
git log --oneline -10 -- scripts/check_license_compatibility.py
# → dd15c35 fix(scripts_lib): ...
# → ee35ed87 fix(license-scan): classify marker-excluded deps via FALLBACK_LICENSES
```

The commit `ee35ed87` (PR #1303) is the most recent. If the issue was filed
referencing lines from before that commit, all line numbers in the issue body are stale.

#### Step 2: See what the most recent commit actually fixed

```bash
git show ee35ed87 -- scripts/check_license_compatibility.py | grep -A 20 "def scan"
```

This confirms whether the issue's stated fix target (e.g., the `scan()` function docstring)
is already addressed in `ee35ed87`. If yes, move to step 3 to find the remaining gap.

#### Step 3: Grep module-level and function-level docstrings separately

Issues about docstring staleness almost always cite a function-level docstring. But module-level
docstrings (the `"""..."""` block at the top of the file, or a `FAILS LOUDLY` block) can also
be stale and are rarely covered by the same fix.

```bash
# Check if any keyword from the fix appears in the module-level block (lines 1-30)
grep -n "FAILS LOUDLY\|marker.*exclud\|FALLBACK\|fallback" scripts/check_license_compatibility.py | head -20
```

If the result shows zero matches for lines 1–27 (the module docstring range) but matches in
lines 257+ (the function), the module-level block is the gap the fix missed.

#### Step 4: Verify issue-cited line numbers against current HEAD

Cross-reference the issue's cited lines (e.g., "lines 248–251") against where those lines
actually live now:

```bash
# Find the current line of the construct the issue cited
grep -n "def scan\|are skipped with a note" scripts/check_license_compatibility.py
```

If the issue cited line 248 but the content is now at line 262, you know the file
has grown by ~14 lines due to the intervening PR. The fix content is the same; only the
address has shifted.

#### Step 5: Confirm the real remaining gap

After verifying both module-level and function-level docstrings, document the specific
gap: what text is missing, what lines it should be added at (current HEAD line numbers),
and which PR already fixed the adjacent content (so the reviewer can understand scope).

```bash
# Show lines 10-20 of the module docstring to see the FAILS LOUDLY block
sed -n '10,20p' scripts/check_license_compatibility.py
```

#### Step 6 (v1.1.0 — Proposed, UNVERIFIED): Re-verify each per-line claim and source commands from the live tree

> **Warning:** This step has not been validated end-to-end. Treat as a hypothesis until CI confirms.

This step generalizes the skill from "docstring line drift" to any externally-filed doc-audit
issue that asserts per-line claims (e.g. "lines 232–234 reference nonexistent `just` recipes").
The core failure mode it guards against: the file may have been **partially fixed** since the
issue was filed, so a blind edit that follows the issue text re-breaks an already-correct line.

1. **Ground-truth the cited range, then check EACH line's claim independently.** Do not treat
   "lines X–Y are broken" as atomic. `sed -n 'X,Yp' <file>` and read each line. In Odysseus #182
   the issue claimed BOTH `agamemnon-start` and `nestor-start` were broken at lines 232–234, but
   line 232 already read the correct `start-agamemnon` — only line 233's `nestor-start` was stale.
   A blind edit would have re-changed the already-correct line.

2. **For command/recipe references, source every documented command from the justfile FIRST.**
   Never trust the command names in the issue body. List the real recipes:

   ```bash
   grep -nE '^[a-z]' justfile                    # every recipe name
   grep -nE '^(start-|[a-z-]+-start)' justfile   # both naming conventions
   ```

3. **Expect MULTIPLE live naming conventions in one justfile.** Odysseus mixes verb-first
   (`start-agamemnon`, `start-nestor`) AND prefix-first (`hermes-start`, `argus-start`,
   `keystone-start`) — both are real. You cannot infer the "correct" name from a single
   convention; grep each candidate. The onboarding doc itself had a MIX of both, and only
   `nestor-start` was actually wrong.

4. **Scope discipline.** The mixed-convention justfile is the root cause, but normalizing it is
   out of scope for a doc-fix issue — flag it in the plan/PR, do not fix it.

**Unverified reliances to record (carry these forward as risks, not facts):**

- Relied on `pixi run npx markdownlint-cli2` as the repo's lint runner **without** verifying that
  recipe/tooling actually exists.
- Did not verify issue #182's acceptance criteria are limited to the doc edit — it is part of
  umbrella issue #174, which could imply broader scope.
- Assumed no OTHER docs (`architecture.md`, `deployment.md`, `runbooks/`) reference the same
  phantom recipe; a repo-wide grep beyond `docs/` was not run. **Do run it.**

#### Step 8 (v1.2.0): Match a documented command to the flags its operation reads

An issue can report that a page documents a follow-up command with a flag that the selected
operation ignores. The parser accepts the flag, the command exits 0, and nothing tells the
operator that the value had no effect. Treat the flag set as a claim to verify, like a line
number.

1. **Read the operation, not the parser.** Find the branch that handles the selected operation.
   Record the attributes it reads. A flag is correct only when a branch that the selected
   operation takes reads it. An attribute that only another operation reads is a defect in the
   documented text, not in the program.
2. **Use the printed message as the reference text.** When a sibling fix corrected the command
   that the installer or CLI prints, the page must print the same flag set in the same order.
   Diff the page command against the emitter, not against your reading of the parser.
3. **Keep the flags the flow needs.** Drop only the ignored flag. Keep the context or lane flag
   when the flow uses one, even if the operation falls back to a default without it, because the
   page must name the same context the operator selected. Copy the emitter's conditional shape:
   the emitter appends the context flag only when it used one.
4. **Delegate required inputs to the parser.** Do not add a test of a help string. Run the
   documented command in a scratch directory. The operation's own input check reports a missing
   required input before any effect. A scratch run that reaches that check proves that the
   documented set is complete.
5. **Sweep the tree for the same defect.** Grep every mention of the flag in live `docs/` pages.
   Treat the other hits as separate commands: an operation-scoped flag is valid for the operation
   that reads it. Do not change a hit in another flow (scope fidelity).
6. **Check what the page guard tests.** A docs test may machine-check only the command table.
   Then the repaired command is prose and no test parses it. Record that limit in the plan and in
   the pull-request body.

**Failure mode this step prevents:** the page keeps a flag that the parser accepts and the
operation ignores. An operator reads the page, believes the value is recorded, and gets no
confirmation or rejection.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Trust issue-cited line numbers verbatim | Used lines 248–251 from the issue body as the edit target | Those lines had shifted to 257–262 after PR #1303 landed; the content was wrong before even reading | Always run `grep -n "def <function>"` to find the actual current line number |
| Assume the function docstring is still stale | Planned to fix the `scan()` docstring as the issue described | PR #1303 had already fixed `scan()`'s docstring; the fix was already on `main` | Run `git show <latest-sha>` to see what the most recent commit actually changed |
| Read only the function-level docstring | Grepped only `def scan` and read 20 lines below it | Missed the module-level `FAILS LOUDLY` block (lines 12–17) which still omitted the marker-excluded case | Grep module-level AND function-level docstrings separately; they are independently maintained |
| Trust "After PR #N this is false" in issue body | Assumed PR #1304 was the relevant merge since issue cited it | The issue was filed from within PR #1304's review process, citing a state PR #1303 had already fixed on `main` | Check whether the referenced PR is actually merged; issues filed mid-PR-process use pre-merge state |
| Skip git log for docstring-only issues | Assumed low-risk docstring fixes don't need git archaeology | The git log revealed the exact SHA that fixed the function docstring, which was necessary to identify the remaining module-level gap | `git log --oneline -10 -- <file>` is a 2-second check that prevents the rest of the plan from being wrong |
| (v1.1.0, unverified) Treat "lines X–Y are broken" as atomic | Would have edited both cited lines 232–234 per Odysseus #182's claim that `agamemnon-start` AND `nestor-start` were phantom | Ground-truth grep showed line 232 already read the correct `start-agamemnon`; only line 233's `nestor-start` was stale — a blind edit re-breaks the already-correct line | Re-verify EACH per-line claim independently; the file may be partially fixed since the issue was filed |
| (v1.1.0, unverified) Trust the command names in the issue body | Planned the edit using the recipe names the issue quoted | Issue command names were stale/wrong; the real recipes live only in the justfile | Source every documented command from the live justfile (`grep -nE '^[a-z]' justfile`) BEFORE planning the edit |
| (v1.1.0, unverified) Infer the "correct" recipe name from one naming convention | Assumed Odysseus used a single convention, so guessed the canonical form | The justfile mixes verb-first (`start-nestor`) AND prefix-first (`hermes-start`) — both are live; the doc had a mix and only `nestor-start` was wrong | You cannot infer the correct name from one convention; grep each candidate against the justfile |
| (v1.2.0) Judge a documented flag by the parser | The issue claimed a documented command carries an ignored flag. The parser declares the flag, so the command is valid syntax | The selected operation branch never reads the attribute; the parser declares flags for every operation | Compare the flag set with the attributes the selected operation reads, and use the emitter as the reference text |
| (v1.2.0) Drop ignored flags together with the context flag | Considered keeping only the manifest and source flags to "minimize" the command | The flow selects a deployment context, and the emitter appends the context flag when it used one; a page without it names a different target | Drop only the ignored flag; keep the context flag, in the emitter's order and conditional shape |
| (v1.1.0, unverified) Fix the root-cause mixed convention inside a doc-fix PR | Considered normalizing the justfile's two naming conventions | That is a refactor, out of scope for a doc-fix issue, and would balloon the change | Flag the root cause in the plan/PR, do not fix it; keep the doc-fix scoped |

## Results & Parameters

### Concrete example (ProjectHephaestus issue #1306)

Issue body said: "`scan()` docstring still has stale text 'are skipped with a note, not treated as a hole'."
Issue cited lines 248–251.

Step 1 revealed: the most recent commit touching the file was `ee35ed87` (PR #1303,
"fix(license-scan): classify marker-excluded deps via FALLBACK_LICENSES").

Step 2 confirmed: PR #1303 already fixed the `scan()` function docstring — the stale
text cited by the issue was removed in that PR.

Step 3 discovered the real gap: the **module-level** `FAILS LOUDLY` block (lines 12–17)
enumerated three behaviors but omitted the fourth: "marker-excluded dependencies get
a FALLBACK_LICENSES entry rather than a HOLE". Zero grep hits for `FALLBACK` in lines 1–27.

Step 4 confirmed line drift: the issue cited lines 248–251, which are now at 257–262
after intervening commits added ~11 lines.

Actual fix target: module docstring lines 12–17, not the function at 257–262.

### Decision tree for follow-up issue planning

```
Received a follow-up / refinement issue with cited line numbers:
│
├─ 1. git log --oneline -10 -- <file>
│   └─ Find the most recent commit touching the file
│
├─ 2. git show <sha> -- <file> | grep -A 20 "<cited function>"
│   ├─ Fix already in latest commit → function docstring gap is CLOSED
│   │   └─ Proceed to step 3 to find remaining gap
│   └─ Fix NOT in latest commit → function docstring still stale
│       └─ Plan the function docstring fix
│
├─ 3. Grep module-level AND function-level docstrings SEPARATELY
│   grep -n "<keyword>" <file> | head -20
│   ├─ Keyword absent in module doc (lines 1-30) but present in function → MODULE GAP found
│   └─ Keyword absent everywhere → broader audit needed
│
└─ 4. Verify issue-cited line numbers vs current grep output
    ├─ Lines match → no drift; issue is up to date
    └─ Lines differ → drift detected; use grep-found line numbers in the plan
```

### Key commands for follow-up issue planning

| Goal | Command |
|------|---------|
| Find most recent commit touching a file | `git log --oneline -10 -- <file>` |
| See what a specific commit changed in a file | `git show <sha> -- <file> \| grep -A 20 "def <fn>"` |
| Find current line of a function | `grep -n "def <fn>" <file>` |
| Grep module-level block separately | `grep -n "<keyword>" <file> \| head -20` (then check which lines are in 1–30 range) |
| Show first 30 lines of a file | `head -30 <file>` or `sed -n '1,30p' <file>` |
| Confirm whether a referenced PR merged | `gh pr view <N> --json state,mergedAt --jq '.state, .mergedAt'` |
| (v1.1.0) Ground-truth a cited line range | `sed -n 'X,Yp' <file>` |
| (v1.1.0) List every real `just` recipe | `grep -nE '^[a-z]' justfile` |
| (v1.1.0) Catch both recipe naming conventions | `grep -nE '^(start-\|[a-z-]+-start)' justfile` |

### Concrete example (Odysseus issue #182 — v1.1.0, UNVERIFIED, planning-stage)

> **Warning:** This example was the planning-stage analysis that motivated the v1.1.0 additions.
> No CI/code was executed to validate the fix end-to-end. Treat as a hypothesis until CI confirms.

Issue body said: `docs/onboarding.md` documents `just nestor-start` and `just agamemnon-start`,
which don't exist — the real recipes are verb-first `start-nestor` / `start-agamemnon`. The issue
cited **lines 232–234** and claimed **both** were broken.

Ground-truth grep showed line 232 **already** read `start-agamemnon` (already correct — the file
had been partially fixed since the issue was filed). Only line 233's `nestor-start` was still
stale. A blind edit following the issue text would have re-changed the already-correct line 232.

The Odysseus justfile mixes TWO live naming conventions: verb-first (`start-agamemnon`,
`start-nestor`) AND prefix-first (`hermes-start`, `argus-start`, `keystone-start`). Both are real;
the doc had a mix of both. The correct command name therefore could NOT be inferred from a single
convention — each had to be grepped against the justfile. Normalizing the mixed convention is the
root cause but out of scope for the doc fix; flag it, don't fix it.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Private delivery repository | Docs-only follow-up issue from a round-1 review of a sibling fix | A cutover page documented a follow-up activation command with a flag that the parser declares and the selected operation ignores; the sibling fix had corrected only the printed installer message. The plan removed the ignored flag, kept the deployment-context flag in the emitter's order, and used the operation's own input check for validation. Verified-local by reading the parser and the operation branch at one bound revision. |
| ProjectHephaestus | Issue #1306 — stale docstring in `scripts/check_license_compatibility.py` | Function docstring already fixed by PR #1303; module-level `FAILS LOUDLY` block was the real remaining gap |
| Odysseus (v1.1.0, **unverified** — planning-stage only) | Issue #182 — phantom `just` recipes in `docs/onboarding.md` | Issue claimed both `agamemnon-start` and `nestor-start` broken at lines 232–234; ground-truth showed line 232 already correct (`start-agamemnon`), only `nestor-start` stale — partial-fix near-miss avoided by re-verifying each per-line claim |
