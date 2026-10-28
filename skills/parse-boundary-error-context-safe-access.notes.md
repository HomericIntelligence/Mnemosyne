# Notes: parse-boundary-error-context-safe-access

Supporting evidence for the main entry. Privacy screened: no repository,
organization, issue, path, or credential identifiers.

## Source session evidence

- A serving-runtime receipt parser validates that component provenance
  contains two complete template-role records. Each role is collected from a
  provenance mapping into a partial field map, then completeness is proven.
- The incomplete-role rejection branch built its typed error context with
  strict indexing of the content-identity field. A boundary test that removed
  one whole role observed `KeyError: 'content_identity'` instead of the typed
  role error.
- Fix: `fields.get("content_identity")` at the two pre-proof raise sites that
  reference the identity (incomplete record, malformed revision kind). The
  success path keeps strict indexing, which static analysis confirms is safe
  after the completeness proof and after the revision-kind membership check.
- Verification: the boundary test that removed the role passed after the fix;
  the focused parser suite (124 tests) and the tokenizer, configuration,
  qualification, and registrar suites (915 tests in one combined run) were
  green; format, lint, and type checks were clean.

## Related corpus entries inspected for duplication

- An MCP dispatcher entry covers translating a KeyError from missing tool
  arguments into a typed error before client I/O. Its trigger is input access
  at a dispatcher, and its rule is wrap-and-translate. The failure mode here
  is different: the typed error already exists, and its own context
  construction crashes. Retrieval intent and fix differ, so a separate entry
  was created instead of an amendment.
- A broad corpus scan found no entry carrying the safe-access-at-raise-site
  decision branch.

## Disposition record

- Disposition: create, one main skill plus this notes file.
- Delivery base: Mnemosyne main at the revision bound during the write-mode
  checkout resolution for this session.
- Write allowlist: `skills/parse-boundary-error-context-safe-access.md`,
  `skills/parse-boundary-error-context-safe-access.notes.md`.
