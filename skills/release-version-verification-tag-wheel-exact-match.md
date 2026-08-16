---
name: release-version-verification-tag-wheel-exact-match
license: BSD-3-Clause
description: "Keep Git tags as the sole authority in dynamic-version releases, refuse aggregate static-file bumps before reads or writes, preserve static-project mutation, and verify tag-to-wheel equality. Use when: (1) one bump utility serves static and hatch-vcs projects, (2) dry-run or JSON can report false success for an unsupported project, (3) machine-readable stdout is contaminated by human output, (4) direct API callers can bypass CLI safety, or (5) release publication needs exact tag and wheel evidence."
category: ci-cd
date: 2026-08-07
version: "2.0.0"
user-invocable: false
verification: unverified
history: release-version-verification-tag-wheel-exact-match.history
tags:
  - python-packaging
  - hatch-vcs
  - semantic-versioning
  - git-tags
  - release-workflow
  - wheel-verification
  - importlib-metadata
  - dynamic-version
  - mutation-preflight
  - json-stdout
  - signed-tags
  - github-actions
  - pypi
  - fail-closed
---

# Release Version Boundaries: Dynamic Refusal and Exact Tag-to-Wheel Match

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-07 |
| **Objective** | Preserve one version authority per project type: allow aggregate static-file bumps only for static projects, refuse dynamic/tag-derived projects before canonical reads or writes, and prove tag-derived releases against the built distribution before publication. |
| **Outcome** | Proposed a two-layer mutation preflight, deterministic human and JSON refusal contracts, byte-preservation regressions, exact Git-to-wheel comparisons, and a signed-workflow handoff. No implementation or CI run was observed. |
| **Verification** | `unverified` — this is a design captured from reviewed implementation plans. Treat it as a hypothesis until the criterion-specific tests and release CI pass. |
| **History** | [changelog](./release-version-verification-tag-wheel-exact-match.history) |

## When to Use

- One version utility supports both static projects and hatch-vcs/setuptools-scm projects, so removing mutation globally would break established static-project behavior.
- A dynamic-version project declares `version` in `[project].dynamic`, but a bump command can still read the current tag, report dry-run success, or write `VERSION`, `[project].version`, or `__version__`.
- A CLI-only check leaves direct `VersionManager.update()` callers unsafe, or a manager-only check happens after the CLI has already resolved the current tag and printed success-shaped output.
- JSON mode calls a human-oriented helper that prints `Would bump version` or `Version bumped` before the JSON status document.
- A version helper falls back from an unavailable Git tag to `importlib.metadata.version()`, allowing a stale editable install to impersonate the canonical source.
- Release verification compares only an `X.Y.Z` prefix, strips `.devN`, `+local`, or other suffixes, or merely checks whether two sources can be resolved.
- A release workflow builds a wheel but checks version metadata through the repository's editable development environment instead of installing the wheel it will publish.
- Tag creation requires signing credentials or another privileged mutation and must remain exclusively behind an explicitly dispatched workflow.
- Publication must fail before any PyPI write when the tag, requested release, and built artifact disagree.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms it.

### Quick Reference

```text
explicit signed-tag workflow -> authoritative vX.Y.Z tag -> build wheel
                                                     |-> read exact tag version
wheel -> disposable environment -> installed metadata|-> compare both to requested X.Y.Z
                                                     `-> publish only when both match exactly

static project bump -> preflight passes -> resolve current version -> update configured files
dynamic project bump -> preflight refuses -> signed-tag workflow (no reads or writes)
```

```bash
# Static project: retain the established aggregate file update behavior.
package-bump-version patch

# Dynamic project: returns nonzero before canonical lookup or mutation.
package-bump-version patch --dry-run
package-bump-version patch --json

