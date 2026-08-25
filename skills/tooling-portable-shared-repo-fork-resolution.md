---
name: tooling-portable-shared-repo-fork-resolution
license: BSD-3-Clause
description: "Resolve a trusted shared repository through an explicit override, an eligible same-owner fork, or canonical-upstream fallback without treating every probe failure as absence. Use when: (1) repository selection depends on remote metadata, (2) a missing optional fork is expected but authentication and network failures must block, (3) shell code uses or proposes `|| true`, which is banned unless a human explicitly signs off and the exception is documented at its call site, (4) a checkout must be origin-verified, clean, synchronized, and revision-bound before use."
category: tooling
date: 2026-06-27
version: "2.0.0"
user-invocable: false
verification: verified-local
tags:
  - repository-resolution
  - trust
  - fork
  - tri-state-probe
  - fail-closed
  - shell
  - failure-swallowing
  - human-signoff
  - remote-metadata
  - revision-binding
---

# Trusted Shared-Repository Resolution

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-27; revised 2026-08-25 |
| **Objective** | Select a portable repository target while preserving the difference between verified presence, confirmed absence, and an indeterminate remote failure. |
| **Outcome** | Use one trust ladder, classify remote probes explicitly, fall back only after confirmed absence, and bind a verified clean checkout to an immutable revision. |
| **Verification** | verified-local — an optional candidate probe returned a confirmed not-found response; explicit classification allowed canonical fallback without hiding authentication, network, or other remote failures. |

## When to Use

- A tool needs a shared repository but must support an explicit trusted owner or a maintained fork.
- A same-owner repository name is not enough to establish fork ancestry or trust.
- A candidate repository may legitimately be absent, while authentication, rate-limit, network, and server failures must stop resolution.
- A shell command chains identity discovery and candidate probing, and the final optional probe makes the whole diagnostic command return nonzero.
- A shell command uses `|| true`, `|| :`, or another construct whose only purpose is to erase a failure status.
- Cached knowledge or automation must be synchronized and bound to an exact revision before use.
- A remote check needs network access that the default execution context may not provide.

## Verified Workflow

### Quick Reference

```text
1. Explicit override present -> validate syntax, identity, access, and target; never fall back.
2. No override -> establish current owner type and write-level permission.
3. Probe the same-owner candidate with a three-way result:
     FOUND  -> verify canonical ancestry and immutable tip before selecting it.
     ABSENT -> select canonical upstream.
     ERROR  -> stop; do not reinterpret the failure as absence.
4. Verify checkout origin and cleanliness, fetch, fast-forward, and bind the exact SHA.
5. Revalidate automatically selected fork identity immediately before use.
6. Ban failure swallowing by default; any exception requires human signoff and call-site documentation.
```

### 1. Define a closed result type for repository probes

A Boolean `exists` result is insufficient because `false` can mean either a confirmed not-found response or a failed request. Return one of three states:

```python
from dataclasses import dataclass
from enum import Enum, auto


class ProbeState(Enum):
    FOUND = auto()
    ABSENT = auto()
    ERROR = auto()


@dataclass(frozen=True)
class RepositoryProbe:
    state: ProbeState
    metadata: dict[str, object] | None = None
    diagnostic: str | None = None
```

Only a provider-confirmed not-found response maps to `ABSENT`. Authentication failure, permission ambiguity, timeout, DNS failure, rate limit, malformed output, and other status codes map to `ERROR` and block resolution.

### 2. Apply one explicit trust ladder

Use this order:

1. **Explicit owner override.** Validate the owner syntax and resolve the exact target. An invalid or inaccessible explicit override is an error; it is an explicit trust decision and must not silently fall back.
2. **Eligible same-owner fork.** Require the current repository owner to be an organization, require write-level access, and prove through remote metadata that the candidate is a fork of the canonical repository. Resolve its default branch and exact tip.
3. **Canonical upstream.** Select it only when no override exists and the optional same-owner candidate is confirmed absent or fails an eligibility check with complete trustworthy metadata.

Matching names never prove ancestry. A user-owned repository, insufficient viewer permission, unrelated same-named repository, or unverified metadata does not qualify as an automatic fork target.

### 3. Handle expected absence without hiding other failures

In shell, branch on the remote probe instead of leaving an expected failing command as the last command in a diagnostic sequence. Capture diagnostics long enough to distinguish confirmed absence from every other failure:

```bash
candidate_meta="$(mktemp)"
candidate_error="$(mktemp)"
trap 'rm -f "$candidate_meta" "$candidate_error"' EXIT

if <forge-cli> repository view "<candidate>" --json >"$candidate_meta" 2>"$candidate_error"; then
  printf '%s\n' 'candidate=found'
elif <confirmed-not-found-check> "$candidate_error"; then
  printf '%s\n' 'candidate=absent; target=canonical-upstream'
else
  sed -n '1,20p' "$candidate_error" >&2
  exit 1
fi
```

The exact not-found classifier must match the provider CLI's stable structured status or documented exit contract. Prefer structured status metadata over parsing human prose. If the CLI cannot distinguish not-found from other failures reliably, use a lower-level API that can; otherwise stop.

Run network-dependent probes in an execution context that has explicit network authorization. A sandbox denial or DNS failure is `ERROR`, not evidence that the candidate does not exist.

### 4. Keep composed diagnostics honest

When several read-only probes are printed together, the overall exit status should represent the trust decision, not whichever command happened to run last. Expected `ABSENT` should print the selected fallback and exit zero. `ERROR` should print a bounded diagnostic and exit nonzero.

### 5. Ban `|| true` and equivalent failure swallowing by default

Do not append `|| true`, `|| :`, or an unconditional zero-status wrapper to any command merely to keep a script moving. The construct discards the command's failure class and makes later success indistinguishable from partial execution.

