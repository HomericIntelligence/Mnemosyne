---
name: tooling-opencode-v2-plugin-install-compat
description: "Check that an OpenCode plugin supports the installed OpenCode major version before you install it. Use when installing, configuring, or removing a community plugin on OpenCode v2."
category: tooling
date: 2026-10-09
version: "1.0.0"
user-invocable: false
tags: [opencode, plugins, major-version-compatibility, configuration]
---

# OpenCode v2 plugin installation and major-version compatibility

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-10-09 |
| **Objective** | Install only plugins that work with the installed OpenCode major version, with the correct v2 command and config format. |
| **Outcome** | A v1 TUI plugin (`opencode-tabs` 0.3.0) installed cleanly on a v2.0.24 host but gave no working feature. It was removed with `opencode plugin remove`. |

## When to Use

- You want to install, configure, or remove a community plugin for OpenCode.
- A plugin README shows a `tui.json` config file or a `"plugin"` string array.
- A plugin install command from a README fails with `Unknown subcommand` or `Unrecognized flag: --global`.
- A plugin appears in `opencode plugin list` but has no visible effect in the TUI.
- Manual edits to `~/.config/opencode/cli.json` disappear after another OpenCode instance runs.

## Verified Workflow

### Quick Reference

Compare the plugin's target version with the local major version before installation:

```bash
opencode --version                                # local major version
opencode plugin add <package>                     # v2 install (no --global flag)
opencode plugin remove <package>                  # v2 removal
opencode plugin list                              # shows installed and local plugins
```

Signals that a plugin targets OpenCode v1, not v2:

- Its README configures `.opencode/tui.json` or a `"plugin"` array. OpenCode v2 migrates `tui.json` into `~/.config/opencode/cli.json` and does not read `tui.json` after migration.
- Its source imports the plugin SDK from `@opencode-ai/plugin`. The v2 TUI exposes the plugin module `@opencode/plugin/tui`.

### Suggested Approach

1. Record the local major version with `opencode --version`.
2. Before installation, read the plugin README and its package manifest (`engines.opencode`, plugin SDK imports, peer dependencies). A `>=1.x` floor does not prove v2 support. Treat v1-only config documentation as a v1 signal.
3. On v2, install with `opencode plugin add <package>`. Do not copy v1 README commands. The v1 form `opencode plugin <package> --global` fails on v2.
4. In v2, a `plugins` entry in `~/.config/opencode/cli.json` is a string or an object `{"package": "<name>", "options": {...}}`. The published schema is `https://opencode.ai/v2/cli.json`. Plugin READMEs that show a tuple `["<name>", {...}]` describe the v1 format; use the v2 object form.
5. Running OpenCode instances rewrite `cli.json` from their in-memory state. Concurrent instances can silently remove manual edits and change unrelated keys. Read the file again after each edit, and prefer the plugin CLI over manual edits while other instances run.
6. If an installed plugin has no effect on v2, remove it with `opencode plugin remove <package>` and verify with `opencode plugin list`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Install with the README command | Ran the v1 README form `opencode plugin <package> --global` on v2. | v2 uses subcommands; the CLI returned `Unknown subcommand` and `Unrecognized flag: --global`. | Use `opencode plugin add <package>` on v2. Check README commands against the local major version. |
| Trust a successful install | Accepted the `installed and added to cli.json` message and the `plugin list` entry as proof of function. | A v1 TUI plugin registers in v2 but gives no working feature. | A clean install is not an interface-compatibility check. Verify the plugin target major version first. |
| Edit cli.json while other instances run | Added plugin options to `cli.json` by hand. | A concurrently running OpenCode instance rewrote the file and removed the edit (it also changed an unrelated key). | Running instances hold the config in memory and write it out. Re-read the file after edits; use the CLI where possible. |

## Results & Parameters

### Configuration

v2 global config with plugin options (`~/.config/opencode/cli.json`):

```json
{
  "plugins": [
    {
      "package": "<plugin-package>",
      "options": {
        "keybinds": { "next": "<leader>]" }
      }
    }
  ]
}
```

Mixed string and object entries in the same `plugins` array are valid under the v2 schema.

### Expected Output

- `opencode plugin add <package>` prints `installed and added to ~/.config/opencode/cli.json` and caches the package under `~/.cache/opencode/npm/`.
- `opencode plugin list` shows the package with its version and source.
- For a compatible plugin, the feature is visible after an OpenCode restart. Plugin changes require a restart.

## References

- [OpenCode v2 CLI configuration schema](https://opencode.ai/v2/cli.json)
- [OpenCode keybinds documentation](https://opencode.ai/docs/keybinds/)
- [Related: OpenCode v2 session deletion effects](tooling-opencode-v2-session-deletion-effects.md)
- Evidence details are in the [notes](tooling-opencode-v2-plugin-install-compat.notes.md).
