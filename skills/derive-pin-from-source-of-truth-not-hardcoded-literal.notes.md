# Supporting Notes: Derive a Pin From Its Source of Truth

These notes hold case evidence and commands for
[derive-pin-from-source-of-truth-not-hardcoded-literal.md](./derive-pin-from-source-of-truth-not-hardcoded-literal.md).
The main entry holds the rules.

## Evidence: literal assertions in quoted heredocs

Two integrity checks in a base-image build script asserted the runtime
version as a literal:

```bash
python3 - <<'PY'
import torch
assert torch.version.cuda == "13.1", torch.version.cuda
assert torch.__version__.startswith("2.11.0"), torch.__version__
PY
```

The same script also read the declared values from a sourced recipe file.
The quoted heredoc delimiter `<<'PY'` prevents shell expansion, so the
declared values could not reach the assertion. A declared value change would
have needed a matching edit in the script, and a missed edit would report a
false mismatch.

The fix passes the declared values as arguments:

```bash
python3 - "$BASE_CUDA_VERSION" "$BASE_PYTORCH_VERSION" \
        "$BASE_TORCHAUDIO_VERSION" <<'PY'
import sys

import torch

expected_cuda, expected_torch, expected_torchaudio = sys.argv[1:4]
assert torch.version.cuda == expected_cuda, torch.version.cuda
assert torch.__version__.startswith(expected_torch), torch.__version__
import torchaudio
assert torchaudio.__version__.startswith(expected_torchaudio), torchaudio.__version__
PY
```

Both argument forms were exercised directly before the commit:

```bash
bash -c 'V=13.1; python3 - "$V" <<"PY"
import sys
assert sys.argv[1] == "13.1"
print("ARGS_OK")
PY'
```

### Diagnostic

A literal assertion produces a failure message that names the artifact, not
the owner of the value. When the reported value looks correct by inspection,
check whether the assertion reads a literal instead of the owner.

## Evidence: materialized copy versus owner

The build wrote an evidence file from the sourced recipe:

```bash
cat > "$work_dir/base-build.env" <<EOF
BASE_CUDA_VERSION=$BASE_CUDA_VERSION
...
EOF
```

A separate check compared a supplied digest with the digest of the recipe
file:

```bash
expected_recipe_sha=$(sha256sum "$repo_dir/paths/to/base-recipe.env" | awk '{print $1}')
if [ "$expected_recipe_sha" != "$BASE_IMAGE_RECIPE_SHA256" ]; then
  echo "override recipe digest does not match the reviewed recipe file" >&2
fi
```

An earlier step read the digest from the evidence file. The evidence file was
written from a different recipe revision, so the two digests differed and the
check refused the input. The failure was correct. The error was to treat the
evidence file as the authority.

### Diagnostic

- The evidence file has a digest that is not the manifest digest.
- The check message names the manifest while the supplied value came from a
  copy.
- Resolve by reading the manifest, not by editing the check.

## Evidence: descriptive documentation turned into a rule

Documentation stated which toolchain lineage the deployment currently uses.
A guard was added to refuse any other lineage, with the claim that the
documentation required it. The documentation described present state. The
guard added a constraint that no requirement asked for, and it would have
blocked a legitimate move to a different lineage.

The correction removed the enforcement claim and left the statement as
current state:

> The deployment currently uses this lineage. This describes the current
> state, not a fixed requirement. Record a new lineage when the deployment
> moves.

### Diagnostic

Ask which sentence in the source states a requirement. If the only candidate
describes what is true now, the documentation does not authorize a blocking
check.

## Evidence: public artifact refused by its own seal

A package shipped a single distribution that served two roles: an
administrative control environment and a public client. The public client
publication scanned every installed file for the bytes of the administrative
root and refused the publication if a file carried them. That rule was
intentional: a file that carries the root can resolve a dependency outside the
public prefix.

Two kinds of file carried the bytes:

- **Packaged data.** A build force-include list copied control-side pool
  launch data into the package. Most of those files named an absolute
  administrative image and weight path.
- **A source constant.** One module held a mapping from cluster name to a
  retired-state path below the administrative root.

Because the data changed with each release, any release whose control data
nested under the administrative root failed its own publication. The gate
could never pass.

### What was rejected, and why

