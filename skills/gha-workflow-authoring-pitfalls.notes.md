# GitHub Actions Workflow-Authoring Notes

Supporting cases for
[`gha-workflow-authoring-pitfalls.md`](gha-workflow-authoring-pitfalls.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Invalid slash job IDs | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/gha-workflow-authoring-pitfalls.md) | verified-local | Hyphenated IDs restored job discovery while preserving slash display names |
| Composite description expression | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/gha-workflow-authoring-pitfalls.md) | verified-local | Plain placeholder avoided metadata expression evaluation |
| Workflow run-block injection | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/gha-workflow-authoring-pitfalls.md) | verified-local | Env-var lift passed security hook and kept shell syntax fixed |
| PR creation permission boundary | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/gha-workflow-authoring-pitfalls.md) | mixed | Repository inspection was verified; organization toggle or alternate credential required external authority |
| Pull-request event fan-out | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/gha-workflow-authoring-pitfalls.md) | verified-local | Split convergence events from expensive workflow-wide CI triggers |
| Dual-trigger reusable workflow | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/gha-workflow-authoring-pitfalls.md) | verified-local | Required typed identifier and one normalized validated job |

## Evidence Detail

The superseded source includes exact workflow fragments, repository settings responses, and
platform-comment templates. The compact main keeps the behavior-changing syntax and policy choices;
target repositories must supply their current event, permission, and concurrency context.

The PR-creation case crosses an organization-admin boundary. Detection and repository-level behavior
were observed, but enabling an organization capability or provisioning an App/token is not implied by
the local verification status.

## Provenance

- Superseded main SHA-256: `32a43f3090e15d0f0040ba159caeb79e0842dd5e2ab168e18900b2a31e8b5698`
- Issue #3335 base: `af4676cc2c54565a41c1e196ad964cf8ccc51e5b`
- Old/new version: `1.4.0` → `2.0.0`
