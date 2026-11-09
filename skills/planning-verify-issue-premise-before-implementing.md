---
name: planning-verify-issue-premise-before-implementing
license: BSD-3-Clause
description: "Verify issue and plan premises against authoritative sources before acting. Use this when an issue, PR plan, review, CI fix, or enforcement change assumes an artifact exists, prior work merged, a live service still needs work, a full population was checked, a CI job gates, an implementation returns a shape, or an integration point exists. Convert the premise into deterministic checks before implementing, closing, gating, or declaring work complete. Includes the temporal check: a premise token absent from the current tree may mean the issue was valid at filing and later overtaken by a merged PR (half-zombie issue) — date the removal with git log --full-history and triage each ask separately. At hand-off, an implement-ready label or a reviewed plan is not a tree-state guarantee: plans decay during dwell as merges land, so re-sweep the plan's anchors at dispatch and branch per-plan, residual-only, or re-plan (a close-out of a discharged plan requires a fresh review bound to the revised plan, and must never re-create machinery a merged redesign removed). Also sweep authority records at hand-off: an owner decision or decision-table row published after the plan review GO can reject the plan's core approach — the label is loop state, not architecture authority; realign the plan to the recorded decision, implement only the residual work (possibly zero), and close with evidence. Also bind self-produced evidence to the environment that produced it: a reproduction run on a stale checkout proves a defect existed, not that it exists — re-run it at the fetched default-branch head, and for a live deployed system compare the deployed artifact's version with the default branch before fix design; deployment lag turns the incident into an operational remediation with no code change. At hand-off, also prove the change is active for its consumer: a local change at a load path outside version control is not durable, so check that the installed copy still contains it before reporting the helper fixed. Also check the GO'd plan text for a prescribed fallback for its own overtaking event (for example: if a named retirement lands first, record the findings on the owning record and close the issue as subsumed): when that trigger is objectively verified at dispatch — the removing change is merged, the owning record is closed, and the anchors are absent — execute the prescribed fallback instead of re-planning, because the fallback was reviewed as part of the plan. Also dispose per ask instead of per issue: when one part already warns, another part still refuses, an opt-in flag still gates the behavior, and a forge action cannot be proven from the tree, report the issue as requirements with each criterion marked held or remaining, and mark each stale documentation, decision-record, or forge claim as uncertain rather than restating it. For a documentation page or decision record that the store retirement removed, name the owning page that absorbed the content and plan against it. Also route each item of the issue's own Proposed fix list to its own disposition: one merged fix can discharge one named remedy while another names an operator-host surface absent from the repository, and a remedy about a live artifact is checked against the artifact producer, so a capability the producer writes only for new instances becomes a cold-path declaration. Also plan a gate, tracker, or blocking rule that uses a status table or dependency list: every data row is its own population member, so re-verify each row's claimed state at plan time and repeat that sweep before each outcome transition (a merge, a cut, a close, a label change), because a row may land after the issue was filed, and the gate that uses the states is the surface that goes stale. Also judge a plan file for use, not only for premise truth: report it as not usable when its content shows a duplicated header and revision block, an edit instruction that deletes one cited range while it keeps a sub-range of that range without a replacement text, an unresolved item that assigns a required action to a different record, or an item that names no exact change; the next actor cannot execute such a plan without a guess. Also grep every path the issue cites before you scope the work: a cited document, store, or record that no longer exists makes the issue premise stale at both ends, so date the removal and re-anchor the deliverable to the current owner, or reject the case as already superseded.h — the removing change is merged, the owning record is closed, and the anchors are absent — execute the prescribed fallback instead of re-planning, because the fallback was reviewed as part of the plan. Also select the vehicle for the residual asks: an open issue can be open only because a merged change used a non-closing reference, so list every PR bound to the issue, read what each already carries, and finish the residual on the bound PR instead of opening a competing one. A vehicle cut before a later repair shows that repair's failure set as stale-base reds — rebase and re-bind before repair."
category: architecture
date: 2026-11-01
version: "3.17.0"
user-invocable: false
verification: unverified
tags: [planning, issue-premise, verify-before-implementing, premise-verification, assumption-verification, authoritative-source, full-population-check, live-state-check, merge-state, prerequisite-verification, unmerged-branch, self-contained-pr, enforcement-gate, integration-point, ci-gate, ruleset, implementation-shape, route-shape, deterministic-gate, no-op-forbidden, issue-claims, follow-up-issue, overtaken-by-events, half-zombie-issue, per-ask-triage, git-history-archaeology, deleted-file-history, plan-dwell, handoff-rebind, dispatch-gate, residual-scope, review-gated-close, stale-reproduction, deployed-artifact-version, deployment-lag, decision-record, owner-decision, authority-rebind, load-path, load-root, converted-check-disposition, proposed-fix-triage, host-side-surface, artifact-producer-capability, cold-path-declaration, host-local-change, supersession-pr, inert-installed-copy, absorbed-document-target, per-criterion-disposition, clause-ledger-partial-discharge, authority-conflict, paired-commit-invariant, gate-rule-rows, blocking-rule, status-table, row-state-sweep, evidence-only-ask, transition-time-rebind, installed-artifact-currency, local-apply-claim, provisioned-tree-reverify, bound-vehicle, competing-pr-avoidance, non-closing-reference-open-issue, stale-base-vehicle-red, documentation-relocation, residual-content-gap]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/planning-verify-issue-premise-before-implementing.history"
history-cleanup-date: "2026-09-20"
---

# Planning: Verify Premises Before Acting

## Overview

Plans fail when they treat issue text, a previous plan, a branch-local grep, or a stale config as the source of truth. Before implementing, closing, gating, or declaring an issue done, identify the premise the plan depends on and verify it against the authority that can actually prove it.

