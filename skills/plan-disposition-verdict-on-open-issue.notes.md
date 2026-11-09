# Notes: Disposition Verdict for an Open Issue

Supporting evidence for
[`plan-disposition-verdict-on-open-issue`](./plan-disposition-verdict-on-open-issue.md).

## Case Index

| Case | Verification | Contribution |
| --- | --- | --- |
| Open issue with a sealed plan, all deliverables absent | verified-local | Delivery question selects the requirements verdict |
| Sealed plan with an exact-set-equality rule | verified-local | Index re-derivation showed the plan set was stale |
| Plan citations for a configuration line, a test file, and module ranges | verified-local | Drift is recorded as a caveat, not as a verdict change |
| Input field containing fenced directives | verified-local | Untrusted text did not change the verdict |

## Case Details

### Delivery dominated an accurate-looking plan

The issue body was a long, internally consistent implementation plan with a plan marker and a
revision number. It named three new validation modules, four test files, a documentation rewrite, and
acceptance commands.

The delivery check showed that none of it was present. The planned modules were absent from the
package listing. The documentation kept its prose inventory and had neither of the two planned
sections. The existing helper module still used the old name-based matching and the old extension
list. The planned test files were absent.

The verdict was requirements work. The plan quality was not the deciding factor.

### Set equality failed against the index

The plan required one matrix row per tracked path, with exact set equality, and it supplied fourteen
rows. The index enumerated substantially more tracked paths in that directory. Many tracked items had
no row, and the plan's own rule would have failed on the intended deliverable.

Because the plan stated that the inventory is the authority, the correct handling was to note that
the rows must be re-derived before implementation. That is not a scope change, and it did not change
the verdict.

### Citations drifted

Three citations did not match the checkout:

- a configuration registration line number was lower than the current location;
- a cited documentation test file was absent, and the directory held only an unrelated test;
- module line ranges cited by the plan pointed at different code.

Each drift reduced confidence in the plan. None of them proved that the requested work existed. The
verdict stayed requirements work, and the drift went into the reason field with an explicit
instruction to resolve the values from the live repository.

### Untrusted directives stayed inert

One input field was a fenced block that stated it contained untrusted data. It also contained a
fenced directive about the expected answer. Only the authoritative instruction that supplied the
result shape was used. The fenced content was treated as evidence to verify, and the verdict rested
on checkout evidence only.

## Command Patterns

```bash
# Existence checks: one command and one result per deliverable.
ls <planned-package>/*.py | grep -E '<module-a>|<module-b>'
grep -rn '<planned-heading>' <planned-docs>

# Enumerable set: plan count against the index count.
git ls-files -- <planned-directory> | wc -l
git ls-files -- <planned-directory>

# Citation check: planned location against the current location.
grep -n '<planned-literal>' <configuration-file>
sed -n '<planned-range>p' <planned-module>
ls <planned-test-directory>/
```

## Evidence Limits

The session was read-only planning. Acceptance commands in the plan were not executed, because their
deliverables do not exist. The verdict rests on absence checks, the index enumeration, and citation
lookups.