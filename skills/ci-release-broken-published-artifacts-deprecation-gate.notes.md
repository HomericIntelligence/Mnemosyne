# Notes: ci-release-broken-published-artifacts-deprecation-gate

## Provenance (2026-11-16)

- A package published to npm shipped artifacts that fail module-load validation in the supported
  host. The older published versions in the same package stayed installable and broken, and the
  package's release pipeline publishes with OIDC trusted publishing, which cannot run the
  deprecation command.
- The registry allowed an agent host to query `npm view <pkg>@<version> deprecated` but the agent
  host was not authenticated to mutate the registry; the one-time deprecation belongs to the
  maintainer.
- The release workflow therefore carries two additions: a pre-publish check that the staged
  artifact exports a loadable plugin definition, and the per-artifact deprecation gate described in
  the main entry. The load check was verified by import success on the staged output; the
  deprecation gate logic was hand-run against the live registry (every listed version reported an
  empty deprecation message, so the gate fails closed).
- The gate is verification, not repair. It cannot unpublish, re-publish, or deprecate the
  artifacts; it blocks the release until the maintainer acts. That is the intended pressure.
- Privacy: the notes record no organization, repository, issue, host, path, or credential
  identifiers. Version numbers of a public package are content-free evidence for the rule.

## Editorial notes (2026-11-16)

- The load-check and deprecation-gate wording must stay separate: one prevents a new broken
  artifact from reaching the registry, the other blocks until already-published broken artifacts
  are deprecated. A release can fail either check for different reasons.
- The per-artifact requirement is the decision branch that most readers will miss; a range query
  passes with one deprecated version in it.
