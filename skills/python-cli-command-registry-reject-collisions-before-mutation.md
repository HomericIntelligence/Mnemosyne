---
name: python-cli-command-registry-reject-collisions-before-mutation
description: "Make decorator-based CLI command registration reject primary-name and alias collisions atomically. Use when: (1) a registry maps both names and aliases into one namespace, (2) registration can overwrite an existing command, (3) duplicate aliases can partially mutate state before failure, (4) tests must cover every collision direction and unchanged-state guarantees."
category: architecture
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags: [python, cli, command-registry, aliases, collisions, atomicity, decorators]
---

# Python CLI Command Registry Atomic Collision Validation

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Prevent a decorator-based command registry from silently replacing commands through primary-name or alias collisions, and guarantee failed registration leaves the registry unchanged. |
| **Outcome** | A proposed validation and parameterized regression-test pattern was derived from the ProjectHephaestus `CommandRegistry`; implementation and CI remain pending. |
| **Verification** | unverified — source-reviewed plan only |

## When to Use

- A CLI registry stores primary command names and aliases in the same dictionary.
- Registering a new command can overwrite an existing primary name or alias.
- A command can repeat its own primary name in `aliases` or contain the same alias twice.
- Decorator registration performs multiple writes and a late collision could leave partially inserted state.
- Reviewers need exhaustive coverage of name-to-name, name-to-alias, alias-to-name, and alias-to-alias collisions.

## Verified Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a
> hypothesis until the focused registry tests and CI pass. The heading is kept
> for the current Mnemosyne validator; the actual status is `unverified`.

### Quick Reference

```python
def register(
    self, name: str, description: str = "", aliases: list[str] | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a command function, rejecting identifier collisions."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        alias_names = list(aliases or [])
        identifiers = (name, *alias_names)

        if len(set(identifiers)) != len(identifiers):
            raise ValueError("command name and aliases must be unique")

        collisions = set(identifiers).intersection(self.commands)
        if collisions:
            names = ", ".join(sorted(collisions))
            raise ValueError(f"command identifiers already registered: {names}")

        command = {
            "function": func,
            "description": description,
            "aliases": alias_names,
        }
        self.commands.update({identifier: command for identifier in identifiers})
        return func

    return decorator
```

### Detailed Steps

1. Treat a command's primary name and every alias as one identifier namespace. A collision is invalid regardless of whether either side was originally a primary name or alias.
2. Copy the caller-provided alias list before storing it. This prevents later mutation of the input list from changing registry metadata.
3. Validate uniqueness inside the new registration before consulting existing state. This catches `name` repeated as an alias and repeated aliases with a clear local error.
4. Intersect the complete identifier set with existing registry keys. Because existing aliases are keys too, this single check covers all four cross-registration collision directions.
5. Perform no registry writes until both validations pass. Then create one command metadata object and update all identifiers in one operation so every name resolves to the same object.
6. In tests, snapshot `registry.commands.copy()` before each rejected decorator application and assert exact equality afterward. Exception assertions alone do not prove atomicity.
7. Parameterize primary-to-primary, primary-to-alias, alias-to-primary, alias-to-alias, self-alias, and repeated-alias cases. Retain successful registration and alias lookup tests as compatibility coverage.

```python
@pytest.mark.parametrize(
    ("name", "aliases"),
    [
        ("build", []),
        ("b", []),
        ("deploy", ["build"]),
        ("deploy", ["b"]),
        ("deploy", ["deploy"]),
        ("deploy", ["d", "d"]),
    ],
)
def test_rejects_duplicate_names_and_aliases(name: str, aliases: list[str]) -> None:
    registry = CommandRegistry()

    @registry.register("build", aliases=["b"])
    def build() -> None:
        pass

    before = registry.commands.copy()
    with pytest.raises(ValueError, match="unique|already registered"):

        @registry.register(name, aliases=aliases)
        def duplicate() -> None:
            pass

    assert registry.commands == before
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Assign the primary name before checking aliases | Wrote `commands[name]` and then looped over aliases | A late alias collision can overwrite an existing entry after the new primary name has already been inserted, making failure non-atomic | Validate the complete namespace before the first mutation |
| Check only duplicate primary names | Guarded `if name in commands` but accepted all aliases | A new primary can collide with an old alias, and a new alias can collide with either an old primary or alias | Store names and aliases in one namespace and intersect all proposed identifiers with its keys |
| Convert identifiers directly to a set | Used a set for collision checks without comparing lengths first | A repeated alias or self-alias collapses silently, hiding invalid input within one registration | Compare set cardinality with the original identifier tuple before external collision checks |
| Assert only that `ValueError` is raised | Tested the error but not registry contents | An implementation can raise after partial insertion and still pass the test | Snapshot and assert exact unchanged state after every rejected case |

## Results & Parameters

Proposed ProjectHephaestus scope:

- Production seam: `hephaestus/cli/utils.py::CommandRegistry.register`.
- Focused suite: `tests/unit/cli/test_utils.py::TestCommandRegistry`.
- Error types: `ValueError` for within-registration duplicates and collisions with existing identifiers.
- Atomicity invariant: `registry.commands` is byte-for-byte equivalent at the mapping level before and after a rejected registration.
- Compatibility invariant: all identifiers for one successful registration reference the same command metadata, existing retrieval behavior remains unchanged, and no dependency or package-boundary change is needed.

Proposed verification:

```bash
uv run pytest tests/unit/cli/test_utils.py::TestCommandRegistry -q
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | CLI boundary-hardening plan | Source-reviewed on 2026-08-06; implementation and CI pending |
