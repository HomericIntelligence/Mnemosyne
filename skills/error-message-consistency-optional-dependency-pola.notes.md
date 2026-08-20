# Error Message Consistency and Optional Dependency POLA — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Missing PyYAML incorrectly reported as unsupported format | [ProjectHephaestus PR #1608](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1608) | `verified-local`: 140 tests; CI pending at capture | Retained branch split, sibling message reuse, caller reconciliation, and alias coverage |
| Invalid output format deliberately falls back to text | [ProjectHephaestus issue #1509](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1509) | `verified-local`: 77 tests after documentation and regressions; CI pending | Retained evidence-first raise-versus-document decision |
| Shared TOML/PyYAML capability resolver | [immutable v3.0.0 source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/error-message-consistency-optional-dependency-pola.md) | `unverified`: implementation plan only | Retained lazy resolver and pre-side-effect failure as design guidance |
| Corpus compaction | [Mnemosyne issue #3335](https://github.com/HomericIntelligence/Mnemosyne/issues/3335) | Batch validation only | Supporting detail moved here; full prior content remains in history |

## Contract decision matrix

| Input/capability state | Public result |
| --- | --- |
| Supported YAML format and dependency available | Parse YAML |
| Supported YAML format and dependency absent | Actionable `RuntimeError` with install guidance |
| Unsupported format with strict API | `ValueError` naming the input |
| Invalid format with established fallback API | Document and test text/default fallback |
| Write requested but resolver fails | No destination created or truncated |

## Test details

- Test both `.yaml` and `.yml` aliases.
- Keep a regression proving unknown formats still use the value-error branch where applicable.
- Assert the stable actionable substring rather than every punctuation detail unless exact text is a
  documented public contract.
- Patch the capability at its lookup path and verify production consults it at call time.
- For lazy imports, isolate `sys.modules` so a previously imported dependency cannot satisfy the
  test accidentally.
- Audit wrappers for exception chaining and tuple-collapse only when handler bodies are identical.

## Evidence boundary

The two completed repairs are local-only. The centralized resolver is plan-only. Skill-level
`verified-local` must not be read as implementation evidence for the resolver design.
