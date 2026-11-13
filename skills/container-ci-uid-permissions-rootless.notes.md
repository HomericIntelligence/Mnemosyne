# Container CI UID Permissions and Rootless Patterns — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Rootless build/dist ownership boundary | [ProjectOdyssey issue #5413](https://github.com/HomericIntelligence/Odyssey/issues/5413) | `verified-ci`: related PRs #5422/#5424/#5425/#5426 merged green | Retained execution-side and narrow exchange-directory rules |
| Multi-stage image reduction | [ProjectScylla PR #649](https://github.com/HomericIntelligence/ProjectScylla/pull/649) | `verified-ci`: 246 MB/30% reduction and runtime checks | Retained complete-venv/entry-point verification |
| Dead container test step | [ProjectScylla PR #1157](https://github.com/HomericIntelligence/ProjectScylla/pull/1157) | `verified-ci`: 3,185 tests in recorded suite | Retained implement/repoint/remove-with-tracking decision |
| uv-managed Python under root-only home | [immutable source case](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/container-ci-uid-permissions-rootless.md) | Reproduced with real Podman build | Retained `/opt/uv-python` shared path |
| Workspace bind mount masks baked venv | [immutable source case](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/container-ci-uid-permissions-rootless.md) | Reproduced with real Podman/compose flow | Retained `/opt/venv` path |
| Podman external image COPY parsing | [immutable source case](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/container-ci-uid-permissions-rootless.md) | Reproduced; correct digest resolved | Retained named-stage and digest-verification rule |
| Hosted container-job runner parity | Private repository CI validation ladder (six hosted runs, no public identifier) | `verified-ci`: final run green with 8,903 cases, 0 failures; per-shard wall time dropped about 30% | Retained mirror-the-runner-identity, named-USER, safe.directory, and interpreter-path rules |

### Runner-parity validation ladder (one variable per run)

| Run | Image delta | Observed failure class |
| --- | --- | --- |
| 1 | Base image, root user | Private-package pull blocked (permissions scope), then git dubious ownership on the mounted checkout |
| 2 | System `safe.directory` baked | Fourteen permission-boundary failures: root bypasses the encoded refusals |
| 3 | uid/gid 1001 (numeric `USER`) | Group fixtures fail: numeric `USER` skips `/etc/group` supplementary loading |
| 4 | Supplementary groups created | Same four failures: membership loads only for a named user |
| 5 | Named `USER` | Job-running cases fail: rendered preflight executes `/usr/bin/python3`, absent in the slim base |
| 6 | `/usr/bin/python3` symlink | Green end to end |

The decisive evidence came from a temporary in-test instrument that printed the subprocess's
stderr (`job.sh: line 22: /usr/bin/python3: No such file or directory`), the event log (empty),
and the tree (destination never created) — none of which reached the test report.

## Boundary worksheet

| Artifact/path | Creator | Consumer | UID namespace | Mount masking risk | Export/reclaim |
| --- | --- | --- | --- | --- | --- |
| Build directory | Fill per repo | Fill per repo | Host or rootless map | Workspace mount | Explicit narrow step |
| Managed Python | Image build root | Runtime non-root | Container | Root home permissions | `/opt/uv-python` |
| Project venv | Image build | Dev compose service | Container | `/workspace` bind | `/opt/venv` |
| OCI output | Builder | Cache/publisher/local loader | Host/container boundary | Directory vs archive | Validate artifact type |

## Evidence boundary

All cases are environment-specific despite CI/reproduction evidence. Re-resolve external digests
and re-check engine/provider support, UID maps, and mount paths on the target runners.
