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

## Evidence: declared identity values and a downgraded check

This case comes from an implementation-planning session. It is evidence for
the decision the plan selected, not for a completed change. No build or test
run confirmed the result.

Two identity literals existed in several modules: an administrator group name
and a service account name. The active profile record had no field for either
value. Enforcement was split across three sites:

- One installer refused the install when the group was absent.
- A later change turned that refusal into a non-blocking note, because the CI
  runners lack the group.
- A separate startup check resolved the account through the context record and
  refused on a mismatch.

The three sites therefore disagreed on the failure mode, and each held its own
copy of the value. The note did not make the runner pass a real requirement.
It removed the only signal that no profile declared the value.

### Planned resolution

1. The profile declares the administrator group and the service account as
   required fields. An absent field is a validation error that names the
   field.
2. Every enforcement site reads the profile value or the context record value.
   No site compares against a literal.
3. One bind point combines the resolved context and the active profile, then
   compares the declared value with the record value. It raises with the
   profile key, the expected value, and the observed value.
4. The refusal comes back for an active profile that requires the value. The
   degraded note remains only where no profile is active.
5. The test harness declares the host identity of the harness, such as the
   primary group and account of the invoking user, in its stub. The production
   check stays strict.

### Literals that stay literal

| Kind | Why the literal stays |
| ---- | --------------------- |
| Schema default anchor | No profile is active before the schema loads, so the default is the only declaration |
| Closed record type | The value is part of the record contract that the writer emits |
| Audit-writer attribution | The writer must state which identity it attributes the record to |

### Diagnostic

- Two check sites report different outcomes for one missing value.
- A value appears in a note or a warning and no profile field declares it.
- The message names the host, not the profile key that should hold the value.

## Parametric assertions to keep

An assertion that compares an artifact with the value the owner declares is
not a literal, even when the owner currently holds a specific value. This
form keeps the built artifact honest across a declared change and should
stay:

```bash
python3 -c "import torch; assert torch.version.cuda == '$BASE_CUDA_VERSION'"
```

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

The declared-identity case was an implementation plan. No build, test, or
deployment observed the planned bind point or the restored refusal. Treat
that section as decision evidence and not as a verified result. The earlier
cases in these notes keep their own stated limits.