This skill consolidates the planning-verify family into one generic workflow. It preserves the issue-specific examples in history and keeps the durable rule here: every consequential claim becomes a deterministic check before it drives scope, disposition, tests, or merge readiness.

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Objective | Merge similar planning-verification memories into a generic rule with concrete issue examples retained. |
| Date | 2026-11-07 |
| Objective | Extend per-ask triage to the issue's own Proposed fix list: each named remedy is a premise with its own discharge check. |
| Version | 3.9.0, minor bump: a multi-part issue routes each item of its own Proposed fix list to a disposition, because a merged fix can discharge one named remedy while the names cited by the other remedies are host-side and leave a documentation residual; a remediation claim about a live artifact is checked against the artifact producer, not only the current tree (carries the 3.7.0 load-root mapping, the 3.6.0 fallback, the 3.5.0 report reader, and the 3.4.0 environment binding). |
| Verification | verified-live: one planning pass discharged one of four named remedies as already merged, found two remedies to name only operator-host scripts absent from the repository, and planned the residual documentation and pre-publish blocker check. |
| Version | 3.5.0, minor bump: premise `report is one pass` — an enforcing reader that raises on the states under test cannot supply the diagnostic, so the plan needs a separate non-validating read (carries the 3.4.0 environment-bound evidence, the 3.3.0 hand-off rebinding, the 3.2.0 temporal check, and per-ask triage). |
| Prior | 3.4.0, minor bump: environment-bound premise evidence — a self-produced reproduction inherits the staleness of the checkout that produced it, and a production failure carries two code versions (deployed artifact and default branch); verify both before fix design (carries the 3.3.0 hand-off rebinding, the 3.2.0 temporal overtaken-by-events check, and per-ask triage that the table last recorded as 3.1.0). |
| Verification | unverified for this consolidation; source examples are preserved verbatim in history. |
| Date | 2026-10-31 |
| Objective | Add the authority-record branch to hand-off rebinding: a decision record published after the plan review GO can reject the plan's core approach while every anchor still holds. |
| Version | 3.5.0, minor bump: the anchor sweep alone returns "anchors hold → dispatch per plan", which dispatches a plan the recorded decision already rejected; sweep decision records beside anchors and realign to the record when they conflict (carries 3.4.0). |
| Verification | verified-live: one implementation dispatch realigned to a recorded owner decision instead of implementing the GO'd plan; the realigned plan converged to zero residual source work and a verified close. |
| Date | 2026-10-31 |
| Objective | Add the prescribed-fallback branch to hand-off rebinding: a GO'd plan can pre-authorize the disposition for its own overtaking event. |
| Version | 3.6.0, minor bump: the void-or-discharged branch first checks the plan text for a condition-triggered fallback; an objectively verified trigger executes the prescribed disposition without a fresh review round (carries 3.5.0). |
| Verification | verified-live: a later-merged retirement deleted the plan's entire anchor surface after the review GO; the plan's own fallback prescribed the close, which executed with zero source edits and no new review round. |
| Date | 2026-11-02 |
| Objective | Add the active-state branch to hand-off rebinding: a change at a load path outside version control can be replaced by a sync, so the fixed-helper claim needs a digest check at the owning revision. |
| Version | 3.10.0, minor bump: a local load-path patch reported active is an unverified premise; verify the installed copy byte for byte and plan against the owning repository (carries 3.8.0). |
| Verification | verified-live: one planning hand-off found all four target pull requests already merged, the consumer supersession patch closed, the owner fix open, and the previously hand-patched installed copy back at the owning default branch. |
| Date | 2026-11-07 |
| Objective | Add the partially discharged plus absorbed-document branch: dispose per ask when one behavior already warns, another still refuses, an opt-in flag still gates it, and a named page or decision record has no file. |
| Version | 3.10.0, minor bump: the zero-match rule dated removals for source sites but left a retired documentation page and a removed decision record without an owner; name the absorbing page and report each criterion as held or remaining (carries 3.8.0 load-path active-state check, 3.7.0 load-root mapping, and 3.6.0 fallback). |
| Date | 2026-11-07 |
| Objective | Add the clause-ledger, authority-conflict, and paired-commit-invariant branches. |
| Version | 3.11.0, minor bump: merged commits can discharge one clause of an issue while the primary ask stays open, so a consumed clause ledger is not a discharge; an issue proposal can contradict a live decision record, and the record wins; two merged commits in one area can be two correct branches of one classification (target). |
| Verification | unverified: one planning session. The clause triage and the paired-commit read were applied; the authority split agreed with the live decision record. No implementation outcome is recorded here. |
| Date | 2026-11-07 |
| Objective | Extend premise verification to the gate that consumes row states: a cut, close, or merge rule keyed on a status table or dependency list goes stale as each row lands. |
| Version | 3.12.0, minor bump: gate rows are population members; sweep every row's claimed state at plan time, and repeat the sweep immediately before each outcome transition. A row resolved after the issue was filed takes the already-complete record path (no new implementation), and the row whose state the issue body misreports is the one that re-plans. (carries 3.8.0) |
| Verification | verified-live: a multi-row blocking tracker was planned with no row assumed; three rows had moved since the issue was written (one fix merged, one fix red and re-reviewed at a moved head, one plan anchored deleted files), and the gate stayed closed on those rows. |
| Date | 2026-11-07 |
| Objective | Add the cited-path check: verify each document, store, or record that the issue itself names, because a stale citation makes the premise stale at both ends. |
| Version | 3.14.0, minor bump: the premise checks start from the issue text, so grep the issue's own cited paths first; a cited path absent from the tree takes the temporal branch, and the deliverable must re-anchor to the current owner instead of re-creating the removed path (carries 3.8.0). |
| Verification | unverified: one read-only issue-disposition session found that both cited paths were absent — a named operations page that does not exist and a decision-record store removed by a merged closeout — and re-pointed the documentation deliverable accordingly; no implementation or CI run was observed. |
| Date | 2026-11-07 |
| Objective | Add the vehicle branch to per-ask triage: after you dispose each ask, select the PR that finishes the residual asks instead of opening a competing one. |
| Version | 3.16.0, minor bump: per-ask triage stopped at the discharge map. Add the `bound_vehicle` parameter, its two commands, the stale-base red check, and three worked examples; an open issue can also be open because a merged change used a reference that does not close it (carries 3.8.0). |
| Verification | unverified: one planning session applied the rule end to end (per-ask discharge map, vehicle selection on a stale-based PR, residual asks named). No merged outcome exists yet. |
| Date | 2026-11-07 |
| Objective | Add the relocated-not-void branch: a retired documentation target whose content has no surviving owner page is residual scope, not a void premise. |
| Version | 3.17.0, minor bump: the void branches close a retired doc target or re-create it, while the reported gap can still be live as content absent from every surviving page; name the owning page from the replacement registry and plan there. |
| Verification | verified-live for the source case; the annotation is a duplicate-intent match, not an independent confirmation. |

