# Notes: GitHub Actions Security Scanning and Supply-Chain Hardening

Supporting evidence for
[`gha-security-scanning-supply-chain`](./gha-security-scanning-supply-chain.md). These notes retain
case-specific paths, references, and outcomes without duplicating the complete prior main, which is
archived in [history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/gha-security-scanning-supply-chain.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| CodeQL, npm audit, Gitleaks, and scan-trigger setup | [immutable source at the #3335 batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/gha-security-scanning-supply-chain.md) | verified-local | Reusable trigger, permission, parser, and required-check rules retained in main |
| Action SHA pinning and transitive setup failure | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/gha-security-scanning-supply-chain.md) | verified-local | Tag dereference and parent-action diagnosis retained; case transcript moved here |
| Verified installers and dependency scanning | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/gha-security-scanning-supply-chain.md) | verified-local | Digest-before-execute contract retained; product/version tables remain recoverable in history |
| CodeQL alert remediation | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/gha-security-scanning-supply-chain.md) | verified-local | Check-run API distinction and focused regression-test rule retained |
| Bandit required gate | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/gha-security-scanning-supply-chain.md) | verified-local | Severity gate, JSON artifact, narrow `nosec`, and weak-hash distinctions retained |
| Fail-closed Bandit LOW baseline | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/gha-security-scanning-supply-chain.md) | unverified | Remains explicitly proposed; no CI success inferred |
| Composite-Action zizmor coverage | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/gha-security-scanning-supply-chain.md) | unverified | Proposed repository-wide inventory and parity contract retained |

## Case Details

### Scanner setup and SARIF

The source cases used separate workflows/jobs for CodeQL and scanner enforcement, with
`pull_request` coverage added where scans had run only on main pushes. A Gitleaks summary gate failed
because POSIX `grep` treated `\s` literally; `jq` against `.runs[].results[]` fixed the decision
boundary. The reusable rule is structural parsing, while exact workflow names and report prose are
case evidence.

For SARIF upload planning, the key ordering was: run scanner and preserve its status, upload with a
job-local `security-events: write`, then enforce the captured result. Fork restrictions and
`if: always()` behavior require repository-specific testing.

### Pins and installers

The action-pin cases distinguished lightweight from annotated tags and retained the release tag as
a comment next to a full commit SHA. One setup-stage failure came from an action's transitive
metadata, demonstrating that a direct pin in the caller cannot repair a broken child reference.

Installer cases recorded concrete versions and platform digests for their repositories. Those
values age and therefore remain in the immutable history rather than canonical recommendations.
The durable contract is version pin + correct platform digest + verification before extraction or
execution.

### Bandit and zizmor proposals

The LOW-baseline design requires duplicate-key rejection, typed schema validation, exact count
comparison, an explicit review reference, and atomic update. A scheduled lane later ran that design:
the per-row triage branch in the main entry passed in CI. Likewise, extending zizmor from workflows
to tracked composite Actions was a reviewed design: required CI/pre-commit use offline parity,
scheduled scans may retain online audits, and regression tests derive roots from tracked files. The
zizmor root extension remains unverified.

### Baseline drift case (2026-11, `verified-ci`)

The scheduled security lane ran a LOW count baseline while the pre-merge lane ran only a
medium-or-higher scan. One scheduled run reported four changed rows: one reduced rule ID and three
increased ones.

- Regenerating on current trunk produced larger counts than the failing run, because three merges
  had landed after it. Triage used the trunk report, not the run report.
- The reduced row traced to a change that replaced two internal asserts with an explicit raise. The
  guard became stronger while the count fell.
- One import-flag row and the matching call and partial-path rows came from the same new call sites.
  Each call site used a fixed argument vector, no shell, captured output, and a finite timeout.
- The baseline update command rewrites its provenance field and re-sorts the keys, so the file has
  one canonical update path. A hand edit loses that property.
- The gate had no pre-merge signal. The only acceptance evidence was the next scheduled run.

## Compaction Disposition

- Kept in main: all distinct triggers, enforcement boundaries, pin/digest rules, SARIF commands, drift triage,
  baseline failure modes, and verification caveats.
- Moved here: project narratives, observed failure sequence, and proposal context.
- Archived only: volatile version/SHA tables, long workflow listings, and full prior examples.
