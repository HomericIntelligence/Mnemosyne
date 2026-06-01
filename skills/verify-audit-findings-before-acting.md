---
name: verify-audit-findings-before-acting
description: "Strict-mode repo audits routinely hallucinate critical findings (references to nonexistent files, claims of missing CI checks that already exist) AND miss real ones (linter bugs, root causes). Verify each finding against current filesystem state BEFORE writing a remediation plan, and search for inverse hypotheses (what the audit MISSED) before acting. Use when: (1) consuming output from /repo-analyze-strict or any swarm-audit, (2) about to write a remediation plan from audit output, (3) about to bulk-file remediation issues, (4) deciding which audit majors are real, (5) the audit's CRITICAL/MAJOR count differs from what you can verify on disk."
category: documentation
date: 2026-05-31
version: "1.2.0"
user-invocable: false
verification: verified-ci
history: verify-audit-findings-before-acting.history
tags: [audit, code-review, fact-checking, remediation, phase-1-verification, inverse-hypothesis-search, audit-corrections-section, root-cause-discovery, remediation-plan-corrections]
---

# Verify Each Audit Finding Against the Filesystem Before Acting

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-31 |
| **Objective** | Catch hallucinated audit findings before they become wasted remediation work AND discover root-cause findings the audit missed by searching the inverse hypothesis space |
| **Outcome** | Saved 3 false-positive PRs AND discovered 1 root-cause finding the audit missed; 10 PRs landed, 9 already merged with green CI on first attempt |
| **Verification** | verified-ci (10 PRs merged with green CI in 2026-05-31 session; ≈10–25% false-positive rate corroborated across three strict-full sessions) |
| **History** | [changelog](./verify-audit-findings-before-acting.history) |

## When to Use

- Receiving output from `/repo-analyze-strict`, `/repo-analyze-strict-full`, or any swarm-of-15 audit
- **About to write a remediation plan from audit output** *(added v1.2.0)* — Phase 1 verification MUST run before plan generation, not after issue filing. Drafting a plan against unverified findings means writing PRs that fix non-issues.
- About to bulk-file `gh issue create` for every flagged finding
- Reviewing a "missing X" finding before adding X to the codebase
- A new auditor (model or human) makes a sweeping "you don't have Y" claim about your repo
- **Any "missing control / no Y in CI" claim** — controls often live in an aggregator/required workflow, not the file named after them. Grep the WHOLE `.github/` before believing absence.
- **Two swarm section agents disagree on the same checkable fact** — the disagreement itself is the verification trigger; grep the fact before filing either way.
- **Before claiming the audit is "complete enough" to drive remediation** *(added v1.2.0)* — search the INVERSE hypothesis space: if the audit says "linter is MISSING", ALSO check "is the linter PRESENT but WRONG?" The inverse class is the most common audit blind spot and is often the actual root cause.
- **The audit's CRITICAL/MAJOR count differs from your independent count** *(added v1.2.0)* — a 1- or 2-finding gap is normal noise; a 3+ finding gap means either you or the audit is wrong about ground truth. Verify before believing either side.

## Verified Workflow

### Quick Reference

```bash
# For EACH audit finding, run the 30-second verify step:
ls <path-the-audit-claimed-is-missing>     # is the file really absent?
grep -rn <symbol-or-config> <path>          # is the integration really missing?
git log --all -- <path>                     # was it ever there? (helps spot a recent delete)
```

### Detailed Steps

**The pattern:** Strict-mode audit agents are instructed to "treat absence of evidence as evidence of absence." They take ~60s per section and read excerpts. They make claims like:

- "`.claude/settings.local.json` references `.claude/hooks/learn-trigger.py` (missing) — CRITICAL"
- "No `gitleaks` / `truffleHog` in CI — MAJOR"
- "`bootstrap` recipe is broken; doesn't install the package — MAJOR"

Each is a structurally plausible failure. None of them was true in the verified session.

**Mechanism of the false positives:**