## When to Use

- An issue or plan names a script, file, branch, PR, route, workflow, ruleset, dashboard, helper, API response, or config as if it already exists.
- A follow-up issue assumes prior work merged, was tested, or is available on `main`.
- A review or issue claims that a fix is mechanical, blocked, already complete, or safe to close.
- A gate, guard, rule, CI job, or enforcement path is being added and the plan assumes the integration point already exists.
- A plan samples only named entities but the requirement applies to a whole population.
- A test assertion depends on an implementation return shape that has not been read from source.
- A live external state, such as GitHub rulesets or CI status, may differ from repository files.
- The next step would be a no-op, defer, close, or human-ratified judgment instead of a runnable proof.
- A premise token has zero matches in the current tree and the issue predates a recently merged migration, rename, or removal PR that could have deleted the premise surface wholesale.
- The issue cites a document, store, decision record, or operations page as the place to update, and you have not yet confirmed that the path exists.
- An issue contains more than one ask (a fix plus a test, a doc edit plus a guard) and any one of them may already be complete while another is still live.
- An implement-ready label or a reviewer-GO'd plan authorizes implementation, but merges continued after the plan was written (plan dwell in a fast-moving repository).
- You dispatch an implementation whose durable scope source is a plan comment written against an older tree, and the dispatch context cannot afford to re-discover premise decay after setup.
- A reproduction of a reported failure succeeded locally and a fix is being designed; a checkout that lags the default branch makes the reproduction prove only that the defect existed, a stale-reproduction premise.
- The failing service runs a deployed artifact, so one incident carries two code versions; the fix can already exist on the default branch while the deployment lags.
- A plan promises a one-pass report of several metadata states, and the only reader named validates and raises on the first bad state (wrong owner, group, type, or mode, or an absent path).
- An issue carries a plan-approved label but has no plan comment. The label is not the plan.
- A decision record, owner decision, or decision-table row for the issue postdates the plan review GO, and the dispatch still carries the implement-ready label.
- A plan or hand-off claims that a fix is already in place in an installed, vendored, or provisioned tree (a skill root, a deployed helper, a plugin directory), and the claim rests on an earlier manual apply rather than a merge.
- Planning an issue whose asks may already be delivered by a merged change, while the issue is still open because that change used a non-closing reference; first find whether an open or merged PR bound to the same issue already carries part of the repair.
- The GO'd plan text contains an explicit fallback for its own overtaking event (a named retirement, migration, or deletion that lands before implementation), and that trigger may already be satisfied at dispatch.
- A previous hand-off applied a change to an installed or deployed load path outside version control, and a sync from the owning repository can replace that copy. Declared success for the fixed helper is then an active-state premise.
- A supersession pull request in the consuming repository carries the patch for an out-of-repository artifact. Its own closure or supersession does not remove the obligation to land the change at the owning repository.
- An issue that was replanned or deferred cites later issues, and merged commits in the tree name those issues. A merged commit can discharge one clause of the primary ask while the primary ask stays open. The primary ask then stays live, and only the discharged clause leaves the scope.
- An issue's own proposal value choices disagree with a live authority record (a design or decision record). The proposal is not authority.
- The unit under test is a classification-and-outcome pair. Two merged commits in the same area then behave like two branches of one decision: one relaxes the enforcement and one keeps it. Find the rule that makes both commits correct, and plan the conversion. Do not pick one side.
- A cut, close, merge, or release gate uses a status table or dependency list, and each row names a different issue, PR, or plan; the rows are the gate's population.
- You re-read a gate tracker whose rows were written at filing time, and work merged since then can change a row from open to merged, merged to red, or plan-approved to plan-anchored-on-deleted-files.
- A request asks for a verdict on whether a plan file is usable, or an actor is about to dispatch an implementation from a plan file it did not author.
- The issue's target file was retired, but the page structure that replaced it has an owning component page, and the reported defect still exists as missing content. This is a relocation gap, not a void premise.

## Verified Workflow

> This is a planning discipline, not proof that every listed command is valid for every repository. Select the authority that applies to the premise and record the exact check result before acting.

### Quick Reference

```bash
# Prior PR/work claimed to have landed.
gh pr view 173 --json state,mergedAt,headRefName
git merge-base --is-ancestor <commit-or-branch> origin/main

# Artifact claimed to exist on the branch where new work will run.
git ls-files <path-or-pattern>
git show origin/main:<path>
rg '<symbol-or-route>' <candidate-paths>

# CI/ruleset claimed to gate, not merely run.
gh api repos/<org>/<repo>/rulesets --jq '.[] | {name, enforcement, conditions, rules}'

# Population claimed complete.
gh repo list "$ORG" --limit 200 --json name --jq '.[].name'
git ls-files | rg '<population-pattern>'

# Reproduction freshness: re-run at the fetched default-branch head, not the
# checkout as-found. A defect that no longer reproduces there is already fixed.
git fetch origin
git worktree add <probe-path> origin/<default-branch>

# Deployed-artifact binding: identify the version the live service runs
# (image tag, release manifest, or installed tree) and test whether the
# failure mechanism still exists at that version and at the default branch.
git log -S '<failure-predicate>' --oneline origin/<default-branch>

# Gate rows: read each row's own state, not the tracker's summary.
for n in <row-issue-numbers>; do
  echo "row $n: $(gh issue view "$n" --json state -q .state)"
  gh pr list --state merged --limit 3 --search "$n in:body" \
    --json number,mergedAt -q '.[] | "  merged PR #\(.number) at \(.mergedAt)"'
done
```

