# Notes: testing-env-gated-marker-misfire-deselection

Supporting evidence for the main skill. Generalized from one live forensic;
identifiers are omitted under the privacy rules.

## Incident chronology (2026-10-30)

1. A gate decision on a reviewed head needed a local full-suite result. The
   host was a shared-compute login host, carrying the production cluster
   scheduler's command-line tools on `PATH`. The repository's suite declares
   an environment-gated marker whose registration states: the marked suite
   requires a dedicated test fixture brought up by a project script, CI
   runners auto-skip it when the environment is absent, and the CI job that
   owns the suite enforces an execution floor so a skip cannot pass as its
   result.
2. The first runs used a harness option override to fit an isolated
   environment. Collection failed on optional grader dependencies until the
   project's locked extras were installed in the isolated environment.
3. The full selection then ran about two hours and reported a large
   pass count plus over one hundred setup errors. Every erroring test sat in
   the environment-marked suite: the marker's support file checks for the
   environment by looking for the production tooling, which the host had, so
   the skip never fired and the suite's fixtures ran against the production
   system and errored.
4. Queue and accounting on the production system showed only pre-existing
   operator jobs and no suite-attributed names; the erroring fixtures had
   failed before submitting real work. No cleanup was required, but the audit
   was necessary evidence, not an assumption.
5. The CI-equivalent re-run used the project's same gate selection with the
   marker deselected (`-m "not <marker>"`): the green counts matched the
   erroring run exactly, the deselected count matched the error population
   exactly, and the run took minutes instead of hours.
6. A side observation fixed the override hazard: the earlier harness-override
   runs had also dropped the project's opt-in gate flag from the configured
   options, so their reported skip counts silently included a marked
   population the project gate normally runs. The deselection run kept the
   project's configured options and changed only which marker was excluded,
   so its counts relate to the project gate without a coverage footnote.

## Why the rule is safe to generalize from one case

- The mechanism is structural, not incidental: any presence-keyed gate fires
  or fails by what the host carries, independent of the specific project.
  Tooling hosts (login nodes, shared build hosts, operator workstations) are
  exactly the hosts where the predicate passes and the fixture is absent.
- The recovery is harness-native: marker deselection is the gate's own
  vocabulary, so the equivalence claim (gate selection minus the population
  that skips on clean runners) needs no interpretation layer.
- The pollution audit is conservative by construction: it costs one queue
  and accounting query, and it converts an assumption about fixture failure
  timing into evidence.

## Limits

- Single case, one harness (pytest markers). Other harnesses express the
  gate differently (filters, labels, build tags); the predicate diagnosis
  and the deselection-versus-override distinction transfer, the flags do
  not.
- The fixture design decides the side-effect ceiling. A gate whose fixtures
  submit before validating can pollute production before erroring; the audit
  in step 5 is the only check on that, and it cannot undo submitted work.
- The equivalence claim covers the runner CI uses for the gate job. A CI job
  that owns the marked suite (with the fixture up and an execution floor)
  has no local equivalent on a host without the fixture; that population
  stays CI-only evidence.
