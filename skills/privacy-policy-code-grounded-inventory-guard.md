---
name: privacy-policy-code-grounded-inventory-guard
license: BSD-3-Clause
description: "Author a privacy / data-retention / deletion policy (GDPR audit finding) for a code repository by grounding the data inventory in grep-verified persistence constants and freezing it with a structural guard test. Use when: (1) an audit finding says no privacy/retention/deletion policy exists for a repo that handles third-party content or developer credentials, (2) writing any compliance/policy doc whose claims can be derived from code (state dirs, cache dirs, crash-dump paths), (3) a policy doc needs protection against silent rot or deletion, (4) tempted to paste a boilerplate GDPR template that overstates the project's data-controller role."
category: documentation
date: 2026-07-17
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [privacy, gdpr, retention, deletion-policy, compliance, data-inventory, structural-guard, doc-rot, audit-remediation, security-policy]
---

# Privacy Policy Authoring: Code-Grounded Inventory + Structural Guard

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-17 |
| **Objective** | Remediate a Section-15 MAJOR audit finding ("no privacy/GDPR retention or deletion policy") for a repo handling GitHub content and developer credentials |
| **Outcome** | Reviewable plan: root-level `PRIVACY.md` whose every claim maps to a code constant, plus a pytest structural guard freezing sections, paths, and cross-links |
| **Verification** | unverified |

## When to Use

- An audit flags a missing privacy / data-processing / retention / deletion policy
- The repository is a locally run library or CLI tool (not a hosted service) that touches third-party content (GitHub issues/PRs) or credentials (tokens in env vars)
- Any compliance document whose factual claims (where data lives, what is persisted) are derivable from source code
- A published policy doc needs a guard so it cannot silently rot, lose sections, or be deleted

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until the implementing PR merges with CI green.

### Quick Reference

```bash
# Step 1: Build the data inventory FROM CODE, not from a template.
# Grep for every persistence surface: state dirs, cache/worktree dirs, dump paths.
grep -rn "DEFAULT_STATE_DIR\|state_dir\|base_dir" <pkg>/ | grep -i "build\|cache\|tmp"
grep -rn "DEFAULT_TARGET_DIRS\|dump\|bundle" <pkg>/forensics/ 2>/dev/null

# Step 2: Confirm what is NOT collected (no telemetry endpoint, creds env-only).
# Reuse the SECURITY.md threat model as evidence rather than re-asserting.

# Step 3: Reuse the repo's already-published contact channel from SECURITY.md
# for data-subject requests. Never invent a new mailbox.

# Step 4: Check for an existing doc-rot invariant before adding your own
# (e.g. a pre-commit script rejecting hard-coded "As of YYYY-MM-DD" stamps)
ls scripts/ | grep -i "policy\|date"

# Step 5: Freeze the policy with a structural guard pytest in the docs test dir.
```

### Detailed Steps

1. **Inventory from code, not boilerplate.** Every row of the policy's data-inventory table must cite a real persistence surface found by grep: automation state dir (`DEFAULT_STATE_DIR = "build/.issue_implementer"` in `automation/models.py`), worktree cache (`build/.worktrees` in `worktree_manager.py`), crash bundles (`DEFAULT_TARGET_DIRS = ("/tmp/crash-bundle/cores",)` in `forensics/coredump_handler.py`). If a claimed store has no code citation, delete the row.

2. **State the honest controller posture.** A locally run library that processes repository content under the operator's own GitHub authorization is not a hosted data controller. Generic GDPR templates written for SaaS overstate obligations (sub-processors, DPAs, cookie notices) and create false commitments. Say what is true: no servers, no telemetry, credentials env-only, GitHub is the system of record.

3. **Reuse published channels and invariants.** Data-subject request contact = the security contact already published in SECURITY.md. Date-stamp hygiene = the repo's existing rule (rot-prone `As of YYYY-MM-DD` stamps are banned in SECURITY.md by a pre-commit script); apply the same regex to the new doc via the guard test instead of adding a second hook (KISS).

4. **Place the policy where governance docs already live.** Root-level, sibling to SECURITY.md and CODE_OF_CONDUCT.md — GitHub surfaces root community-health files. Cross-link from SECURITY.md and the docs index so it is discoverable from both entry points.

5. **Freeze it with a structural guard test** in the repo's docs test suite (pattern: existing ADR structural guard). Assert: file exists; required section headings present (Scope, Data Inventory, Retention, Deletion Procedures, Data Subject Requests, Sub-processors); the real persistence paths appear verbatim; SECURITY.md and the docs index both link to it; no `As of \d{4}-\d{2}-\d{2}` stamp. TDD order: guard test first (RED), then the doc (GREEN).

6. **Retention claims must be enforceable.** For ephemeral local caches, the honest retention statement is "operator-deletable at any time; no fixed obligation because GitHub is the system of record" — not an invented N-day schedule nobody enforces. Reserve fixed windows (e.g. 30-day crash-bundle review) for genuinely secret-bearing artifacts, and label them as operator guidance.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed / Was Rejected | Lesson Learned |
|---------|----------------|------------------------------|----------------|
| Boilerplate GDPR template | Standard SaaS privacy-policy skeleton | Claims controller role, sub-processors, cookie/tracking sections that are false for a local CLI library | Derive posture from the threat model; false compliance claims are worse than none |
| New privacy mailbox | Dedicated privacy@ contact | Unmonitored mailboxes rot; SECURITY.md already publishes a monitored channel | Reuse the published security contact for DSRs |
| Absolute date stamps | "As of 2026-07-17 we retain..." | Repo precedent: hard-coded dates in SECURITY.md rotted and are now blocked by a pre-commit check | Extend the existing no-hardcoded-date invariant to the new doc via the guard test |
| Second pre-commit hook | New hook script to guard PRIVACY.md dates | Duplicates an existing mechanism; pytest guard in the docs suite covers it in one place | One structural guard test beats parallel hook infrastructure (KISS/DRY) |

## Results & Parameters

```bash
# Planning-phase evidence (ProjectHephaestus issue #2175, plan reviewed by pipeline):
# Persistence surfaces confirmed by grep before writing any policy row:
#   hephaestus/automation/models.py:151      DEFAULT_STATE_DIR = "build/.issue_implementer"
#   hephaestus/automation/worktree_manager.py:90   base_dir default repo_root/build/.worktrees
#   hephaestus/forensics/coredump_handler.py:62    DEFAULT_TARGET_DIRS = ("/tmp/crash-bundle/cores",)
# Existing doc-rot invariant reused:
#   scripts/check_security_policy_no_hardcoded_date.py  (regex: As of \d{4}-\d{2}-\d{2})
# Guard-test pattern followed:
#   tests/unit/docs/test_adr_records.py  (repo-root via Path(__file__).resolve().parents[3])

# Verification commands the implementing PR must run:
uv run pytest tests/unit/docs/test_privacy_policy.py -v
uv run pytest tests/unit/docs -v
uv run python scripts/check_security_policy_no_hardcoded_date.py
uv run pre-commit run markdownlint-cli2 --files PRIVACY.md SECURITY.md docs/index.md
```

## Evidence

- ProjectHephaestus issue #2175 ("[majo] Publish privacy retention and deletion policy", Section 15 MAJOR audit finding) — implementation plan posted to the issue enumerates every file:line citation above.
- Repo precedent for the no-hardcoded-date rule: ProjectHephaestus issue #730 and `scripts/check_security_policy_no_hardcoded_date.py`.
- Structural-guard precedent: `tests/unit/docs/test_adr_records.py` (ADR skeleton + bidirectional index sync).