1. Name the premise before choosing a fix. Common premise classes are: artifact exists, prior PR merged, branch contains a helper, live work remains, all entities were checked, CI job gates, implementation returns a shape, or an enforcement integration point exists.
2. Pick the authoritative source. Use `origin/main` or `HEAD` for branch-local artifacts, GitHub PR metadata for merge state, live APIs for rulesets and repository population, workflow/ruleset definitions for gates, and source code for return shapes.
3. Convert the claim into a deterministic command. The command should be repeatable by the next agent and should return a result that changes the plan if false.
4. Choose the next action from evidence: implement remaining work, record an unresolved dependency, or report that the request is already satisfied. If the premise is uncertain, continue investigation and independent work; do not call it complete without supporting evidence.
5. When a premise token has zero matches in the current tree, do not stop at "premise false" or "misrouted issue". Date the disappearance: `git log --full-history -- <deleted-or-renamed-path>` finds the removing commit, `git show <removing-sha>^:<path>` proves whether the premise held immediately before removal, and `gh issue view <n> --json createdAt` places the issue relative to that removal. Valid-at-filing plus later removal is overtaken-by-events — a different disposition from never-valid or misrouted, and it forbids "correcting" the premise surface back into existence.
6. Triage per-ask, not per-issue. Enumerate every deliverable in the issue body and give each its own premise check and disposition. A half-zombie issue can have its primary ask verified already-complete while a secondary ask (a test, a guard, documentation) is still live; implement only the residual asks and record why the completed ask needs no re-implementation. An issue that carries its own Proposed fix list is a multi-ask issue too: route each named remedy to its own disposition, because one merged change can discharge one remedy while the others stay live. When a remedy depends on a named file or state, locate that name before planning the remedy. A remedy that names files absent from the repository so far that no commit ever added them is an operator-host or external surface: plan the in-repository declaration and record the external correction, do not recreate the files. When a remedy claims that a live artifact lacks a capability, check the artifact producer that would write the capability. A producer that writes it only for newly started instances makes the remedy a cold-path declaration, not a retrofit. An issue that was deferred or replanned can cite later issues, and a defect class often has several clauses (one command, one comparison, one message, one wait). A merged commit that names this issue or a cited issue can discharge one clause while the primary ask stays open: date each clause by its cited issue and its commit. Do not record a consumed clause ledger as a discharge of the primary ask.
6a. Treat the rows of a gate rule as a population, not as prose. When the deliverable is a cut, close, merge, or release gate keyed on a status table or dependency list, each row is a separate premise: the row's claimed state (issue open or closed, PR merged or red, plan approved or stale). Read every row from the issue and PR API at plan time. A row with no live work left (fixed by a PR that merged after the issue was filed) takes the already-complete record path: verify the shipped behavior and record the evidence; do not re-implement. A row whose state the issue body misreports is the row that needs the work. Repeat the sweep immediately before each outcome transition, because the gate is the surface that uses the row states and a merge can land between the plan and the transition.
   When the plan converts a set of existing checks, name the production load path of each check before you select one implementation point. Map each model, validator, or call site to the loader, entry point, or command that reaches it in production. A check whose only caller is a test has no production behavior to convert: record that disposition and leave its current code path unchanged. When the checks reach production through more than one load root, plan one hook for each root; one shared hook silently drops every check on the other roots, which is an accidental removal, not a conversion. For every converted check, the behavior test must call its real load path, not a private helper.

   Also read the issue's proposal value choices against the live authority record. When a proposal says to remove or widen a guard and a decision record says that guard class stays enforced, the proposal is stale. The recorded decision sets the split, and the plan keeps the guard and relaxes only the classes the record demotes.
7. If an artifact exists only on an unmerged branch, consider an authorized stacked branch or a self-contained change that avoids duplication. If dependent edits cannot proceed, record the dependency and continue independent work until the needed code is available.
8. For enforcement and CI, prove consumption. A job that runs is not a gate unless the branch protection or ruleset requires its context. A guard cannot be added at an integration point that does not exist.
9. For populations, enumerate the full set from the authority before sampling. Named issue examples are clues, not coverage.
10. For implementation behavior, read the actual route/function/helper before asserting response shape, return keys, side effects, or test expectations.
10a. Check the issue's own citations before the plan's anchors. An issue names the files it wants changed (an operations page, a decision-record path, a store directory). Those citations are part of the premise, not coordinates to trust. List every path and symbol the issue cites and check each one in one pass:
10b. Bind an installed or provisioned artifact the same way. A manual apply into an installed tree is a premise with the lifetime of that install: a later install, upgrade, or re-provision replaces the tree and removes the change without a record. Treat a recorded apply as unverified currency. Re-check the installed artifact for the change before any plan relies on it, and name the source that can restore the change. A change that exists only in the installed tree has no owner and no delivery: land it at the source, then re-provision from the source and re-verify the installed artifact. A red required check on the source change is not a reason to keep an in-tree patch; it is work in the source lane.
    ```bash
    # The issue's cited paths, checked in one pass.
    for p in <cited-path-1> <cited-path-2>; do git cat-file -e "HEAD:$p" 2>/dev/null && echo "present $p" || echo "absent $p"; done
    # Date any absent path against the issue.
    git log --full-history --oneline -1 -- <absent-path>
    git log --diff-filter=D --oneline -- <absent-directory>/ | head -1
    gh issue view <number> --json createdAt
    ```
    Decide from the result. When a cited path is absent and a merged change removed it after the issue was filed, the premise is stale at both ends: apply the temporal check of step 5, name the current owner of the content, and re-anchor the deliverable to it. Do not plan a write to a path that no policy keeps, and do not re-create a removed store to satisfy the citation. When the cited path never existed, say so and record who owns the content now. When a cited path is absent with no removal, treat the citation as unverified and ask for the intended target. Report the substitution in the disposition so the reviewer can check it.
