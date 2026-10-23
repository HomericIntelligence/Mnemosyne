---
name: tooling-opencode-v2-plugin-install-compat
description: "Check that an OpenCode plugin supports the installed OpenCode major version before you install it, and confirm that both the server and the TUI side are registered. Use when installing, configuring, or removing a community plugin on OpenCode v2; when a plugin appears installed but its tools, commands, or sidebar are absent; or when a plugin README tells you to add the package to both opencode.json and cli.json."
category: tooling
date: 2026-10-09
version: "1.2.0"
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
- A plugin reports one half of its function only: the sidebar is present but the agent tools and slash commands are absent, or the reverse.
- Manual edits to `~/.config/opencode/cli.json` disappear after another OpenCode instance runs.
- A plugin README tells you to add the same package to both `opencode.json` and `cli.json`.

## Verified Workflow

### Quick Reference

Compare the plugin's target version with the local major version before installation:

```bash
opencode --version                                # local major version
opencode plugin add <package>                     # v2 install (no --global flag)
opencode plugin remove <package>                  # v2 removal
opencode plugin list                              # shows installed and local plugins

# Select the configuration file from the cached package entrypoints
PKG=~/.cache/opencode/npm/<name>@latest/*/node_modules/<name>
node -e "console.log(JSON.stringify(require('$PKG/package.json').exports))"
```

| Package exports | Required registration | CLI loads the TUI part? |
| --- | --- | --- |
| `.` only, or `./server` | `opencode.json(c)` | No TUI part |
| `.` and `./tui` | `opencode.json(c)`, and it must be present there | Yes, from the server plugin list |
| CLI-only, or a TUI-only package | `cli.json` | Yes, this is the only entry |

The `opencode.json(c)` entry is the load-bearing one for any package with a server entrypoint. A dual-entrypoint package that appears only in `cli.json` gives the TUI part without the server part, so its tools and commands never load.

Signals that a plugin targets OpenCode v1, not v2:

- Its README configures `.opencode/tui.json` or a `"plugin"` array. OpenCode v2 migrates `tui.json` into `~/.config/opencode/cli.json` and does not read `tui.json` after migration.
- Its source imports the plugin SDK from `@opencode-ai/plugin`. The v2 TUI exposes the plugin module `@opencode/plugin/tui`.

### Suggested Approach

1. Record the local major version with `opencode --version`.
2. Before installation, read the plugin README and its package manifest (`engines.opencode`, plugin SDK imports, peer dependencies). A `>=1.x` floor does not prove v2 support. Treat v1-only config documentation as a v1 signal.
3. On v2, install with `opencode plugin add <package>`. Do not copy v1 README commands. The v1 form `opencode plugin <package> --global` fails on v2.
4. In v2, a `plugins` entry in `~/.config/opencode/cli.json` is a string or an object `{"package": "<name>", "options": {...}}`. The published schema is `https://opencode.ai/v2/cli.json`. Plugin READMEs that show a tuple `["<name>", {...}]` describe the v1 format; use the v2 object form.
5. Select the configuration file from the plugin's entrypoints. Do not copy a README that tells you to write both files:
   - `opencode.json(c)` owns server plugins. A package that exports `.` or `./server` must have an entry here.
   - `cli.json` owns CLI-only plugins. These plugins run in the terminal and stay active against a remote server.
   - A package that exports both `.` and `./tui` needs an entry in `opencode.json(c)`. The CLI gets the active plugin list from the connected server, so the same package does not also need a `cli.json` entry.
6. Read the package `exports` field in the cached package to select the file. A package with a `./tui` export is not CLI-only.
7. Verify both sides after installation. A package with a server entrypoint must show a server row and, if it has a `./tui` export, a TUI row:

   ```bash
   opencode plugin list | grep <package>
   opencode plugin check          # prints "Server" and "TUI" sections
   ```

   Then query the loaded server plugins and confirm that the plugin is `active`:

   ```bash
   opencode api get /api/plugin | grep <plugin-id>
   ```

