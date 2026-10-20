---
name: model-version-retarget-issue-tracked-enablement
description: "Retarget an issue-tracked model enablement or release to a newly published upstream version. Use when: (1) a request says 'enable this version' and gives an upstream model link, (2) several issues mention the model family but only one issue binds the model repository, (3) the upstream name is mutable and an immutable revision must be pinned with its observation date, (4) dependent build, qualification, policy, and approval issues still pin the old revision."
category: tooling
date: 2026-10-18
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [github, gh-cli, huggingface, model-release, revision-pinning, immutable-artifact, issue-tracked-enablement, retarget, upstream-version]
---

# Model Version Retarget for Issue-Tracked Enablement

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-18 |
| **Objective** | Retarget one issue-tracked model enablement release from the prior upstream checkpoint to a newly published dated refresh, bind an immutable revision, and notify every dependent pipeline issue. |
| **Outcome** | Operational. One minimal body edit on the canonical release issue, one retarget-decision comment on that issue, and four flag comments on dependent build, qualification, policy, and approval issues. Each remote write was re-read after mutation. A sibling model bound in the same dependent issues was explicitly left unchanged. |
| **Verification** | verified-local — every mutated remote object re-fetched and checked. |

## When to Use

- A user gives an upstream artifact link (a model-hub repository, a new dated
  release) and asks to "enable this version" or to "update the issue" for a
  tracked model.
- The project tracks model enablement in GitHub issues. One release issue
  binds the model repository. Sibling issues own the image build, isolated
  qualification, admission or fair-share policy, and input approval.
- The upstream repository name or branch is mutable; artifact identity must be
  an immutable revision (a commit SHA).
- Several open issues match the model keyword: an epic, dashboard or registry
  bugs, capacity and policy items, and the release issue. Only one carries the
  binding line.
- Dependent issues bind a second, different model in the same body. An
  unscoped edit would retarget that model too.

Do not use this workflow for a repository-wide rename of logical references;
that is
[logical-model-family-rename-with-storage-exceptions](logical-model-family-rename-with-storage-exceptions.md).
Do not use it for first-time enablement planning; that is the planning-issue
flow.

## Verified Workflow

### Quick Reference

```bash
# 1. Find candidate issues. The canonical target carries the artifact BINDING.
gh search issues --author=@me "<model-family>" --json repository,number,title,state

# 2. Resolve the immutable upstream revision. A mutable name is not identity.
curl -s "https://huggingface.co/api/models/<org>/<repo>" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['sha'])"

# 3. Fetch the COMPLETE body to a file before editing. Never edit from a
#    truncated buffer fetched with '.body[0:N]'.
gh issue view <N> --repo <owner>/<repo> --json body --jq .body > body.md
wc -c body.md

# 4. Edit only the binding lines locally; then replace and re-read.
gh issue edit <N> --repo <owner>/<repo> --body-file body.md
gh issue view <N> --repo <owner>/<repo> --json body --jq .body | grep -n "<new-repo-id>"

# 5. Record the decision; flag dependents by comment.
gh issue comment <N> --repo <owner>/<repo> --body-file retarget.md
```

### Detailed Steps

1. Bind the exact target issue. Search open issues for the model keyword and
   read candidate bodies and comments. The canonical target is the issue whose
   body binds the artifact, for example a "Model repository:" line or an
   outcome sentence that names the repository. Epics and dependents only
   mention the family name. When old and new versions share a family name,
   epic rows and titles that use the family name stay valid; do not churn
   them.
2. Verify upstream evidence before citing it. Read the model card or release
   page: release date, what the refresh changes, license, and context. Then
   resolve the immutable revision with the hub API
   `GET /api/models/{org}/{repo}`; the top-level `.sha` field is the current
   default-branch commit. Record the SHA and the UTC observation date. The
   quoted link and page title are not identity.
3. Read the complete issue before any edit. Fetch the full body to a local
   file with `--json body --jq .body > file` and check its size. Fetch the
   comments to learn the gating state: dependency-blocked plans, pending
   automation reviews, operator capacity decisions. Do not touch sections
   that these records manage.