11. Bind self-produced evidence to the environment that produced it. A reproduction, benchmark, or trace is a premise with the staleness of the tree it ran on. Re-run it at the fetched default-branch head before designing a fix: a defect that no longer reproduces there is already fixed, not implementable scope.
12. For a failure in a live deployed service, check two versions before assigning code work: the deployed artifact and the default branch. Fixed at the default branch but failing in the deployed artifact is deployment lag — the remediation is operational, and writing the same code again is a redundant fix. Only a defect that reproduces at the default branch earns a code change.
13. Bind gate rows at the outcome boundary, not only at plan time. A blocking rule that reads row states (row merged, row has a merge, cut allowed) is a reader of live state. Before you arm a merge, a cut, or a close, re-run the row sweep from step 7 and record each row's state with its evidence. A row that regressed after the plan (a red check on a moved head, a review that turned NO-GO) blocks the transition exactly as an unmerged row does. Name the blocking row on the owning record instead of granting the transition an exception.
14. Preserve the evidence in the plan: command, observed output summary, and how it changed scope or disposition.

15. Verify that each helper the plan names can return the value the plan reports, in every state the plan must report. A validating reader enforces one expected identity and raises on a mismatch, on an absent path, and on a wrong type. A collect-all report must list those same states as rows, so one validating reader cannot be its evidence source. Read the helper body, not its signature or its parameters. A parameter that looks optional, such as an `expected_mode=None`, often leaves the owner, group, and type checks in place. Plan a non-validating read that opens each item relative to a retained descriptor and reads the raw metadata, or name a helper that does the same. Record the premise row for each state the plan calls clean.
16. Read the policy facts the plan cites. A policy table can leave a field unset for some entries and set it for others, and an unset field has no rule to cite. Name the one authority for each expected value and say which entries fall back to code that is not the policy table.
17. Order the report against the work it protects. If the report must arrive before an expensive stage, the caller needs a cheap preview at that point. A report that runs only inside the final publisher arrives after that stage. State this limit and add the preview, or state why the later report is acceptable.
18. Judge a plan file for use as well as for premise truth. A plan can pass every cited anchor check and still be unusable. Read the edit instructions against each other: an instruction that deletes a cited line range invalidates a later instruction that keeps a sub-range of that range, unless the plan states the replacement text. A structured defect, such as a duplicated header with two revision blocks, shows that the file came from a concatenation and that a later reader may edit the wrong section. An unresolved item that sends a required action to a different record, and an item that names no exact change, leave the next actor with a guess. Report the usable or not usable verdict, and name each defect that controls it.

### Hand-off rebinding: a reviewed plan is not a tree-state guarantee

A plan records the tree at authoring time. A review GO records agreement at review time. Neither re-runs itself when later merges land. During the dwell between plan approval and implementation dispatch in a fast-moving repository, four things can happen: later merges deliver part or all of the plan's scope; later merges delete the plan's anchors (symbols, modules, documents); a deliberate redesign supersedes the plan's mechanism; an authority record published after the review GO rejects the plan's core approach. An implement-ready label does not re-check any of this.

Run the same premise checks on the plan's own anchors at each hand-off (planning to dispatch, dispatch to implementation), before the implementation context spends its budget:

1. Extract every symbol, path, constant, and test name the plan cites, and sweep them with `git grep` and `git show origin/main:<path>`.
2. For each missing anchor, date the removal (`git log --full-history`/`git log -S`) and name the merged change that removed it.
3. Sweep authority records beside the anchors: decision records, accepted ADRs, owner decisions, and decision-table rows that name the issue or its subject. For each record, read its decision and its timestamp against the plan review's timestamp.
4. Branch exactly one way:
   - *Label without a plan comment*: treat the issue as unplanned. Plan it and review it before you implement.
   - *Anchors hold and no record conflicts*: dispatch per plan.
   - *Partially discharged*: dispatch the residual asks only, with anchors re-derived on the current tree; record the per-ask discharge map.
   - *Void or fully discharged, plan prescribes a fallback*: before re-planning, read the GO'd plan text for a condition-triggered fallback for its own overtaking event (for example: "if the retirement lands first, record the verified findings on the owning record and close the issue as subsumed"). When the plan contains that prescription and the trigger is objectively verified — the removing change is merged, the owning record is closed, and the anchors are absent from the tree — execute the prescribed fallback and close with the trigger evidence. The fallback was reviewed as part of the plan, so no fresh review round is required. Never re-create the removed machinery to satisfy the frozen scope.
   - *Void or fully discharged, no prescribed fallback*: re-plan — update the retained plan revision, run it through the review exchange again, and close only on a fresh GO bound to current-tree evidence. Never implement the frozen scope; never re-create machinery a merged redesign deliberately removed.
   - *Owner fix in flight, consumer code discharged*: when the owning-location decision supersedes a consumer-side patch, do not reopen the consumer patch and do not apply a local patch as the long-term route. Track the owning change and land it first.
   - *Relocated, not void*: the retired target was documentation, and the reported gap is content that no surviving page carries. Do not close the issue as subsumed and do not restore the retired page. Name the owning component page that the replacement structure designates, prove the content is absent from that page, and plan the insertion there against the current page contracts. When an open delivery against the retired page exists, a replacement pull request supersedes it; a merge or a rebase re-creates the retired page.
   - *A record rejects the plan's core approach*: realign — derive the realigned plan from the recorded decision, not from the plan text, and implement only the residual work the record leaves. The residual can be zero: when the delivered behavior already matches the recorded decision, verify the pinned behaviors with fresh runs, publish the realign record with the evidence, and close as verified-already-complete. Never implement the rejected approach because a label says GO; the label is loop state, the record is architecture authority.
