---
name: container-ci-uid-permissions-rootless
description: "Fix rootless container CI permissions and build-layout failures. Use for subuid-owned artifacts, Dockerfile ARG scope, bind-mounted workspace writes, multi-stage or OCI builds, uv/pixi isolation, compose masking, external-image COPY failures, dead container test steps, hosted-runner container jobs whose permission-boundary tests fail, missing supplementary groups under a numeric USER, git dubious-ownership refusals on the mounted checkout, or a hardcoded system interpreter path that the slim base ships elsewhere."
category: ci-cd
date: 2026-07-18
version: "2.1.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
tags:
  - podman
  - rootless
  - uid-mapping
  - permissions
  - container-ci
  - multistage
  - oci
  - uv
  - pixi
  - bind-mount
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/container-ci-uid-permissions-rootless.history"
history-cleanup-date: "2026-09-20"
---

# Container CI UID Permissions and Rootless Patterns

## Overview

Rootless container failures usually cross an ownership or mount boundary: host and container UIDs
do not mean the same thing, build arguments are stage-scoped, bind mounts hide image content, or a
tool installs into a root-only path before `USER` changes. Identify which side creates and consumes
each artifact, then make that boundary explicit and narrow.

The consolidated patterns have CI evidence, and the uv/container gotchas were reproduced with real
Podman builds. Case links and platform detail are in
[container-ci-uid-permissions-rootless.notes.md](container-ci-uid-permissions-rootless.notes.md),
with the full prior version in
[container-ci-uid-permissions-rootless.history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/container-ci-uid-permissions-rootless.history).

## When to Use

- Host commands cannot write `build/` or `dist/` after rootless Podman ran.
- Numeric ownership shows a subuid such as `100000+` or `524288`.
- A host-side recipe cannot find a tool installed only inside the container.
- `COPY --chown` receives an empty user/group because `ARG` was declared before another `FROM`.
- A bind-mounted workspace is unwritable by the runtime UID.
- A compose provider ignores Podman-specific user-namespace options.
- A multi-stage image needs build/runtime dependency separation.
- OCI output, architecture emulation, or cached-image extraction has the wrong artifact form.
- uv-managed Python is installed under `/root`, or a workspace bind mount hides `.venv`.
- Podman rejects `COPY --from=<tag>@<digest>` or the digest does not exist.
- CI references a test directory that is absent from the repository.
- A hosted-runner job moved into a `container:` image passes setup but fails
  permission-boundary, group-assignment, or interpreter-path tests that pass on the bare runner.

## Verified Workflow

### 1. Map artifact ownership and execution side

```bash
id
podman unshare cat /proc/self/uid_map
ls -ldn build dist .venv /opt/venv 2>/dev/null
podman compose version
```

For each recipe, record whether it executes on the host or in the container and which side created
its inputs/outputs. A host consumer of subuid-owned output needs an explicit export/reclaim step;
commands requiring container-only tools should run through the shared container wrapper.

### 2. Keep creation and consumption on one side when possible

```make
package:
    $(CONTAINER_RUN) build-package --output /workspace/dist
```

If the host must pre-create a directory written by arbitrary rootless-mapped users, grant only that
dedicated exchange directory the required access. Avoid recursive chmod across mixed-ownership
trees. For stale output from another mapping, use a rootless namespace-aware reclaim command, then
recreate the directory under the intended owner.

### 3. Scope Dockerfile arguments per stage

`ARG` values declared before `FROM` are available to image selection but must be re-declared in
each stage that uses them:

```dockerfile
ARG UID=1000
ARG GID=1000

FROM build-base AS builder
ARG UID
ARG GID
RUN groupadd --gid "${GID}" app && useradd --uid "${UID}" --gid "${GID}" app

FROM runtime-base AS runtime
ARG UID
ARG GID
COPY --from=builder --chown=${UID}:${GID} /out /app
```

Build with explicit values and inspect numeric ownership inside the resulting image.

### 4. Make runtime home/workspace writable without broadening everything

Create the runtime user and owned home/work directories during build. If a mounted home is not
writable, set a fallback to a dedicated writable path in the entry point. Do not apply recursive
mode `700` to caches/interpreters that another mapped UID must traverse.

Compose portability is empirical: inspect the active provider and rendered configuration. Do not
assume Docker Compose and `podman-compose` honor the same user namespace keys.

### 5. Mirror the bare-runner identity and system paths in hosted container jobs

A hosted runner executes jobs as a fixed user with a uid, a gid, and a supplementary-group set,
and the mounted workspace keeps the host uid as its owner. A container image that replaces such a
runner must reproduce that surface, or identity-sensitive behavior changes:

- Run the image as the same uid and gid the runner uses. Permission-refusal and authority tests
  encode refusals that root bypasses; under a root container, fourteen such cases failed across
  five modules that pass as the runner identity.
- Name the user in `USER`. The container runtime loads supplementary groups from `/etc/group` only
  for a named user; a numeric `USER uid:gid` gives the process the primary group alone, and
  group-assignment fixtures then find no assignable gid. Create missing group names before
  `usermod -aG`, because slim bases do not ship every runner group name.
- Bake `git config --system --add safe.directory '*'` into the image. The mounted checkout keeps
  the host uid as its owner, so git in the container rejects it as a dubious owner and every git
  step fails.
