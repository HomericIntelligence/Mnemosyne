---
name: github-actions-env-var-lift-for-workflow-injection-hook
description: "PreToolUse security_reminder_hook (or actionlint / zizmor / CodeQL workflow-injection query) blocks an Edit to a `.github/workflows/*.yml` file because the surrounding `run:` block contains a `${{ … }}` template expression — even when the expression is a trusted `steps.*.outputs.*` or `inputs.*` value and your edit does not touch it. Use when: (1) you need to make an unrelated change inside a `run:` block (e.g. prefix a command with `pixi run`) and the hook rejects the diff; (2) the hook fires on `github.event.issue.title`, `.body`, `github.head_ref`, `head_commit.message`, etc.; (3) any linter flags `${{ ... }}` interpolation directly in a shell command line. Fix: lift the templated expression out of `run:` into an `env:` block on the same step, then reference it as a quoted shell variable (`\"$VAR\"`) inside `run:`. Do NOT bypass the hook — it points at a real injection sink class."
category: ci-cd
date: 2026-05-24
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - github-actions
  - workflow-injection
  - security-hook
  - pretooluse
  - env-var-lift
  - run-block
  - actionlint
  - zizmor
  - codeql
  - pixi
---

# GitHub Actions `env:` Var Lift for Workflow-Injection Hook

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-24 |
| **Objective** | Edit a `run:` block in a GitHub Actions workflow when the Claude Code `PreToolUse` `security_reminder_hook` (from the ProjectHephaestus plugin) — or any equivalent linter — rejects the diff because a pre-existing `${{ … }}` expression lives inside the same `run:` block |
| **Outcome** | Lift the templated expression into an `env:` block on the same step, reference it as a quoted shell variable inside `run:`. The hook accepts the edit, and the workflow becomes legitimately safer against workflow injection |
| **Verification** | verified-ci — applied to `.github/workflows/docs.yml` on `HomericIntelligence/ProjectOdyssey` PR #5445 (commit `702a5a2e`). The `validate-readme-commands` check went from FAILURE to SUCCESS after the env-var lift |
| **Reference** | <https://github.blog/security/vulnerability-research/how-to-catch-github-actions-workflow-injections-before-attackers-do/> |

## Symptom

You attempt an `Edit` on `.github/workflows/<name>.yml` to make a small, unrelated change inside a `run:` block — for example, adding `pixi run` in front of `python3`. The `PreToolUse:Edit` hook rejects the diff, citing workflow-injection risk, because the same `run:` block contains a `${{ … }}` template expression (often a `steps.*.outputs.*` value or `inputs.*` that was already there before your edit).

The hook scans the entire new file region, not just the changed bytes, so any `${{` inside the relevant `run:` block trips it regardless of whether you authored that part.

The hook fires on these `${{ … }}` sources especially (all attacker-controllable):

- `github.event.issue.title`, `github.event.issue.body`
- `github.event.pull_request.title`, `github.event.pull_request.body`
- `github.event.comment.body`, `github.event.review.body`, `github.event.review_comment.body`
- `github.event.head_commit.message`, `github.event.commits.*.message`
- `github.event.commits.*.author.email`, `github.event.commits.*.author.name`
- `github.event.pull_request.head.ref`, `github.event.pull_request.head.label`
- `github.head_ref`

…and the hook **also** fires on trusted sources like `steps.*.outputs.*` and `inputs.*`. That is a semantic false-positive but the principled fix is identical, and applying it makes the workflow strictly safer.

## Root Cause Hypothesis

Interpolating any `${{ … }}` expression directly into a shell command line is a well-known code-injection sink class: the value is spliced into the shell **before** the shell parses quotes, so even backtick-quoting the expression in YAML does not help. Quoting only becomes effective once the value is in a shell variable, where `"$VAR"` is parsed by the shell after expansion.

The hook therefore uses a coarse rule — **any** `${{` in a `run:` block is rejected — because:

1. It cannot statically distinguish trusted sources (`steps.*.outputs.*`) from untrusted ones (`github.event.issue.title`).
2. Even "trusted" sources can transitively carry attacker input if produced by an earlier `run:` step that itself consumed untrusted input.
3. The `env:` lift is the only fix that is correct **regardless** of source trust.

## When to Use

1. `PreToolUse:Edit` (or `PreToolUse:Write`) rejects a diff on `.github/workflows/*.yml` with a workflow-injection message.
2. The rejected `run:` block contains at least one `${{ … }}` expression.
3. Your actual edit is unrelated to the templated expression (you just need to change a neighboring shell command).
4. Or: `actionlint`, `zizmor`, or GitHub's CodeQL workflow-injection query is flagging the same line.

If the hook is blocking the **entire** `Edit` tool on `.github/workflows/*.yml` by path alone (no `${{ … }}` involved), use `edit-tool-blocked-workflow-files` instead — that is a different hook with a different fix.

## Verified Workflow

### Quick Reference

**BEFORE — vulnerable and hook-blocked:**