4. Make the smallest edit. Update only the outcome line and the model
   repository line. Add the observed revision and observation date next to the
   binding. Keep the existing "pin the immutable revision; do not use a
   mutable name" instruction unchanged. Keep the issue title when it names the
   family that still applies.
5. Verify the published body by re-fetching it and grepping for the new
   repository identifier.
6. Record the retarget as a decision comment on the canonical issue: new
   repository, revision, observation date, and which downstream records are
   now stale and must be re-planned. State that the comment changes no scope,
   grants, or gates.
7. Propagate by comment, not by dependent body edit. With user authority,
   post one flag comment on each dependent issue whose inputs pin the old
   artifact (image build, isolated qualification, admission policy, input
   approval). In each flag, state what must now bind the new revision and name
   the sibling artifacts that are unaffected. A body edit on an issue that
   binds a second model can silently retarget that model; a comment cannot.
8. Do not re-plan from the flag comments. Re-planning belongs to the
   issue's planning gate. The flags only mark which inputs are stale.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Select the target by title match | Several open issues matched the model keyword: one epic, alias and cache bugs, and one release issue | Title text names the family everywhere; only the release-issue body contained the repository binding line. Selecting by title alone can update a tracking row or the epic and leave the binding stale | Read candidate bodies and comments. The canonical target is the issue that binds the artifact, not the issue whose title matches best |
| Edit from a preview-length body buffer | First body fetch used `--jq '.body[0:3500]'` for inspection; the output stopped mid-word before the last sections | `gh issue edit --body-file` replaces the complete body. Rewriting from the truncated buffer would have silently destroyed the automation and acceptance sections at the tail | Always stage the complete body to a file and check the byte count before an edit. Preview slices are for reading, not for rewriting |
| Treat the spoken version name as identity | The request said "v1" while the linked release was a "V4.1" family refresh | A spoken name can disagree with the linked artifact. Searching or editing against the spoken token targets a repository that does not exist, or the wrong one | Trust the link. Resolve the exact named repository on the hub, then its immutable SHA. Use the spoken name only as a search keyword |
| Edit dependent bodies to match | Dependent build and approval issues bound a second, different model beside the retargeted one | A body edit scoped to one model can silently rewrite the sibling model's inputs. Approval issues are decision records; silent edits defeat the review trail | Flag dependents with comments that name unaffected siblings. Reserve body edits for the single canonical binding carrier |

## Results & Parameters

### Configuration

```yaml
issue_search: 'gh search issues --author=@me "family-name"; add --involves=@me for a union'
revision_endpoint: "https://huggingface.co/api/models/{org}/{repo}"
revision_field: ".sha (top-level default-branch commit); pair with lastModified and the UTC observation date"
body_protocol:
  fetch: "gh issue view N --repo OWNER/REPO --json body --jq .body > file; check wc -c"
  edit: "binding lines only; keep title and gate-managed sections"
  write: "gh issue edit N --repo OWNER/REPO --body-file file"
  verify: "re-fetch body; grep the new repository identifier"
propagation:
  canonical_issue: "one decision comment: new repo, SHA, observation date, stale records"
  dependents: "one flag comment each; name unaffected sibling artifacts; no body edits"
```

### Expected Output

- The canonical release issue binds the new repository and its immutable
  revision, with the observation date recorded.
- The review trail shows one retarget-decision comment on the canonical
  issue.
- Each dependent issue (build, qualification, policy, approval) shows one
  flag comment that marks its stale model input and names unaffected
  siblings.
- No sibling model, title, epic row, or gate-managed section changed.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal model-serving enablement tracker | Retarget of a dated upstream refresh (public: `deepseek-ai/DeepSeek-V4.1-Flash-1017`) across one release issue and four dependent issues | [notes.md](./model-version-retarget-issue-tracked-enablement.notes.md) |

## References

- [Hugging Face Hub API: models](https://huggingface.co/docs/hub/api)
- [logical-model-family-rename-with-storage-exceptions](logical-model-family-rename-with-storage-exceptions.md) — a rename of logical references is a different operation from a version retarget
- [gh-issue-author-or-assignee-union](gh-issue-author-or-assignee-union.md) — author-or-assignee issue search pattern
- [hf-repo-size-estimation-paginated-tree](hf-repo-size-estimation-paginated-tree.md) — HF API reads paginate and need completeness checks