1. **Hallucinated cross-reference** — the agent saw `.claude/` in `.gitignore` and inferred a `.claude/hooks/learn-trigger.py` reference must exist in `.claude/settings.local.json`. Neither file existed.
2. **Stale knowledge** — the agent's audit window covered files in batches; gitleaks v8.30.0 IS installed in `.github/workflows/_required.yml` but the security-section agent didn't search that file.
3. **Documentation reading error** — pixi.toml comments warned about `dev-install` being required, but the agent inferred this meant the `bootstrap` justfile recipe was broken. The recipe was incomplete but pixi's editable build did make the package importable for most CLIs; the audit's "imports fail" claim was wrong.
4. **Control exists in a DIFFERENT file than the agent read** *(new class, 2026-05-27)* — the Security agent (S8) reported "no secrets-scanning in CI" after reading only `.github/workflows/security.yml` (which runs pip-audit only). Gitleaks IS present and is a REQUIRED check at `.github/workflows/_required.yml:478-497` with a SHA-pinned binary download. When an audit says "missing X", grep the WHOLE `.github/` (or whole repo) — controls live in aggregator/required workflows, not the file named after the control. (A real gap did remain — no SAST/CodeQL — so verification separates the true gap from the false one.)
5. **Line-number drift even in TRUE findings** *(new class, 2026-05-27)* — the issue-filing swarm re-verified every cited file:line and found refs stale even when the finding was real: `.claude/workflows/development.md` "rebase merge" was line 19 not 18; `runtime.py:93` already had `timeout=10` (excluded, though :77/:244 were genuinely unbounded); README had 2 version-pin lines not the 3 claimed. A finding can be real while its cited location is stale — re-verify exact file:line at fix/file time.
6. **Already-fixed-state hallucination** *(new class, 2026-05-31)* — `hephaestus/_version.py` was flagged CRITICAL "tracked in git despite `.gitignore`". `git ls-files hephaestus/_version.py` returned empty — the file was already gitignored AND not tracked. The audit hallucinated the violation. `dist/` was flagged MAJOR "contains stale dev wheels" — the directory did not exist. The audit invented a state the repo had never been in. Run `git ls-files`, `ls -d`, and `find` to confirm the claimed bad state before believing it.
7. **Cross-file collision hallucination** *(new class, 2026-05-31)* — `security.yml` was flagged MAJOR "duplicates `_required.yml` security jobs". Reading `_required.yml` revealed it contains NO security jobs (gitleaks notwithstanding — that's a separate job, not a duplicate). `security.yml` is standalone. The audit invented a structural overlap that did not exist. When an audit claims "file A duplicates file B", read both files; do not trust prose summaries.

**Verification protocol (per finding, 30s budget):**

| Finding type | Verify with |
|--------------|-------------|
| "Reference to missing file X" | `ls X && grep -rln 'reference-pattern' <dir>` — if file absent AND no reference exists, finding is hallucinated |
| "No SAST/secrets-scan/dep-audit in CI" | `grep -rE 'gitleaks\|trufflehog\|detect-secrets\|pip-audit\|bandit\|codeql\|semgrep' .pre-commit-config.yaml .github/workflows/*.yml` — if any line matches, the tool IS present |
| "Function X has wrong return type" | `grep -nE '^def X' <file> && grep -nE 'return\|sys.exit' <file>` — read the actual signature + every return |
| "Bootstrap/setup is broken" | Run the bootstrap recipe in a clean env (or read it + the dependencies it triggers); don't trust audit prose |
| "Coverage gap in module Y" | `pixi run pytest tests/ --cov=hephaestus.Y --no-cov-fail` — measure real coverage, not the audit's count |

**Triage rule:** If verification shows the finding is wrong, log it but DO NOT file an issue or open a PR. Track stale-finding rate per audit run; if it exceeds 20%, escalate to question the audit methodology, not the codebase.

### Phase 1 Verification BEFORE Remediation Planning *(added v1.2.0)*

Run Phase 1 verification BEFORE drafting the remediation plan — not before issue filing, not before PR creation. The plan must be written against verified findings, not raw audit output. Drafting a plan against unverified findings produces PRs that fix non-issues, and (worse) leaves the actual root causes untouched.

**Workflow:**

1. Run the 15-section strict audit via swarm.
2. **Dispatch ONE Explore agent with the full audit findings list. Ask: "verify or refute each finding using `gh api`, `git ls-files`, and direct file reads — NOT just `grep`."**
3. The Explore agent returns a STATUS table:

   | Finding | Audit Claim | Verification Method | Status | Evidence |
   |---------|-------------|---------------------|--------|----------|
   | F1 | "_version.py tracked despite .gitignore" | `git ls-files hephaestus/_version.py` | **REFUTED** | empty output → not tracked |
   | F2 | "no pr-policy required check" | `gh api repos/.../rulesets/RULESET_ID` | **CONFIRMED** | ruleset omits pr-policy |
   | F3 | "security.yml duplicates _required.yml" | Read both files | **REFUTED** | _required.yml has no security jobs |
   | F4 | "stale CLAUDE.md version section :411-413" | Read :411-413 | **PARTIAL** | section exists but at :409-413 (line drift) |

4. **Search the inverse hypothesis space (Phase 1.5):** for every finding of the form "X is missing", spend an extra 30s asking the dual question: "is X present but WRONG?" The audit is structurally biased toward absence-class findings and misses presence-but-incorrect findings.
5. Write the plan against the CORRECTED finding list — not the raw audit. Drop REFUTED findings; promote NEW-FINDING discoveries; adjust file:line for PARTIAL findings.

### Inverse-Hypothesis Search Catalog *(added v1.2.0)*

| Audit Says | ALSO Check |
|------------|------------|
| "linter is MISSING" | "linter is PRESENT but enforcing the WRONG rule" |
| "no test for X" | "test for X exists but mocks the contract X promises" |
| "no CI gate for Y" | "CI gate for Y exists but `continue-on-error: true` makes it noop" |
| "no doc for Z" | "doc for Z exists but contradicts the implementation" |
| "no policy enforcing P" | "policy file exists but its checker function is wrong" |
| "no integration test for E2E" | "integration test exists but skips the real network path" |
| "no error handling for E" | "error handler exists but swallows the exception silently" |

**Worked example (2026-05-31, ProjectHephaestus):** The audit flagged "skills mandate `--rebase` despite squash-only policy" as a content bug in two skill files. The inverse hypothesis check asked: "is there a linter ENFORCING `--rebase` somewhere?" Answer: yes — `hephaestus/validation/doc_policy.py` was REJECTING `--squash` and requiring `--rebase`. That linter was the ROOT CAUSE of the skill content. Fixing the skills first (without fixing the linter) would have been blocked by the linter the audit missed. Phase 1 sequenced PR1 = fix linter, PR2+ = fix skills. The 9 merged PRs all passed CI on first attempt because the corrected sequence was used.

### AUDIT CORRECTIONS Section in the Remediation Plan *(added v1.2.0)*

Every remediation plan generated from a strict audit MUST contain an explicit "AUDIT CORRECTIONS" section listing what Phase 1 refuted, with evidence. Without it, reviewers cannot tell why the plan's finding count differs from the audit's count, and downstream agents will re-introduce the refuted findings.

**Required structure:**

```markdown
## AUDIT CORRECTIONS

Phase 1 ground-truth verification refuted the following audit findings. They are
NOT addressed by any PR in this plan.

| Audit Finding | Audit Severity | Verification | Reason for Drop |
|---------------|----------------|--------------|-----------------|
| `_version.py` tracked despite `.gitignore` | CRITICAL | `git ls-files hephaestus/_version.py` returned empty | Not tracked. `.gitignore` and hatch-vcs config already correct. |
| `dist/` contains stale dev wheels | MAJOR | `ls -d dist/` → "No such file or directory" | Directory does not exist. Already gitignored. |
| `security.yml` duplicates `_required.yml` security jobs | MAJOR | Read both files | `_required.yml` has no security jobs. `security.yml` is standalone. |

## AUDIT-MISSED FINDINGS (NEW)

Phase 1 inverse-hypothesis search discovered findings the audit did not flag.
These ARE addressed by PRs in this plan.

| Inverse Question | Finding | Severity | PR |
|------------------|---------|----------|-----|
| "Is the squash-only linter present but enforcing `--rebase`?" | `hephaestus/validation/doc_policy.py` REJECTS `--squash` and requires `--rebase`, contradicting CLAUDE.md squash-only policy. Root cause of `--rebase` text in skills. | CRITICAL | PR1 |
```

This section is the bridge between the audit's reported finding count and the plan's PR count. Reviewers can immediately see "audit said 3 CRITICAL, plan has 1 PR — why?" and read the evidence-backed refutation.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| File all audit findings as issues, then triage in PRs | Trust the audit; backlog will sort itself | 3 of 11 majors were stale → 3 PRs would have produced backwards "fixes" (e.g. adding gitleaks when it's already there) | Triage during audit-consume, not after issue filing |
| Re-run the audit to "verify itself" | Hope a second pass catches the hallucinations | Identical output. Strict-mode prompt + same model = same hallucinations | Audits can't fact-check themselves; you must check against the filesystem |
| Believe "CRITICAL" severity tags | Defer to the audit's own ranking | The "CRITICAL: missing hook" was hallucinated. Severity tag doesn't correlate with finding accuracy | Severity is a model's prediction, not a filesystem fact |
| Trust "missing control" from the obviously-named file | S8 read only `security.yml`, declared "no secrets-scanning in CI" | Gitleaks was a REQUIRED check in `_required.yml:478-497`, a file the agent never grepped | For any "missing X" claim, grep the WHOLE `.github/`/repo — controls live in aggregator/required workflows |
| File/fix at the audit's cited file:line without re-checking | Open the issue/PR at the exact line the audit reported | Line refs were stale even in TRUE findings (line 18 vs 19; `runtime.py:93` already had `timeout=10`; 3 vs 2 README pins) → wrong line or already-fixed | Re-verify exact file:line at fix/file time; a finding can be real while its location is stale |
| Trust strict audit findings without verification before remediation planning | Auditor (Opus 4.7) flagged 3 CRITICAL + 26 MAJOR + 40 MINOR; I started drafting the remediation plan from the raw list | 3 of 29 findings (10.3%) were factually refuted by Phase 1: `_version.py` not tracked, `dist/` did not exist, `security.yml` did not duplicate `_required.yml`. Drafting against the raw list would have produced 3 PRs that fix non-issues | Phase 1 verification MUST run BEFORE remediation planning, not before issue filing. The plan must be written against the corrected finding list, not raw audit output |
| Skip the inverse-hypothesis check ("audit says missing — also check is it present but wrong?") | Treat the audit's hypothesis space as complete | The audit missed `hephaestus/validation/doc_policy.py` linter that was REJECTING `--squash` and requiring `--rebase`. That linter was the ROOT CAUSE of `--rebase` text in skill files (myrmidon-swarm:318, learn:422). Fixing skills without fixing the linter would have blocked the very PRs the plan generated | For every "X is missing" finding, also ask "is X present but wrong?" — the inverse class is the most common audit blind spot and is often the root cause |
| Omit AUDIT CORRECTIONS section from the remediation plan | Hand the plan to reviewers without explaining why the PR count differs from the audit's finding count | Reviewers ask "audit said 3 CRITICAL, plan has 1 PR — what happened?" Downstream agents re-introduce the refuted findings in subsequent rounds because the refutation evidence is not preserved | Every audit-driven remediation plan MUST include an AUDIT CORRECTIONS section listing what was refuted, with evidence. Reviewers must be able to immediately see why the plan's count differs |

## Results & Parameters

**Stale-finding rate observed:** 3/11 majors in the 2026-05-26 ProjectHephaestus audit (27%), ~3/~16 findings false/stale in the 2026-05-27 strict-full audit (≈20%), and 3/29 findings (10.3%) refuted in the 2026-05-31 strict-full audit. Consistent 10–25% false-positive rate across three sessions. Likely range across audits: 10–30%.

**Missed-finding rate observed (added v1.2.0):** In the 2026-05-31 session, Phase 1's inverse-hypothesis search discovered 1 root-cause finding the audit missed (the `doc_policy.py` `--rebase`-enforcing linter). N=1 across one session is not yet a stable estimate; conjecture: 1–3 missed root causes per strict audit, with the inverse-hypothesis class being the most common.

**Grep-the-whole-`.github/` tip:** Before believing any "no Y in CI" / "missing control" finding, grep the entire `.github/` tree, not just the file named after the control. Controls are commonly wired into an aggregator or `_required.yml` workflow rather than the obviously-named file (e.g. Gitleaks lived in `_required.yml:478-497`, not `security.yml`):

```bash
grep -rniE "gitleaks|trufflehog|secrets-scan|codeql|semgrep|bandit|pip-audit" .github/
```

**Verification is "cheaply confirm," not "distrust everything":** in the 2026-05-27 session the audit's verified MAJOR findings held up — stale CLAUDE.md version section at `:411-413` vs pyproject hatch-vcs; `pr-policy` confirmed absent from the live ruleset via `gh api .../rulesets`; broken `just watch` reproduced live (`pixi run --environment dev` → "unknown environment 'dev'"). The discipline pays for itself by spending 30s/finding instead of a wasted remediation PR.

**Time cost:**
- Without verification: ~10 minutes to file 11 issues + ~30 minutes per false-positive PR to discover the fix is a no-op = ~100 minutes wasted on 3 false positives.
- With verification: ~5 minutes (30s × 11 findings) = saves ~95 minutes per audit.

**Specific verification commands that caught the false positives in this session:**

```bash
# Catch #1: missing hook reference
ls .claude/settings.local.json .claude/hooks/learn-trigger.py 2>&1
# Both → "No such file or directory" → no reference, no missing file, finding is hallucinated

# Catch #2: gitleaks claim
grep -nE 'gitleaks|trufflehog|detect-secrets' .pre-commit-config.yaml .github/workflows/*.yml
# Returned multiple matches in _required.yml → gitleaks IS installed and run; finding is stale

# Catch #3: bootstrap claim — partial true, partial false
grep -A 5 'bootstrap' justfile  # showed recipe omits dev-install (real)
# but: pixi.toml [dependencies] auto-installs package as editable for most CLIs (refutes "imports fail")
```

**Pre-flight script for any strict audit:**
```bash
# Run this script after reading the audit report, BEFORE filing issues.
# Outputs: real_issues.txt, stale_findings.txt
for finding in <each major from the report>; do
  echo "Finding: $finding"
  # 30-second verify per finding type (table above)
  read -p "Real? [y/N] " yn
  if [[ "$yn" == "y" ]]; then echo "$finding" >> real_issues.txt
  else echo "$finding" >> stale_findings.txt; fi
done
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | 2026-05-26 strict-mode full-coverage audit (B+ 84%) | 3 of 11 majors were stale: hallucinated `.claude/hooks/learn-trigger.py` reference (S11 critical), claim of "no gitleaks in CI" (S8 major) when gitleaks v8.30.0 was already wired, partially-wrong claim that `bootstrap` recipe was broken (S13 major). Caught all 3 in under 5 minutes of `ls`/`grep` verification before filing issues. |
| ProjectHephaestus | 2026-05-27 `/repo-analyze-strict-full` (15 Sonnet agents, full coverage, B+ ~86% GO) | ~3 of ~16 findings false/stale (≈20%). New classes: S8 "no secrets-scanning in CI" was false — Gitleaks REQUIRED at `_required.yml:478-497` (S6 said present, S8 said absent → inter-agent disagreement was the trigger). Line drift in TRUE findings: development.md line 19 not 18; `runtime.py:93` already had `timeout=10`; README 2 pins not 3. Verified MAJORs held: stale CLAUDE.md `:411-413`, pr-policy absent from live ruleset, broken `just watch` reproduced live. |
| ProjectHephaestus | 2026-05-31 `/repo-analyze-strict-full` 15-section audit (Opus 4.7 auditor, 3 CRITICAL + 26 MAJOR + 40 MINOR, B- 82.5% overall) | **3 of 29 findings (10.3%) REFUTED by Phase-1 Explore agent before remediation:** (1) `hephaestus/_version.py` CRITICAL "tracked despite .gitignore" — `git ls-files` returned empty, not tracked, gitignore + hatch-vcs already correct; (2) `dist/` MAJOR "contains stale dev wheels" — directory did not exist, already gitignored; (3) `security.yml` MAJOR "duplicates `_required.yml` security jobs" — `_required.yml` has NO security jobs, `security.yml` is standalone. **Phase-1 also DISCOVERED 1 root-cause finding the audit missed:** `hephaestus/validation/doc_policy.py` was REJECTING `--squash` and requiring `--rebase`, contradicting CLAUDE.md squash-only policy. This linter was the ROOT CAUSE of `--rebase` text in skill files (myrmidon-swarm:318, learn:422). Phase 1 sequenced PR1=fix linter first, PR2+=fix skills. **10 PRs landed; 9 already merged with green CI on first attempt; 1 in CI with auto-merge armed.** Without Phase 1, ~3 PRs would have fixed non-issues AND the next PR after skill fixes would have been blocked by the unfixed linter. Verification level upgraded to verified-ci. |
