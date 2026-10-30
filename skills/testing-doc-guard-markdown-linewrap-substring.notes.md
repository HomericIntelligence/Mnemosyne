# Doc-Guard Line-Wrap Substring Matching — Case Notes

These notes retain dated evidence for decisions that extend the canonical
entry. The current guidance lives in
[skills/testing-doc-guard-markdown-linewrap-substring.md](testing-doc-guard-markdown-linewrap-substring.md).

## Case Index

| Case | Source | Verification |
| --- | --- | --- |
| Rich panel wrapped inside the `--watch` token; single-space joining failed CI | [Immutable source at case base](https://github.com/LLM360/comet/blob/a757aadf/tests/test_cli_issue_3520.py) | verified-ci |

## Cases

### 2026-10-30 — comet PR #3547: the renderer wraps inside a token

The comet pull lane added CLI error-panel guards that assert usage text from
`typer`/Rich output (for example
`--watch combines only with the gateway status.`). The tests passed locally
and failed in CI, twice, across two normalization strengths:

1. Raw substring failed because the local terminal and the CI runner wrap at
   different widths.
2. Strip ANSI codes and box-drawing glyphs, then collapse `\s+` to one space,
   still failed on the operator's own branch head: the CI runner's effective
   width wrapped the needle itself. `--watch` became `-` on one line and
   `-watch` on the next; joining with a single space reproduced `- -watch`,
   which the needle `--watch` cannot match.

The final helper removes all whitespace from both sides of the comparison
after stripping ANSI codes (`\x1b[...m`) and box-drawing characters
(`│╭╮╰╯─`): `"".join(text.split())`. Verification ran the suite over a
`COLUMNS` matrix (40/60/80/120) — 25/25 green at every width — and the
merged PR head `a757aadf` went green in CI with 51 passing checks. The PR
merged as squash commit `f7a37516` on 2026-10-30.

Decision that the case supports: for styled terminal output, single-space
normalization is insufficient. Remove all whitespace from needle and
haystack, strip non-text glyphs first, and verify at several console widths
including one narrower than any local terminal.
