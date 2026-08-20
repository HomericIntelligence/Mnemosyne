# Docstring, API Documentation, and Comment Hygiene — Notes

Supporting case evidence for
[`docstring-api-doc-generation-and-comment-hygiene`](docstring-api-doc-generation-and-comment-hygiene.md).
The exact 30,530-byte v1.2.0 main is archived once in
[`docstring-api-doc-generation-and-comment-hygiene.history`](docstring-api-doc-generation-and-comment-hygiene.history),
with SHA-256 `b61f3ef3127af173828449a3513260b8efed6c30ab964e7974b8d03488776379`.

## Case Index

| Case | Source | Verification status | Reusable result |
| --- | --- | --- | --- |
| Copy/view and package re-export contracts | [Immutable v1.2.0 source](https://github.com/HomericIntelligence/Mnemosyne/blob/10e28497993009cc221cb991e1ee183e6117eda8/skills/docstring-api-doc-generation-and-comment-hygiene.md) | historical verified project cases; exact downstream receipts retained in history | Audit sibling methods and package summaries together |
| Backward-pass catalog and Float16 notes | [Immutable v1.2.0 source](https://github.com/HomericIntelligence/Mnemosyne/blob/10e28497993009cc221cb991e1ee183e6117eda8/skills/docstring-api-doc-generation-and-comment-hygiene.md) | mixed historical verification | Preserve formulas/thresholds that change test choices; move case arithmetic out of main |
| Module-docstring line-wrap audit | [ProjectScylla issue #1364](https://github.com/HomericIntelligence/ProjectScylla/issues/1364) and [PR #1397](https://github.com/HomericIntelligence/ProjectScylla/pull/1397) | verified-ci | Search orphaned fragments and validate the full edited module |
| Subprocess helper POLA contract | [ProjectHephaestus issue #797](https://github.com/HomericIntelligence/ProjectHephaestus/issues/797) | historical case; implementation receipt not asserted here | Document swallowed exceptions and exact success/failure return shapes |
| Dynamic demo version | [ProjectHephaestus issue #787](https://github.com/HomericIntelligence/ProjectHephaestus/issues/787) | historical case; smoke evidence retained in history | Import public `__version__` backed by canonical metadata |
| Module/function contract drift | [ProjectHephaestus issue #1306](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1306) and [PR #1303](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1303) | locally audited; follow-up status retained in history | A function-doc fix does not automatically update the module summary |
| NOTE/TODO/FIXME cleanup passes | [Immutable v1.2.0 source](https://github.com/HomericIntelligence/Mnemosyne/blob/10e28497993009cc221cb991e1ee183e6117eda8/skills/docstring-api-doc-generation-and-comment-hygiene.md) | mixed across repositories | Classify limitation, future work, defect, or obsolete text before editing |

## Detailed Case Notes

### Copy, view, and ownership language

The original project cases distinguished a slice operation that allocates an independent tensor
from a `slice(start, end, axis)` operation that aliases storage and increments ownership state.
Those differences affect caller behavior, so they remain in the retrievable decision rule. The
project-specific memory table and worked tensor cases remain in the exact archived snapshot.

### Catalog and Float16 evidence

Catalog updates depended on four synchronized header counts and an established placement before a
summary table. Float16 accumulation used the rough bound `n × epsilon`, where `n` depends on kernel
area and input channels. The project used machine epsilon near `9.77e-4`; at tolerance `1e-1`,
roughly `n < 102` was the safe accumulation region. Its reusable gradient-check parameters were
`3e-4` for float32 matmul-heavy layers and `1e-3` for other dtypes. Case-specific decisions included
`1e-1` for convolution/BatchNorm backward, a `0.10` wide plus `0.01` absolute check for linear
backward, and `1e-2` float32/`1e-1` other for activation backward. These are historical project
parameters, not universal thresholds; recalculate them for another kernel and dtype.

### Comment classification

A cleanup pass should assign every marker one disposition:

1. current limitation with version context;
2. linked limitation with a concrete resolution condition;
3. future work expressed as `TODO`;
4. likely defect linked to an issue;
5. obsolete/shipped placeholder removed after verification.

Do not add a second issue reference to an already-linked multi-line note, and do not treat a
runtime status string containing “NOTE” as documentation debt.

## Verification Checklist

- Diff implementation and docs separately; a docs-only claim requires no executable change.
- Verify signatures, callers, exports, return/error contracts, and sibling/module summaries.
- Render the configured API generator when rendered output is the product consumer.
- Recompute all catalog counts and confirm section placement/formulas.
- Smoke-run versioned demos against an installed package.
- Report platform-skipped formatters as skipped, not passed.