| Considered approach | Why it was not the answer |
| ------------------- | ------------------------- |
| Relax or exempt the seal | The seal is the requirement. An exception makes the public client unsafe to publish. |
| Scan the packaged data for the bytes and delete the matches during publication | The published tree then depends on the current data, so a later data edit changes the artifact with no code change. |
| Rewrite the protected literal in the installed file with the same run-time value | This changes the artifact after the build, and the bytes remain in the compiled files. It hides the condition instead of removing it. |
| Assemble the literal from parts in the source checkout | The run-time value is the same, the source no longer names the location, and the build still copies the bytes into bytecode. |

### What worked

1. The projection step omits one fixed path prefix that holds control-only
   data, and drops the matching inventory rows and the directory entry in the
   same loop. The inventory, the tree, and the seal scan then cover one
   population. The checks that run on the source archive stay in place, so a
   malformed excluded member still fails closed.
2. The exclusion is by path, not by content, so the public tree is identical
   for every release of the same source.
3. The sealed-data rewrite already in the projection (removing one key from a
   packaged profile) covered the remaining packaged hit.
4. The redundant constant was deleted. The run-time retired-state path already
   derived from the resolved administrative root. The one consumer, a
   control-side probe, now reads the administrative root from the cluster
   profiles and raises when no profile declares one, so a pruned profile set
   cannot silently remove the protection.

### Evidence boundary

- Two focused tests failed before the change and passed after it: the
  projection contract, and a guard that no shipped source file carries a
  declared administrative root.
- A real local build was projected and scanned: no protected bytes, no
  control-data members, and the packaged profiles remained.
- The plan review confirmed that the constant had one definition, one product
  consumer, and one test, and that the packages did not contain other
  protected payloads.
- The end-to-end publication against the live deployment root was an operator
  action outside the session. Its result was not observed, so this case does
  not establish verification beyond the local checks.

## Parametric assertions to keep

An assertion that compares an artifact with the value the owner declares is
not a literal, even when the owner currently holds a specific value. This
form keeps the built artifact honest across a declared change and should
stay:

```bash
python3 -c "import torch; assert torch.version.cuda == '$BASE_CUDA_VERSION'"
```

## Evidence: policy values moved from constants to a profile

Context: a control-plane service enforced one administrator group and one
service account, and both names were module constants and repeated literals
across many modules. An owner decision made both names required fields of the
cluster profile, and each check must enforce the declared value. This entry
records a planning session only. The issue was planned; no source change and
no test run confirmed the outcome.

The survey classified each check site into four groups. The groups are the
reason the durable rule is "classify first"; a blind literal sweep would have
broken the isolation in the second group.

| Class | Site shape | Decision |
| ----- | ---------- | -------- |
| Policy declaration copy | A runtime identity or ownership check that holds a project context or an already-loaded profile | Resolve the declared value. Existing resolver first. |
| Trust-isolation literal | A bootstrap file verifier that must run without project configuration and states that limit in its own module comment | Keep the literal and record the reason. |
| Stored-record vocabulary | A closed enum, a grant table that a database migration mirrors, and typed receipt fields | Keep. A declared change needs a migration or a schema change. |
| Test-only default | A classmethod default that only tests exercise | Keep, and record that no runtime caller uses it. |

Other decisions from this plan:

- The profile keys take the names that the requirement text uses, so a
  refusal names an unambiguous key. A generic name such as `principal` would
  be ambiguous beside the deployment-spec field of the same kind.
- The install preflight replaced a non-blocking note with a blocking finding.
  A check that degrades to a note cannot refuse a value the profile requires.
- Repair paths re-pin ownership from the resolved names, not from a constant.
- The SQL statements inside the bootstrap flow take the declared value as a
  bind parameter. A quoted SQL literal is the same copy as a Python literal.
- The residual constant is deleted when no check reads it. One constant stays
  as a function-parameter default for path-only helpers with no active
  profile.

Bounded searches used during the survey:

```bash
# Every runtime identity check.
grep -rn 'getpwnam(\|getgrnam(\|administrator_gid()' src --include=*.py

# Every literal that can be a policy copy.
grep -rn '"<service-account>"' src --include=*.py | grep -vE 'Literal\[|: str = |Field\(default='

# Field use before you delete a constant.
grep -rn "CONSTANT_NAME" src tests scripts docs
```

Evidence boundary: the survey read the source and the tests and ran no test.
The check-site count and the classification are a planning result, not a
verified behavior.

## Bounded searches used