- Link each system interpreter path that code executes as a contract (for example
  `/usr/bin/python3`) to the path where the base image ships its interpreter
  (`/usr/local/bin/python3`). Trust-boundary scripts hardcode the system path on purpose; repair
  the image, not the contract.

Validate one variable per hosted run: change the image or its pin, rerun, and read the new failure
set. When the test harness reports only the final assertion, add a temporary instrument to the
failing test that prints the subprocess's stderr, event log, and tree; the decisive evidence was
one bash line naming the missing file.

### 6. Separate build and runtime stages

Copy runtime libraries and executable entry points, not only site-packages:

```dockerfile
FROM build-base AS builder
RUN python -m venv /opt/venv && /opt/venv/bin/pip install .

FROM runtime-base
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
```

Verify imports and console scripts in the final stage. Image-size reduction is secondary to a
complete runtime; removing `bin/` silently drops entry points.

### 7. Keep managed Python and venv outside masked/root-only paths

```dockerfile
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
RUN uv sync --frozen && chmod -R a+rX /opt/uv-python /opt/venv
USER app
```

Putting uv's Python under `/root/.local/share/uv` makes the interpreter unreachable after switching
users. Keeping the project venv under `/workspace/.venv` lets a development bind mount over
`/workspace` hide it. `/opt` avoids both failure modes.

### 8. Alias external image sources and verify digests

```dockerfile
FROM ghcr.io/astral-sh/uv:<tag>@sha256:<verified-digest> AS uv_source
FROM runtime-base
COPY --from=uv_source /uv /uvx /bin/
```

Some Podman/buildah versions reject tag-plus-digest directly in `COPY --from`. A named stage makes
the reference unambiguous. Resolve the digest before editing the Dockerfile; `manifest unknown` is
not a permissions problem.

### 9. Validate OCI and cache artifact forms

Install emulation before creating the multi-architecture builder. OCI layout output is a directory,
not automatically a tarball; archive it only at the consumer boundary. For local forensic replay,
verify the cached file type before loading or extracting it. Keep dependency-manager caches in
dedicated volumes; do not mount over tool installation directories.

### 10. Remove or implement dead CI steps honestly

If a workflow runs tests from a nonexistent path, determine whether tests were deleted, renamed,
or never implemented. Point to a real suite, implement the missing contract, or remove the dead step
with a linked tracking issue. Do not leave a green no-op that suggests coverage exists.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Run container-tool recipe on host | Tool and mapped ownership exist only in container | Use the shared container wrapper |
| 2 | Recursively chmod build tree | Traverses host-owned siblings and broadens access | Change only owned exchange artifacts |
| 3 | Declare UID/GID ARG only before first FROM | Later stages see empty values | Re-declare ARG per consuming stage |
| 4 | Depend on provider-specific compose userns option | Alternate provider ignores it | Inspect provider and use explicit UID/writable paths |
| 5 | Copy only site-packages from builder | Console entry points disappear | Copy complete venv or both packages and bin |
| 6 | Install uv Python under `/root` | Non-root user cannot traverse it | Use shared readable install directory |
| 7 | Bake venv into bind-mounted workspace | Mount masks the venv | Put venv outside workspace |
| 8 | Use tag-plus-digest directly in COPY source | Podman cannot resolve stage/image expression | Alias verified image as named stage |
| 9 | Treat OCI directory as tar | Consumer uses wrong extraction/load operation | Inspect artifact type and archive explicitly |
| 10 | Keep nonexistent test step | Green/no-op misrepresents coverage | Implement, repoint, or remove with tracking |
| 11 | Run the hosted container job as root | Permission-refusal tests fail: root bypasses the encoded refusals | Run as the bare-runner uid/gid |
| 12 | Set a numeric `USER uid:gid` | Supplementary groups never load; group fixtures find no assignable gid | Name the user so `/etc/group` memberships load |
| 13 | Assume the slim base ships `/usr/bin/python3` | Preflight dies with "No such file or directory" before the job body | Symlink the interpreter to the contract path |
| 14 | Diagnose from the harness's final assertion | The subprocess's stderr never reaches the report | Instrument the test to print job stderr, events, and tree |

## Results & Parameters

- Rootless diagnosis: numeric ownership plus `podman unshare` mapping.
- Docker build parameters: explicit `UID`/`GID`, re-declared in every consuming stage.
- uv paths: `UV_PYTHON_INSTALL_DIR=/opt/uv-python` and
  `UV_PROJECT_ENVIRONMENT=/opt/venv` in the reproduced migrations.
- Final image verification: runtime imports and console entry points as the non-root user.
- Source multi-stage case reduced image size by 246 MB (about 30%) while retaining runtime checks.
- Runner-parity case: a one-variable-per-run validation ladder over six hosted runs took a
  container test job from zero passing shards to a fully green suite, and the removed
  package-install step cut per-shard wall time by about thirty percent.
- Acceptance: build, run, bind-mount development path, artifact ownership, multi-arch/OCI consumer,
  and CI all pass on the supported container engine.

## Evidence Boundary

The cases were verified across specific Podman/buildah/compose versions and repositories. Recheck
provider support, UID maps, image digests, and mount paths in the target environment rather than
treating numeric examples as universal.