5. Prove that the change is active for the consumer, not only present in its source. A local change at a load path outside version control can be replaced by the next sync from the owning repository. Name the sync mechanism, the exact files that must match byte for byte, and a digest check at the required revision; run that check before you report the helper fixed. The installed or deployed copy is a second authority, and the source tree alone does not prove its state.
6. Use an independent plan review for scope as well as for anchors. It can replace a heavy mechanism, such as a claim-file protocol, with a small handler when the current tree already gives the guarantee.
7. A direct close or re-dispatch on the stale plan is not a shortcut: it loses the required review round and attaches the verdict to evidence the tree no longer supports. The exception is the plan's own prescribed fallback: its disposition and trigger were reviewed as part of the GO'd plan, so executing it attaches the verdict to the reviewed prescription plus fresh trigger evidence, not to a new judgment.

### Worked Examples

| Issue or Context | Premise Type | Verification | Correct Disposition |
|---|---|---|---|
| ProjectHermes #556 and #674 | Branch-scoped artifact and helper existence | Scanned all branches, checked merge ancestry, and grepped the working tree for the named helper. | The work was valid but not present on `main`; make the PR self-contained by regenerating or adding the helper rather than waiting on a sibling branch. |
| ProjectProteus #182 and #185 | Follow-up issue assumes prerequisite work exists on `main` | Checked `gh pr view` merge state and `git show origin/<branch>:<file>` versus current `main`. | Add an explicit merge gate or expand scope; do not reference recipes or claims absent from the branch where the hook runs. |
| ProjectProteus #184 | CI job runs but may not gate | Compared workflow presence with ruleset/required-context state. | Treat ungated CI as advisory until branch protection or rulesets require it. |
| ProjectHephaestus #1207 | Enforcement guard assumes an integration point exists | Read the installed architecture and found no hook path for the proposed guard. | Ship the library/CLI verifier and clear earlier unverified guard assumptions instead of pretending the integration point exists. |
| ProjectAgamemnon #316 | Test plan assumes route/API response shape | Read the actual route and implementation return keys before writing assertions. | Assert the real shape, not the issue text's inferred shape. |
| Ecosystem branch migration #24 | Named subset treated as full population | Enumerated the live repository population and current branch state. | Expand to the full population or close as already complete when live state proves no remaining work. |
| Doc-config enforcement gate and Grafana issue #179 | Gate matcher assumes exact shipped layout | Tested the matcher against the post-fix tree using tracked files. | Validate the shipped layout with `git ls-files`; do not rely on pre-fix paths or recursive filesystem assumptions. |
| Ruleset/live-state issue #177 | Static repository file treated as source of truth | Read live GitHub rulesets and compared them to proposed file edits. | Preserve live applied enforcement; a static edit that weakens live state is a regression. |
| Multi-part bug issue with its own Proposed fix list | Each named remedy treated as one requirement | Checked each remedy: one named publish-only mode already merged; two remedies named host-side scripts that no commit ever added; one remedy claimed a live job lacked a restart marker while the template already wrote it for new jobs. | Discharged the merged remedy, planned the cold-path declaration for the running instance, and planned documentation plus a pre-publish check as the residual; do not recreate host-side scripts. |
| ProjectHephaestus #2166 | Premise token absent from current tree; multi-ask issue | `grep -ci pixi CONTRIBUTING.md` returned 0 today, but `git log --full-history -- pixi.toml` showed a uv-migration PR (#2236) deleted the file two days after the issue was filed, and `git show <migration-sha>^:CONTRIBUTING.md` contained the exact broken command the issue reported. | Primary ask (fix the command) verified already-complete via the migration; residual ask (documentation validation test) still live — implement only the test and do not reintroduce a "corrected" command for a removed toolchain. |

| Three implement-ready issues in one fast-moving multi-lane repository | Reviewed-plan decay during dwell; discharge-by-merge | Anchor sweep at dispatch on each plan: one plan's residue identifiers already absent (`git grep` zero, removal dated to a merged cleanup change) while one secondary ask remained; one plan's subject module deliberately retired by a later merged change with its remaining ask already shipped; one plan's mechanism superseded by a merged redesign series and its gating event already recorded. | Residual-only dispatch for the first (secondary ask implemented, evidence node added); re-plan, review GO, then close for the second and third; zero frozen-scope implementations, zero re-created machinery, zero wasted dispatches on the full plan scope. |
| Consumer issue for a helper outside the consumer repository | Hand-off rebind found four target pull requests already merged, the consumer patch closed, and the owner fix open; the earlier local install was reported active | Re-confirm the installed copy against the owning revision (the local copy no longer held the change); plan a byte-for-byte digest gate before any fixed-helper claim |
| Docs-store cleanup issue in a fast-moving repository | Reviewed-plan decay during dwell; overtaking retirement with a prescribed fallback | The anchor sweep at dispatch found every plan anchor absent (the store directory had zero tracked files and the store guard test no longer named it); the removal dated to a merged closeout change, and the owning epic record was closed. The GO'd plan's own fallback prescribed: record the verified findings on the owning record and close the issue as subsumed. | Executed the prescribed fallback with zero source edits: findings re-verified at the plan's own commit, recorded on the closed owning record, and the issue closed as subsumed — no re-plan round spent on a zero-work close. |
| Feature issue whose own citations were stale | Cited-path check at disposition time | The issue named an operations page and a decision-record path. The page did not exist, and a merged closeout had removed the whole decision-record store while moving its policy text into code and other pages. | Kept the deliverable but re-anchored it to the current owner of the content, recorded the substitution and the uncertain forge-side asks in the reason, and did not plan a write to the removed paths. |

