# Notes: Query Tool Error Payload in the Data Stream

## Source

Observed in a read-only queue-state check while driving a pull-request backlog.
The check reported zero entries in the merge queue. A second query with the same
intent reported that one entry was already waiting.

The cause was a malformed query document: one extra closing brace. The query tool
returned a parse error and a nonzero exit status. The consumer read only standard
output.

## Reproduction shape

The general condition is a tool that writes its error document to the data
stream. The following shape reproduces it without any external service.

```bash
# A tool that writes an error document to stdout on failure.
$ tool query --expr 'broken'
{"errors":[{"message":"unexpected token at column 12"}]}
$ echo $?
1
```

A consumer that parses standard output only receives a mapping with an `errors`
member and no data member. A lookup of the expected data key fails, or a default
of zero applies.

```bash
# The failure reads as an empty result.
$ tool query --expr 'broken' 2>/dev/null \
  | python3 -c 'import json,sys; print(len(json.load(sys.stdin).get("results", [])))'
0
```

The exit status is one. The count is zero. The two do not describe the same
outcome.

## Why the status is easy to lose

A shell pipeline returns the exit status of its last command. When the last
command is a successful parser, the pipeline succeeds. The query tool's status is
discarded.

```bash
$ tool query --expr 'broken' 2>/dev/null | cat
{"errors":[{"message":"unexpected token at column 12"}]}
$ echo $?
0
```

`set -o pipefail` changes the pipeline result to the first failing stage.

## Why an inline expression increases the risk

A projection option that extracts one value from the document, such as a filter
expression, usually prints the error document unchanged when the request fails.
The caller then has a value of the wrong shape, not a missing value.

```bash
$ tool query --expr 'broken' -q '.data.results | length'
{"errors":[{"message":"unexpected token at column 12"}]}
$ echo $?
1
```

The printed value is not a number. If the consumer coerces it, the result is
again an authoritative-looking zero.

## Detection

- Compare a reported zero with any related command that reported an error.
- Search helpers for a parse that starts a pipeline.
- Search for a default on a lookup of a count or list key.
- Search for inline query or expression construction from shell arguments.

## Bounding the advice

The rule applies to any tool that shares one stream for data and errors. It does
not apply to a tool that writes all errors to a separate stream and returns an
empty data document only on success. That tool still needs the exit-status check
for transport failures, but the parse cannot misread an error as an empty set.

The rule does not require a change to the query tool. The consumer owns the
failure policy.

## Verification

The corrected pattern was verified against the same failing query:

```bash
$ set -o pipefail
$ if ! raw="$(tool query --expr 'broken')"; then echo "query failed" >&2; fi
query failed
```

The parse runs only after the status is zero. An absent outer field raises. A
nonempty error member raises.