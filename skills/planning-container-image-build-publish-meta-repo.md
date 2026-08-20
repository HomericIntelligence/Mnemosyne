---
name: planning-container-image-build-publish-meta-repo
description: "Use when planning or reviewing a GHCR build/publish workflow in a git-submodule meta-repository. Verify ownership scope, current docker action SHAs, lowercase package names, per-Dockerfile architecture support, trigger/tag/promotion policy, permissions, required-check wiring, and ADR status from live repository evidence. A new job is not enforced merely because it exists; attach validation to an already-required context or update governance explicitly. The workflow remains unverified until images build, push, and pull on each declared platform."
category: ci-cd
date: 2026-06-20
version: "2.0.0"
user-invocable: false
license: BSD-3-Clause
verification: unverified
history: planning-container-image-build-publish-meta-repo.history
tags: [planning, containers, ghcr, docker, buildx, multi-arch, submodules, required-checks, supply-chain, adr]
---

# Container Image Build/Publish Planning for a Submodule Meta-Repository

## Overview

Image-publish plans often present guesses as decisions: remembered action pins, assumed registry
casing, universal multi-architecture promises, or a CI job presumed required because it appears in a
workflow. Verify each against the current repository and live provider before finalizing the plan.

The overall workflow remains `unverified`: cited findings were checked against one repository, but no
end-to-end image build/push matrix was executed. Case details are in
[the notes](./planning-container-image-build-publish-meta-repo.notes.md); exact prior content is in
[history](./planning-container-image-build-publish-meta-repo.history).

## When to Use

- A meta-repo owns a few Dockerfiles and includes application repositories as submodules.
- A plan adds `.github/workflows/image-publish.yml`, GHCR tags, Buildx, or QEMU.
- Docker action SHAs were copied from memory, a template, or an old workflow.
- `linux/amd64,linux/arm64` is proposed without auditing every downloaded binary.
- Package names use the mixed-case organization slug without a lowercase contract.
- A validation job is added without proving its status context is protected.
- An ADR is marked Accepted before reading the repository status convention.
- Scope silently narrows from all fleet images to only meta-repo-owned images.
- A reviewer NOGOs the plan for unverified pins, platforms, policy wiring, or ownership.

## Verified Workflow

This is a proposed planning workflow. Do not claim it is verified until its resulting implementation
builds, publishes, and pulls the declared images.

### Quick Reference

```bash
# Inventory ownership and build inputs.
git ls-files '*Dockerfile*' '.gitmodules' '.github/workflows/*' docs/adr/
git submodule status --recursive

# Resolve each action tag now; dereference annotated tags when needed.
gh api repos/docker/build-push-action/git/ref/tags/<tag> --jq '.object|{type,sha}'

# Find architecture-specific downloads and base images.
rg -n 'amd64|x86_64|arm64|aarch64|TARGETARCH|curl|wget|ADD https?://' \
  --glob '*Dockerfile*'

# Compare workflow job names with live required contexts.
rg -n '^\s+name:|schema-validation|image' .github/workflows/
gh api repos/<owner>/<repo>/rulesets --paginate

# Read, rather than guess, ADR lifecycle policy.
sed -n '1,80p' docs/adr/template.md
```

### 1. Establish image ownership and altitude

List every tracked Dockerfile and classify it as physically owned, generated, or inside a submodule.
Read `.gitmodules` and the component release workflows. Building a submodule application image in
both its source repository and the meta-repo creates competing tag/promotion authorities.

Turn scope into an explicit decision table: image, owner repository, Dockerfile/context, publisher,
platforms, package name, triggers, and rationale. If issue wording supports multiple interpretations,
leave an open decision in a Proposed ADR rather than silently choosing the narrow one.

### 2. Verify immutable action pins and permissions

Resolve current tags for checkout, QEMU, Buildx, registry login, metadata, and build/push actions.
Handle annotated tags and record full commit SHAs with version comments. Reuse a repository pin only
after proving it resolves to the intended release today.

Keep default permissions read-only. Give `packages: write` only to publish jobs and only on trusted
events; PR validation builds should not log in or push. Avoid exposing registry credentials to
fork-controlled code. Preserve provenance/SBOM settings where required by repository policy.

### 3. Audit each Dockerfile before declaring platforms

