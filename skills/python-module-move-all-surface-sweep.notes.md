# Python Module Move All-Surface Sweep — Supporting Notes

These notes hold supporting evidence. The main skill holds the rules.

## Reference-pattern evidence (2026-11-05, v1.1.0 amendment)

### Observation

A split of one large module into two sibling modules kept the old module name as an
import alias at the package re-export layer. The plan's done criterion was a
zero-reference sweep whose alternatives included `base as stage_base(_mod)?`.

The implemented tree had four correct hits from that alternative:

| Hit | New form | Verdict |
| --- | --- | --- |
| Parenthesized re-export in a type-checking block | `stage_base as stage_base_mod` | Correct new import of the moved module |
| Absolute import in a sibling module | `import <package>.stage_base as stage_base_mod` | Correct new import |
| Test module alias | `import <package>.stage_base as stage_base` | Correct new import |
| Coordinator-edge test alias | `import <package>.stage_base as stage_base_mod` | Correct new import |

The pattern also matched a new module name of the form `stage_<old>` in a new module
path, which cannot be a stale old-location reference.

### Why the pattern failed

The pattern was pre-run on the tree before the move. In that state every match was a
stale reference, so the pattern looked correct. The move changed which strings are
stale: the alias form survived at the new location.

### Corrected pattern

The corrected gate matched only old locations:

```text
<old-package>\.<old-module>|<old-package>/<old-module>|from \.{1,2}<old-module> import|from <package> import <old-module>
```

Result: zero matches. A separate search for the old module name found only the four
new-form imports and the new module names.

### Failure consequence

Reporting the plan-literal pattern as a failure blocks a correct change. Reporting it
as a pass without inspection hides a real stale reference that presents in one of the
adjudicated forms. Name each hit and the new form that explains it.

## Results note

The verified case bound this amendment to one executed change: the split succeeded,
the focused suite passed, the affected suite passed, static checks passed, and the
change opened a pull request. The reference-sweep correction was the only change that
the plan needed at execution time.