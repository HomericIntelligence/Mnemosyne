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