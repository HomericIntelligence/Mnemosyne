# tool-reference-local-match-first — supporting evidence

## Source case (generalized)

In an interactive session, a user asked for "the version of <name>" with several
typos elsewhere in the sentence. `<name>` was one letter short of a major
JavaScript runtime's name. The agent treated the name as a misspelling, ran the
runtime's version command, and reported that version. The user corrected: "i
mean, <name>, `~/<name>`" — a private helper script for compute allocations.

The probe that resolved the target:

```bash
ls ~/<name>            # found a directory with the script
head ~/<name>/<name>   # VERSION="x.y.z" hardcoded near the top
```

Decision-affecting details from the case:

- The private tool was a directory that contained a script. It was not installed
  on `PATH`, so `command -v <name>` alone would not have found it. The
  home-directory existence check was the decisive step.
- The sentence contained other typos ("ehat", "bing"), which made the
  misspelling hypothesis attractive. The tool name itself was spelled exactly.
- The private tool identified its own version with a `VERSION` constant in the
  script. Inspecting the artifact gave the correct answer without any assumption
  from the public tool's behavior.

## Privacy

The private tool name, the local path, and host details are withheld as
non-public identifiers. The generalized form keeps the full decision value:
exact-name local match outranks the typo-of-famous-tool interpretation.
