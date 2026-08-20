# E2E Experiment Runner Bug Notes

Supporting cases for
[`e2e-experiment-runner-bug-patterns.md`](e2e-experiment-runner-bug-patterns.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Retry and checkpoint semantics | [ProjectScylla PR #126](https://github.com/HomericIntelligence/ProjectScylla/pull/126) | verified-local | Separated infrastructure state from judged outcome and protected concurrent writes |
| Resume restoration and repeated-resume paths | [ProjectScylla PR #476](https://github.com/HomericIntelligence/ProjectScylla/pull/476) | verified-local | Restored tier/run context and aligned validation/load paths |
| Until and signal behavior | [ProjectScylla PR #1080](https://github.com/HomericIntelligence/ProjectScylla/pull/1080) | verified-local | Compared post-advance state and propagated shutdown callback |
| Rate-limit response handling | [ProjectHephaestus immutable source case](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/e2e-experiment-runner-bug-patterns.md) | mixed | Detected stdout/exit-zero envelopes and retained zero reset sentinel |
| Judge parsing, prompt reuse, and validity | [ProjectScylla PR #1491](https://github.com/HomericIntelligence/ProjectScylla/pull/1491) | verified-local | Parsed complete JSON, reused durable prompt, and filtered invalid judges before consensus |
| Rerun constructor and checkpoint states | [ProjectScylla PR #1558](https://github.com/HomericIntelligence/ProjectScylla/pull/1558) | verified-local | Bound arguments to correct method and used accepted completion values |
| Full historical campaign set | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/e2e-experiment-runner-bug-patterns.md) | mixed | Preserves links to the complete listed PR set and dryrun/fullrun observations |

## Evidence Detail

The prior source lists ProjectScylla PRs #126, #142, #476, #1080, #1102, #1469, #1476, #1491,
plus PRs #1543, #1544, #1546, and #1558, along with exact files, commands, state tables, fixtures,
and test classes.
Those details remain in history. The compact main retains the cross-cutting invariants and a staged
verification matrix rather than prescribing old file locations.

Some observations were derived from multiple dryrun/fullrun experiments and post-hoc artifact
inspection; others were covered by code/tests. The skill therefore uses `mixed` instead of upgrading
the whole corpus to verified CI.

## Provenance

- Superseded main SHA-256: `80fa68b767a6d72855b7a247dc702ec63daa9e75194d898c872f57a9e2f4445d`
- Issue #3335 base: `af4676cc2c54565a41c1e196ad964cf8ccc51e5b`
- Old/new version: `1.1.0` → `2.0.0`
