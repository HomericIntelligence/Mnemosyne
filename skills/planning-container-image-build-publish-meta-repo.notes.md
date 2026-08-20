# Notes: Container Image Build/Publish Planning in a Meta-Repository

Supporting evidence for
[`planning-container-image-build-publish-meta-repo`](./planning-container-image-build-publish-meta-repo.md).
The complete prior main is in [history](./planning-container-image-build-publish-meta-repo.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Initial Odysseus image-publish plan | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/planning-container-image-build-publish-meta-repo.md) | unverified | Retained end-to-end warning and ownership/platform/pin/policy checklist |
| Required-check NOGO and re-plan | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/planning-container-image-build-publish-meta-repo.md) | repo-verified finding | Retained attach-to-existing required-context decision; no workflow execution inferred |
| Multi-architecture Dockerfile audit | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/planning-container-image-build-publish-meta-repo.md) | repo-verified finding | Retained per-image platform matrix after amd64-only asset discovery |
| Action pins, GHCR casing, ADR status, and scope | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/planning-container-image-build-publish-meta-repo.md) | repo-verified findings | Retained fresh resolution, lowercase policy, Proposed status, and explicit altitude decision |

## Case Details

The initial plan proposed publishing meta-repository-owned images while leaving submodule application
images to their source repositories. Review correctly treated that scope as a decision requiring DRY
and ownership evidence, not an implicit reading of the issue.

A proposed universal amd64/arm64 matrix conflicted with an owned Dockerfile that downloaded a literal
amd64 NATS asset. The revised plan used per-image platforms. Action SHAs were re-resolved during the
session, GHCR lowercase naming became a policy assertion, and the ADR followed the repository
Proposed status convention.

The central gate finding was that a new workflow job would not automatically join the fixed required
context set. The re-plan placed deterministic validation inside the already-required
`schema-validation` context, avoiding an unnecessary ruleset edit. These source facts were inspected,
but no image was built or published, so the workflow remains unverified.

## Compaction Disposition

- Kept in main: ownership altitude, pin resolution, platform audit, registry/tag/permission contract,
  required-context wiring, ADR policy, and end-to-end acceptance.
- Moved here: issue/review sequence and repository-specific observations.
- Archived only: volatile action SHA table and long proposed workflow examples.