```bash
# Find literal assertions that should read their owner.
grep -rn '"13\.1"\|== 13\.1\|startswith("2\.11\.0")' scripts/*.sh scripts/*.sbatch

# Confirm that a script is already parametric.
grep -n "expected_cuda" scripts/probe-image-gpu.sh
```

Run a syntax check on each changed script:

```bash
bash -n scripts/build-base-image.sh
```

## Verification limits

The fix was verified by syntax checks and direct exercises of the
argument-passing forms. The full image build that consumes the script had
not completed when these notes were written, so the end-to-end build path
remains unconfirmed.

## Evidence: policy literal promoted to a required configuration field

A planning session examined a request to move a policy literal into required
configuration. The literal was an identity and role value that a check site
compared with the name in a policy file. The requester wanted the value to
become a declared field, not a constant. The session produced the decision
rules in step 11 of the main entry.

### Evidence boundary

- The source survey was read-only.
- The output was a plan.
- No implementation was written.
- No test run confirmed any branch of the rule.
- The missing-field message probes were proposed, not executed.

Treat each branch as a hypothesis until an implementation and a test run
confirm it.

### Decision branches

1. **Authority.** The policy value moves to a declared field on the
   configuration record that the loader validates. The constant stays only as
   the schema default. A check site must refuse when no declaration exists,
   and it must never fall back to the constant. A fallback makes the constant
   the true authority again, and the drift returns.
2. **Key names.** When code compares two records field to field, reuse the key
   name that the other record already uses for the same concept. Do not reuse
   a similar key with a different contract. One example is a key that the
   system supplies only when it differs from the default. One name then has
   two rules, and a reader must know which record they hold.
3. **Failure shape.** A required field in a permissive schema breaks existing
   callers and test fixtures. Probe the missing-field message before you
   select the shape. The message must name the missing field. A cross-field
   validator that reports only "the model is invalid" does not satisfy this
   condition. Prefer a local per-field validator, or a modelled optional field
   with a validator that names the key.
4. **YAML comments.** Do not put a trailing inline comment after the first
   `key: value` line of a YAML file. The comment corrupts later parsing
   expectations in that file's readers. Put the prose in the plan or the
   documentation page instead.
5. **Enforcement scope.** Leave provenance literals unchanged, and list each
   one as an exception with its reason:

   - a `Literal`-typed default that records history
   - SQL text
   - a grant table that a database migration also encodes

   File a separate follow-up record for an external fixture that must also
   change. One example is a bootstrap verifier that cannot import the
   application package by design.
6. **Finish check.** Sweep every remaining literal with a targeted search, and
   map each hit to a stated reason:

   ```bash
   grep -rn "POLICY_NAME\|POLICY_ROLE" src scripts tests
   ```

   For a policy literal, the reason must name the declared field that
   replaced it, or the exception that keeps it.

### Known boundary: silent-default resolver entry

The entry `pola-consolidate-duplicated-silent-default-resolver.md` shares the
theme of this entry but has a different trigger. It handles a silent default
in a duplicated leaf expression, where a missing value selects an unrelated
resource. This entry handles a policy value that must become a declared
field. The two triggers overlap when a leaf expression holds a policy
literal. Use this entry for the authority and the failure message, and use
the resolver entry for the consolidation and the fail-loud choice. The
resolver entry is out of scope for this amendment.

### Evidence: a plan review found the constant re-introduced

A later review loop examined a plan for the same promotion. Four review
rounds changed the failure shape of the plan, not the code.

- The first plan set the new fields with `Field(default=<constant>)` and also
  required that an absent key fail validation. Both rules cannot hold.
- The next plans used strict fields with no default and added a source-scan
  invariant for the trust sites. Residue remained: an allowlist did not match
  the measured population, and the constructor census was incomplete.
- The last plan removed the documentation gap but added a classmethod that
  merged the constants into the payload when a key was absent. The plan then
  stated that the check path and the test fixtures call that classmethod. The
  enforcement path stopped reading the declaration, and the constant was
  again the effective authority.

Measurements from that loop, kept as a method rather than a fixed count:

- An `ast` walk that collects exact string constants found several hundred
  matches in one data module. A raw token search found more files and more
  hits, because it also counts imports and substrings. Match an exact string
  constant when you measure the enforcement population.
- A layer map listed the identity module below the configuration module in
  the dependency order. The plan claimed the opposite direction. Read the
  layer list and the current importers before you use a direction to justify
  a re-export.