# Release CI, after build and before publish.
TAG_VERSION="${TAG#v}"
VERIFY_ENV="build/version-verify"
WHEEL="$(find dist -maxdepth 1 -type f -name '*.whl' -print -quit)"
test -n "${WHEEL}" || { echo "No built wheel found" >&2; exit 1; }
uv venv "${VERIFY_ENV}"
uv pip install --python "${VERIFY_ENV}/bin/python" "${WHEEL}"
"${VERIFY_ENV}/bin/package-check-version-consistency" \
  --repo-root "${GITHUB_WORKSPACE}" \
  --expected-version "${TAG_VERSION}" \
  --verbose
```

### Detailed Steps

1. **Classify the project's version authority before doing version work.** Parse
   `pyproject.toml` structurally. When `[project].dynamic` contains `version`, static-file
   mutation is unsupported even if `VERSION` or `__version__` files happen to exist. When the
   declaration is absent (or no `pyproject.toml` exists), preserve the utility's established
   static-project behavior.

   Keep the detector broader than one backend when possible: the capability boundary is the
   dynamic declaration, while `[tool.hatch.version] source = "vcs"` is useful corroborating
   evidence for hatch-vcs repositories.

2. **Put the same preflight at the API and CLI boundaries.** The reusable manager owns a
   repository-neutral capability check, and its aggregate `update()` calls that check before
   parsing the requested version or touching any configured file. A narrower direct helper such
   as `update_pyproject_file()` may remain a safe no-op for dynamic projects, but aggregate update
   must reject rather than continue into secondary files.

```python
def ensure_update_supported(self) -> None:
    """Reject aggregate file updates for dynamically versioned projects."""
    if self.pyproject_file is None or not self.pyproject_file.exists():
        return

    if is_dynamic_version_project(self.pyproject_file.read_text()):
        raise ValueError(
            "static version-file updates are unsupported when "
            "[project].dynamic contains 'version'"
        )


def update(self, version: str, verbose: bool = True) -> None:
    """Update all configured version files for a static-version project."""
    self.ensure_update_supported()
    major, minor, patch = parse_version(version)
    # Existing static-project update sequence follows unchanged.
```

   The CLI repeats the preflight before canonical-version resolution. This is deliberate defense
   in depth: the CLI must not read a tag or report dry-run success for an unsupported operation,
   while direct callers must not bypass the invariant by invoking `update()` themselves.

3. **Make argument and output ordering explicit.** The safe sequence is:

   1. validate the requested bump part;
   2. construct the manager and run the dynamic-version preflight;
   3. resolve and parse the current version;
   4. calculate the next version;
   5. return dry-run output or perform the guarded aggregate update;
   6. run the post-update consistency check;
   7. report success.

   Catch both `OSError` (manifest unreadable) and `ValueError` (unsupported mutation) at the CLI
   boundary. Keep the manager's message generic; add repository-specific signed-release guidance
   only in the console layer.

```python
def report_bump_refusal(exc: OSError | ValueError) -> int:
    print(f"ERROR: version bump refused: {exc}", file=sys.stderr)
    print(
        "  This repository releases through its signed-tag workflow; "
        "see the release documentation.",
        file=sys.stderr,
    )
    return 1
