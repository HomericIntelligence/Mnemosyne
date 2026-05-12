---
name: podman-compose-mount-clone-aware
description: "Make `podman compose up` clone-aware so it recreates the dev container when bind-mounted to a stale clone. Use when: (1) you maintain multiple checkouts of the same repo, (2) `restart` doesn't pick up host edits, (3) container shows correct status but stale code."
category: tooling
date: 2026-05-11
version: 1.0.0
verification: verified-ci
user-invocable: false
---

# Skill: Podman Compose Mount Clone-Aware

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-11 |
| **Objective** | Prevent stale bind-mount bugs when the same repo is cloned to multiple paths and shares a single dev container name |
| **Outcome** | ✅ Verified — `just podman-up` correctly recreates the container when invoked from a different clone |
| **Verification** | verified-ci (shipped in HomericIntelligence/ProjectOdyssey PR #5389) |
| **Category** | tooling |

A dev container's bind mount source path is fixed at *container creation time*. If you have two clones of the same repo (e.g. `~/ProjectOdyssey` and `~/Projects/ProjectOdyssey`) and the container was created from clone A, then `podman compose restart` and even plain `podman compose up` from clone B will keep using clone A's path as the mount source. The container reports "Up" and "healthy" while silently serving stale code.

## When to Use

Invoke this skill when any of the following symptoms appear:

- `just <recipe>` reports "Unknown mode", "command not found", or similar — but the host justfile clearly defines the recipe. The container is reading an *older* justfile from a different clone.
- Edits to source files on the host don't take effect inside the container even after `podman compose restart`.
- `podman inspect <container> --format '{{range .Mounts}}{{.Source}}{{end}}'` shows a different source than `pwd`.
- The container is "Up" and recently restarted, but behaves like it's running an older revision of the code.
- You maintain multiple working copies of the same repo and share a single dev container name across them.

Do NOT use this skill for:

- Single-clone setups (no mount-aliasing problem exists).
- Cases where the container is genuinely broken — first verify the mount source mismatch with `podman inspect`.

## Verified Workflow

### Quick Reference

```bash
# Diagnose: what is currently mounted?
podman inspect projectodyssey-dev-1 \
  --format '{{range .Mounts}}{{if eq .Destination "/workspace"}}{{.Source}}{{end}}{{end}}'

# Correct fix for switching clones:
podman compose down       # from the OLD clone's directory
cd /path/to/new/clone
podman compose up -d dev  # from the NEW clone's directory
```

### Clone-Aware `podman-up` Justfile Recipe

The verified fix is to make the `podman-up` recipe self-check the existing container's mount source and recreate it when it disagrees with `pwd`:

```just
podman-up:
    #!/usr/bin/env bash
    set -euo pipefail
    EXPECTED="{{repo_root}}"
    EXISTING=$(podman inspect projectodyssey-{{podman_service}}-1 \
        --format '{{{{range .Mounts}}{{{{if eq .Destination "/workspace"}}{{{{.Source}}{{{{end}}{{{{end}}' 2>/dev/null || echo "")
    if [ -n "$EXISTING" ] && [ "$EXISTING" != "$EXPECTED" ]; then
        echo "⚠️  Container exists with workspace mount '$EXISTING'"
        echo "    but this invocation is from '$EXPECTED'."
        echo "    Recreating container against the current clone..."
        podman compose down
    fi
    podman compose up -d {{podman_service}}
```

### Footgun: Go-Template Escaping Inside `just`

`just` uses `{{ ... }}` as its own template delimiter. When you embed a Go-template (used by `podman inspect --format`) inside a justfile recipe, **every** Go-template `{{` and `}}` must be doubled to `{{{{` and `}}}}`.

Compare:

- Go-template (works at the shell): `{{range .Mounts}}{{.Source}}{{end}}`
- Inside a justfile: `{{{{range .Mounts}}{{{{.Source}}{{{{end}}`

If you forget to double-escape, `just` will try to interpret `range`, `.Mounts`, etc. as just-template expressions and blow up with a parse error — or worse, silently produce empty output that makes the check look like "no existing container" and skip the recreate step.

### Workflow Steps

1. **Detect the mismatch.** Add the inspect-and-compare block above to your `podman-up` recipe (or run it manually on demand).
2. **Tear down on mismatch.** `podman compose down` from the current directory will stop *and remove* the container whose name matches the compose project — even though its mount points at a different clone, the container is named off the compose project, not the path.
3. **Bring it back up from the new clone.** `podman compose up -d <service>` creates a fresh container whose bind mount resolves to `pwd`.
4. **Verify.** Re-run the `podman inspect` command from the Quick Reference. The source should now match the current clone.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Restart in place | `podman compose restart` from the new clone | Restart re-runs the existing container's entrypoint; it does NOT re-evaluate the compose file's bind-mount paths. The old clone's path stays mounted. | `restart` is fundamentally wrong for switching mount sources — it never re-resolves paths. Always `down` + `up`. |
| Compose up without down | `podman compose up -d` from the new clone, expecting it to recreate the container | `compose up` sees an existing container with the same project name and leaves it alone. It does not detect that the bind-mount source on disk has moved. | An existing container with the project name shadows the new mount config. You must explicitly `down` first. |
| Mount both clones | Added a second bind mount so the container saw both clones at once | Two `/workspace*` mounts create a dual-source-of-truth: recipes, IDE indexers, and caches each pick a different canonical path and behavior diverges. | Don't paper over the aliasing problem with more mounts — pick one and recreate when it changes. |
| Hard-coded pre-flight | `[[ "$PWD" == "$EXPECTED_MOUNT" ]]` with a baked-in expected path | Only works when the mount path is known up front; breaks immediately when a developer adds a third clone or moves one. | Discover the actual mount via `podman inspect` instead of hard-coding it — the inspect-based check works for any number of clones. |

## Results & Parameters

**Shipped in:** [HomericIntelligence/ProjectOdyssey PR #5389](https://github.com/HomericIntelligence/ProjectOdyssey/pull/5389)

**Verification procedure:**

1. Clone the repo to two locations (e.g. `~/ProjectOdyssey` and `~/Projects/ProjectOdyssey`).
2. From clone A, run `just podman-up`. Container is created with clone A as the `/workspace` mount.
3. `cd` into clone B and run `just podman-up` again.
4. Recipe detects mismatch, prints the warning, runs `podman compose down`, then `up -d`.
5. `podman inspect` confirms the mount source is now clone B.
6. Repeat in the opposite direction.

**Parameters / assumptions:**

- Compose project name and container suffix (`projectodyssey-dev-1`) must match your compose configuration. Adjust to your project.
- The bind-mount destination inside the container is `/workspace`. If yours differs, update the `eq .Destination "/workspace"` predicate.
- `{{repo_root}}` is a just builtin that resolves to the directory containing the justfile — i.e. the clone you're invoking from. This is what makes the recipe clone-aware without hard-coding paths.
- Assumes a single shared compose project name across clones. If each clone uses a distinct `COMPOSE_PROJECT_NAME`, the mount-aliasing problem doesn't exist and this skill doesn't apply.
