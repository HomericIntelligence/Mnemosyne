---
name: github-ruleset-write-scope-404
description: "Use when: (1) `gh api --method PATCH repos/<o>/<r>/rulesets/<id>` returns `404 Not Found` even though `GET` on the identical URL succeeds and `gh api repos/<o>/<r> --jq .permissions` shows `admin:true`; (2) diagnosing whether a ruleset-write failure is a real permission gap or a `gh` CLI / request-shape bug before trying workarounds; (3) planning a batch ruleset mutation (e.g. flipping `required_status_checks` across many repos) and need to pre-flight whether the current token can actually write, not just read; (4) a classic OAuth token (`gho_...`) with `repo`+`workflow` scopes and confirmed repo-admin role still cannot PATCH/PUT a repository ruleset; (5) deciding the correct remediation — `gh auth refresh -h github.com -s admin:org` vs. a fine-grained PAT vs. the GitHub UI — for a ruleset-write permission gap."
category: ci-cd
date: 2026-07-19
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - github
  - rulesets
  - branch-protection
  - permission-404-not-403
  - admin-org-scope
  - gh-cli
  - oauth-token-scope
  - write-vs-read-permission
  - gh-auth-refresh
  - credential-gap
  - merge-queue
---

# GitHub Ruleset Writes Can 404 (Not 403) Despite Repo-Admin GET Access

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-19 |
| **Objective** | Diagnose why `gh api --method PATCH repos/<o>/<r>/rulesets/<id>` failed with `404 Not Found` on 4+ HomericIntelligence repos, when `GET` on the identical URL succeeded, `repos/<o>/<r> --jq .permissions` confirmed `admin: true`, and the token's OAuth scopes (`repo`, `workflow`, `delete:packages`, `gist`, `read:org`, `write:packages`) looked sufficient — before concluding it was a real bug versus a real permission gap. |
| **Outcome** | Confirmed a genuine credential-scope gap, not a `gh` CLI defect: reproduced the identical 404 with a raw `curl PATCH` using the token from `gh auth token` (ruling out `gh`-specific request malformation), and with a trivial single-field PATCH body (ruling out payload-shape issues). The repository ruleset **write** endpoint requires a scope beyond what repo-admin + `repo`/`workflow` OAuth scopes grant on a classic token — GitHub masks the authorization failure as `404` instead of `403`, matching the documented pattern where GitHub hides resource existence from callers who cannot act on it. Remediation: `gh auth refresh -h github.com -s admin:org` (interactive device-code/browser flow — cannot be driven headlessly) to add the missing scope; a fine-grained PAT with `Administration: write` on the target repos, or the GitHub UI ruleset editor, are the alternatives when the interactive refresh cannot be run in-session. |
| **Verification** | verified-local — the diagnostic sequence (GET succeeds, PATCH 404s via `gh api`, PATCH 404s via raw `curl` with the same bearer token, `.permissions.admin==true` confirmed, OAuth scopes read from the `X-Oauth-Scopes` response header) was run live against `HomericIntelligence/Agamemnon` and 3 sibling repos. The credential refresh itself was NOT completed in-session (it requires a human-interactive browser/device-code step outside agent control); this entry captures the diagnosis and remediation instructions, not a post-refresh confirmation that the PATCH then succeeds. |

## When to Use

- `gh api --method PATCH` (or `PUT`) on a `repos/<o>/<r>/rulesets/<id>` URL returns `404 Not Found`,
  but `gh api repos/<o>/<r>/rulesets/<id>` (`GET`, no method flag) on the exact same URL succeeds and
  returns the full ruleset JSON.
- You've already confirmed `gh api repos/<o>/<r> --jq .permissions` shows `"admin": true` for the
  current user/token, so classic "not an admin" is ruled out, but the write still fails.
- Before spending time debugging `gh` CLI flags, payload shape, or `--input` file quoting — rule out
  a genuine credential-scope gap first, since it produces the exact same symptom (silent 404) as a
  malformed request.
- Planning a batch mutation across many repos' rulesets (e.g. the `required_status_checks` flip
  pattern in `github-ruleset-required-status-checks-management`) — pre-flight write access on ONE
  repo with a trivial single-field PATCH before assuming the same credential will work everywhere.
