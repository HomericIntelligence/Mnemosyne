# Persistence Backing-Store Planning Notes

Supporting cases for
[`persistence-backing-store-test-harness-driven-choice.md`](persistence-backing-store-test-harness-driven-choice.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Test-harness-driven SQLite choice | [Odysseus issue #71](https://github.com/HomericIntelligence/Odysseus/issues/71) | unverified | Preferred embedded storage because ctest ran without live NATS |
| Dependency mechanism revision | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/persistence-backing-store-test-harness-driven-choice.md) | unverified | Replaced guessed FetchContent with verify-first Conan/imported target plan |
| Compiler versus static-analysis NOGO | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/persistence-backing-store-test-harness-driven-choice.md) | unverified | Corrected NOLINT misconception and scoped raw C API to dedicated target |
| Durability correctness revision | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/persistence-backing-store-test-harness-driven-choice.md) | unverified | Added complete rc checks, total state reconstruction, and absolute path |

## Evidence Boundary

The plan read current dependency and CMake policy files and identified a server target with scoped
warning suppressions. The proposed SQLite recipe version, generated target name, warning coverage,
filesystem path implementation, schema, and restart behavior were not built or executed.

All proposed numeric versions and target spellings are therefore verify-first placeholders. The
skill’s reusable value is its decision and evidence structure, not a claim that this implementation
passed.

## Provenance

- Superseded main SHA-256: `73fd9652a7ac6aeac56b3f9e28d4f516877282a307a36349a2f87149be920729`
- Issue #3335 base: `d377a8924aff84e5cc193b720130b4c57e38c5c3`
- Old/new version: `1.2.0` → `2.0.0`
