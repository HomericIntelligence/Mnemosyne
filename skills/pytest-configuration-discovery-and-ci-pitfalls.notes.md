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
| Runner outside the project environment | Session validation evidence, 2026-10-30 | verified-local | The locked default environment had no runner; the documented extras invocation imported the project package and the targeted test passed |

## Evidence Detail

The source preserves exact collection counts, timeout measurements, dependency lock deltas, fixture
paths, and configuration excerpts. Those are project-specific observations; the compact main keeps
the commands and decision rules and requires fresh counts for the target repository.

Timeout calibration used observed duration rather than one universal constant. The retained rule is
to choose a documented floor and margin, then find and update assertions tied to the prior value.

A project that keeps its test runner in an optional extra builds a default locked environment
without that runner. A bare runner invocation then resolves the runner from `PATH`; that foreign
interpreter cannot import the project package, so conftest collection fails with
`ModuleNotFoundError` for the project's own package. The discriminating check is a direct
interpreter import under the project environment against the runner's import failure. The base
install without the extra failed this way; the documented extras invocation installed the runner in
the project environment and the targeted test passed. An addopts override did not apply, because
the inherited flags were not the cause.

## Provenance

- Superseded main SHA-256 (concatenate):
  `abb76d834b4e312b38eb40f1f739ff940183` + `8746676bdcaa18868e9bd6dced12`
- Issue #3335 base: `af4676cc2c54565a41c1e196ad964cf8ccc51e5b`
- Old/new version: `1.4.0` → `2.0.0`
