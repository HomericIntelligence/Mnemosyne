# Automation Pipeline Observability Notes

Supporting cases for
[`automation-pipeline-observability-and-dryrun.md`](automation-pipeline-observability-and-dryrun.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Dry-run mutation leak | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/automation-pipeline-observability-and-dryrun.md) | verified-precommit | One return boundary prevented PR, learning, and follow-up phases |
| Curses failure visibility and durable logs | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/automation-pipeline-observability-and-dryrun.md) | verified-precommit | Persisted phase status, command output, and tracebacks outside worktrees |
| Composition-root wiring audit | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/automation-pipeline-observability-and-dryrun.md) | verified-local | Distinguished tested components from runtime-constructed components |
| Heterogeneous scope arguments | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/automation-pipeline-observability-and-dryrun.md) | verified-precommit | Passed issue lists only to required-arg phases while preserving rediscovery |
| Silent Bash abort and Python rewrite | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/automation-pipeline-observability-and-dryrun.md) | verified-precommit | Replaced implicit trap/job-control semantics with explicit phase results |

## Evidence Detail

The source contains exact UI dimensions, timeout constants, implementation script names, wiring
matrices, argument inventories, and Python orchestrator sketches. Those are case evidence rather than
portable defaults. The compact main keeps the result schema and decision boundary.

The shell rewrite threshold is qualitative: repeated independent silent-abort causes after several
safety-layer fixes indicate structural complexity. One understood shell failure alone does not
mandate a rewrite.

## Provenance

- Superseded main SHA-256: `2b1f606c2573d1059e2db7ae70d47df7626a829c5f5df2406f74a227e01ac16f`
- Issue #3335 base: `d377a8924aff84e5cc193b720130b4c57e38c5c3`
- Old/new version: `1.2.0` → `2.0.0`
