# Notes: source-literal-census-profile-enforced

Supporting evidence for the 2026-11 plan-review instance. Generalized; no source-project,
module, or issue identifiers.

## Census shape observed

- The value was an account name, for example `service.account`. An `ast` walk over the source
  package found about 330 exact string constants in about 21 files, and about 45 constants that
  contained the value as a substring in about 27 files.
- One module held most of the exact constants: about 290 policy-table rows, one dataclass field
  default, four identity comparisons, and two message substrings.
- The remaining exact constants were: one `Literal` field on the deployment contract, two
  comparisons in that contract's own validator, four receipt-model `Literal` fields across three
  modules, one grant-table key, one string-valued enum, one SQL seed predicate, and about ten guard
  comparisons across six service modules and one command module.
- A `grep` line count of the same value returned a different number, because it counted JSON,
  docstrings, comments, and test files. The review rejected the `grep`-based count and the
  `grep`-based substring count in two consecutive rounds.

## Review findings that drove the revisions

1. A constant moved from a core module into a higher-layer schema module made the core module import
   the higher layer. The import-layer gate forbids that edge, and the plan's claim that the schema
   module imported only third-party and standard modules was false.
2. A conversion of a value comparison inside a context-free helper changed the numeric identity
   resolution of every caller. The reviewer required an exemption with a reason.
3. A dataclass field default was listed as a convertible data row and as a sentence in another
   section. The default is evaluated when the class is defined, so no configuration object can be in
   scope.
4. A census test that let a converted module hold zero literals could not detect a re-introduced
   literal. The reviewer required a per-file table with both counts.
5. A fallback that built a default configuration object when the file was absent turned a missing
   value into a pass-by-default. The reviewer rejected it as the behavior the issue supersedes, and
   the test lanes that used a cluster without a shipped file would have kept the degraded mode.
6. The guard functions would have loaded the configuration on each request. The reviewer required
   one bind-time read and one stated outcome for an absent file.
7. A host-presence check for the account had no scope item in the issue.

## Measurement recipe

```python
import ast
from pathlib import Path

exact: dict[str, int] = {}
partial: dict[str, int] = {}
for path in sorted(Path("src").rglob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            key = str(path)
            if node.value == "service.account":
                exact[key] = exact.get(key, 0) + 1
            elif "service.account" in node.value:
                partial[key] = partial.get(key, 0) + 1
```

Run the walk on the head commit before the change and again after the change. The difference must
equal the converted sites exactly, for both maps.

## Verification record

- The plan passed its final review with the census, the rule sentence, the guard table, and the
  named fixture edits in place.
- No conversion code was implemented in the session, so this entry stays `unverified`.