```yaml
- name: Run README command validation
  run: |
    python3 scripts/validate_readme_commands.py \
      --level ${{ steps.validation-level.outputs.level }} \
      --output validation-report.md \
      README.md
```

**AFTER — env-var lift, hook-accepted, injection-safe:**

```yaml
- name: Run README command validation
  env:
    VALIDATION_LEVEL: ${{ steps.validation-level.outputs.level }}
  run: |
    pixi run python3 scripts/validate_readme_commands.py \
      --level "$VALIDATION_LEVEL" \
      --output validation-report.md \
      README.md
```

### Recipe

1. Identify every `${{ … }}` expression inside the target `run:` block.
2. For each one, add an entry to a step-scoped `env:` block:
   - Choose an `UPPER_SNAKE_CASE` name that reflects the value (e.g. `VALIDATION_LEVEL`, `ISSUE_TITLE`, `HEAD_REF`).
   - Set the value to the original `${{ … }}` expression verbatim.
3. Replace each `${{ … }}` inside `run:` with `"$NAME"` — **always double-quoted**, so the shell handles arbitrary content (spaces, special chars, attacker-supplied payloads) safely.
4. If the `run:` block is the entire step body and there is no existing `env:`, add one as a sibling key on the same step (same indent level as `run:`).
5. Re-attempt the `Edit`. The hook should now accept the diff.

### Multi-Expression Example

**BEFORE:**

```yaml
- name: Comment on issue
  run: |
    gh issue comment ${{ github.event.issue.number }} \
      --body "Triaged: ${{ github.event.issue.title }}"
```

**AFTER:**

```yaml
- name: Comment on issue
  env:
    ISSUE_NUMBER: ${{ github.event.issue.number }}
    ISSUE_TITLE: ${{ github.event.issue.title }}
  run: |
    gh issue comment "$ISSUE_NUMBER" \
      --body "Triaged: $ISSUE_TITLE"
```

Note `"$ISSUE_TITLE"` inside the double-quoted `--body` string does **not** need extra quoting — it's already inside double quotes, which is what makes it safe.

## Results & Parameters

- **Hook decision**: `Edit` accepted on next attempt.
- **Runtime behavior**: identical — `$VAR` expands to the same string the inline `${{ … }}` would have produced.
- **Security posture**: strictly improved, even for "trusted" sources, because future maintenance can change the source without re-introducing an injection sink.
- **Cost**: ~3 added YAML lines per expression. No CI runtime cost.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Edit the `run:` block in place, leaving the existing `${{ steps.*.outputs.* }}` untouched | Direct `Edit` call adding `pixi run` prefix | `PreToolUse` hook scans the whole new file region, not just the changed bytes; any `${{` in the affected `run:` block trips it | The hook is positional within the YAML structure, not diff-scoped |
| Ask the user to bypass the hook for one edit | Offered "skip hook" as an option | The hook is pointing at a real (pre-existing) anti-pattern; bypassing it leaves a known injection sink in place | Bypass is almost never the right call when the hook flags a real sink class |
| Quote the templated value inline: `"${{ steps.*.outputs.* }}"` and leave it in `run:` | Considered but not executed | The hook matches `${{` regardless of surrounding quotes; YAML-level quoting does not stop shell-level injection because the value is spliced before the shell parses | Move the expression OUT of `run:` entirely; shell-level `"$VAR"` quoting is what actually mitigates injection |
| Argue "but `steps.*.outputs.*` is trusted" | Reasoning step, not a code change | True semantically, but misses the principled point that any `${{ … }}` in `run:` is a sink regardless of current source trust | Apply the env-var lift uniformly — it is the right thing to do for trusted sources too |

## Caveats

- **Always double-quote `"$VAR"` in shell**, even for numeric-looking values like issue numbers. Unquoted `$VAR` is itself an injection vector if the value ever contains whitespace or globs.
- **Do not name env vars with `GITHUB_` prefix** — that prefix is reserved by GitHub Actions for its own variables and may collide or be silently overridden.
- **The `env:` block is per-step**, not per-job. If you have the same expression in multiple steps, lift it in each one (or move it to a job-level `env:` if appropriate, but a step-level lift is the minimal, locally-scoped change).
- **Composite actions and reusable workflows** follow the same pattern — `env:` works at every level where `run:` is allowed.
- **Heredocs are still risky**: even `cat <<EOF` inside `run:` will splice `${{ … }}` before the shell sees the heredoc body. Lift to `env:` and use `"$VAR"` inside the heredoc instead.
- **Related but different hook**: if `Edit` is blocked on `.github/workflows/*.yml` by path alone (no `${{` involved), see `edit-tool-blocked-workflow-files` — that hook has a different root cause and a different workaround (use `Bash` with `python3 -c` for surgical edits).

## Permanent Fix Location

This pattern is a project-wide convention. Consider documenting it in the consuming repo's
`.claude/shared/error-handling.md` (or equivalent) so all agents apply it by default — not just
when the hook fires. The GitHub Security Lab article linked above is the canonical external
reference.
