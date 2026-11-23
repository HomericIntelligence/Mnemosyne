# Notes: Pytest Coverage Thresholds and Enforcement

Supporting evidence for
[`pytest-coverage-threshold-and-enforcement`](./pytest-coverage-threshold-and-enforcement.md). The
exact prior main is in [history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/pytest-coverage-threshold-and-enforcement.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Aggregate threshold consolidation | [immutable source at the #3335 base](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pytest-coverage-threshold-and-enforcement.md) | verified-ci | Kept single-source-of-truth and `addopts` override audit |
| Merge-preview coverage divergence | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pytest-coverage-threshold-and-enforcement.md) | verified-ci | Kept preview-tree comparison and justified omit rule |
| Per-module floors | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pytest-coverage-threshold-and-enforcement.md) | verified-ci | Kept Cobertura parsing, missing-module failure, and margin guidance |
| Raise a branch floor with targeted tests | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pytest-coverage-threshold-and-enforcement.md) | verified-local | Kept `-o addopts=''`, branch-rate authority, and `NN->exit` interpretation |
| Fail-closed secure XML loader | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pytest-coverage-threshold-and-enforcement.md) | unverified | Retained as proposed, not shipped |
| Optional dependency and omitted-module backstops | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pytest-coverage-threshold-and-enforcement.md) | verified-ci | Kept install/no-skip and integration-backstop rules |
| Native lcov/geninfo repair | [immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/pytest-coverage-threshold-and-enforcement.md) | verified-local | Kept sequential path/toolchain diagnosis; exact logs archived |
| Sharded coverage gate | Hosted nightly unit job, 2026-11-23 | verified-ci | Kept per-shard append, one final aggregate gate, and separate selection proof |

## Case Details

### Aggregate and preview-tree gates

The consolidation cases removed duplicated values from workflow commands and pytest `addopts` so
`[tool.coverage.report].fail_under` controlled the aggregate decision. Planning still had to inspect
`--override-ini=addopts=` and the repository consistency checker; absence of a flag is not always an
accepted configuration.

In the preview-tree case, GitHub combined the PR with newer main content, adding a measured file that
the local PR checkout did not contain. Comparing per-file output identified the denominator change.
An omit was appropriate only because that module was intentionally outside the unit measurement and
received a separate backstop.

### Branch-rate floor raise

An isolated run initially printed an aggregate threshold failure even though selected tests passed.
Clearing `addopts` separated test outcome from repository policy. Terminal combined coverage differed
from Cobertura `branch-rate`; the validator used the latter. Missing-branch markers such as
`NN->exit` pointed directly to the false side needing a test. The floor was set only after XML
measurement and then exercised through the full gate.

### Secure-loader proposal

The proposed loader unifies aggregate and module parsing and distinguishes missing file, unavailable
secure parser, malformed/prohibited XML, invalid rate, absent module, and ambiguous normalized path.
The source described parser- and CLI-boundary tests, including JSON `passed: false`. No downstream
implementation evidence was supplied, so status stays unverified.

### Sharded coverage gate

A full unit job stopped near the middle with no pytest summary. The cause was memory exhaustion,
not a test hang. The run was split into three sequential pytest invocations over disjoint test
roots. Coverage data was erased once before the first shard. Each shard used `--cov-append` and
`--cov-fail-under=0`; the final shard wrote the XML report. One final
`coverage report --fail-under=85` step used the combined data.

Before the missing module tests, the shards passed and a separate per-module checker reported
87.47% line coverage and passed. The combined gate measured 84.85% and exited 2. The checker did not
enforce the aggregate metric, so it could not substitute for the final gate.

After adding the tests for the under-covered module, the combined gate measured 85.23% locally and
85.27% in the hosted run. The per-module checker reported 87.89% to 87.93%, and the nightly run was
green.

Test-selection equivalence was checked separately. The three shard selectors covered the same
13,479 node IDs as one unsharded collection, with no missing, extra, or duplicate nodes. That check
proves suite selection, not coverage accounting. Both checks are needed.

Boundary: this case used sequential shards in one job. Concurrent shards need separate
`COVERAGE_FILE` values and a combine step. Do not append concurrently to one data file.

### lcov sequence

Native coverage repairs proceeded in dependency order: canonical project/build paths, correct CMake
source directory, gcov binary matching the compiler, then `geninfo` filesystem behavior. Blanket
ignore flags before those corrections hid the root cause. Exact repository paths and logs remain in
history because they are not reusable parameters.

## Compaction Disposition

- Kept in main: all decision-changing commands, metric distinctions, failure states, and evidence
  boundaries.
- Moved here: case outcomes and why particular policy choices were accepted.
- Archived only: long project output, exact old threshold tables, and repeated walkthroughs.