| Documentation and behavior-change issue with one already-shipped warn path, one live refusal site, and a removed store record | Mixed premise: partially discharged behavior plus doc anchors that no longer exist | Enumerated every criterion in the issue body. One warn path already shipped under the existing drift mechanism. One named refusal site still refused. An opt-in flag still gated the behavior. The named documentation page was retired and survives only as a ledger row. The named decision record had no file and survives only as prose references from component pages. The issue-closing forge action was not provable from the tree. | Returned a requirements disposition with each criterion marked held or remaining, replaced the doc targets with the owning pages, reused the existing warning mechanism instead of adding a framework, and stated each stale claim as uncertain rather than restating it. |
| Open bug issue with a six-ask body; a merged repair commit and an open fix PR bound to the same issue | Per-ask discharge by merge, plus vehicle selection | Owned the issue or read the branch that closes it, and it is bound to the issue. Read each ask against the default branch: a merged CI-repair commit had already updated four of the five stale tests, removed the dead selector write, and threaded an explicit selector into the rendered calls; one documentation line and one error-wrapper site were still open. The open PR's diff carried the code fix but no test pinned it, and no wrapper. | Plan against the open PR: rebase it onto the current default branch, add the missing test and the wrapper, and close from one vehicle; do not open a competing PR and do not send the residual to a fresh branch unless the PR branch is not writable. |
| Branch head red with many failing shards plus lint and typecheck | Stale-base attribution of a vehicle's own checks | The vehicle's merge base predated a merged CI-repair change, and the failing modules were the ones that repair had touched. | Classify the reds as stale-base candidates (see `pr-ci-failure-triage-preexisting-vs-introduced`), rebase, and re-bind checks to the new head; repair only what survives.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---|---|---|---|
| Current-branch-only artifact check | Concluded a script or helper never existed after grepping only the working tree. | The artifact lived on an unmerged sibling branch. | Scan `origin/main` and relevant remote branches before deciding an issue premise is false. |
| Correct but blocked plan | Acknowledged a valid dependency but left the work waiting on another PR. | The plan was not actionable today. | Reproduce or vendor the prerequisite into the current PR when possible; otherwise encode a hard dependency. |
| NOGO assumptions left unresolved | Listed unverified assumptions after review identified them as gating. | The next agent still had to guess. | Convert each assumption into a check, disposition, or explicit blocker. |
| Named subset scan | Checked only repositories or files named in the issue. | An unnamed population member changed the result, or the work was already complete. | Enumerate the full population from the authority before planning coverage. |
| One post-load hook for checks with several load roots | Planned one validation pass behind one loader for checks with several load roots. | Most checks never reached that loader and were effectively deleted, with no error. | Map each check to its load root; state the disposition of checks with no production load path. |
| Missing integration point ignored | Planned a guard at an architecture hook that was absent. | There was nowhere reliable to attach enforcement. | First verify the integration point exists; otherwise change scope to create or replace it. |
| Shallow contract checks | Treated a job that runs as a gate, inferred a response shape from the issue text, edited a static config without reading live rulesets, and designed a gate against an assumed layout. | The job was not required, the shape differed, the static edit would have weakened live enforcement, and the matcher missed the tracked tree. | Verify required contexts, read the implementation, compare with live state, and test a gate against `git ls-files`. |
| Zero-match grep treated as invalid or misrouted issue | Concluded from a zero-hit grep that the issue premise was false or belonged to another repository. | The premise was true when the issue was filed; an intervening merged migration PR had removed the surface wholesale. | Absence in the current tree has three explanations — never valid, misrouted, or overtaken by events; date the removal against the issue's creation date before choosing. |
| Dispose a multi-ask issue by its headline bug | Verified the primary symptom and planned one fix for the whole issue | Three other remedies in the issue's own Proposed fix list stayed undischarged: one was already merged, one depended on a capability the running instance could not get, and one depended on host-side scripts | Enumerate the issue's own Proposed fix list as separate premises and give each a disposition |
| Per-issue zombie disposition | Treated an issue overtaken by a later PR as fully complete and closable. | One of its asks (a validation test) was never delivered by the overtaking PR. | Dispose each ask separately; an overtaken issue can still carry live residual work. |
| Label-trust dispatch | Dispatched the full plan on an implement-ready label without re-sweeping the anchors. | Later merges had deleted every cited anchor; the implementation context spent its budget re-discovering that. | Rebind at the hand-off and select the branch from the sweep result. |
| Close on the stale plan | Closed a premise-voided issue by citing the existing plan and label. | Review rejected the close because the plan anchored a module deleted by a later merged change; the label described readiness on a tree that no longer existed. | A close-out of a discharged plan requires the revised plan published through the review exchange and a fresh GO bound to current-tree evidence. |
| Dispatch on the GO'd plan after a conflicting decision record | Started to implement the plan the label approved, although a recorded owner decision published after the review GO rejected the plan's core approach; every anchor still held, so the anchor sweep alone returned "dispatch per plan". | The anchor sweep checks the tree, not the authority: a decision record can reject a plan whose symbols all still exist, and the label follows the review, not the record. | Sweep decision records beside anchors at hand-off; when a record rejects the plan's core approach, realign to the record, implement only the residual work it leaves (possibly zero), and close with fresh run evidence — never implement the rejected approach because a label says GO. |
| Collect-all report built on a validating reader | Planned a multi-item metadata report on the module's existing open helpers, and said the report would read the mode and group without raising. | The helpers raise on a foreign group, on a wrong type, and on an absent path before the caller receives any value, so the report would surface the first mismatch as an exception, not as a row. | Before you plan a report, read the helper body. If it validates, plan a raw descriptor-relative read for the collecting pass. |
| Expected value taken from a policy table that leaves it unset | Attributed one mode tuple to named policy entries. | Those entries carry no mode field, so the tests would encode a value the policy never states. | Cite the one authority for each expected value and state which entries have no policy rule. |
| Reproduce-then-fix on the checkout as-found | Reproduced a production error against the local tree and filed an issue with a plan draft and review round before checking the default branch. | The checkout lagged the default branch, which already contained the fix, and the deployed artifact predated the branch; the issue closed as already-fixed after the review budget was spent. | Bind self-produced evidence to the environment version that produced it: re-run the reproduction at the fetched default-branch head and compare the deployed artifact's version before fix design; deployment lag makes the remediation operational, not code. |
| Gate-row states trusted from the tracker body | Planned a cut gate from the tracker's own table, which said one row had no PR, one row had an open PR, and one row was fixed on the default branch. | The first row's fix had merged after the tracker was filed, the second row's PR was red and NO-GO at a stale path, and a third row's approved plan cited two files that the default branch had deleted. The gate would have closed on stale row states. | Read each row from the issue and PR API at plan time, repeat the sweep before the cut, and take the already-complete record path for a row that merged after filing. |
| Save/restore rollback plan file judged for use | Asked whether a remediation plan file was usable. The plan cited correct anchors, but one edit deleted a stop-rule line range while a later edit kept a sub-range of it with no replacement text, the file carried two header and revision blocks, an unresolved item left the edit authority with another record, and one item only said to update a state line. | Correct premises gave a misleading readiness signal; the self-contradictory and unspecified edits would have forced the implementer to guess. | Report not usable and name the defects that control the verdict; premise truth alone does not make a plan executable. |
| Cited documentation path taken as the edit target | Scoped an issue's documentation update to the page the issue named, and treated a cited decision record as the rule authority, without checking either path. | The named page did not exist in the tree, and a merged closeout had removed the cited decision-record store. An implementation would have created an unowned document and a record the repository no longer keeps, while the real content lived in other pages and in code. | Grep every path the issue cites in one pass before you scope; date an absent path and re-anchor the deliverable to the current owner instead of re-creating the removed surface. |
| Competing PR opened beside a bound vehicle | Started a fresh branch for all six asks of an open issue although an open PR bound to that issue already carried four of them. | The duplicated work forced two reviews and a yield of one lane, and the reviewer had to compare two diffs of the same intent. | List the PRs bound to the issue and read their diffs first; finish the residual asks on the bound vehicle, and open a separate PR only when that vehicle is not writable. |

