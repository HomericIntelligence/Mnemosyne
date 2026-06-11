---
name: git-trailer-human-identity-vs-model-provenance
description: "Keep a stable human-shaped identity in git commit identity slots (Co-Authored-By) and route volatile machine metadata (model id, version, run id) to a separate custom trailer (Implemented-By). Use when: (1) generating git commit trailers in automation, (2) deciding where model/version/run metadata goes in a commit, (3) debugging broken mailmap/shortlog/contribution aggregation from automated commits, (4) a model id or version string is leaking into a Co-Authored-By name slot, (5) writing a regression test that locks a commit-trailer identity slot to a human-shaped value."
category: tooling
date: 2026-06-11
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: []
---
# Git Trailer: Human Identity vs Model Provenance

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-11 |
| **Objective** | Stop automation from putting a model id into the `Co-Authored-By:` name slot; split stable human identity from volatile model provenance into two distinct git trailers |
| **Outcome** | ✅ `Co-Authored-By:` carries a stable human name; new `Implemented-By:` trailer carries the model id; locked by a regex regression test. PR #1011 merged to ProjectHephaestus main with green CI |
| **Verification** | verified-ci |

## When to Use

- You are generating git commit trailers programmatically in an automation pipeline
- You are deciding where to put model/version/run metadata in a commit message
- `git mailmap`, `git shortlog`, or GitHub contribution aggregation is fragmented because automated commits use a different "author" name per run/model
- A model id (e.g. `claude-haiku-4-5`) or version string is appearing in the NAME slot of a `Co-Authored-By:` trailer
- You want a regression test that asserts an identity slot stays human-shaped and that machine metadata does not leak into it

## Verified Workflow

The core rule: **identity slots hold stable, human-shaped names; machine provenance gets its own custom trailer.**

### Quick Reference

```text
# WRONG — model id in the Co-Authored-By name slot (breaks mailmap/shortlog)
Co-Authored-By: claude-haiku-4-5 <noreply@anthropic.com>

# RIGHT — stable human name in the identity slot, model provenance in its own trailer
Implemented-By: claude-haiku-4-5
Co-Authored-By: Claude Code <noreply@anthropic.com>

# Codex branch
Implemented-By: Codex
Co-Authored-By: Codex <noreply@openai.com>
```

```python
# Split the two concerns into two helpers:
def _coauthor_for_agent(agent):
    # returns the STABLE HUMAN NAME + email for the identity slot
    # Claude -> ("Claude Code", "noreply@anthropic.com")
    # Codex  -> ("Codex", "noreply@openai.com")
    ...

def _provenance_for_agent(agent):
    # returns the MACHINE METADATA (model id) for the Implemented-By trailer
    # Claude -> implementer_model()  (honors HEPH_IMPLEMENTER_MODEL override)
    # Codex  -> "Codex"
    ...

# commit_changes emits BOTH trailers: Implemented-By line, then Co-Authored-By line.
```

### Detailed Steps

1. **Identify the leak.** Find the helper that builds the `Co-Authored-By:` line. If it
   places a model id, version string, or run id into the name slot
   (e.g. `return (implementer_model(), "noreply@anthropic.com")`), that is the bug.
2. **Split identity from provenance.** Keep `_coauthor_for_agent(agent)` returning a
   stable human-shaped name (`Claude Code` / `Codex`). Add a new
   `_provenance_for_agent(agent)` returning the volatile model id (honoring any
   `HEPH_IMPLEMENTER_MODEL` env override), or the literal `Codex` for the Codex branch.
3. **Emit two trailers.** In `commit_changes`, write the `Implemented-By: <model-id>`
   line first, then the `Co-Authored-By: <human name> <email>` line.
4. **Lock it with a regex test.** Assert the identity slot is human-shaped and the model
   id does NOT appear in it:

   ```python
   _COAUTHOR_HUMAN_NAME_RE = re.compile(r"^Co-Authored-By: [A-Za-z].* <.*@.*>$")
   ```

   - `test_claude_coauthor_is_human_name_not_model_id`: line equals
     `Co-Authored-By: Claude Code <noreply@anthropic.com>` AND the model id
     (`claude-test-model-9`) is absent from the `Co-Authored-By` line.
   - `test_claude_implemented_by_carries_model_id`: `Implemented-By: claude-test-model-9` present.
   - `test_implemented_by_reflects_env_override`: `HEPH_IMPLEMENTER_MODEL` honored in `Implemented-By`.
   - `test_codex_coauthor_is_codex_human_name`: Codex branch compliant.
5. **Run the suite and confirm CI is green** before merging.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | `_coauthor_for_agent` returned `(implementer_model(), "noreply@anthropic.com")` — the raw model id (e.g. `claude-haiku-4-5`) as the co-author NAME | Looked convenient (single trailer, model visible in `git log`) but a per-model name fragments `git mailmap`, `git shortlog`, and GitHub contribution aggregation — each model id is treated as a distinct contributor; the name slot is meant for a stable human-shaped identity per the git trailer / RFC 5322 convention | One trailer cannot serve both "who is credited" (stable identity) and "what produced this" (volatile machine metadata). Split them into two trailers. |

## Results & Parameters

**Source:** ProjectHephaestus `hephaestus/automation/pr_manager.py`

```text
# Trailers emitted by commit_changes (Claude branch, model claude-haiku-4-5):
Implemented-By: claude-haiku-4-5
Co-Authored-By: Claude Code <noreply@anthropic.com>

# Codex branch:
Implemented-By: Codex
Co-Authored-By: Codex <noreply@openai.com>
```

**Regression test:** `tests/unit/automation/test_pr_manager.py::TestCoAuthorLine`

```python
_COAUTHOR_HUMAN_NAME_RE = re.compile(r"^Co-Authored-By: [A-Za-z].* <.*@.*>$")
# test_claude_coauthor_is_human_name_not_model_id
# test_claude_implemented_by_carries_model_id
# test_implemented_by_reflects_env_override   (honors HEPH_IMPLEMENTER_MODEL)
# test_codex_coauthor_is_codex_human_name
```

Env override: `HEPH_IMPLEMENTER_MODEL` overrides the model id placed in `Implemented-By:`.

**Generalizable rule:** When automation generates commit trailers, never put volatile
machine metadata (model ids, version strings, run ids) into identity slots like
`Co-Authored-By:`. Keep identity stable and human-shaped; route machine provenance to a
separate custom trailer (`Implemented-By:`, `Generated-By:`, etc.). Lock it with a regex
test asserting the identity name slot is human-shaped and that machine metadata does not
leak into it.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | PR #1011 / issue #717 | model-id-in-coauthor-name broke mailmap; split into Co-Authored-By (human) + Implemented-By (model) |
