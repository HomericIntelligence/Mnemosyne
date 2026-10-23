# Notes: OpenCode v2 plugin installation and major-version compatibility

Supporting evidence for [tooling-opencode-v2-plugin-install-compat](tooling-opencode-v2-plugin-install-compat.md).
Recorded 2026-10-09 on an OpenCode v2.0.24 host with the public npm package `opencode-tabs` 0.3.0.

## Version and API signals

- `opencode --version` reported `opencode v2.0.24`.
- The plugin manifest declared `engines.opencode: ">=1.17.20"` and
  `peerDependencies: {"@opentui/solid": "^0.4.5", "solid-js": "^1.9.12"}`.
- The plugin source imports `TuiPluginModule` from `@opencode-ai/plugin/tui`.
- The v2.0.24 binary bundles the TUI plugin module under the name `@opencode/plugin/tui`.
- The plugin README documents configuration in `.opencode/tui.json` with a `"plugin"` array
  and tuple entries `["opencode-tabs", {"keybinds": ...}]`.
- The v2 binary contains a migration path that reads `tui.json` plus `kv.json` and writes the
  merged result to `cli.json` (log line: `migrated cli config`).

## Observed command behavior on v2.0.24

- `opencode plugin opencode-tabs --global` (the v1 README form) failed:
  `Unknown subcommand "opencode-tabs" for "opencode plugin"` and
  `Unrecognized flag: --global in command opencode plugin`.
- `opencode plugin add opencode-tabs` succeeded:
  `TUI plugin "opencode-tabs" installed and added to .../cli.json`.
  The package was cached under `~/.cache/opencode/npm/opencode-tabs@latest/`.
- `opencode plugin list` showed the package with version `0.3.0` and source `opencode-tabs`.
- After installation, the user reported the plugin had no function on v2.
- `opencode plugin remove opencode-tabs` removed the entry and printed
  `Plugin "opencode-tabs" removed from .../cli.json`.

## v2 plugins schema (from https://opencode.ai/v2/cli.json)

Each item in `plugins` is `anyOf`:

- a string package specifier; or
- an object with required `package` (string) and optional `options` (object or null),
  `additionalProperties: false`.

Top-level keys include `keybinds`, `leader`, `tabs`, `session`, `theme`, `experimental`, `plugins`.

## Concurrent-instance config rewrite

- An edit that added a plugin entry with options to `cli.json` was lost when a concurrently
  running instance rewrote the file. The same rewrite changed an unrelated key
  (`session.verbosity` `low` → `medium`).
- Several long-running OpenCode processes existed on the host at the time
  (a `serve --service` process and automation-loop CLI runs).
- Recovery: re-apply the change with `opencode plugin add`, then re-read the file.
  A later read may still show a rewrite by another instance; repeat verification
  after the other instances exit.

## Dual-entrypoint package and redundant cli.json entry (2026-10-23, OpenCode v2.1.1)

Recorded on an OpenCode v2.1.1 host with a published npm plugin that exports both a
server and a TUI entrypoint.

### Observed facts

- `opencode plugin add <package>` printed `Plugin "<package>" installed and added to
  .../opencode.json`. The `plugins` array of `opencode.json` received the package
  specifier. `cli.json` was not modified by the command.
- `opencode plugin list` showed the package as `local.<plugin-id>.server` with the
  published version and the npm package as the source. The `.server` suffix comes from
  the plugin's own `Plugin.define({ id })` value, not from the configuration.
- The cached package `package.json` declared:
  `"." -> ./dist/server.js`, `"./server" -> ./dist/server.js`, `"./tui" -> ./src/tui.ts`.
  The server module and the TUI module were both present in the cached package.
- Server log evidence of a clean load:
  `msg="loading plugin" id=<package> entrypoint=file://.../dist/server.js ... role=server`.
  No `failed to load plugin` entry and no `err_*` reference appeared.
- The plugin created its durable state file on load, in the plugin's own data directory
  with owner-only permissions. The file contained the current schema version and empty
  goal and archive maps. This is runtime evidence that `setup` ran.

### The redundant edit

The vendor README said to add the package to both `opencode.json` (`plugins`) and
`cli.json` (`plugins`) so that the sidebar and command palette work. The edit was made
to `cli.json` on that instruction. The official V2 documentation states the opposite:

> Plugins configured in `opencode.json(c)` that expose a TUI component are loaded
> automatically by the CLI. You do not need to add the same package to `cli.json`.

The `cli.json` entry was removed. `opencode plugin list` and the server log showed the
same clean load after removal. `cli.json` remained valid JSON with no `plugins` key.

### Decision rule taken from the documentation

- `opencode.json(c)`: server plugins, and packages that expose a TUI component.
- `cli.json`: CLI-only plugins that must stay active against a remote server.

### Evidence limits

- The TUI rendering (sidebar, palette) was not observed directly. No TUI session was
  driven to completion. The claim that the CLI loads `./tui` from the server plugin list
  rests on the official documentation, plus the package shape and the clean load.
- End-to-end plugin function was not tested. The configured model provider refused the
  connection on this host, so no turn reached a model. This is unrelated to the plugin.
- The documentation statement is versioned to the V2 documentation at the time of
  recording. Recheck it on other V2 minor versions.

## Evidence limits

- The claim "the plugin does not work on v2" rests on the user report after installation
  plus the v1-only signals above. No source-level load test of the v1 TUI plugin API on
  v2.0.24 was performed.
- Behavior was verified on v2.0.24 only. Recheck the CLI surface on other v2 versions.
