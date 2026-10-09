# Notes: OpenCode V2 Invalid TUI Plugin Module

Supporting evidence for `tooling-opencode-v2-invalid-tui-plugin` (v1.0.0, 2026-10-09).
All package facts come from the public npm registry and the public OpenCode
documentation. The failure was reproduced on a public OpenCode v2.0.24 release.

## Observed failure

- The TUI plugin list showed the plugin `opencode-tabs` with status `failed` and
  the error `Invalid V2 TUI plugin module: opencode-tabs`.
- The plugin was referenced only from the global CLI configuration
  (`~/.config/opencode/cli.json`) in the valid V2 object form:

  ```json
  { "package": "opencode-tabs", "options": { "keybinds": { "next": "<leader>]", "previous": "<leader>[" } } }
  ```

- No credentials, environment variables, or network access were involved. The
  package download into the OpenCode npm cache succeeded; the module load then
  failed.

## Package evidence (opencode-tabs@0.3.0, newest published version at the time)

From the cached `package.json` under
`~/.cache/opencode/npm/opencode-tabs@latest/*/node_modules/opencode-tabs/`:

- `engines: { "opencode": ">=1.17.20" }` (V1 range).
- Build dependency `@opencode-ai/plugin@1.18.10` (V1 plugin package; V2 uses
  `@opencode/plugin` and `@opencode/plugin/tui`).
- `peerDependencies`: `@opentui/solid ^0.4.5` (the V2 CLI plugin guide requires
  `>=0.5.8`).
- `exports` map contains only `"./tui": "./dist/tui.mjs"`.

From the cached `dist/tui.mjs` (V1 module shape):

```js
const plugin = {
  id: "opencode-tabs",
  tui: async (api, options) => {
    api.slots.register({ slots: { app_bottom() { ... } } });
  }
};
export { plugin as default };
```

The V2 loader requires a default export produced by
`Plugin.define({ id, setup(context) })` imported from `@opencode/plugin/tui`.

The plugin README documents V1 configuration (`.opencode/tui.json` with a
`plugin` array) and the removed V1 CLI form `opencode plugin <name> --global`,
which the V2 CLI rejects with a help message.

npm `versions` at the time: `0.1.0`, `0.2.0`, `0.3.0`. No V2-compatible release
existed.

## Remediation applied

- Removed the plugin entry from the `plugins` array in `cli.json`. The
  configuration remained valid JSON.
- Native V2 session tabs were already configured in the same file
  (`tabs.mode: "on"`) and replace the plugin's function, so no capability was
  lost.
- Deleted the stale package cache `~/.cache/opencode/npm/opencode-tabs@latest/`
  (optional cleanup).
- The V2 keybind reference lists native tab commands (`session.tab.next`,
  `session.tab.previous`, `session.tab.close`, ...) for a keyboard replacement.

## Keybind reference evidence (v1.1.0)

Source: OpenCode V2 keybind reference (`https://opencode.ai/v2/docs/cli/keybinds`),
retrieved 2026-10-09:

- `leader` defaults to `ctrl+x`; `keybinds.leader` overrides it; the top-level
  `leader.timeout` object sets the wait after the leader key.
- Binding value forms: key string, comma-separated alternatives, array, object
  (`{ "key": ..., "preventDefault": ... }`), `none`, or `false`. Unknown command
  IDs are rejected.
- Defaults table lists each `session.tab.*` command ID and its default binding.

Cross-check: the command-ID set agrees with the `keybinds` properties in the
published V2 configuration schema (`https://opencode.ai/v2/cli.json`).

Conflict scan: a full read of the defaults table found no default binding that
uses `<leader>]` or `<leader>[` (the closest, `which-key.group.next`, uses
`ctrl+alt+]`).

Applied configuration: the example `tabs` + `keybinds` block from the main entry
was written to a live `cli.json` on a v2.0.24 host and validated against the
published V2 schema without errors.

Default-preservation rule (v1.1.1): the V2 keybind reference shows no merge
between an explicit entry and the documented defaults. Its example sets
`app.exit` to `["ctrl+c", "ctrl+d"]`, a strict subset of the documented default
`ctrl+c,ctrl+d,<leader>q`. Replacement semantics are inferred from that example,
not stated explicitly; the limit is recorded. The applied live configuration
(only `<leader>]` and `<leader>[`) replaced the defaults
`ctrl+tab,alt+down` / `ctrl+shift+tab,alt+up`; the comma-separated form
restores both.

## Limits

- Verified on one public OpenCode release (v2.0.24). Later V2 releases can change
  the error text or the module contract; if the text differs, verify the module
  shape against the current V2 plugin guide before you apply this rule.
