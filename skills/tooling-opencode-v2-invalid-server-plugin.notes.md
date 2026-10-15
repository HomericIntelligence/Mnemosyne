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

## Session evidence: unreleased V2 port and payload-free Git install (2026-10-15)

Public software: the `@homericintelligence/athena-opencode` npm package and its public
repository `HomericIntelligence/Athena`. One session on OpenCode v2.0.27 (2026-10-15)
supplies the evidence.

- `opencode plugin list` showed the configured package with no installed version
  (`-`). `opencode plugin add <name>` in this state reported that the plugin is
  already configured and did not install the package.
- The server log recorded `failed to load plugin` with
  `cause="Cause([Fail(PluginModule.LoadError: Plugin must export a default definition`
  `with an id and an effect or setup function. (cause: SchemaError(Expected object`
  `at ["default"])))])"` for the cached package under
  `~/.cache/opencode/npm/@homericintelligence/athena-opencode@latest/`.
- Registry data: `npm view` showed versions 0.4.4 through 0.5.3. Version 0.5.3 is the
  newest published release (2026-09-16). Its module default-exports
  `async function athenaPlugin()` that returns `{}`, a V1-era shape.
- Repository data: `git ls-remote` showed tag `v0.6.0`
  (commit `5c6c87c92349f6902c0028a73452fea9ceb8edf5`). Its module default-exports
  `{ id: "@homericintelligence/athena-opencode", setup() { ... } }`, the V2 shape.
- The Git package specification
  `github:HomericIntelligence/Athena#v0.6.0::path:npm/athena-opencode` installed and
  loaded with no `failed to load plugin` entry. `opencode plugin list` then showed
  version `5c6c87c`. But the documented effect was absent: no skills appeared in
  `~/.config/opencode/skills/`.
- The cached Git package contained only `plugin.js`, `package.json`, and `README.md`.
  The package `files` list includes `skills`, `LICENSE`, and `NOTICE`. The publish
  workflow copies `skills/` into the package before publication, so the Git tag does
  not contain the payload. `setup()` runs a function that throws when the payload is
  absent; the plugin catches the error and writes it with `console.warn`, which does
  not reach the OpenCode log.
- Remediation: `opencode plugin remove` deleted the package entry. A clone at tag
  `v0.6.0` supplied `skills/`, and a copy to
  `~/.config/opencode/skills/athena/` delivered the corpus. OpenCode discovered the
  17 skills without a service restart; the configuration-directory skills watcher
  applied the change.
- Decision detail: the registry route had no published V2 port, the Git route had a
  V2 module without its payload, and direct payload installation from the immutable
  tag was the only working route. When the plugin gains a published V2 release, the
  package route restores automatic payload synchronization at startup.
