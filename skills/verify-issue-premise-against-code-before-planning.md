---
name: verify-issue-premise-against-code-before-planning
license: BSD-3-Clause
description: "Check issue claims against current code and enumerate matching sites so a stale premise, an incidental search token, or an impossible stated mechanism does not misdirect the change."
category: documentation
date: 2026-06-19
version: "1.4.0"
user-invocable: false
verification: unverified
tags:
  - planning
  - issue-premise
  - verify-before-planning
  - stale-issue
  - follow-up-issue
  - ci-cd
  - github-actions
  - grep-the-premise
  - wrong-file
  - workflow-disambiguation
  - pixi
  - actions-cache
  - enumerate-all-sites
  - ratify-scope
  - under-scoping
  - self-fulfilling-narrowing
  - multi-site
  - derived-pin
  - identity-hash-pin
  - non-participation-claim
  - base-control-delta
  - failure-attribution
  - flaky-isolation
  - symptom-versus-mechanism
  - impossible-mechanism
  - invariant-check
  - algorithm-probe
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/verify-issue-premise-against-code-before-planning.history"
history-cleanup-date: "2026-09-20"
---

# Verify the Issue Premise Against the Code Before Planning

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-19 |
| **Objective** | An issue's description of "what the current code does" is a CLAIM to verify against the actual files, not ground truth to plan on. Grep the distinctive premise tokens to confirm WHICH file/job matches, and enumerate EVERY site before scoping — ratifying in-scope and excluded sites explicitly. (v1.3.0) When the premise pins a VALUE, also enumerate the binding surfaces its literal text cannot reach (derived hashes, field asserts, bare tuples) and close the enumeration with a RECORDED base-control test delta. (v1.4.0) When the premise names a MECHANISM for a symptom, test whether that mechanism can produce the symptom at all before planning a repair. |
| **Outcome** | Plan written for ProjectAgamemnon #248 ("Add pixi.lock restore-only cache fallback on miss"). **(v1.0.0)** The premise implied `python-client.yml`, but those jobs use the full `actions/cache@v4` (auto-saves) — grepping the premise tokens disambiguated `_required.yml`. **(v1.1.0)** The first plan revision fixed only `pixi-check` and got a NOGO: grepping an incidental token silently dropped the sibling job `lint`. Grepping the issue's OWN premise token enumerated both in-scope jobs plus one look-alike to ratify as out-of-scope. **(v1.3.0)** A private serving-config change (parallelism 16→8): the issue's "value does not participate in the deployment identity" claim was STALE; the literal grep missed 4 derived pins; a recorded base-control run proved 58 failures PRE-EXISTING and isolated the change-only pin sites. **(v1.4.0)** A sharding issue reported that a sharder "silently drops" tests when the count changes. Exercising the real sharder over randomized partitions assigned every node exactly once — the mechanism was impossible — and a quoted refusal named the wrong component. Both premise claims were corrected before planning. |
| **Verification** | unverified — PLANNING session only; no plan revision was implemented or run through CI, and the proposed cache restore/save split was not executed end-to-end |

This is a planning-DISCIPLINE learning, distinct from the cache-mechanics skill
`pixi-cache-true-unreliable`. The lesson is not "how cache syntax works" — it is "do not
trust the issue's narration of the current code; grep the premise's distinctive tokens and
plan against the file that actually matches."

**v1.1.0 extends the theme from disambiguation to exhaustive enumeration:** v1.0.0 answers
"WHICH single file does this premise point to?", v1.1.0 answers "ALL N sites it matches — fix
every in-scope one and ratify every excluded look-alike". The failure modes differ (wrong
file vs under-scoping), but both share one root: grep the issue's OWN premise token, not an
incidental token from your first-found site.

