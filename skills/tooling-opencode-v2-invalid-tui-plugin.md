---
name: tooling-opencode-v2-invalid-tui-plugin
description: "Diagnose and resolve the OpenCode V2 error `Invalid V2 TUI plugin module`. Use when: (1) a TUI plugin shows status failed with this error, (2) a V1-era community plugin must work in OpenCode V2, (3) you must choose between removal with a native replacement or an upstream port."
category: tooling
date: 2026-10-09
version: "1.0.0"
user-invocable: false
tags: [opencode, plugin, tui, api-migration, package-compatibility]
---

# OpenCode V2 Invalid TUI Plugin Module

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-09 |
| **Objective** | Diagnose and resolve an OpenCode V2 TUI plugin that fails to load with `Invalid V2 TUI plugin module`. |
| **Outcome** | Successful. Verified against OpenCode v2.0.24 and the published package that caused the failure. |

## When to Use

- The TUI reports `Invalid V2 TUI plugin module: <package>` and the plugin status is `failed`.
- You evaluate a community plugin that can be V1-era before you add it to a V2 configuration.
- You decide between removing a plugin, using a native V2 feature, or requesting an upstream port.

## Verified Workflow

### Quick Reference

```bash
# Inspect the downloaded package that OpenCode cached for the plugin
PKG=~/.cache/opencode/npm/<name>@latest/*/node_modules/<name>
cat "$PKG/package.json"                 # engines.opencode < 2 => V1-era package
grep -o "@opencode-ai/plugin\|@opencode/plugin" "$PKG"/dist/*.mjs | sort -u
grep -o "export {[^}]*}" "$PKG"/dist/*.mjs | tail -3
```

V1 markers: an `engines.opencode` range below 2, a build against the V1 package
`@opencode-ai/plugin`, and a default export of the form
`{ id, tui: async (api, options) => ... }` that uses `api.slots.register(...)`.
V2 requires a default export built with `Plugin.define({ id, setup(context) })`
from `@opencode/plugin/tui` and peer `@opentui/solid` `>=0.5.8`.

### Suggested Approach

1. Read the error literally. It names a module-shape problem, not a configuration
   problem. The object form `{ "package": "...", "options": {...} }` in `cli.json`
   is valid V2 syntax. Do not rewrite configuration syntax to fix this error.
2. Confirm the module shape with the Quick Reference commands. The package cache
   keeps the exact artifact that the loader rejected, so no download is necessary.
3. Select the remediation:
   - If a native V2 capability covers the plugin's function, remove the plugin
     entry and configure the native capability. Example: native V2 session tabs
     (`tabs` settings and the published `session.tab.*` keybind command IDs)
     replace a community tabs plugin.
   - If the function is unique, check the npm versions for a V2-compatible
     release. If none exists, request an upstream port to
     `@opencode/plugin/tui` (`context.ui.slot`, `context.keymap.layer`).
4. Remove the entry from the `plugins` array. The stale package cache under
   `~/.cache/opencode/npm/<name>@latest/` is harmless; delete it if you want.
5. Restart the TUI to apply the change. `cli.json` is client-side; a service
   restart is not necessary.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| README install command | Ran `opencode plugin <name> --global` from the plugin's V1-era README. | The V2 CLI has no such positional form; it prints help and exits. | Read install and compatibility instructions for the running major version. V1-era package READMEs do not describe V2 commands. |

## Results & Parameters

### Configuration

```jsonc
// cli.json: native V2 session tabs replace a community tabs plugin
{
  "tabs": { "mode": "on", "scope": "cwd", "layout": "vertical" },
  "keybinds": {
    "session.tab.next": "<leader>]",
    "session.tab.previous": "<leader>["
  }
}
```

### Expected Output

- The plugin error does not occur at the next TUI start.
- The native capability, for example the tab bar and tab keybinds, is available.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| OpenCode v2.0.24 (public release) | Load failure of the public `opencode-tabs@0.3.0` package; diagnosis and removal | [notes.md](../skills/tooling-opencode-v2-invalid-tui-plugin.notes.md) |

## References

- [OpenCode V2 CLI plugin guide](https://opencode.ai/v2/docs/build/plugins/cli)
- [OpenCode V2 CLI plugin configuration](https://opencode.ai/v2/docs/cli/plugins)
- [OpenCode V2 keybind reference](https://opencode.ai/v2/docs/cli/keybinds)
- [OpenCode V1 to V2 migration guide](https://opencode.ai/v2/docs/migrate-v1)
- [Related skill: tooling-opencode-v2-session-deletion-effects](tooling-opencode-v2-session-deletion-effects.md)
