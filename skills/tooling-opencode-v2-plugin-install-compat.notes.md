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

## Evidence limits

- The claim "the plugin does not work on v2" rests on the user report after installation
  plus the v1-only signals above. No source-level load test of the v1 TUI plugin API on
  v2.0.24 was performed.
- Behavior was verified on v2.0.24 only. Recheck the CLI surface on other v2 versions.
