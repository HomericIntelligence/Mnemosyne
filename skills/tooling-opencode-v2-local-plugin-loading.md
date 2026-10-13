---
name: tooling-opencode-v2-local-plugin-loading
description: "Make a locally developed or checkout-based plugin load in OpenCode V2. Use when: (1) a configured plugin is absent and no error message or error reference is shown, (2) a filesystem path in the plugins configuration does not load, (3) you must select a mounting form for a local plugin."
category: tooling
date: 2026-10-13
version: "1.0.0"
user-invocable: false
tags: [opencode, plugin, local-plugin, configuration, silent-failure]
---

# OpenCode V2 Local Plugin Loading and Silent Skips

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-13 |
| **Objective** | Make a locally developed or checkout-based plugin load in OpenCode V2, and identify a silent skip. |
| **Outcome** | Successful. Three mounting forms and one silent failure mode verified on OpenCode v2.0.24 through v2.0.26. |

## When to Use

- A configured plugin has no effect and shows no error message or `err_<id>` reference.
- `opencode plugin list` does not show a plugin that you added.
- You develop a plugin in a local checkout and must select a mounting form for it.
- A plugin installation step completed, but the plugin features are not available.

## Verified Workflow

### Quick Reference

1. Verify the loaded set before you change the configuration:

```bash
opencode plugin list
```

2. If the plugin is absent with no error reference, suspect a silent skip. Then select the mounting form:

| Mounting form | Requirement | Result when the requirement is not met |
| --------- | --------- | --------- |
| npm package spec in the `plugins` array (for example `name@latest`) | A published or cached package with a valid entrypoint | Loud load error with a recorded error reference if the module shape is invalid |
| Reference to a local directory | A root `index.js` in the directory, or a package `main`/`exports` entry that resolves to one | Silent skip: no error, no log reference, absent from the loaded set |
| Drop-in file `~/.config/opencode/plugins/<name>.js` | A `.js` file directly in the user plugins directory | Loads as a local plugin without a `plugins` configuration entry |
| Raw filesystem path as a `plugins` entry | Not supported; the array holds npm package specs | The plugin does not load; use a package spec or the drop-in directory instead |

### Suggested Approach

First, classify the failure by its signature. This classification selects the applicable rule:

- **Silent skip.** The plugin is in the configuration, but it is absent from the loaded set, there is no error reference, and the log has no INFO `loading plugin` line for it. The loader never attempted the entrypoint. Use this skill.
- **Loud rejection.** The load attempt produced an error reference (`err_<id>`) or a named module error. The loader attempted the entrypoint and rejected it. Use [tooling-opencode-v2-invalid-server-plugin](tooling-opencode-v2-invalid-server-plugin.md) or [tooling-opencode-v2-invalid-tui-plugin](tooling-opencode-v2-invalid-tui-plugin.md).

Then recover the silent skip:

1. If you referenced a local directory, add a root `index.js` that exports the plugin definition, or set the package `main`/`exports` field so that it resolves to a real entrypoint.
2. If you added a raw file path to the `plugins` array, remove it. Move the file to `~/.config/opencode/plugins/<name>.js` as a drop-in, or install a package spec.
3. Restart the client and verify the loaded set again.

Two adjacent rules stay in their canonical entries. Do not duplicate them here:

- A V2 server plugin module must have a default-export definition with an `id` and an `effect` or `setup` function. See [tooling-opencode-v2-invalid-server-plugin](tooling-opencode-v2-invalid-server-plugin.md) for the diagnosis and the V1-to-V2 module migration.
- V2 configuration uses the `plugins` key. The V1 `plugin` key is ignored. See [tooling-opencode-v2-plugin-install-compat](tooling-opencode-v2-plugin-install-compat.md) for the configuration and command format.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Raw file path as a `plugins` entry | Added an absolute `.js` file path to the V2 `plugins` array. | The array resolves npm package specs, not filesystem paths. The plugin did not load. | Mount a local file with the drop-in directory convention, not with a configuration entry. |
| Directory reference without a root entrypoint | Referenced a project checkout directory that had no root `index.js`. | Silent skip: the plugin was absent from `opencode plugin list`, with no error message, no error reference, and no log line. | A directory reference must have a root `index.js`, or a package entrypoint that resolves to one. Verify the entrypoint before you configure the reference. |
| V1 module shape kept in the entrypoint | Loaded a package whose default export had a V1-style module shape. | Loud rejection with a recorded error reference. | See [tooling-opencode-v2-invalid-server-plugin](tooling-opencode-v2-invalid-server-plugin.md) for the full diagnosis. |

## Results & Parameters

### Configuration

Package-spec mounting in `~/.config/opencode/opencode.json`:

```jsonc
{
  "plugins": ["<package-name>@latest"]
}
```

Drop-in mounting needs no configuration entry:

```text
~/.config/opencode/plugins/<name>.js
```

A drop-in file or a root `index.js` must contain the V2 definition shape:

```js
export default {
  id: "<plugin-id>",
  setup: async (context) => ({
    // hooks, tools, or commands
  }),
}
```

### Expected Output

- `opencode plugin list` shows the plugin.
- The log has an INFO `loading plugin` entry with the plugin id and entrypoint.
- The plugin hooks, tools, or commands operate.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode v2.0.24 through v2.0.26 | Local plugin mounting from project checkouts and a user drop-in file, in an isolated local environment. Public stable releases. | [notes.md](../skills/tooling-opencode-v2-local-plugin-loading.notes.md) |

## References

- [OpenCode plugins documentation](https://opencode.ai/docs/plugins/)
- [tooling-opencode-v2-invalid-server-plugin](tooling-opencode-v2-invalid-server-plugin.md)
- [tooling-opencode-v2-plugin-install-compat](tooling-opencode-v2-plugin-install-compat.md)
- [tooling-opencode-v2-invalid-tui-plugin](tooling-opencode-v2-invalid-tui-plugin.md)
