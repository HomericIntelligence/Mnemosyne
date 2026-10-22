# Notes: OpenCode V2 Local Plugin Loading and Silent Skips

Supporting evidence for `tooling-opencode-v2-local-plugin-loading`. The main skill
holds the rules. This file holds the generalized verification records.

## Context

The evidence comes from installing locally developed plugins from project
checkouts on OpenCode v2 public stable releases (v2.0.24 through v2.0.26), in an
isolated local environment. All identifiers are generalized.

## Experiment records

1. **Directory reference without a root entrypoint.** A plugin was packaged in a
   project checkout directory that had no root `index.js`. The directory was
   referenced for loading. Result: silent skip. `opencode plugin list` did not
   show the plugin. The log had no INFO `loading plugin` line for it and no
   error reference. Nothing in the client surface indicated a failure.
2. **Same directory with a root entrypoint added.** A root `index.js` that
   re-exports the built definition was added. Result: the log gained an INFO
   `loading plugin` entry with the plugin id and entrypoint, and the plugin
   appeared in the loaded set.
5. **Directory with `package.json` `main` but no root `index.js`.** A plugin
   directory contained a valid `package.json` with `"main": "plugin.js"` and a
   resolvable target file, but no root `index.js`. Result: silent skip on
   OpenCode v2.0.29. `opencode plugin list` did not show the plugin, the log
   had no INFO `loading plugin` line, and no error reference was recorded.
   Adding a root `index.js` that re-exports the definition made the plugin
   load immediately. The loader does not consult `package.json` `main` or
   `exports` during discovery.
3. **Drop-in file.** A small shim file was placed directly in
   `~/.config/opencode/plugins/`:

   ```js
   export { default } from "<absolute-path-to-the-built-entrypoint>"
   ```

   Result: the plugin loaded with no `plugins` configuration entry.
4. **Raw file path as a `plugins` entry.** An absolute `.js` file path was added
   to the `plugins` array in `opencode.json`. Result: the plugin did not load.
   The array resolves npm package specs (registry or cached packages), not
   filesystem paths. The drop-in directory is the supported form for a local
   file.

## Diagnostic commands

Verify the loaded set:

```bash
opencode plugin list
```

Check for a load attempt in the log:

```bash
grep -h "loading plugin" <opencode-state-dir>/log/*.log | grep "<plugin-id>"
```

- An INFO `loading plugin` line with an id and entrypoint: the loader attempted
  the entrypoint. If the plugin still fails, look for a recorded error reference
  and use `tooling-opencode-v2-invalid-server-plugin`.
- No line at all: the loader never attempted the entrypoint. Check the mounting
  form against the decision table in the main skill.

Check a directory entrypoint before you configure a reference to it:

```bash
ls <directory>/index.js
grep -E '"(main|exports)"' <directory>/package.json
```

## Notes on the failure signature

The silent skip has a distinct signature: presence in the configuration plus
absence from the loaded set, with no error reference and no log line. This
signature is the primary retrieval cue. The loud failure modes of V2 (schema
rejection with `err_<id>`, `Invalid V2 TUI plugin module`) each produce a named
error or reference; they are covered by their own entries.
