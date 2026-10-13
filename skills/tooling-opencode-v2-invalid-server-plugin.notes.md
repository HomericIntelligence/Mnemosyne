# Notes: tooling-opencode-v2-invalid-server-plugin

Supporting evidence for the main entry. All commands and package names refer to public
software. One session on OpenCode v2.0.26 (2026-10-12) supplies the evidence.

## Log evidence

The client dialog showed `Server plugin error`, `Runtime: server`, and one reference
per load cycle. The server log `~/.local/share/opencode/log/opencode.log` recorded
(reformatted for notes):

```text
level=INFO msg="loading plugin" id=oh-my-openagent@latest entrypoint=file:///.../.cache/opencode/npm/oh-my-openagent@latest/<install-id>/node_modules/oh-my-openagent/dist/index.js role=server
level=WARN message="failed to load plugin" target=oh-my-openagent@latest ref=err_<hex>
cause="Cause([Fail(PluginModule.LoadError: Plugin must export a default definition with an id and an effect or setup function. (cause: SchemaError(Missing key\n  at [\"default\"][\"effect\"]\nMissing key\n  at [\"default\"][\"setup\"])))])" role=server
```

The same shape failed at every load cycle over several hours with a different
reference each time. Every reference used the same `cause`.

## Package evidence

The cached package was the newest line of the public `oh-my-openagent` npm package.
Its `dist/index.js` ends with a V1-style multi-runtime module:

```js
var pluginModule = createPluginModule();
var omoPlugin = pluginModule.server;
var src_default = pluginModule;
// pluginModule is { id: "oh-my-openagent", server: serverPlugin }
```

The newest published version available at the time (`npm view oh-my-openagent
versions`: 5.1.30, `dist-tags.latest`) shipped the same export shape, so an upgrade
could not fix the failure. The failure is at default-export schema validation,
before plugin code runs; environment variables and credentials were not examined by
the loader, so they were excluded as causes.

## Decision details

- Removal target: the `plugins` array in the global `~/.config/opencode/opencode.json`.
  The project under test contributed no plugin configuration.
- The parallel entry `tooling-opencode-v2-invalid-tui-plugin` covers the TUI runtime
  (`cli.json`, `Invalid V2 TUI plugin module`, V1 marker `{ id, tui: fn }`, restart the
  TUI client). This entry covers the server runtime (`opencode.json(c)`, the
  LoadError text above, V1 marker `{ id, server: fn }`, restart the service). The two
  share the general rule: a V1-shaped default export fails V2 module validation;
  confirm the shape in the cached package; remove, replace, or request an upstream
  port.
- The change applies when the service next loads plugins. A restart was deferred by
  operator choice in the observed session; the warning repeats until then and is
  harmless because the entry is already disabled by configuration.
