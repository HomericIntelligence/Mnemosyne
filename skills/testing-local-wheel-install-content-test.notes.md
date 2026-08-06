# ProjectHephaestus Artifact-Lane Design Notes

## Session Context

- Date: 2026-08-05
- Verification: `unverified`
- Scope: packaging integration tests, pytest marker configuration, required/release CI routing,
  and workflow documentation only
- Production API/dependency/migration/ADR changes: none proposed
- Source of truth retained: existing wheel-package and sdist-inclusion rules in `pyproject.toml`

These notes preserve the ProjectHephaestus-specific implementation contract that motivated v2.0.0
of the reusable skill. They are design evidence, not proof that the implementation or CI passed.

## Controlled Artifact Constants

```python
CURRENT_TEST_VERSION = "1.0.1"
PREVIOUS_TEST_VERSION = "1.0.0"
SOURCE_DATE_EPOCH = "1735689600"
DIST_NAME = "HomericIntelligence-Hephaestus"
```

The session fixture is intended to produce two current wheel/sdist pairs and one previous wheel.
Each build uses:

```text
LC_ALL=C.UTF-8
PYTHONHASHSEED=0
SETUPTOOLS_SCM_PRETEND_VERSION=<current-or-previous-version>
SOURCE_DATE_EPOCH=1735689600
TZ=UTC
```

`PYTHONPATH` is removed. Builds run from the parent of the checkout via
`python -m build <repo> --wheel --outdir <distinct-dir> --no-isolation`, with `--sdist` for the two
current builds. Missing `build` or `uv`, failed subprocesses, and zero/multiple matching artifacts
must raise rather than skip.

## Planned Test Layout

| Path | Contract |
|------|----------|
| `tests/integration/artifact_support.py` | Typed controlled-build helpers, exact artifact discovery, streaming SHA-256, and package source inventory |
| `tests/integration/conftest.py` | One session-scoped `controlled_artifacts` fixture using a pytest temp root under `build/` |
| `tests/integration/test_package_lifecycle.py` | Direct current-wheel install, direct current-sdist install, previous-to-current upgrade, uninstall, and missing-tooling failures |
| `tests/integration/test_sdist_contents.py` | Reproducibility, safe tar members, and exact sdist manifest equality |
| `tests/integration/test_wheel_contents.py` | Reproducibility, safe ZIP members, exact wheel manifest, full `RECORD`, and existing entry-point metadata equality |
| `tests/unit/ci/test_artifact_lane.py` | Required-build selection, general-lane exclusion, aggregate-gate membership, and release inclusion |

The `artifact` marker belongs beside the existing pytest markers in `pyproject.toml`.

## Exact Hephaestus Inventories

The package inventory is every regular file under `hephaestus/`, excluding `__pycache__`, `.pyc`,
and `.pyo`, plus generated `hephaestus/_version.py`.

The sdist manifest is exactly that inventory plus:

```text
README.md
LICENSE
NOTICE
COMPATIBILITY.md
pyproject.toml
PKG-INFO
```

The wheel manifest is exactly the package inventory plus these paths below its single derived
`.dist-info` prefix:

```text
METADATA
WHEEL
entry_points.txt
licenses/LICENSE
licenses/NOTICE
RECORD
```

Tar validation must reject absolute paths, traversal, duplicate stripped paths, links, devices,
FIFOs, and unsupported member types before exact equality. ZIP validation must reject absolute,
traversal, and duplicate names before manifest or `RECORD` checks.

Every `RECORD` row must be unique and the row paths must equal the member names. Only the `RECORD`
self-entry may have empty integrity fields. Every other row must have a URL-safe-base64 SHA-256
digest and decimal size matching the member bytes.

## Installed Lifecycle Matrix

Representative base-layer entry points:

```text
hephaestus-system-info
hephaestus-check-python-version
```

Each environment uses the current Python 3.13 interpreter, an absolute venv Python/script path,
and a non-repository run directory. `PYTHONPATH` is absent. Before its initial install, the test
must prove both `hephaestus` and `HomericIntelligence-Hephaestus` distribution metadata are absent.

1. Current wheel: direct install into an empty venv, assert `1.0.1`, execute both scripts with
   `--help`, and require exit zero plus usage output.
2. Current sdist: repeat the same contract in a second empty venv.
3. Upgrade/uninstall: install the `1.0.0` wheel, assert `1.0.0`, upgrade to the `1.0.1` wheel,
   assert `1.0.1` and no stale dist-info, run both scripts, uninstall by distribution name, then
   prove package code, metadata, and both script files are absent.

The direct current-wheel test is intentionally independent from upgrade: an upgrade can retain
state and cannot prove a clean install.

## CI Routing Contract

- General integration job: `-m "not nightly and not artifact"` with
  `--basetemp=build/pytest-integration`.
- Existing required `build` job: replace sampled build/smoke commands with the artifact marker and
  `--basetemp=build/pytest-artifacts`; retain the job identity and aggregate-gate membership.
- Release integration step: retain `-m "not nightly"`, which includes artifact tests, and use
  `--basetemp=build/pytest-release-integration`.
- Keep `installed-cli-tests`: it exercises every automation-extra script, while the new lane owns
  artifact reproducibility, sdist installation, upgrade, and uninstall.

## Proposed Acceptance Commands

```bash
uv run pytest \
  tests/integration/test_sdist_contents.py::test_sdist_build_is_reproducible \
  tests/integration/test_wheel_contents.py::test_wheel_build_is_reproducible \
  --override-ini="addopts=" --basetemp=build/pytest-artifacts-repro \
  -v --strict-markers
```

```bash
uv run pytest \
  tests/integration/test_sdist_contents.py::test_sdist_complete_manifest_matches_source \
  tests/integration/test_wheel_contents.py::test_wheel_complete_manifest_matches_source \
  tests/integration/test_wheel_contents.py::test_wheel_record_covers_and_hashes_every_member \
  --override-ini="addopts=" --basetemp=build/pytest-artifacts-integrity \
  -v --strict-markers
```

```bash
uv run pytest \
  tests/integration/test_package_lifecycle.py::test_current_wheel_clean_install_runs_representative_entry_points \
  tests/integration/test_package_lifecycle.py::test_current_sdist_clean_install_runs_representative_entry_points \
  --override-ini="addopts=" --basetemp=build/pytest-artifacts-clean-install \
  -v --strict-markers
```

```bash
uv run pytest \
  tests/integration/test_package_lifecycle.py::test_wheel_upgrade_and_clean_uninstall \
  --override-ini="addopts=" --basetemp=build/pytest-artifacts-lifecycle \
  -v --strict-markers
```

```bash
uv run pytest \
  tests/integration/test_package_lifecycle.py::test_missing_build_frontend_fails_closed \
  tests/integration/test_package_lifecycle.py::test_missing_uv_fails_closed \
  tests/unit/ci/test_artifact_lane.py \
  --override-ini="addopts=" --basetemp=build/pytest-artifacts-gate \
  -v --strict-markers
```

```bash
uv run pytest tests/integration \
  --override-ini="addopts=" --basetemp=build/pytest-artifacts \
  -v --strict-markers -m artifact
```

Focused static validation is intended to run `ruff check` and `mypy` over the new/modified artifact
test helpers and the workflow-structure test.

## Review Correction Preserved

The reviewed design originally risked treating previous-to-current upgrade as current-wheel install
coverage. The corrected contract adds a separate current-wheel direct clean-install test, retains a
separate current-sdist venv, and reserves the third environment for upgrade and uninstall. This
distinction changes behavior and is the main reason the older sampled-wheel skill required a major
rewrite rather than a small additive amendment.
