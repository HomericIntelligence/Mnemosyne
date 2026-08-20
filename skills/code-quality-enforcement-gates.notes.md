# Code-Quality Enforcement Gate Notes

Supporting cases for
[`code-quality-enforcement-gates.md`](code-quality-enforcement-gates.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Ruff C901 and bounded extraction | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/code-quality-enforcement-gates.md) | verified-local | Reduced complexity while preserving orchestration and error order |
| Mypy strictness and override narrowing | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/code-quality-enforcement-gates.md) | verified-local | Reached zero before config change and retained only residual subtrees |
| Constructor annotation gap | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/code-quality-enforcement-gates.md) | verified-local | Targeted ANN204 plus AST positive/negative property guard |
| Deprecation warning and docs sync | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/code-quality-enforcement-gates.md) | verified-local | Zero-warning prerequisite and independent insertion-point checks |
| Production asserts and temp paths | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/code-quality-enforcement-gates.md) | verified-local | Explicit exceptions and isolated portable temporary paths |
| Audit/reviewer ground-truth check | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/code-quality-enforcement-gates.md) | mixed | Distinguished introduced failures from main failures and corrected stale tracking state |

## Detailed Verification

The original cases contain repository-specific file lists, diagnostic counts, configuration blocks,
and audit tables. They demonstrate the workflow but are not universal thresholds. The reusable main
therefore keeps commands as parameterized templates and requires a fresh zero-baseline measurement.

The constructor case used a focused lint rule because broad annotation enforcement would have pulled
unrelated debt into the change. Its regression parsed Python syntax and checked both annotated and
unannotated fixtures, avoiding a source-string test.

The documentation-sync case showed why one broad search can be false-green when the same tokens occur
elsewhere. Each semantic section must be isolated before checking its required symbol, replacement,
timeline, and example.

## Provenance

- Superseded main SHA-256: `7d98b34914dd2831e6b746764b27c686e0d61da9a4bbc60b0cfde95c70bad94e`
- Issue #3335 base: `e7f342098c41f3d5fda1bf7c7fedf754abdaaad2`
- Old/new version: `1.5.0` → `2.0.0`