**v1.3.0 extends it from textual match surfaces to DERIVED-VALUE binding surfaces, and adds
an attribution discipline for red suites.** Where else is value `V`, or a value COMPUTED from
`V`, pinned, when no text search for `V` can find it? Bare tuples, field-equality assertions,
and content-derived identities (a sha256 digest contains no decimal `16`). And "a change
turned the suite red — which failures are mine?" is closed with a RECORDED base-control delta,
never with intuition. Failure modes again differ (invisible-to-grep pins vs misattributed
environment failures) under the same root: enumerate by evidence, not by the first textual
form searched.

**v1.4.0 extends the same theme from "where is this claim about?" and "what does it touch?"
to "can this claim even be true?".** v1.0.0 asked which file, v1.1.0 which sites, v1.3.0 which
derived values — all assuming the issue's causal story is sound and only its coordinates are
uncertain. v1.4.0 covers the case where the symptom is REAL and reproducible but the named
MECHANISM cannot produce it: an algorithm that assigns every input exactly once cannot drop an
item between partitions; a check in one component cannot emit another's error text. A plausible
cause plus a real symptom is the most dangerous combination, because the symptom reproduces and
appears to confirm the story, and the resulting repair targets code that is not at fault. The
discipline: read the algorithm, state its invariant, and EXERCISE it.

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until
> CI confirms.

## When to Use

- Planning any issue whose description ASSERTS the current code's structure or configuration
  ("the workflow uses `cache: false`", "the job re-downloads X", "we currently call Y").
