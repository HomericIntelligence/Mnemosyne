# Notes: Bounded Startup Release Check

Supporting evidence for [cli-startup-release-check.md](cli-startup-release-check.md).
The main entry gives the rules. This file gives the discovery evidence and the
limits.

## Provenance

- Source: a session that recovered requirements for a startup release check in a
  Python shared-utilities package with many console scripts.
- Mode: requirements recovery. Read-only inspection of one clean checkout.
- The feature was not implemented. There is no runtime evidence. The main entry
  is marked `verification: unverified` for this reason.

## Discovery Evidence (generalized)

The following observations gave the constraints in the main entry:

- The installed version comes from distribution metadata for the published
  distribution name. That name is not the import name. The lookup returns a
  sentinel such as `unknown` when the distribution is not installed.
- No release lookup, update notice, or startup check existed in the package
  itself. The only update-check switch in the tree disabled the update check of
  an external bundled tool. That switch did not apply to the package.
- Release-time verification compared a Git tag with the installed artifact. It
  did not do a runtime release lookup. It was not a reusable mechanism.
- The package has an optional extra. Some console scripts are base-importable
  shims that load the extra only when it is present. A check in the shared shim
  path reaches every command. The optional-extra rule of the recommendation
  agrees with this structure.

## Test Design Notes

- Inject the release read. Use a fixture that returns a controlled release
  document. Do not use the live release service in unit or integration tests.
- Use an isolated installation to test the installed side. Resolve the
  executable through `PATH` to show that the notice describes the running
  installation, not the checkout.
- Call the shared startup helper two times in one process and assert one
  release read and one notice.
- Import the library package and assert zero release reads and empty stderr.
- Assert stdout bytes for a JSON command. Assert that the notice is on stderr.

## Limits

- The exact release source and the exact timeout value are decisions for each
  repository. The main entry does not mandate them.
- The evidence did not test an editable installation. The expected result
  follows from version ordering, not from a measurement.
- A package with one entry point does not need a shared shim. The same rules
  apply to the single entry path.