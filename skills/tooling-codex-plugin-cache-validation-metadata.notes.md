# Codex Plugin Cache Validation Metadata: Notes

## Evidence from the installation session

A Codex marketplace install placed the plugin in a versioned cache directory. The harness
also wrote this metadata file into the plugin root and the marketplace root:

```json
{
  "source_type": "git",
  "source": "https://github.com/<owner>/<repo>.git",
  "ref_name": "<release-tag>",
  "sparse_paths": [],
  "revision": "<commit>"
}
```

The repository self-contained check rejected the repository URL in the `source` field. It
reported this failure:

```text
self-contained: The file '.codex-marketplace-install.json' references a forbidden repository
```

The same validator passed on a temporary copy of the plugin tree when the copy excluded
`.codex-marketplace-install.json`. The plugin skills loaded and ran. The metadata file had
the expected Git provenance values for the release tag.

## Limits

The evidence comes from one Codex version and one plugin layout. A future harness may write
a different metadata file name or location. Inspect the failure text and the file content
before you assume the same cause.