- The issue is a FOLLOW-UP to a prior issue/PR (e.g. #248 was a follow-up from #62) — the
  earlier state it narrates may have since changed.
- CI / GitHub-Actions / workflow issues, where the SAME step pattern (a cache step, a setup
  step, an install step) appears in MULTIPLE workflow files and the issue names none of them
  exactly — or names the wrong one.
- You are about to start editing the first file whose name "sounds like" the issue's subject,
  without confirming the described tokens actually live there.
- The premise's distinctive tokens may have ALREADY been fixed — in which case the right plan
  is "state it's already addressed," not a no-op change.
- **(v1.1.0)** Planning any issue that fixes a RECURRING code pattern — a CI workflow step
  repeated across jobs, a lint rule, a config key — where the same pattern likely appears in
  more than ONE place. Especially after you have already written a SINGLE-site plan, and
  especially when a sibling or look-alike site exists in the same file/dir. Use the requested outcome and observed defect to select scope; explain excluded look-alikes.
- **(v1.3.0)** The issue pins a CONFIG VALUE at named sites ("change `ep` from 16 to 8 at
  these places"), or asserts NON-participation ("`V` is NOT part of identity or artifact
  `Y`"). Tests can pin values DERIVED from `V` (hashes, content-addressed IDs, rendered
  payloads) that a text search for `V` can never find, and non-participation claims go stale
  as derivations gain inputs over time — verify them by COMPUTING the derivation, not by
  trusting the prose.
- **(v1.3.0)** A config change turns suites red on an environment-hostile host (shared or
  network-mounted filesystem; tmp/home under the mount) and you must separate MISSED
  binding sites (change-only failures) from pre-existing environment failures before
  repairing any pin.

- **(v1.4.0)** The issue names a SPECIFIC MECHANISM for a symptom ("the sharder drops a test
  when the count changes", "the cache step re-downloads") rather than merely a file. Verify
  the mechanism can produce the symptom before planning a repair: a real symptom is not
  evidence that the stated cause is real.
- **(v1.4.0)** The issue quotes an error message, exception class, or exit code. Re-derive
  it; the text may come from a neighbouring component that validates the same condition.
- **(v1.4.0)** The claim is about an ALGORITHM's completeness or fairness ("every item is
  assigned exactly once", "no item is lost", "each shard gets a balanced share"). These are
  invariants you can test directly in seconds, without reproducing the reported run.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. It was produced in a PLANNING
> session only; no code was written or run, and CI never executed. The section is titled
> "Verified Workflow" only to satisfy the marketplace validator (which requires that exact
> heading). Treat every step below as a **Proposed Workflow / hypothesis** until CI and a human
> planner confirm it.

### Quick Reference

```bash
# 1. EXTRACT the distinctive string tokens from the issue's PREMISE (not its title).
#    For #248: "cache: false", "pixi install --locked", the exact cache key string.

# 2. GREP those tokens across the relevant dir — let the code, not the prose, name the file.
grep -rn 'cache: false' .github/workflows/
grep -rn 'pixi install --locked' .github/workflows/
#    The INTERSECTION is the disambiguator:
grep -rln 'pixi install --locked' .github/workflows/ \
  | xargs grep -l 'cache: false'
#    -> .github/workflows/_required.yml   (job: pixi-check)  == the REAL target
#    NOT python-client.yml, whose jobs use the full actions/cache@v4 (auto-saves).

# 3. If the match lands in a DIFFERENT file than the issue names, plan against the MATCH and
#    call out the discrepancy in the plan's Approach, citing the grep as evidence.

# 4. If the premise tokens DON'T match anywhere, the premise may be ALREADY-FIXED.
#    State that explicitly in the plan instead of implementing a no-op.

# 5. (v1.1.0) ENUMERATE ALL SITES, then RATIFY scope. Grep the issue's OWN premise token —
#    NOT an incidental token from the first site you found.
grep -rn 'cache: false' .github/workflows/_required.yml   # the issue's premise token
#    -> matches TWO jobs: `lint` (lines 72-89) AND `pixi-check` (lines 153-170). Both in-scope.
#    A first plan grepped `pixi install --locked` (incidental, never named by the issue) and
#    matched ONLY pixi-check -> silently dropped `lint` -> NOGO.

#    For each match, CLASSIFY:
#      in-scope    = matches the issue's EXACT defect (cache:false skips built-in save)
#      look-alike  = matches the token but has a DIFFERENT defect, e.g.
#                    security-dependency-scan: built-in setup-pixi caching is ON (no `cache:`
#                    key) -> a separate broken-cache:true problem, OUT of scope for #248.

#    In the PLAN, list EVERY in-scope site to fix AND EVERY excluded look-alike with reasons.
#    A silent omission reads as an oversight (NOGO); an explicit ratified deferral does not.

#    WATCH per-site DIVERGENCE before templating one fix across sites:
#      lint  uses cache key `pixi-lint-*` and path clients/python/.pixi
#      pixi-check uses cache key `pixi-*` and a different path
#    A uniform save would write under a key the restore never looks up -> silent cache miss.

# 6. (v1.3.0) The premise pins a VALUE: enumerate DERIVED binding surfaces too.
grep -rn 'field_name' src/ tests/                       # the field NAME and its readers
grep -rEn '\([0-9]+, *[0-9]+, *16|\.field == *16' tests/  # bare tuples, field asserts
#    A content-derived identity (sha256 of a payload containing 16) contains NO '16',
#    so text grep can NEVER enumerate it. Follow each reader to every derivation
#    (launcher flags, rendered payloads, identity hashes) and RECOMPUTE the derived value.
#    "V is not part of identity Y" is a CLAIM: compute identity Y before AND after the
#    change and compare — derivations gain inputs over time.

# 7. (v1.3.0) After the change, CLOSE the enumeration with a recorded base-control delta.
pytest <affected-modules> -rf 2>&1 | tee <scratch>/full-run.log     # FULL fidelity — never tail -N
grep '^FAILED' <scratch>/full-run.log | awk '{print $2}' > <scratch>/failed-nodes.txt
git stash && pytest $(cat <scratch>/failed-nodes.txt) -rf 2>&1 | tee <scratch>/base-control.log; git stash pop
diff <(grep '^FAILED' <scratch>/full-run.log | sort) <(grep '^FAILED' <scratch>/base-control.log | sort)
#    failing identically on base => PRE-EXISTING environment failure: ratify excluded, do NOT fix
#    failing ONLY with the change => a MISSED binding site: recompute the pin, update it, re-run

# 8. (v1.3.0) Suspect flake? Re-run the single node ALONE with the change applied.
pytest <node-id> -x 2>&1 | tee <scratch>/isolate.log
#    passes alone => load-dependent flake, not a regression: record it; expand scope only
#    if the isolation reproduces

# 9. (v1.4.0) MECHANISM CHECK — before planning a repair, can the stated cause produce the
#    symptom at all? Read the code that the issue blames, state its invariant, then EXERCISE it.
#    Example: the issue says a balanced partitioner "drops an item when the input grows".
python3 - <<'PY'
# Import the REAL module, not a copy. Drive it over the claimed failure mode.
for trial in range(500):
    items = [f"t{i}" for i in range(random.randint(shards, 500))]
    got = []
    for idx in range(shards):
        got.extend(partition(items, shard_index=idx, shard_count=shards))
    assert sorted(got) == sorted(items)   # assigned exactly once, none dropped
PY
#    invariant holds => the stated mechanism is impossible; the symptom has another cause.
#    Name the alternative and require the issue to supply that evidence.

# 10. (v1.4.0) Re-derive every quoted message. Grep the LITERAL text the issue quotes.
grep -rn '<quoted error text>' src/ | head
#    different component than the issue names => the repair target is wrong, not the symptom
```

### Detailed Steps

1. **Treat the issue body's "the current code does X" as a CLAIM, not ground truth.** An
   issue — especially a follow-up — narrates a snapshot of the code that may be stale or simply
   wrong about which file is involved. #248's premise asserted `setup-pixi` with `cache: false`
   skipping the built-in save and "fully re-downloads .pixi on cold cache." That description
   matched a job, but NOT the one the wording implied.

2. **Extract the distinctive tokens from the premise.** Pull the literal strings that pin down
   the scenario: here `cache: false`, `pixi install --locked`, and the exact cache key. These
   are the search surface — not the issue's title or your guess at the file.

3. **Grep those tokens across the relevant directory and take the INTERSECTION.** `grep -rn`
   each token over `.github/workflows/`. Individually each token appears in several files; the
   FILE THAT CONTAINS ALL OF THEM is the real target. For #248 the `cache: false` +
   `pixi install --locked` intersection resolved to exactly one place: `_required.yml` job
   `pixi-check`. The `python-client.yml` jobs matched `pixi install` but used the full
   `actions/cache@v4` action (which auto-saves) — i.e. they are NOT the issue's scenario.

4. **When the match is in a different file than the issue names, plan against the match and
   document the discrepancy.** Do not silently re-target; in the plan's Approach state "the
   issue's wording implies X, but grepping the premise tokens shows the described scenario lives
   in Y (job Z)," and include the grep as evidence so a reviewer can verify the redirection.

5. **If the premise tokens match NOWHERE, suspect an already-fixed premise.** A follow-up issue
   may describe a state a prior PR already changed. In that case the correct plan is to state
   "the described condition no longer exists (grep evidence)" rather than implementing a change
   that is a no-op or, worse, re-introduces removed behavior.

6. **Flag SHA-pin-by-analogy and other unverified externals as reviewer risks.** When the plan
   pins sub-actions (`actions/cache/restore`, `actions/cache/save`) to the parent action's SHA
   by analogy, say so explicitly and mark it unverified — do not present an assumed ref
   resolution as confirmed.

7. **(v1.1.0) Enumerate EVERY site matching the premise BEFORE scoping — grep the issue's OWN
   premise token, not an incidental one.** The defining token is the one the ISSUE states
   (`cache: false`). A distinctive token that merely happens to appear at your first-found site
   (`pixi install --locked`) is a SELF-FULFILLING filter: it matches only that site and silently
   excludes valid siblings. `grep -rn` the premise token across the relevant scope (whole file /
   dir / repo) to list ALL candidate sites. In #248 the premise token `cache: false` matched TWO
   jobs (`lint` and `pixi-check`) in the SAME file; the incidental-token grep matched only one,
   dropped `lint`, and earned a NOGO.

8. **Classify each candidate in-scope vs look-alike and explain the scope.**
   For each match, decide: does it have the issue's EXACT defect (in-scope), or does it merely
   share the token while having a DIFFERENT defect (look-alike, out of scope)? In #248
   `security-dependency-scan` matched the area but had the built-in setup-pixi cache ON (no
   `cache:` key) — a separate broken-`cache:true` problem, not #248's "`cache:false` skips save."
   In the plan, list every in-scope site to fix AND every excluded look-alike WITH the reason
   ("excluded because it has defect Y, not the issue's defect X"). Which sites to fix is a
   decision to resolve from the request and evidence; a silent omission of a matching site reads as an oversight
   (NOGO), an explicit ratified deferral does not.

9. **(v1.1.0) Check per-site DIVERGENCE before applying a templated fix.** Sites matching the
   same premise can still differ in their details. In #248 the two jobs used DIFFERENT cache keys
   (`pixi-lint-*` vs `pixi-*`) and different paths. A uniform fix copied from one job would write
   the save under a key the other job's restore never looks up — a silent save-under-wrong-key
   cache miss. Inspect each in-scope site's specifics and fit the fix to each, rather than
   templating one site's parameters across all.

10. **(v1.3.0) When the premise pins a value, enumerate the DERIVED binding surfaces, not
    only the value's literal forms.** Text grep over `V`'s flag and key forms is necessary
    but insufficient: pins of values computed FROM `V` contain no `V` text at all. A sha256
    identity over a payload that includes `V` holds no decimal digits of `V`; a topology
    tuple `(16, 1, 16, 2)` and a field assertion `.ep == 16` never match a grep for
    `--ep-size 16`. Grep the FIELD NAME and its readers, follow each reader to the
    derivations it feeds (launcher flags, rendered payloads, identity hashes), and list
    each pin by how its value is PRODUCED, not by the text it contains. Verify every
    NON-participation claim by computing the claimed-unrelated derivation before and after
    the change: in the source case "not part of the identity" was true when the issue was
    filed and false at implementation time.

11. **(v1.3.0) Close the enumeration with a RECORDED base-control delta before attributing
    ANY failure to the change.** Capture full-fidelity logs to files (`2>&1 | tee`,
    pytest `-rf` short summary) — never truncate the failing-node list with `| tail -N`;
    in the source case a `tail -3` summary destroyed the failure evidence and forced a
    45-minute re-run to rebuild it. Extract the exact failing node IDs, `git stash` the
    change, run ONLY those node IDs on the unmodified base commit, restore, and diff the
    two `FAILED` sets. Failures identical on base are pre-existing environment failures —
    RATIFY them as excluded. On a shared or network-mounted filesystem, pair this with the
    environment pinning in `testing-shared-host-env-pinning-and-baseline` (path and
    trust-ancestor assertions fail whenever tmp/home resolve under the mount, regardless
    of the change). Failures present ONLY with the change are the authoritative
    enumeration of missed binding sites: recompute each pin from the new value and update
    it. Never read a red suite as "the change is wrong" until the delta says so.

12. **(v1.3.0) Classify a suspect flake by isolation before expanding scope.** Re-run the
    single node alone with the change applied. A failure that passes alone is
    load-dependent, not a regression; record the isolation result and continue. Expand
    scope only when the isolation reproduces the failure.

13. **(v1.4.0) Test whether the stated MECHANISM can produce the symptom.** Steps 1–12 verify
    that the issue points at the right file and the right sites. This step verifies that the
    story connecting them is possible. Extract the causal clause from the issue body, not the
    title ("X drops an item when Y", "X refuses Z because W"), read the code that implements X,
    and write down its invariant: a partitioner that appends each item to exactly one bin
    guarantees completeness for ANY input. If the invariant holds universally, the mechanism
    cannot be the cause no matter how the symptom looked.

14. **(v1.4.0) Exercise the invariant, then name the alternatives — and re-derive every quoted
    message.** Import the real module and drive it over the claimed failure mode with many
    randomized inputs (in the source case, every item was assigned exactly once across 4–32
    partitions and up to 500 items, and the reported counts totalled the input length), which
    refutes the claim in seconds. A refutation alone is not enough — the symptom was observed.
    List the candidate causes in likelihood order (never collected, differing environment,
    differing base) and name the artifact that settles each. Finally grep the literal quoted
    error text: in the source case the quoted loader exempted the exact mode described, and a
    path-policy validator with a different check name emitted the text, so a repair in the
    quoted component would not have changed the behaviour.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Took the issue's "`cache: false` skips save" premise at face value | Assumed it referred to `python-client.yml` | Those jobs use the full `actions/cache@v4`, which auto-saves — not the issue's scenario | Grep the premise tokens; don't assume the first pixi workflow is the target |
| Assumed `actions/cache/restore` + `/save` share the parent action's pinned SHA | Pinned both sub-actions to `27d5ce7...# v5.0.5` without independently verifying the sub-action paths resolve at that commit | Unverified — sub-action path resolution at a pinned SHA was assumed, not checked against the GitHub Actions API/marketplace | Flag SHA-pin-by-analogy assumptions as a reviewer risk; verify the ref resolves before relying on it |
| **(v1.1.0)** Scoped the fix by grepping `pixi install --locked` | Assumed that token defined the issue's target job | It's incidental to ONE job; the issue's real premise token is `cache: false`, which also matched the `lint` job — silently dropped → NOGO | Grep the issue's OWN premise token, not a distinctive token from your first-found site |
| **(v1.1.0)** Fixed only the first matching job and didn't mention the others | Treated single-site as obviously-complete | Reviewer reads a dropped matching sibling as an oversight; ambiguous scope must be surfaced, not silently resolved | Enumerate all sites; ratify which are in/out of scope with reasons |
| **(v1.1.0)** Considered treating all pixi-cache jobs uniformly | Would have copied one job's cache key to all | `lint` and `pixi-check` use DIFFERENT keys (`pixi-lint-*` vs `pixi-*`) and paths; a uniform save would write under a key the restore never looks up | Check per-site divergence before applying a templated fix |
| **(v1.3.0)** Audited binding sites by grepping only the value's literal flag/key forms (`--ep-size 16`, `"ep": 16`) | Searched only the textual surface | Missed 4 pins on derived surfaces: a bare tuple `(16, 1, 16, 2)`, field asserts `.ep == 16`, and two sha256 identity digests that contain no `16` — the suite surfaced them as failures after the first implementation | Enumerate derived binding surfaces (field-name readers, tuples, asserts, recomputed identities), not only the value's literal text |
| **(v1.3.0)** Read a red suite as change-caused and summarized it with `tail -3` | Attributed all failures to the change; truncated the failure output | Truncation destroyed the failing-node list: a 45-minute re-run was needed to rebuild it; a recorded base-control run of the SAME node IDs on the unmodified base then proved 58 failures PRE-EXISTING host-environment failures | Log at full fidelity; run the recorded base-control delta BEFORE attributing any suite failure to the change |
| **(v1.4.0)** Read the reported symptom as confirmation of the reported cause | The issue gave a symptom plus a specific story ("the partitioner drops an item when the count grows") | Driving the real partitioner over randomized inputs assigned every item exactly once, so the mechanism was arithmetically impossible. Only then did the real candidates appear (collection difference, environment, base) | A real symptom does not confirm a stated cause; state the invariant and exercise it |
| **(v1.4.0)** Trusted the quoted exception class as the component to change | The issue quoted a loader exception for an unsafe-directory refusal | That loader exempts the exact mode described; a path-policy validator with a different check name emitted the text, so a repair in the quoted component would not have changed the behaviour | Grep the literal quoted text and confirm which component emits it |

## Results & Parameters

### The disambiguating grep (the core of this skill)

```bash
# Each token alone is ambiguous across workflow files; the INTERSECTION is the answer.
grep -rln 'pixi install --locked' .github/workflows/ | xargs grep -l 'cache: false'
# -> .github/workflows/_required.yml  (job: pixi-check)
#    python-client.yml is EXCLUDED: its jobs use the full actions/cache@v4 (auto-save),
#    which is NOT the "cache: false skips save" scenario the issue describes.
```

### Residual uncertainties to hand the reviewer (accumulated)

- **v1.0.0/v1.1.0:** sub-action SHAs resolve at the parent action's tag; `cache/save` ignores
  `restore-keys`; the compound `&&` `if:` is valid expression syntax; cited line numbers are a
  snapshot; the enumerated in-scope set is complete and each exclusion (auto-save jobs, the
  look-alike scan job) is deliberate.
- **v1.3.0:** the union of {literal grep + field readers + change-only test delta} is complete —
  the delta is the closure check, because a stale pin re-surfaces as a change-only failure;
  identity hashes verified only locally; sibling topologies left at the old value.
- **v1.4.0:** a refuted mechanism does NOT explain the symptom. Hand the reviewer the
  alternative causes and the artifact that settles each, and state plainly that the reported run
  was not re-executed.

### Related skills

- `pixi-cache-true-unreliable` — the cache-MECHANICS skill (when `cache: true` / built-in save is
  unreliable). THIS skill is the planning-discipline complement: verify which file/job the issue
  actually describes before applying any cache fix.
- `planning-follow-up-issue-line-number-drift` — verify cited line numbers against current HEAD;
  complementary "the follow-up issue's coordinates may have drifted" discipline.
- `planning-verify-issue-premise-before-implementing` — verify an issue-named ARTIFACT exists
  (repo-wide, across branches) before concluding it was never built. THIS skill instead
  disambiguates WHICH same-repo file/job a premise's tokens actually match.
- `testing-shared-host-env-pinning-and-baseline` — pin umask/TMPDIR/PATH on a shared host and
  baseline clean HEAD at the same subset before attributing failures. THIS skill adds the
  complementary closure: derived-pin enumeration and the exact-failing-node base-control delta.
- `pr-ci-failure-triage-preexisting-vs-introduced` — the PR-checks counterpart taxonomy
  (introduced vs pre-existing vs environmental). Use it when the red surface is CI checks,
  not a local suite.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectAgamemnon | Issue #248 ("Add pixi.lock restore-only cache fallback on miss") — a follow-up from #62 | unverified — planning session only. The premise implied `python-client.yml`, but grepping `cache: false` + `pixi install --locked` resolved the described scenario to `_required.yml` job `pixi-check`. Plan proposes splitting that job's single restore-only `actions/cache@v5` into a restore + a guarded save after `pixi install --locked`. Not implemented or CI-run. |
| `<private serving-config repository>` | Tracked issue flipping one parallelism value (16→8) in one tracked config profile | [notes.md](./verify-issue-premise-against-code-before-planning.notes.md) — validated locally: value-form grep missed 4 derived pins; a recorded base-control delta isolated 58 pre-existing environment failures from the change-only pin sites; suites green locally; upstream CI pending at write time |
| `<reviewed service repository>` | Two issue reviews of a reported "silently drops an item" claim and a "wrong component emits the refusal" claim | [notes.md](./verify-issue-premise-against-code-before-planning.notes.md) — verified-local. The partitioner invariant held over 500 randomized partitions (every item assigned exactly once); the quoted refusal text belonged to a different component than the issue named. Both corrections were posted before any plan. |
