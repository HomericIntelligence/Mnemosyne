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

## Session evidence: stale cache refreshed by plugin update (2026-11)

Public software: the public skills-delivery npm package and its public repository.
One session on OpenCode v2.2.5 (log entries dated 2026-11-04) supplies the evidence.

- The server log recorded `failed to load plugin` with the same `SchemaError(Expected
  object at ["default"])` cause for the plugin.
- The cache under `~/.cache/opencode/npm/<name>@latest/*/` held release 0.5.3, whose
  module default-exported a function. The newest published release at the time was
  0.6.0, whose module default-exports `{ id, setup }`.
- `opencode plugin check` reported the package as failed at the old cached revision.
- `opencode plugin update <name>` reported the load check as failed and also updated
  the Server plugin. A fresh cache directory appeared with the 0.6.0 package.
- `opencode plugin list` showed the plugin at 0.6.0.
- A standalone server run loaded the plugin from the new cache directory without a
  `failed to load plugin` entry.
- The stale 0.5.3 cache directory was removed after the update.
- Decision detail: when the published release already contains the V2 module shape,
  the package route restores payload delivery without a manual install. Verify the
  installed version with `opencode plugin list` after the update, then restart the
  service (or start a standalone server) to load the refreshed plugin.

## Session evidence: in-place V1-to-V2 adaptation of a local-only bundle (2026-11-23)

One session supplies the evidence. Public software: OpenCode v2.2.5 and its plugin
loader (`packages/core/src/plugin/module.ts`), which decodes the namespace `default`
against `{ id, effect } | { id, setup }`. Internal plugin, host, and path names are
generalized; no account or credential evidence is stored.

- Install form: a single TypeScript bundle in the user plugins directory. The daemon
  injected it as a managed absolute file entrypoint on every reload. It was not an
  npm package and not a Git package specification.
- Log evidence: one `level=WARN message="failed to load plugin"` entry per daemon
  start after the host upgraded past v2.1.1, each with
  `cause="Cause([Fail(PluginModule.LoadError: Plugin must export a default definition
  with an id and an effect or setup function. (cause: SchemaError(Expected object
  at [\"default\"])))])"` and a new `ref=err_<hex>`. The loader validates only the
  export shape, before any plugin code runs.
- Diagnosis: `Expected object at ["default"]` names a factory default export (`var
  plugin = async () => ({ ... })`), not the `{ id, server: fn }` record of the older
  notes. The three sibling plugin files in the same directory loaded without error,
  which confined the cause to this file.
- No upgrade route: the bundle source exists in no npm release and no upstream
  repository. The ecosystem registry contains only a skills-delivery plugin, and it
  loads without error. The bundle was the only source of its function.
- Adaptation (see the main entry for the branch): a backup copy preserved the
  original tail; `export default { id, setup }` replaced the factory export. `setup`
  builds a compat client, registers the legacy hook surface on V2 domains
  (`tool.transform`, `command.transform` for 21 command names, `session.hook` for
  prompt and compaction, `tool.hook` for execute before/after), and consumes
  `context.event.subscribe()` with a `data`-to-`properties` wire mapping. Removed
  legacy types were synthesized from their V2 successors:
  `session.compacted` from `session.compaction.ended`, and
  `server.instance.disposed` from `global.disposed`. `tool()` records registered
  with the host charset rule `^[A-Za-z0-9_-]+$`; the declared input schema decodes
  arguments in the host path, so no plugin-side re-parse is needed.
- Validation: `node --experimental-strip-types` on a harness that imports the real
  file, asserts the default export against the loader schema, runs `setup` with a
  stub V2 Context, and executes one registered goal tool end to end (21 checks
  passed). `node --experimental-strip-types --check` validated syntax. Deferred
  service restarts were not needed because the daemon watcher reloads the entrypoint.
- Failure modes found during adaptation and fixed before validation: a typo in the
  prompt text mapper, two hook mappers that referenced helpers never defined, a
  redundant client literal, a floating command handle, one dead constant, and an
  argument-validation branch written for zod that rejected every call for
  effect-shaped schemas. Each of these loads cleanly; the harness caught them.
  A clean load is not evidence that registrations work.
- Live confirmation: the server log shows `msg="loading plugin"` with the entrypoint
  path at the edit time of the adapted file, followed by no `failed to load plugin`
  entry. The pre-fix identical failures remain the log record; no identical
  `cause` string appears after the adaptation.
- Decision detail: for a local-only bundle, adaptation in place is faster than a
  fork or a port request that no publisher can merge, and it preserves the exact
  runtime behavior the rest of the ecosystem already exercised (tool registrations,
  command handlers, event consumers). When a publisher exists, prefer the published
  port route.
