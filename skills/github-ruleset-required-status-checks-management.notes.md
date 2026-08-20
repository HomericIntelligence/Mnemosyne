# GitHub Ruleset Required Check Notes

Supporting cases for
[`github-ruleset-required-status-checks-management.md`](github-ruleset-required-status-checks-management.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Require-before-emit and integration ID | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/github-ruleset-required-status-checks-management.md) | verified-local | Required context was gated on default-branch emission and copied Actions integration identity |
| Emitted-name mismatch | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/github-ruleset-required-status-checks-management.md) | verified-ci | Keystone rename caused branches and main to emit the canonical required name |
| Thirteen-repository emit-before-require rollout | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/github-ruleset-required-status-checks-management.md) | verified-ci | Added only canonical names observed on main and PR heads; retained old checks |
| Dual-layer strictness | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/github-ruleset-required-status-checks-management.md) | verified-ci | Classic and ruleset strict flags both had to be false to stop behind-state churn |
| Deferred shared-policy boundary | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/github-ruleset-required-status-checks-management.md) | verified-local | Mutation paused until explicit cross-repository authorization was restored |

## Evidence Detail

The source records exact repository lists, ruleset IDs, emitted check inventories, and payload
examples. Those are campaign evidence, not durable identifiers. Always discover the live applying
ruleset and copy integration identity from its existing checks.

Some early examples prepared an admin-only payload without performing the mutation. They prove the
read/transform mechanics locally but do not claim a live policy outcome. Later lifecycle and
strictness cases provide the `verified-ci` boundary retained by the main.

## Provenance

- Superseded main SHA-256: `7d1b6c911878b36d341bc25402d1f51504940f85c397c3c485d8162fd26d6821`
- Issue #3335 base: `af4676cc2c54565a41c1e196ad964cf8ccc51e5b`
- Old/new version: `1.3.0` → `2.0.0`
