# Pytest Configuration and Discovery Notes

Supporting cases for
[`pytest-configuration-discovery-and-ci-pitfalls.md`](pytest-configuration-discovery-and-ci-pitfalls.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Shadowed pytest configuration | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/pytest-configuration-discovery-and-ci-pitfalls.md) | verified-local | Removed dual config and proved the effective pyproject options |
| Pythonpath and integration discovery | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/pytest-configuration-discovery-and-ci-pitfalls.md) | verified-local | Restored scripts imports and aligned bare/marker collection |
| Slim job addopts and partial coverage | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/pytest-configuration-discovery-and-ci-pitfalls.md) | verified-local | Bound plugin options and fail-under to appropriate environments/suites |
| Stray test outside testpaths | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/pytest-configuration-discovery-and-ci-pitfalls.md) | verified-ci | Explicit pass contrasted with zero default collection; relocation restored CI inventory |
| Redundant namespace-package path insertion | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/pytest-configuration-discovery-and-ci-pitfalls.md) | verified-local | Package-prefix import worked under configured pythonpath without per-test mutation |
| Host-dependent expected path | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/pytest-configuration-discovery-and-ci-pitfalls.md) | verified-ci | Derived golden from production constant and ran full parameter matrix |

## Evidence Detail

The source preserves exact collection counts, timeout measurements, dependency lock deltas, fixture
paths, and configuration excerpts. Those are project-specific observations; the compact main keeps
the commands and decision rules and requires fresh counts for the target repository.

Timeout calibration used observed duration rather than one universal constant. The retained rule is
to choose a documented floor and margin, then find and update assertions tied to the prior value.

## Provenance

- Superseded main SHA-256 (concatenate):
  `abb76d834b4e312b38eb40f1f739ff940183` + `8746676bdcaa18868e9bd6dced12`
- Issue #3335 base: `af4676cc2c54565a41c1e196ad964cf8ccc51e5b`
- Old/new version: `1.4.0` → `2.0.0`
