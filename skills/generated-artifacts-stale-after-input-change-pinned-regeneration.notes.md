# Notes: generated-artifacts-stale-after-input-change-pinned-regeneration

Supporting evidence for the main skill. All repository-specific identifiers are generalized.

## Propagation mechanics (why a rename staleness-fans-out)

The repository's audit pipeline binds each report to its inputs by embedding an
input-bindings structure in every emitted artifact. The structure records each input file's
repository-relative path and content digest, for example:

```json
[{"path": "analysis/catalog/format_ledger.json", "role": "format_ledger", "sha256": "48..."}]
```

The rename rewrote strings inside that hashed input file. Its digest changed
(`48d859e5...` to `2579fe72...`), and because the bindings are embedded per record (each CSV
row carries the serialized bindings JSON), one digest change became a change in every row of
every coverage artifact and in the audit summary files. Total: 41 files, 254 lines, all of
them the same digest substitution. Zero metric values changed.

Files whose content does not embed the bindings (per-model detail reports, the summary CSV)
were byte-identical after regeneration, so only 2 of the audit tree's 45 declared streams and
the 39 coverage artifacts actually changed.

## Which trees were stale vs. never stale (the skew A/B)

Local checks were first run under a newer local renderer stack (plotting library 3.11.2 vs.
CI pin 3.10.1). Results, compared against the same checks re-run in a venv pinned to the CI
install set:

| Tree | Failed under unpinned local tools | Failed under CI-pinned tools | Verdict |
| --------- | --------- | --------- | --------- |
| Model-data audit summary | yes | yes | real drift (embedded input digest) |
| Coverage heatmaps (all models) | yes | yes | real drift (embedded input digest) |
| Catalog Pareto report | yes | no | pure skew; regenerates byte-identical under the pin |
| Runtime Pareto reports (11) | yes | no | pure skew; regenerates byte-identical under the pin |
| Rendered infographics (2) | no | no | unaffected |

The three "yes/no" rows are the evidence for the A/B rule: failing freshness checks on a dev
host with non-pinned renderers can be false staleness. Had those trees been regenerated under
the unpinned stack and committed, CI would have recomputed different bytes and failed again.

## Single-pass regeneration driver (pattern)

The audit CLI emits exactly one report stream per invocation from a deterministic build that
takes several minutes (an 8k-record input load and analysis). Regenerating 45 streams serially
was projected at roughly four hours. The `--check` path regenerates all 45 streams in memory
from one load, so the driver loads once and renders each stream:

```python
inputs = load_audit_inputs(catalog, expected_grid, source_root, destination_root)
audit = build_audit(inputs)                      # the expensive part runs once
models = [m["model_id"] for m in summary(audit)["model_summaries"]]
for stream in [None, *models]:                   # repository summary + one per model
    for fmt in ("json", "md", "csv"):
        write(target_path(stream, fmt), render_report(audit, stream, fmt))
# verify afterwards with the stock CLI: audit-model-data --check -> exit 0
```

Time: one multi-minute load plus seconds for all 45 renders. The stock `--check` (still
single-process) confirmed byte equality, so the hand-checked streams are authoritative.

If no single-pass builder exists and the invocations are independent processes, parallelize
them (for example `xargs -P`) instead of serializing.

## Enumeration method for the freshness surface

The workflow was read directly and every check-mode step was listed before fixing anything:

1. a migration-verify step (data-level, exit 0 throughout);
2. the model-data-audit `--check` with three `--fail-on` flags;
3. a coverage-heatmaps `--check`;
4. a catalog Pareto `--check` with a long model-id argument list;
5. a runtime Pareto `--check` over 11 report directories;
6. and 7. two rendered-report `--check` steps.

Fixing only step 2 (what CI reported) would have left step 3 red; the one-pass repair avoided
a second red master run.

## Observed timings

- Single audit render (any stream): several minutes.
- All 45 audit streams via the single-pass driver: one load plus seconds of rendering.
- Coverage heatmap regeneration (13 models, 39 files): a few minutes in the pinned venv.
- Runtime Pareto regeneration (11 reports): minutes; final bytes identical to HEAD.

## Verification record

- Pinned environment: plotting library 3.10.1, numerical stack at the CI pins
  (numpy 2.2.5, pandas 2.2.3), installed from the two requirements files the CI install step
  uses.
- All seven CI freshness/check invocations re-run locally with their exact workflow command
  lines in that environment: every one exited 0.
- The full test suite had already passed in CI on the pre-repair tree, so the repair PR
  changes only artifact bytes.

## Privacy and scope provenance

Captured from one CI-repair session in a Python benchmark-telemetry repository. Repository,
organization, project, path, host, and pull-request identifiers are withheld per the privacy
policy; tool names and public version numbers are retained because they change execution.