- Deciding what to actually tell the user/operator: this is not something an agent can silently work
  around — it requires either an interactive credential refresh, a differently-scoped PAT, or manual
  UI action, and the agent should say so plainly rather than retry variations of the same call.

## Verified Workflow

### Quick Reference

```bash
# 1. Confirm GET works and reports admin:true (rules out "not an admin" as the cause)
gh api repos/<o>/<r> --jq '.permissions'          # -> {"admin": true, ...}
gh api repos/<o>/<r>/rulesets/<id> | head -c 200  # -> succeeds, returns ruleset JSON

# 2. Attempt the write and observe the EXACT status
gh api --method PATCH repos/<o>/<r>/rulesets/<id> --input patch.json
# -> {"message":"Not Found","documentation_url":"...","status":"404"}

# 3. Rule out gh CLI / request-shape bugs: reproduce with raw curl + the same bearer token
curl -sS -X PATCH -H "Authorization: token $(gh auth token)" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/<o>/<r>/rulesets/<id>" \
  -d '{"enforcement":"active"}'                    # trivial single-field body
# Identical 404 via raw curl => NOT a gh-CLI or payload-shape bug; a real auth/scope gap.

# 4. Read the token's actual OAuth scopes from the response header (classic tokens only)
gh api user -i 2>&1 | grep -i "x-oauth-scopes"
# e.g. "delete:packages, gist, read:org, repo, workflow, write:packages" — repo+workflow present,
# repo-admin confirmed, yet the ruleset WRITE endpoint still 404s: repo+workflow is NOT sufficient
# for ruleset mutation; it needs org-level ruleset administration.

# 5. Remediation options, in order of preference:
gh auth refresh -h github.com -s admin:org     # interactive: browser or device-code, NOT scriptable
# OR: a fine-grained PAT with "Administration: write" permission on the target repo(s)
# OR: the GitHub UI ruleset editor at
#     https://github.com/<o>/<r>/rules/<id>/edit
```

### Detailed Steps

1. **Do not assume a 404 on a write means the endpoint or resource is wrong.** The exact same URL
   (`repos/<o>/<r>/rulesets/<id>`) that returns a full JSON body on `GET` can 404 on `PATCH`/`PUT`
   purely because the token lacks write authorization for that specific resource class. GitHub's API
   uses 404 (not 403) for authorization failures on resources the caller is not permitted to know
   exist or act on — this is a documented, intentional information-hiding pattern, not a bug.

2. **Rule out "not an admin" first, cheaply.** `gh api repos/<o>/<r> --jq .permissions` returning
   `admin: true` for the current viewer is necessary but **not sufficient** — repo-admin role and
   ruleset-write authorization are evaluated separately for this endpoint class.

3. **Rule out a `gh` CLI or payload defect before concluding it's a credential gap.** Reproduce the
   identical write with raw `curl` using the exact bearer token from `gh auth token`, and with the
   smallest possible payload (a single already-true field, e.g. `{"enforcement":"active"}`, not a
   full reconstructed ruleset body). If the raw `curl` PATCH 404s identically, the `gh` CLI's request
   construction, `--input` file handling, and payload shape are all exonerated — only genuine
   credential/scope differences remain as the cause.

4. **Read the token's granted OAuth scopes directly, don't infer them.** `gh api user -i` includes an
   `X-Oauth-Scopes` response header listing the classic token's actual granted scopes. In this case
   the token carried `repo`, `workflow`, `delete:packages`, `gist`, `read:org`, `write:packages` —
   plausible-looking scopes that do NOT include ruleset-administration authority. `repo` alone
   (ordinarily sufficient for most repo-level writes: branch pushes, releases, most content APIs)
   does not extend to the newer repository-rulesets write surface.

5. **The fix requires an interactive step an agent cannot complete unattended.**
   `gh auth refresh -h github.com -s admin:org` opens a browser or prints a device code — there is no
   headless/scripted equivalent. When operating as an agent without a human present to complete that
   flow, the correct move is to **stop and report the exact blocker plus the exact remediation
   command**, staging the intended mutation payload (via `GET`, verified, and saved to a file) so it
   is ready to execute the instant the credential is refreshed — not to retry variations of the same
   call hoping a different flag succeeds.

