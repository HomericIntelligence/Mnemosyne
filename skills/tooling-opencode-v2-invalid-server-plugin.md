---
name: tooling-opencode-v2-invalid-server-plugin
description: "Diagnose and resolve the OpenCode V2 server plugin error `Plugin must export a default definition with an id and an effect or setup function`. Use when: (1) a plugin shows `Server plugin error` with `Runtime: server` and a reference `err_*`, (2) a V1-era server plugin must work in OpenCode V2, (3) you must choose between removal, an upstream V2 port, or a replacement, (4) the newest published npm package has a V1 shape but the upstream repository can have an unreleased V2 port, (5) a Git-installed plugin loads without an error but has no effect."
category: tooling
date: 2026-10-13
version: "1.1.0"
user-invocable: false
tags: [opencode, plugin, server, api-migration, package-compatibility]
---

# OpenCode V2 Invalid Server Plugin Module

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-13 |
| **Objective** | Diagnose and resolve an OpenCode V2 server plugin that fails to load with `Plugin must export a default definition with an id and an effect or setup function`. |
| **Outcome** | Successful. Verified against OpenCode v2.0.26 and the published package that caused the failure. A second case on OpenCode v2.0.27 used direct payload installation from an immutable upstream tag. |

## When to Use

- The client reports `Server plugin error` with `Runtime: server`, status `failed`, and a
  reference `err_*`.
- A plugin entry in `plugins` of an `opencode.json(c)` configuration causes the failure.
  This config owns server plugins; `cli.json` owns TUI plugins.
- You evaluate a community server plugin that can be V1-era before you add it to a V2
  configuration.
- The newest published npm release has a V1 shape. You must find whether the upstream
  repository has a newer V2-compatible module, for example on the default branch or at
  a newer tag.
- A plugin that a Git package specification installed loads with no
  `failed to load plugin` entry in the log, but its documented effect is absent.
- The plugin function is static payload delivery, for example a copy of a skill corpus
  into a harness directory.

## Verified Workflow

### Quick Reference

```bash
# 1. Find the recorded cause for the reported reference. Do not infer the cause.
grep "err_<reference>" ~/.local/share/opencode/log/opencode.log   # role=server

# 2. Inspect the cached package that the loader rejected
PKG=~/.cache/opencode/npm/<name>@latest/*/node_modules/<name>
grep -n '"version"' "$PKG/package.json" | head -1
tail -c 800 "$PKG"/dist/*.js          # last export block shows the default definition

# 3. Look for an unreleased V2 port in the upstream repository
git ls-remote --tags <repo-url> | sort -V | tail -3   # newest release tags
# Compare the default-export shape at the newest tag with the cached package.

# 4. When the plugin only delivers a static payload, install the payload directly
git clone --depth 1 --branch <tag> <repo-url> <tmp>
cp -r <tmp>/<payload> ~/.config/opencode/skills/<namespace>/
```

V2 server plugins require a default definition with an `id` and an `effect` or `setup`
function, for example `Plugin.define({ id, setup(context) })` from `@opencode/plugin`.
A V1-era server plugin exports a definition of the form
`{ id, server: async (input, options) => hooks }`. The loader fails schema validation
of the default export at module load time, so the failure occurs before any plugin
code runs and repeats at every load cycle with a new reference.

A Git package specification installation can succeed at module load time but have no
effect. A publish workflow can generate the package payload, for example a bundled
skills directory, and the Git tag does not contain that payload. A plugin that catches
the resulting error and writes it to the console leaves no failure entry in the
server log. Inspect the cached package content under `~/.cache/opencode/npm/` when an
error-free load has no effect.

### Suggested Approach

1. Match the reference from the dialog to the server log entry. The entry records
   `level=WARN ... message="failed to load plugin" ... ref=err_* role=server` and a
   `cause` string. If the server log is not accessible, ask for the matching entry.
2. Read the cause literally. `SchemaError(Missing key at ["default"]["effect"] ...`
   `["default"]["setup"])` names a module-shape problem, not a configuration problem.
   Do not rewrite `plugins` syntax to fix this error.
3. Confirm the module shape with the Quick Reference commands. Check the newest
   published version with `npm view <name> versions` if the cached version is not
   current. A V1 shape in the newest published release means no published V2 port.
   Before you conclude that no V2 port exists, check the upstream default branch and
   the newest release tag. The repository can contain an unreleased V2 port.
4. Select the remediation:
   - Remove the plugin from `plugins` in the applicable `opencode.json(c)` when the
     function is not required.
   - Use a V2-compatible replacement plugin when one provides the function.
   - When the function is static payload delivery, install the payload directly from
     an immutable tag or commit. Remove the dead plugin entry from the configuration.
     Verify that the harness discovers the payload.
   - When the function is unique, request an upstream port to `@opencode/plugin`.
     OpenCode V2 does not run V1 plugin implementations.
5. Restart the service to apply the change: `opencode service restart`. Deleting the
   stale cache directory `~/.cache/opencode/npm/<name>@latest/` prevents a reinstall
   attempt on restart.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | The direct approach was successful. | N/A | Bind the diagnosis to the logged reference before you inspect the package. |
| Install an already-configured package | Ran `opencode plugin add <name>` when `plugins` in `opencode.json` already contained the entry. | The command reported that the package is already configured and did not install it. | `plugin add` only edits configuration in that state. Use `opencode plugin list` to see the installed state. To change the source, remove the entry and add the new form. |
| Install the V2 port from a Git package specification | Added `github:<org>/<repo>#<tag>::path:<subdir>` because the published npm package had a V1 shape. | The module loaded without a log entry, but the effect was absent: the publish workflow generates the payload directory and the Git tag does not contain it. The plugin caught the missing-payload error and wrote it only to the console. | An error-free load does not prove payload delivery. Check the cached package for the payload. Install a publish-generated payload directly from the immutable tag. |

## Results & Parameters

### Configuration

```jsonc
// opencode.json: keep only V2-compatible plugin entries
{
  "plugins": ["<v2-compatible-plugin>"]
}
```

### Expected Output

- The loader does not report `failed to load plugin` for the removed entry after the
  next service start.
- Other plugin entries continue to load.
- After a direct payload installation, the harness discovers the payload. For OpenCode
  skills, the new skills appear in the harness skill list. A restart is not necessary
  when the harness watches the skills directory.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode v2.0.26 (public release) | Load failure of the public `oh-my-openagent` server plugin (5.1.29 cached, 5.1.30 newest published at the time); diagnosis and removal | [notes.md](../skills/tooling-opencode-v2-invalid-server-plugin.notes.md) |
| OpenCode v2.0.27 (public release) | V1-only published npm release 0.5.3 of a skills-delivery plugin; V2-compatible module at unreleased upstream tag v0.6.0; payload absent from the Git installation route; direct corpus installation from the tag | [notes.md](../skills/tooling-opencode-v2-invalid-server-plugin.notes.md) |

## References

- [OpenCode V2 plugins guide](https://opencode.ai/v2/docs/build/plugins)
- [OpenCode V1 to V2 plugin migration guide](https://opencode.ai/v2/docs/build/plugins/migrate-v1)
- [OpenCode V2 troubleshooting](https://opencode.ai/v2/docs/troubleshooting)
- [Related skill: tooling-opencode-v2-invalid-tui-plugin](tooling-opencode-v2-invalid-tui-plugin.md)
- [Related skill: tooling-opencode-v2-plugin-install-compat](tooling-opencode-v2-plugin-install-compat.md)