Use an explicit conditional or capture and classify the exit status instead:

```bash
if output="$(<command>)"; then
  handle_success "$output"
else
  command_status=$?
  handle_expected_or_fatal_failure "$command_status"
fi
```

An exception is permitted only when a human explicitly signs off. The call site must document all of the following immediately above the suppression:

```bash
# failure-swallow-approved: human-reviewed
# tolerated failure: <one exact failure class>
# safe continuation: <why no required state or evidence is lost>
# observability: <where the failure remains visible>
<command> || true
```

The signoff is scoped to that call site and exact failure class. It is not permission to suppress future failures from the same command. If the tool cannot distinguish the approved failure from authentication, corruption, partial mutation, data loss, or other unsafe outcomes, the exception is invalid and the command must fail.

Repository checks should add a static guard that rejects `|| true`, `|| :`, and equivalent known suppression forms unless the adjacent approval block is present. Review must still validate the reason; a comment marker is evidence of the required review, not self-authorization.

### 6. Verify and revision-bind the checkout

Before consuming the selected repository:

1. Require the configured origin to identify the resolved repository.
2. Refuse local changes; never overwrite them or silently rewrite the remote.
3. Fetch and prune the selected origin.
4. Resolve the remote default branch and fast-forward the local default branch only.
5. Record the exact resulting commit SHA and trust basis.
6. For an automatically selected fork, re-query owner type, permission, ancestry, repository identity, default branch, and tip immediately before use.

Any mismatch between the reported trust decision, checkout origin, or checked-out revision is blocking.

### 7. Test every branch of the trust decision

Use behavior-based tests with concrete subprocess results:

```text
explicit valid override       -> exact target, no automatic fallback
explicit invalid override     -> error
eligible verified fork        -> fork selected at exact tip
candidate confirmed absent    -> canonical upstream selected
candidate unauthorized        -> error
candidate rate-limited        -> error
candidate timeout/DNS failure -> error
candidate wrong ancestry      -> canonical upstream or policy error, never selected
dirty checkout                -> error
origin mismatch               -> error
fork moves before use         -> revalidation error
unapproved `|| true`          -> static guard failure
approved suppression          -> exact adjacent rationale plus human-review evidence required
```

Assert both target selection and command exit status. A test that checks only printed text can miss a correct fallback followed by an unintended nonzero shell result.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Leave the optional probe as the last command | Ran identity checks followed by a candidate lookup expected to return not-found | The useful fallback decision was known, but the composed command still returned the lookup's nonzero status | Handle expected absence inside an explicit conditional and return the trust decision's status |
| Swallow every lookup failure | Added `2>/dev/null || true` around the candidate check | Authentication, rate limits, network failures, and malformed responses became indistinguishable from confirmed absence | Model `FOUND`, `ABSENT`, and `ERROR`; only confirmed absence authorizes fallback |
| Treat `|| true` as harmless shell glue | Used it for cleanup, optional discovery, or best-effort reporting without review | The same spelling also hid permission errors, partial mutations, and broken evidence collection; callers could not tell which operation completed | Ban failure swallowing by default; require human signoff and an adjacent exact-failure, safety, and observability explanation for every exception |
| Approve a command family globally | Documented that one tool is generally “best effort” | Different call sites have different state and evidence consequences, and future tool versions can add new failure modes | Scope approval to one call site and one distinguishable failure class |
| Trust a same-named repository | Selected `<current-owner>/<shared-name>` when it existed | Naming does not prove fork ancestry, maintenance, or authority | Verify owner type, viewer permission, canonical ancestry, branch, and immutable tip |
| Fall back after an invalid explicit override | Treated an inaccessible override like a missing optional candidate | The user explicitly chose a trust target; silently substituting another repository violates that decision | Explicit override failure is fatal |
| Probe without network authorization | Ran a required remote check in a context where network access was restricted | Connectivity failure could be mistaken for absence or produce misleading partial diagnostics | Use an authorized network-capable context and keep connectivity failures fatal |
| Use a generic truthy subprocess mock | Returned an unconstrained mock for structured metadata | Truthy placeholder fields sent the resolver down a branch no real response justified | Test concrete status, stdout, stderr, and metadata shapes for every result state |

## Results & Parameters

### Resolution Contract

| Input or evidence | Result |
| ----------------- | ------ |
| Valid explicit override | Select exact verified target |
| Invalid, inaccessible, or indeterminate explicit override | Stop |
| Verified eligible organization fork | Select fork and bind exact default-branch tip |
| Confirmed candidate absence | Select canonical upstream |
| Authentication, permission ambiguity, timeout, DNS, rate limit, server error, malformed metadata | Stop |
| Candidate exists but ancestry is wrong | Never select automatically |
| Dirty checkout or origin mismatch | Stop |
| Automatic fork changes before use | Stop during revalidation |
| Unapproved failure swallowing | Reject through review and static checks |
| Human-approved call-site exception | Continue only for the documented, distinguishable failure; retain an observable failure signal |

### Required Report

```text
resolved_repository: <owner>/<repository>
revision: <full-commit-sha>
trust_basis: explicit override | maintained organization fork | canonical upstream
candidate_probe: found | absent | not-applicable
checkout: clean, origin-verified, fast-forwarded
```

Do not report `candidate_probe: absent` when the probe could not complete. That state is `ERROR`, and resolution has not succeeded.

## Verified On

| Context | Evidence | Status |
| ------- | -------- | ------ |
| Optional same-owner candidate resolution | A remote lookup returned a confirmed not-found result; explicit classification selected canonical upstream and returned success, while the same workflow preserves non-not-found failures as blocking | verified-local |
