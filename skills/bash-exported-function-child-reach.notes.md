# Notes: bash-exported-function-child-reach

Supporting evidence for [bash-exported-function-child-reach](bash-exported-function-child-reach.md).
This file is not part of normal retrieval.

## Source evidence

- Context: a migration that removed an environment-variable transport from rendered batch scripts.
  One variable moved to a lowercase script local, another to a ready file, and another to a function
  local read by a single-quoted `bash -c` engine command.
- Observed failure: four batch render tests failed with an exit status of 143 and a missing per-rank
  evidence file. No test reported the real message.
- Real message after enabling xtrace and capturing the child's standard error:
  `environment: line N: <var>: unbound variable`, with `set -uo pipefail` active in the child.
- Diagnosis: the failing command was the registrar command inside an exported function. The reported
  line number was about 12 lines above the failing command because bash re-serialized the function:
  the file had about 170 lines in the function, the child imported 133.

## Serialization detail

`export -f name` stores the function as text. `declare -f name` in a child shows the imported form.
Multi-line commands, such as an engine command built with trailing backslashes, collapse onto one
line. Line numbers in child error messages therefore refer to the imported form, not the file.

Practical consequence: do not spend time reading the file at the reported line. Dump the imported
form first.

## Diagnosing commands

```bash
# Run the child with tracing.
SHELLOPTS=xtrace PS4='+L${LINENO}+ ' bash -c '<script text>'

# Dump the imported function text as the child sees it.
declare -f child_function

# List variables a function reads.
sed -n '/^child_function() {/,/^}/p' script.sh \
  | grep -oE '\$\{?[A-Za-z_][A-Za-z0-9_]*' | sed 's/\${\?//;s/}$//' | sort -u
```

## Reach matrix

| Consumer | Reaches the value when | Check |
| --- | --- | --- |
| Parent shell only | Normal assignment | none |
| `export -f` function in a child | Parent exported the value | `declare -f`, child xtrace |
| `bash -c 'literal $var'` child | Parent exported the value | single-quote the vector |
| `bash -c '...'` quoted argument, read later | Parent function exported the value | read from a file instead when possible |
| Harness that runs a slice | Harness supplies the value | assert the slice start line |

## Harness lesson

A harness that slices a generated script, for example from a host-list line onward, skips every
earlier assignment. The test then fails with a script defect message that is in fact a harness gap.
Fix both: export in the script for production, and supply the value in the harness environment.

## Stub fidelity lesson

An earlier transport passed the port through an environment variable. After the migration, the port
moved to a ready file and then into a function local. A stub that still read the engine argument read
`None`, because the argument was inside one quoted `bash -c` word. The correct stub read the ready
file. The number then matched the leased port.

## Time cost observed

- Time to first real message: about 20 minutes of wrong-line reading.
- Time from real message to fix: under 10 minutes, including one false positive from a stale stub.

## Verification limits

- Verified locally by live reproduction with full child output, then by the targeted tests.
- The full module suite was not part of this verification pass.
- No sensitive values, host names, or organization identifiers are recorded here.