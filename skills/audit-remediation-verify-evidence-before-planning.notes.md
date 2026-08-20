# Audit Remediation Evidence Verification — Case Notes

These notes retain project-specific evidence moved during
[Mnemosyne #3335](https://github.com/HomericIntelligence/Mnemosyne/issues/3335).

## Case index

| Case | Source | Status | Disposition |
| --- | --- | --- | --- |
| Partial frontmatter audit | [ProjectHephaestus #1553](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1553) | verified-local | One named target already compliant; fix only the missing target |
| Subpackage count/list | [#1449](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1449) | verified-local | Count was correct, listing short; synchronized same-defect docs and extended guard |
| Bare `gh` subprocess | [#1456](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1456) / [PR #1520](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1520) | verified-local | Source and AST guard already fixed; allowlist note only was planned |
| Deferred imports | [#1465](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1465) | verified-local | One of two cited imports already gone; hoisted only `tempfile` and reused behavior test |
| Fully stale package artifact | [#1468](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1468) | verified-local | Source, test dir, and named `.pyc` gone; existing structure guard covered recurrence |
| Publish attestation flag | [#1501](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1501) | verified-local evidence; remediation unverified | Line and action SHA stale, substantive flag absence valid |
| Setup commands | [#1502](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1502) | verified-local | Citation drifted ~26 lines; content finding still valid |
| API membership/history | [#1506](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1506), [#1507](https://github.com/HomericIntelligence/ProjectHephaestus/issues/1507) | unverified plans | Re-derived `__all__`; guard membership, label “Added” inference |

## Durable case details

For #1449, live discovery found 20 subpackages while a documented tree listed 19: the prose count
was right and the enumeration wrong. The implementation added the missing member, synchronized two
same-defect documents, and extended the existing tree-membership test using RED then GREEN. It did
not regex-pin prose counts.

For #1468, both directories and the named bytecode artifact were absent. A naive search for
`hephaestus.git` matched `hephaestus.github`; anchoring the package boundary removed every false
positive. The existing test-structure guard already rejected source-less test directories, so the
correct result was documentary closure rather than a new guard.

For #1501, the live publish action had moved and its pin changed, but the attestation flag was still
absent and `id-token: write` present. The planned assertion mirrored the repository's existing
workflow-content tests and added YAML structure checking. The external action input name was not
verified against the pinned `action.yml`, so implementation remained explicitly uncertain.

## Verification boundaries

Evidence collection was executed locally. Some resulting edits/tests were only planned; those rows
remain unverified. A focused pytest run that passed tests but tripped the global coverage floor was
reported as a passing behavior subset, not as a green repository gate.