```

   If the CLI supports JSON, pass an explicit `emit_human_output=False` flag into the shared bump
   helper. Emit exactly one status document on stdout after the helper returns, including on error;
   diagnostics and release guidance remain on stderr. Never infer output mode from global state.

```python
exit_code = bump_version(
    root,
    part=args.part,
    dry_run=args.dry_run,
    verbose=False,
    emit_human_output=False,
)
message = (
    "version bump refused"
    if exit_code != 0
    else ("dry run complete" if args.dry_run else "version bumped")
)
emit_json_status(exit_code, message=message, part=args.part, dry_run=args.dry_run)
```

4. **Separate authority, evidence, and proposal.** Give each value one role:

   - **Canonical authority:** the latest reachable release tag matching the project's strict `vX.Y.Z` contract.
   - **Requested version:** the exact version the release workflow intends to publish, normally `${TAG#v}`.
   - **Installed evidence:** the exact `importlib.metadata.version(<distribution-name>)` value from a newly installed wheel.
   - **Proposal:** the next semantic version computed locally from the canonical tag. It has no authority until the gated release workflow creates the signed tag.

5. **Fail closed when the tag is unavailable.** Do not let installed package metadata stand in for the canonical source. A missing tag usually means the checkout lacks tag history or the repository has not established release authority; either condition should stop version-sensitive work with a useful error.

```python
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _dist_version
from pathlib import Path
import sys

DIST_NAME = "Your-Distribution-Name"


def _version_from_metadata() -> str | None:
    """Return the exact installed distribution version, or None."""
    try:
        return _dist_version(DIST_NAME)
    except PackageNotFoundError:
        return None


def _get_canonical_version(repo_root: Path) -> str:
    """Return the authoritative version from a reachable vX.Y.Z tag."""
    version = _version_from_git_tag(repo_root)
    if version is None:
        print(
            "ERROR: could not determine the canonical version from a vX.Y.Z Git tag.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return version
```

6. **Compare the requested version independently and exactly.** Parse the requested input for shape, but do not normalize the observed installed value before comparing it. Exact string equality is intentional: `1.2.3.dev1` and `1.2.3+local` are not the requested release `1.2.3`.

```python
def check_version_consistency(
    repo_root: Path,
    requested_version: str,
    verbose: bool = False,
) -> int:
    """Require both the canonical tag and installed wheel to equal the request."""
    try:
        parse_version(requested_version)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    canonical = _version_from_git_tag(repo_root)
    installed = _version_from_metadata()
    errors: list[str] = []

    if canonical != requested_version:
        errors.append(
            f"canonical Git tag version is {canonical or '<not found>'}, "
            f"expected {requested_version}"
        )
    if installed != requested_version:
        errors.append(
            f"installed distribution version is {installed or '<not found>'}, "
            f"expected {requested_version}"
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if verbose:
        print(f"Canonical tag version: {canonical}")
        print(f"Installed distribution version: {installed}")
    return 0
```

   Require `--expected-version` on the consistency-check CLI. This makes the release request explicit and prevents a resolution-only check from declaring success merely because two unrelated values exist.

7. **Keep aggregate bumps static-project-only.** For a shared utility, do not remove working
   static-project mutation merely because one consumer migrated to hatch-vcs. Preserve the
   existing major/minor/patch calculation, dry-run behavior, write order, and post-write
   consistency check after the preflight succeeds. For a dynamic project, refuse every mode before
   `_get_canonical_version()` and before any write.

```python
def bump_version(
    repo_root: Path,
    part: str,
    dry_run: bool = False,
    verbose: bool = False,
    *,
    emit_human_output: bool = True,
) -> int:
    """Increment version files for a statically versioned project."""
    if part not in {"major", "minor", "patch"}:
        print(f"ERROR: invalid bump part: {part}", file=sys.stderr)
        return 1

    manager = VersionManager(repo_root=repo_root)
    try:
        manager.ensure_update_supported()
    except (OSError, ValueError) as exc:
        return report_bump_refusal(exc)

    current_str = _get_canonical_version(repo_root)
    current = parse_version(current_str)
    new_str = calculate_increment(current, part)

    if dry_run:
        if emit_human_output:
            print(f"Would bump version: {current_str} -> {new_str}")
        return 0

    try:
        manager.update(new_str, verbose=verbose)
    except (OSError, ValueError) as exc:
        return report_bump_refusal(exc)

    if check_version_consistency(repo_root, verbose=verbose) != 0:
        print("ERROR: post-bump consistency check failed", file=sys.stderr)
        return 1

    if emit_human_output:
        print(f"Version bumped: {current_str} -> {new_str}")
    return 0
```

   The second manager preflight closes the direct-API race between the CLI check and mutation. It
   must run before success reporting. It does not provide transactional rollback for static
   projects; existing static partial-write behavior is a separate contract.

```json
{
  "status": "error",
  "exit_code": 1,
  "message": "version bump refused",
  "part": "patch",
  "dry_run": true
}
```

8. **Keep tag mutation in one explicit workflow.** The refused command must not print manual `git tag` instructions that encourage operators to bypass key import, signing, branch, or dispatch controls. Direct operators to the existing release action that owns signed-tag creation.

9. **Verify the artifact that will be published.** After building, create a disposable environment under the repository's ignored build directory, install the discovered wheel into it, and invoke the checker binary from that environment. Do not invoke the checker through `uv run`, an editable install, or the source checkout at this gate.

```yaml
- name: Verify canonical and installed versions
  shell: bash
  env:
    TAG: ${{ needs.resolve-release.outputs.tag }}
  run: |
    set -euo pipefail
    TAG_VERSION="${TAG#v}"
    VERIFY_ENV="build/version-verify"
    WHEEL="$(find dist -maxdepth 1 -type f -name '*.whl' -print -quit)"
    if [ -z "${WHEEL}" ]; then
      echo "::error::No built wheel found for version verification"
      exit 1
    fi

    uv venv "${VERIFY_ENV}"
    uv pip install --python "${VERIFY_ENV}/bin/python" "${WHEEL}"
    "${VERIFY_ENV}/bin/package-check-version-consistency" \
      --repo-root "${GITHUB_WORKSPACE}" \
      --expected-version "${TAG_VERSION}" \
      --verbose
```

10. **Protect ordering and immutability with executable tests.** Cover the behavior, not internal calls:

    - aggregate manager update rejects a dynamic project before touching a seeded manifest,
      `VERSION`, or configured package `__init__.py`;
    - normal and `--dry-run` CLI invocations return nonzero for a dynamic project, emit no success
      stdout, provide the signed-release path on stderr, and never call canonical lookup;
    - `--json` and `--json --dry-run` return nonzero and produce one parseable error document on
      stdout without creating an absent `VERSION` file;
    - static-project JSON dry-run remains successful and produces one parseable status document,
      with no `Would bump version` prefix;
    - existing static/no-manifest aggregate-update tests remain green;
    - exact success when canonical and installed values both equal the request;
    - failure when either source is missing or differs;
    - failure for development/local installed versions such as `1.2.3.dev1` when `1.2.3` was requested;
    - byte-for-byte preservation of `VERSION`, `pyproject.toml`, package `__init__.py`, and any other sentinel file;
    - no filesystem entries created by a refused dynamic-project operation;
    - the installed-wheel verification step appears after build and before publish;
    - the verification command comes from `build/version-verify`, includes `--expected-version`, and fails when no wheel exists.

11. **Retain the source/build computation gate.** A pre-build check such as `TAG_VERSION == hatchling version` and the post-build installed-wheel check prove different things. Keep both: the first verifies VCS-derived build computation; the second verifies the actual artifact consumer before publication.

## Verified Workflow

_Not applicable._ This skill was captured from an implementation plan and is `unverified`: no code was applied, no criterion-specific test ran, and no release CI result was observed. The actionable methodology is under **Proposed Workflow** and must remain hypothesis-level until implementation and CI confirm it. This placeholder exists because `scripts/validate_plugins.py` currently requires the literal `## Verified Workflow` heading; it makes no verification claim.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | --------------- | --------------- | ---------------- |
| Use installed metadata as the canonical fallback | Returned `importlib.metadata.version()` when no release tag was reachable | A stale editable install or unrelated installed wheel can hide a shallow/tagless checkout and impersonate the source of truth | Fail closed when the authoritative tag is unavailable; installed metadata is independent evidence, never authority |
| Normalize installed metadata to `X.Y.Z` before comparison | Stripped `.devN`, `+local`, or compared only the release prefix | A stale/development build such as `1.2.3.dev1` passes a check requesting the final `1.2.3` artifact | Preserve the exact metadata string and compare it directly to the exact request |
| Apply aggregate update to every project type | Rewrote `VERSION`, `[project].version`, or package version constants after detecting that `version` is dynamic | Reintroduced competing authorities and could partially update secondary files | Reject aggregate mutation for dynamic projects before parsing or writing; retain the established path for static projects |
| Preflight only in the CLI | Rejected dynamic projects in the console entrypoint but left `VersionManager.update()` unchanged | Direct API callers could bypass the safety boundary and mutate configured files | Put a generic preflight in the manager and invoke it again in the CLI before canonical lookup |
| Preflight only in the manager | Relied on `update()` to reject the dynamic project | The CLI could resolve the current tag and report a successful dry run without ever calling `update()` | Run the CLI preflight before canonical resolution and every dry-run/success path |
| Treat `--dry-run` as automatically safe | Returned success before invoking the mutation layer | Unsupported dynamic projects received a false-success result even though the real operation could never be performed | Capability validation precedes dry-run branching |
| Reuse human output in JSON mode | Let the shared bump helper print `Would bump version` or `Version bumped` before emitting JSON | Stdout contained multiple formats and could not be parsed as one JSON document | Give JSON mode explicit stdout ownership with `emit_human_output=False`; keep diagnostics on stderr |
| Put repository workflow guidance in the manager exception | Named one project's release workflow in a reusable version utility | Coupled the library layer to one repository's operational policy | Keep the manager error repository-neutral and add signed-release guidance in the console layer |
| Verify through the editable development environment | Ran the consistency checker with `uv run` after building a wheel | The check can inspect repository metadata rather than the wheel that will be uploaded, so packaging defects escape | Install the wheel into a fresh disposable environment and invoke its installed console script |
| Check the wheel after publication | Put artifact verification after the PyPI action | The irreversible external write already happened before the gate could fail | Order build -> isolated install -> exact verification -> publish, and freeze that ordering in a workflow test |
| Print manual tag commands from the preview CLI | Told operators to copy the proposal into `git tag` commands | Bypasses the established explicit dispatch, signing-key import, and mutation controls | Point to the one authoritative signed-tag workflow instead of teaching a parallel release path |

## Results & Parameters

### Authority and Evidence Contract

| Value | Source | Comparison rule | Failure behavior |
| ------- | ------- | ------- | ------- |
| Canonical version | Reachable strict `vX.Y.Z` Git tag | Strip only the leading tag marker defined by the repository, then require exact equality to the request | Missing or mismatched tag fails closed |
| Requested version | Explicit CLI input / release tag with `v` removed | Validate the required semantic-version shape; retain the exact requested string | Invalid input returns nonzero before publication |
| Installed version | `importlib.metadata.version(<distribution-name>)` inside the wheel-only environment | Preserve `.devN`, `+local`, and other suffixes; exact equality only | Missing or mismatched metadata fails closed |
| Static-project next version | Major/minor/patch increment of the configured canonical source | Aggregate mutation is permitted only after the preflight passes | Existing static update and consistency behavior remains unchanged |
| Dynamic-project release version | Signed `vX.Y.Z` tag created by the repository's release workflow | The local static-file bump command refuses before resolving or calculating it | No files or tags change; CLI returns nonzero and points to release documentation |

### Mutation Boundary Parameters

| Parameter | Recommended value | Purpose |
| ------- | ------- | ------- |
| Capability signal | `"version" in project.get("dynamic", [])` | Reject static-file aggregation based on the standards-level declaration |
| Manager exception | `ValueError` with repository-neutral wording | Protect direct API callers without coupling the library to operational policy |
| Manifest read failure | `OSError`, reported as a refusal | Fail closed when capability cannot be determined reliably |
| CLI preflight position | after bump-part validation, before canonical lookup | Prevent unsupported dry-run and structured invocations from reporting success |
| Aggregate preflight position | first statement in `update()` | Prevent parsing and every configured write |
| JSON human-output control | keyword-only `emit_human_output=False` | Give structured mode sole ownership of stdout |
| Dynamic refusal rollback | none | The operation fails before mutation, so byte-preservation tests replace rollback logic |

### Release Gate Parameters

| Parameter | Recommended value | Purpose |
| ------- | ------- | ------- |
| Verification environment | `build/version-verify` | Disposable, repository-local, ignored generated state |
| Wheel discovery | `find dist -maxdepth 1 -type f -name '*.whl' -print -quit` plus non-empty guard | Select the built wheel and fail clearly when build produced none |
| Checker invocation | `${VERIFY_ENV}/bin/<check-command>` | Proves the executable and metadata come from the installed artifact |
| Required CLI input | `--expected-version "${TAG#v}"` | Makes the release request explicit |
| Workflow ordering | after build, before publish | Prevents irreversible publication on mismatch |
| Release rollback/data migration | none | Tag verification and disposable build content do not migrate persistent data |

### Proposed Acceptance Matrix

| Project mode | Invocation | Canonical lookup | Files written | Stdout | Exit |
| ------- | ------- | ------- | ------- | ------- | ------- |
| static | normal | yes | existing configured update | human success | `0` |
| static | `--json --dry-run` | yes | none | one success JSON document | `0` |
| dynamic | normal or `--dry-run` | no | none | empty | nonzero |
| dynamic | `--json` or `--json --dry-run` | no | none | one error JSON document | nonzero |
| dynamic | direct aggregate `update()` | not applicable | none | not applicable | raises before mutation |

Seed an existing `VERSION`, the dynamic manifest, and an auto-detected package
`__init__.py` with sentinel bytes. For each refusal case, assert byte-for-byte equality; for the
absent-`VERSION` JSON case, assert the file was not created. Monkeypatch canonical lookup to fail
the test if called. Parse all structured stdout with one `json.loads()` call.

### Exact Release Evidence Matrix

| Canonical | Installed | Requested | Expected |
| ------- | ------- | ------- | ------- |
| `1.2.3` | `1.2.3` | `1.2.3` | pass |
| `1.2.2` | `1.2.3` | `1.2.3` | fail: tag mismatch |
| `1.2.3` | `1.2.2` | `1.2.3` | fail: artifact mismatch |
| `1.2.3` | `1.2.3.dev1` | `1.2.3` | fail: exact metadata mismatch |
| `1.2.3` | `1.2.3+local` | `1.2.3` | fail: exact metadata mismatch |
| missing | `1.2.3` | `1.2.3` | fail: authority unavailable |
| `1.2.3` | missing | `1.2.3` | fail: artifact metadata unavailable |

### Verification Status

- **Observed successes:** none; both source sessions were implementation plans rather than executed changes.
- **Observed failures:** none executed. The Failed Attempts table records design hazards identified during review, not runtime experiments.
- **Pending evidence:** criterion-specific manager/CLI tests, static behavior regressions, Ruff and mypy on modified Python files, workflow regression tests, and a green release CI run that builds and installs the wheel before publication.
- **Originating context:** ProjectHephaestus plans first proposed compute-only tag-driven behavior, then refined the shared CLI contract to refuse dynamic projects while retaining static mutation. Project-specific command and workflow names are examples; the capability, output-channel, and authority/evidence boundaries apply to mixed-mode version tooling generally.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Reviewed implementation plans, 2026-08-05 through 2026-08-07 | Unverified proposal: no code, tests, or release CI run were observed. The refined plan adds dynamic-project refusal before canonical lookup/write, single-document JSON output, sentinel preservation tests, signed-workflow guidance, and the pre-publication wheel gate. |

## Related Skills

- [python-packaging-pyproject-editable-install](./python-packaging-pyproject-editable-install.md) — broad hatch-vcs migration, distribution-name lookup, editable install, and packaging setup.
- [testing-local-wheel-install-content-test](./testing-local-wheel-install-content-test.md) — locally proving wheel contents, entry points, and optional-import boundaries from an installed artifact.
- [gha-release-package-workflow-patterns](./gha-release-package-workflow-patterns.md) — broader GitHub Actions packaging and publishing workflow patterns.
- [tooling-cli-batch-terminal-outcome-contracts](./tooling-cli-batch-terminal-outcome-contracts.md) — broader terminal-outcome and single-document JSON CLI contracts.