8. If only one row or one section is present, read the configuration file that the missing side needs. An installer can write a dual-entrypoint package to `cli.json` alone, which leaves the server side unregistered.
9. Running OpenCode instances rewrite `cli.json` from their in-memory state. Concurrent instances can silently remove manual edits and change unrelated keys. Read the file again after each edit, and prefer the plugin CLI over manual edits while other instances run.
10. If an installed plugin has no effect on v2, remove it with `opencode plugin remove <package>` and verify with `opencode plugin list`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Install with the README command | Ran the v1 README form `opencode plugin <package> --global` on v2. | v2 uses subcommands; the CLI returned `Unknown subcommand` and `Unrecognized flag: --global`. | Use `opencode plugin add <package>` on v2. Check README commands against the local major version. |
| Trust a successful install | Accepted the `installed and added to cli.json` message and the `plugin list` entry as proof of function. | A v1 TUI plugin registers in v2 but gives no working feature. | A clean install is not an interface-compatibility check. Verify the plugin target major version first. |
| Assume which file `plugin add` writes | Expected `plugin add` to write `cli.json`, from an earlier V2 version and from the vendor README. | On v2.1.1 it wrote `opencode.json`. The target file depends on the plugin entrypoints and the host version. | Read both configuration files after installation. Do not infer the target file from an earlier version. |
| Edit cli.json while other instances run | Added plugin options to `cli.json` by hand. | A concurrently running OpenCode instance rewrote the file and removed the edit (it also changed an unrelated key). | Running instances hold the config in memory and write it out. Re-read the file after edits; use the CLI where possible. |
| Add the package to both configuration files | Followed a plugin README that said to register the package in `opencode.json` and `cli.json` for the sidebar and command palette. | `plugin add` had already registered the package in `opencode.json`. The package exports both `.` and `./tui`, so the CLI loads the TUI part from the server plugin list. The second entry was redundant. | Check the package `exports` field and the official V2 CLI plugin documentation before you add a second entry. A vendor README can prescribe configuration that V2 does not require. |
| Accept a TUI-only registration for a dual-entrypoint package | A dual-entrypoint package was present only in `cli.json`, and `opencode.json` had an empty `plugins` array. `plugin list` showed the package, so the installation looked complete. | The server row and the agent tools and slash commands were absent. Only the TUI half was registered. Adding the package to `opencode.json` `plugins` made the server row `active` and registered the commands. | A package that exports `.` and `./tui` must have an `opencode.json(c)` entry. Confirm a server row and a TUI row before you call the installation complete. |

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

A package with server and TUI entrypoints needs one entry in `opencode.json`. Do not add it to `cli.json`:

```json
{
  "plugins": ["<package-with-server-and-tui-exports>"]
}
```

Do not leave `plugins` empty in `opencode.json` and rely on a `cli.json` entry for such a package. That combination registers the TUI part only. After you add the `opencode.json` entry, the CLI reports both halves:

```text
Server
  <plugin-id> <version> (current)
TUI
  <package> <version> (current)
```

### Expected Output

- `opencode plugin add <package>` caches the package under `~/.cache/opencode/npm/` and writes one configuration file. The file depends on the plugin entrypoints and the host version. On OpenCode v2.1.1 with a package that exports `.` and `./tui`, it wrote the `plugins` array in `opencode.json`. An earlier installer on the same host wrote `cli.json` alone. Read both files after installation instead of assuming which file changed.
- `opencode plugin list` shows the package with its version and source. For a dual-entrypoint package, a complete installation also shows the server row from `/api/plugin`.
- The server log shows `msg="loading plugin" ... entrypoint=.../dist/server.js` for the server entry. A load with no `failed to load plugin` entry and no `err_*` reference is a clean load.
- For a compatible plugin, the feature is visible after an OpenCode restart. Plugin changes require a restart.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| OpenCode v2.0.24 (public release) | v1 TUI plugin install, `plugin add` vs v1 README command, concurrent `cli.json` rewrite | [notes.md](./tooling-opencode-v2-plugin-install-compat.notes.md) |
| OpenCode v2.1.1 (public release) | Dual-entrypoint package (`./server` and `./tui`) installed with `plugin add`; a redundant `cli.json` entry added from the vendor README and then removed | [notes.md](./tooling-opencode-v2-plugin-install-compat.notes.md) |
| OpenCode v2.1.4 (public release) | Dual-entrypoint package present in `cli.json` alone with an empty `opencode.json` `plugins` array; server row, tools, and commands absent until the `opencode.json` entry was added | [notes.md](./tooling-opencode-v2-plugin-install-compat.notes.md) |

## References

- [OpenCode v2 CLI configuration schema](https://opencode.ai/v2/cli.json)
- [OpenCode v2 CLI plugins: automatic TUI loading from `opencode.json(c)`](https://opencode.ai/v2/docs/cli/plugins)
- [OpenCode v2 building CLI plugins: `./tui` export and `cli.json` for CLI-only packages](https://opencode.ai/v2/docs/build/plugins/cli)
- [OpenCode keybinds documentation](https://opencode.ai/docs/keybinds/)
- [Related: OpenCode v2 session deletion effects](tooling-opencode-v2-session-deletion-effects.md)
- Evidence details are in the [notes](tooling-opencode-v2-plugin-install-compat.notes.md).
