# Notes: Agent Git Authority Rule Authoring

## Source

A repository instruction file gained a git-operations section that listed the permitted and the
prohibited operations. An independent review of the merged text found two major defects and several
minor ones. A corrective change closed the major defects. A second change closed the remaining items
in the tags and the drift between two files.

## Evidence: `--force` disables the lease check

Reproduced in a throwaway repository on Git 2.56.0. Two clones wrote the same branch. Clone A pushed
its commit. Clone B then ran:

```bash
git push --force --force-with-lease=refs/heads/<branch>:<stale-oid> <remote> <branch>
```

Result:

```text
 + <b>...<a> <branch> -> <branch> (forced update)
```

Exit status 0. The commit from clone A was no longer reachable from the remote branch. The lease
value was the oid that clone B had seen before clone A pushed. Git reported no stale-lease failure,
because `--force` disables the lease check.

The same test with the lease only, and no `--force`, gave `stale info` and a non-zero exit. That
rejection is the expected safe behavior.

## Evidence: a branch push can send tags

Reproduced on Git 2.56.0 with a local bare remote:

```bash
git config push.followTags true
git tag -a v1 -m rel
git push -u origin HEAD:refs/heads/b1
git ls-remote ../remote.git
```

Output included:

```text
<oid>   refs/heads/b1
<oid2>  refs/tags/v1
<oid2>  refs/tags/v1^{}
```

A second branch push with `--no-follow-tags` sent the branch only. `git push -h` lists
`--[no-]follow-tags` on this version.

## Evidence: an allowed prefix cannot exclude a flag

A permission pattern such as `git push origin *` also permits a force push, because the pattern
cannot exclude a flag. The same limit applies in reverse: a rule that prohibits one flag does not
exclude the other spellings of the same effect. Both are the same defect at different layers.

## Evidence: a dropped closing keyword

A pull-request body edit removed a duplicate line and also removed the only closing keyword. The pull
request then merged without closing its issue, and the issue needed a manual close. The lesson is a
review step: read the body diff for the closing keyword before merge. This is a separate intent from
the git authority rules above and is not in the main entry.

## Evidence: the drift between two files

Two instruction files stated the force-push command. A correction changed one file to the leased
form and left the other file with a different, unsafe form. The fix was to state the command once and
link from the second file. No automated check read either file: a documentation build limited to a
separate directory did not cover them, so a broken anchor and a stale command both passed.

## Limits

- The push tests used local bare remotes and a single Git version.
- The denial behavior depends on the host. The entry states the rule text, not a host behavior.
- No automated check validates the relation between an instruction file and the commands it names.
  The reviewer must read the rule and run the adversarial spelling test.

## Related

- [Main entry](agent-git-authority-rule-authoring.md)
- [Force-push blocked: preserve the PR or reopen safely](tooling-force-push-blocked-reopen-as-fresh-branch.md)