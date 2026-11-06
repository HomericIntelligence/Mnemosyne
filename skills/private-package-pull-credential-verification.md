---
name: private-package-pull-credential-verification
license: BSD-3-Clause
description: "Use when: (1) CI jobs pull a container image from a private registry and anonymous pulls are refused, (2) a publish or promotion gate reports 401 while the same jobs pull the image successfully, (3) one read credential must serve many repositories, or (4) a workflow must reject an unusable credential before it reaches a repository secret."
category: ci-cd
date: 2026-11-05
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags: [ghcr, registry, credentials, github-actions, secrets, private-packages, basic-auth, container]
---

# Verify a Pull Credential for a Private Container Package

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-05 |
| **Objective** | Give CI a working read credential for a private container package and make an unusable credential fail at the gate instead of at the consumer |
| **Outcome** | Successful — the corrected probe passed and the consumer jobs pulled the private image |
| **Verification** | verified-ci |

A private package makes the consumer credential part of the build contract. Two
probes disagree in practice: the container client pulls the image, while a
hand-written token request reports 401 for the same credential. The difference is
the request encoding, not the credential.

## When to Use

- CI jobs pull an image from a registry that refuses anonymous pulls.
- A publish gate reports 401 while the consuming jobs pull the same image.
- One read credential must serve many repositories, including future ones.
- A gate checks a credential before or after it is stored as a workflow secret.
- Public visibility for the package is refused by a hosting or organization policy.

## Verified Workflow

### Quick Reference

Mint a pull token the way a container client does:

```bash
CREDENTIALS="$(printf 'git:%s' "${GHCR_TOKEN}" | base64 | tr -d '\n')"
curl --silent --output /dev/null --write-out '%{http_code}\n' \
  --header "Authorization: Basic ${CREDENTIALS}" \
  "https://ghcr.io/token?scope=repository:<namespace>/<image>:pull&service=ghcr.io"
```

A `200` proves the credential can pull that image. `401` with
`{"errors":[{"code":"UNAUTHORIZED","message":"authentication required"}]}`
means the request or the credential is wrong; check the encoding first.

### Suggested Approach

1. Decide the owner of access. If the package cannot be public, CI owns the
   credential, and no operator workaround replaces that decision.
2. Compare encodings before replacing a secret. The registry token endpoint
   accepts a classic token only as the password half of HTTP Basic auth.
   `Authorization: Bearer <token>` returns 401 even for a valid token, so a
   bearer probe manufactures a false negative while client logins succeed.
3. Gate on a real resolution, not on the presence of a secret. Mint a token,
   then resolve each consumed tag (a mutable alias and an immutable
   `git-<sha>`-style tag). Fail with the variable name the consumer must set.
4. Provision once, at organization scope, with visibility for all repositories,
   so a new repository inherits access with no workflow change. Offer a
   per-repository mode for hosts without organization admin rights.
5. Keep the credential out of logs, command lines, and error text. Read it from
   the environment inside the function that uses it, pass it on standard input
   to a login, and never echo it.
6. Fail closed when the credential is absent. A workflow that silently skips the
   pull check reports the same green state as one that verified it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Bearer header | Sent `Authorization: Bearer <classic token>` to the token endpoint | Returned 401 `authentication required` for a valid token | Classic tokens authenticate as the password half of Basic auth; a bearer probe proves nothing about the credential |
| Public package | Asked the registry to make the package public | The organization policy refused public container packages | When public visibility is unavailable, CI must own the credential and the gate must prove the consumer credential resolves the tags |
| Secret rotation | Re-created the secret before reviewing the request encoding | No change; the valid credential still returned 401 | Compare the probe with the client login first; a 401 is not evidence of a bad token |
| Presence-only check | Asserted the secret name existed in the workflow | Passed while every consuming job failed to pull | Verify by resolving a published tag, not by inspecting configuration |

## Results & Parameters

### Configuration

| Parameter | Value | Note |
| --------- | ------- | ------ |
| Scope string | `repository:<namespace>/<image>:pull` | Pair it with `service=ghcr.io` |
| Token class | Classic personal access token | Requires `read:packages` |
| Basic username | Any stable value, commonly `git` | The registry validates the token half |
| Storage | Organization secret, visibility all | Per-repository secrets are the fallback |
| Gate targets | Mutable alias and immutable tag | Both must resolve |

### Example

A workflow with ten container jobs pulled a private image successfully with a
client login, while its publish gate reported 401 for the same credential.
Correcting the gate to Basic auth made it pass without changing the secret, and
the gate then reported the package visibility and both resolved tags.
