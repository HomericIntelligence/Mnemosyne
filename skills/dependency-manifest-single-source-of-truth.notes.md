# Dependency Manifest: Single Source of Truth — Notes

## Artifact runtime floor vs repository toolchain floor (v1.3.0)

### Evidence shape

- A portable artifact (an npm package and a portable archive) carries helper scripts that
  run on the consumer's interpreter.
- The repository toolchain pinned Python 3.14.8, and the artifact's packaged runtime floor
  reused that pin.
- The release runner used the documented host floor, Python 3.12.3.
- The staging helper stopped before packaging:
  `requires Python 3.14.8 or newer. This interpreter is 3.12.3.`
- The source already parsed at the 3.12 syntax level, and the README already documented
  Python 3.12 or newer for the packaged helpers.

### Fix

- Set the packaged runtime floor to `(3, 12, 3)`.
- Keep the repository toolchain floor at its pinned patch release.
- Change the drift test to pin the runtime floor and assert it is at or below the
  toolchain floor.
- Change the packaged-floor test to compare the archive floor with the source runtime
  floor, not with `pyproject.toml`.
- Stage the artifact with the runtime-floor interpreter, and run every packaged helper
  with `--help` to prove imports.

### Verification

- The focused test suite passed on the toolchain interpreter (251 tests and 41 subtests).
- The staging helper produced the package on Python 3.12.14.
- Every packaged helper ran `--help` on Python 3.12.14 with no `SyntaxError` or
  `ImportError`.
- The next release run passed the staging step and published the npm package with
  provenance.

### Failed attempt

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Apply "highest floor wins" to every interpreter floor | Raised the artifact runtime floor to the toolchain pin | The release job on the documented host floor failed at the staging helper | Scope the floor rule: the artifact runtime floor is a consumer contract, not a manifest to unify |

Do not copy project names, paths, hostnames, issue IDs, or internal versions into the main
entry. Interpreter versions are public language versions and are necessary to the decision.
