---
name: tooling-opencode-v2-invalid-server-plugin
description: "Diagnose and resolve the OpenCode V2 server plugin error `Plugin must export a default definition with an id and an effect or setup function`. Use when: (1) a plugin shows `Server plugin error` with `Runtime: server` and a reference `err_*`, (2) a V1-era server plugin must work in OpenCode V2, (3) you must choose between removal, an upstream V2 port, or a replacement."
category: tooling
date: 2026-10-13
version: "1.0.0"
user-invocable: false
tags: [opencode, plugin, server, api-migration, package-compatibility]
---

# OpenCode V2 Invalid Server Plugin Module

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-13 |
| **Objective** | Diagnose and resolve an OpenCode V2 server plugin that fails to load with `Plugin must export a default definition with an id and an effect or setup function`. |
| **Outcome** | Successful. Verified against OpenCode v2.0.26 and the published package that caused the failure. |

## When to Use

- The client reports `Server plugin error` with `Runtime: server`, status `failed`, and a
  reference `err_*`.
- A plugin entry in `plugins` of an `opencode.json(c)` configuration causes the failure.
  This config owns server plugins; `cli.json` owns TUI plugins.
- You evaluate a community server plugin that can be V1-era before you add it to a V2
  configuration.

## Verified Workflow

### Quick Reference

```bash
# 1. Find the recorded cause for the reported reference. Do not infer the cause.
grep "err_<reference>" ~/.local/share/opencode/log/opencode.log   # role=server

# 2. Inspect the cached package that the loader rejected
PKG=~/.cache/opencode/npm/<name>@latest/*/node_modules/<name>
grep -n '"version"' "$PKG/package.json" | head -1
tail -c 800 "$PKG"/dist/*.js          # last export block shows the default definition
```

V2 server plugins require a default definition with an `id` and an `effect` or `setup`
function, for example `Plugin.define({ id, setup(context) })` from `@opencode/plugin`.
A V1-era server plugin exports a definition of the form
`{ id, server: async (input, options) => hooks }`. The loader fails schema validation
of the default export at module load time, so the failure occurs before any plugin
code runs and repeats at every load cycle with a new reference.

### Suggested Approach

1. Match the reference from the dialog to the server log entry. The entry records
   `level=WARN ... message="failed to load plugin" ... ref=err_* role=server` and a
   `cause` string. If the server log is not accessible, ask for the matching entry.
2. Read the cause literally. `SchemaError(Missing key at ["default"]["effect"] ...`
   `["default"]["setup"])` names a module-shape problem, not a configuration problem.
   Do not rewrite `plugins` syntax to fix this error.
3. Confirm the module shape with the Quick Reference commands. Check the newest
   published version with `npm view <name> versions` if the cached version is not
   current. A V1 shape in the newest release means no V2 port exists.
4. Select the remediation:
   - Remove the plugin from `plugins` in the applicable `opencode.json(c)` when the
     function is not required.
   - Use a V2-compatible replacement plugin when one provides the function.
   - When the function is unique, request an upstream port to `@opencode/plugin`.
     OpenCode V2 does not run V1 plugin implementations.
5. Restart the service to apply the change: `opencode service restart`. Deleting the
   stale cache directory `~/.cache/opencode/npm/<name>@latest/` prevents a reinstall
   attempt on restart.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | The direct approach was successful. | N/A | Bind the diagnosis to the logged reference before you inspect the package. |

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

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode v2.0.26 (public release) | Load failure of the public `oh-my-openagent` server plugin (5.1.29 cached, 5.1.30 newest published at the time); diagnosis and removal | [notes.md](../skills/tooling-opencode-v2-invalid-server-plugin.notes.md) |

## References

- [OpenCode V2 plugins guide](https://opencode.ai/v2/docs/build/plugins)
- [OpenCode V1 to V2 plugin migration guide](https://opencode.ai/v2/docs/build/plugins/migrate-v1)
- [OpenCode V2 troubleshooting](https://opencode.ai/v2/docs/troubleshooting)
- [Related skill: tooling-opencode-v2-invalid-tui-plugin](tooling-opencode-v2-invalid-tui-plugin.md)
- [Related skill: tooling-opencode-v2-plugin-install-compat](tooling-opencode-v2-plugin-install-compat.md)