6. **A fine-grained PAT or the GitHub UI are equally valid alternatives to the OAuth scope refresh.**
   If an interactive `gh auth refresh` session is inconvenient, a fine-grained personal access token
   scoped with `Administration: write` on the specific target repositories accomplishes the same
   thing without touching the primary account's broader OAuth grant. The GitHub web UI's ruleset
   editor (`https://github.com/<o>/<r>/rules/<id>/edit`) always works regardless of API-token scope,
   since it authenticates via the browser session.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|----------------|-----------------|
| Assumed the 404 meant a malformed `gh api --input` payload | Rebuilt the PATCH body from a fresh `GET`, stripped server-managed fields, retried `--input file.json` | Still 404'd identically — the payload was never the problem | Reproduce with a trivial single-field body via raw `curl` before debugging payload construction; if the trivial body also 404s, the payload was never at fault |
| Assumed `admin: true` on the repo meant write access to everything | Treated the confirmed repo-admin permission as proof the credential could mutate any repo resource | Ruleset writes are gated on a scope independent of repo-admin role | Repo-admin role and specific-endpoint write authorization (rulesets, in this case) are evaluated separately; confirm the specific write, not a proxy permission |
| Tried `PUT` instead of `PATCH` hoping a different verb would be accepted | `gh api --method PUT` with a minimal `-f` field | Silently fell through to a `GET`-shaped response (no body content to justify a write) rather than erroring, which was initially confusing | A verb swap on an authorization-gated endpoint does not bypass the gate; use the diagnostic curl reproduction instead of guessing verbs |
| Retried the same `gh api PATCH` call multiple times expecting a transient failure | Assumed rate-limiting or eventual consistency | The failure was fully deterministic (auth/scope), not transient | A 404 on a write that is stable across repeated identical calls with a confirmed-valid GET is a scope gap, not a flake — don't retry-loop it |

## Results & Parameters

- **Reproduced on:** `HomericIntelligence/Agamemnon`, `Argus`, `Charybdis`, `Hermes` (rulesets API,
  `repos/<o>/<r>/rulesets/<id>` for the `homeric-main-baseline` ruleset on each).
- **Token type:** Classic OAuth token (`gho_...` prefix), scopes `repo`, `workflow`,
  `delete:packages`, `gist`, `read:org`, `write:packages`. `repos/<o>/<r> --jq .permissions` reported
  `admin: true` for all four repos.
- **Symptom:** `GET repos/<o>/<r>/rulesets/<id>` → 200 with full ruleset JSON. `PATCH` (any payload,
  including a single already-true field) on the identical URL → `{"status":"404"}`. Raw `curl` with
  the same bearer token reproduced the identical 404, ruling out `gh` CLI involvement.
- **Root cause:** the token's scopes did not include organization-level ruleset administration
  authority, which the rulesets write endpoint requires independent of repo-admin role.
- **Remediation not completed in-session:** `gh auth refresh -h github.com -s admin:org` requires an
  interactive browser/device-code step; this entry documents the diagnosis and the exact remediation
  command, staged for execution once a human completes the interactive refresh.

### Related skills

- `github-ruleset-required-status-checks-management` — the GET→append→PUT mechanics for ruleset
  mutation once write access is confirmed working; that skill's "admin-only" warnings on its PUT
  steps are the same class of gap this entry diagnoses precisely.
- `github-ruleset-review-count-governance` — another ruleset-mutation skill whose write steps carry
  the same unstated admin-authorization precondition.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/Agamemnon, Argus, Charybdis, Hermes | Ecosystem-wide merge-queue ruleset flip (staged, blocked on credential) | verified-local; GET succeeded and confirmed `admin:true` on all 4 repos; PATCH 404'd identically via both `gh api` and raw `curl` with the same bearer token; `X-Oauth-Scopes` header read directly to confirm the token's actual granted scopes lacked ruleset-write authority. Remediation (`gh auth refresh -s admin:org`) identified but not completed in-session (requires human-interactive step). |