## Results & Parameters

Use the smallest command that proves or disproves the premise. Record the command and the observed fact in the plan or PR comment.

```bash
# Merge state and branch ancestry.
gh pr view <number> --json state,mergedAt,headRefName
git merge-base --is-ancestor <sha-or-ref> origin/main

# Vehicles bound to the issue, and what each already carries.
gh pr list --state all --search "<issue-number> in:body,title" \
  --json number,state,headRefName,body
git diff --stat origin/main...<vehicle-branch>
git log --oneline <merging-commit>..origin/main -- <ask-files>

# Artifact and source-of-truth checks.
git show origin/main:<path>
git ls-files <path-or-pattern>
rg '<symbol-or-route>' <candidate-paths>

# Rulesets and gate enforcement.
gh api repos/<org>/<repo>/rulesets --jq '.[] | {name, enforcement, rules, conditions}'
gh pr checks <number>

# Full population checks.
gh repo list "$ORG" --limit 200 --json name --jq '.[].name'
git ls-files | rg '<population-pattern>'

# Tracked-tree gate simulation.
git ls-files | <gate-command-or-filter>

# Premise surface deleted from the current tree: date the removal.
git log --full-history --oneline -1 -- <deleted-path>
git show <removing-sha>^:<path>
gh issue view <number> --json createdAt

# Reproduction and deployment version binding.
git fetch origin
git worktree add <probe-path> origin/<default-branch>
git log -S '<failure-predicate>' --oneline origin/<default-branch>
```

Parameters to capture:

- `premise`: the exact claim the plan relies on.
- `authority`: the source that can prove or disprove it.
- `command`: the deterministic check used.
- `observed_result`: concise output or fact, not speculation.
- `disposition`: self-contained implementation, explicit dependency, expanded scope, verified close, verified already-complete, or partially complete (residual asks only).
- `per_ask_dispositions`: for multi-ask issues, one disposition per deliverable, not one for the whole issue; include one entry per item of the issue's own Proposed fix list, naming the exact check and how it changed the scope.
- `authority_conflict`: for a proposal value choice that a decision record rejects, record the proposal clause, the record clause, and the plan's resulting split. Do not put the rejected proposal in the plan.
- `paired_commit_invariant`: for two merged commits in one area that appear to disagree, record each call site and the classification that makes both correct. A paired-commit conflict with no such classification is a blocker, not scope for one side.
- `handoff_rebind`: the anchor-sweep result at each hand-off — `anchors_hold`, `partially_discharged` (with the per-ask discharge map), or `void_or_discharged` — plus the removing merged change for each deleted anchor and the selected branch (per-plan, residual-only, prescribed-fallback, re-plan). For `prescribed_fallback`, record the quoted plan fallback clause, the objective trigger evidence (removing change merge state, owning record state, anchor absence), and the close disposition.
- `load_path_state`: for a change at a load path outside version control, the sync mechanism, the files that must match byte for byte, the owning revision used for the check, and the digest result.
- `environment_binding`: for self-produced evidence, the tree version that produced it (`HEAD` of the reproduction tree) and the fetched default-branch revision re-run result; for a deployed service, the deployed artifact version and the default-branch result — `real_defect`, `already_fixed_on_branch`, or `probe_or_environment_defect`.
- `gate_row_states`: for a gate rule keyed on a status table, one entry per row — the row's claimed state, the checked state of its issue and PRs, the sweep time, and the disposition (`already-complete`, `needs-work`, `re-plan`, `blocking`).
- `plan_file_verdict`: for a plan file judgement, `usable` or `not_usable`, plus the controlling defects (duplicated header or revision block, a deletion that voids a kept sub-range, an action assigned to another record, an unspecified change).
- `installed_artifact_binding`: the recorded apply or install event and its time, the installed artifact path and modification time, the source commit that must carry the change, and the re-verify command result — `present`, `absent_after_reprovision`, or `unverified`.
- `bound_vehicle`: for each ask, the PR bound to the issue and its state, cost base ancestry (`git merge-base --is-ancestor`), diff surface against the ask's files, and the answer to one question: does the vehicle already contain this ask? The cost of continuing on that vehicle is a rebase plus the residual asks; the cost of a competing PR is duplicate review plus a forced yield. Record the base ancestry once, because a vehicle cut before a repair landed shows that repair's failure set as stale-base reds.
- `examples`: issue-specific facts belong in the plan and in this skill's history, not in new duplicate memories unless the rule is genuinely different.