Multi-arch support is per image, not a workflow-wide aspiration. Inspect base-image manifests,
download URLs, package repositories, compiled extensions, and shell architecture mapping. A literal
`linux-amd64` asset makes an arm64 matrix false unless the Dockerfile maps `TARGETARCH` to the
publishers naming scheme and the asset exists.

Use a per-image matrix with exact supported platforms. For each platform, require an actual build;
when emulation is used, distinguish “builds under QEMU” from “runs on native hardware.” Do not add
arm64 merely because setup-qemu is present.

### 4. Define package and tag contracts

Normalize GHCR owner/image names to lowercase and verify the convention against provider docs or an
existing package. Specify tags for PR validation, default branch, semver releases, and immutable
commit SHA. Decide whether `latest` exists and which event promotes it. Make cache keys include image
and architecture so layers do not collide.

Metadata generation, package visibility, retention, attestations, and pull verification are part of
the contract. A successful `build-push-action` step alone does not prove consumers can authenticate
and pull the manifest.

### 5. Wire validation into an actually required context

Map each new job or step to the live ruleset required-status-check contexts. A workflow job can run
green forever without blocking merges if its context is absent. Conversely, deleting or renaming a
pinned context blocks every PR because GitHub waits for a result that never reports.

Prefer adding deterministic policy validation to an existing required job when that preserves the
canonical fixed context set. Otherwise update workflow, ruleset, canonical-check documentation, and
behavior tests together under the repository governance process. Never merely mention the admin
change as future reviewer work.

### 6. Use repository ADR conventions

Read the ADR template/index and next-number policy. New records normally start Proposed when that is
the documented lifecycle; do not stamp Accepted based on the plans recommendation. Record ownership,
registry/tag policy, platform exceptions, promotion, rollback, and unresolved scope decisions.

### 7. Acceptance mapping

1. Policy tests enumerate exactly the intended owned Dockerfiles and lowercase image names.
2. Every action reference is a verified full SHA.
3. PR events build without login/push; trusted branch/tag events publish with least privilege.
4. Each declared platform builds; manifest inspection reports only supported platforms.
5. Published immutable tags can be pulled and their digest matches workflow output.
6. Required-context mapping proves the validation is merge-blocking.
7. ADR status and index follow live repository rules.
8. Rollback removes publish triggers/tags without orphaning a pinned check.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Copy action SHAs | Used remembered/template pins | Pins were assertions without live resolution | Resolve every tag during planning |
| Promise universal multi-arch | Set amd64 and arm64 globally | An owned Dockerfile downloaded an amd64-only asset | Audit and matrix platforms per image |
| Add a new required job | Put a job in `_required.yml` | Live ruleset did not require its context | Attach to an existing required job or update governance atomically |
| Change rulesets unnecessarily | Assumed every new validation needs a context | Existing schema-validation context could own the step | Preserve fixed context sets when semantics fit |
| Use mixed-case GHCR name | Copied organization spelling | Registry package naming requires a normalized contract | Lowercase and test package names |
| Mark ADR Accepted | Treated plan approval as architecture acceptance | Repository template required Proposed | Read lifecycle policy first |
| Silently narrow scope | Built only owned images without recording why | Issue could mean submodule/fleet images too | Make ownership altitude an explicit decision |
| Claim implementation success | Repo findings were verified | No image was built or pushed | Keep overall status unverified until end-to-end execution |

## Results & Parameters

| Parameter | Required plan decision |
| --- | --- |
| Image inventory | Tracked Dockerfiles classified by owner repository |
| Action references | Freshly resolved full SHAs with release comments |
| Package name | `ghcr.io/<lowercase-owner>/<lowercase-image>` |
| Platforms | Per-image list backed by Dockerfile/base/asset audit |
| PR behavior | Build/test only; no package write or registry credential |
| Publish behavior | Trusted branch/tag only; job-local `packages: write` |
| Required gate | Existing required context or coordinated ruleset update |
| ADR status | Repository template value, usually Proposed for new ADRs |
| Verification | Build, push, manifest inspect, pull-by-digest on declared platforms |

## Verified On

- Repository assumptions in the cited re-plan were inspected directly.
- No image build/publish matrix was run; aggregate status remains `unverified`.

## Companions

- [Case notes](./planning-container-image-build-publish-meta-repo.notes.md)
- [Version history and exact superseded snapshot](./planning-container-image-build-publish-meta-repo.history)
