# Evidence for planning-required-config-key-removal

## Source

One plan-review session for a feature issue that moved a required administrator group and a
required service account from module constants into cluster profile configuration.

The session ran four review rounds against the same plan.

## Round sequence (generalized)

1. **Round 0.** The plan set the new fields with `Field(default=<module constant>)` while asserting
   that an absent key fails validation. Both cannot hold. Decision: no-go.
2. **Round 1 and 2.** The plan moved to strict fields with no default, added an `ast`-based literal
   invariant for the trust sites, and enumerated the population. Residue: the allowlist did not
   match the measured population, and the constructor census was incomplete.
3. **Round 3.** The allowlist and census were corrected. A documentation gap remained for the
   required keys and the refusal behaviour.
4. **Round 4.** The plan removed the documentation gap but added `ClusterProfile.from_mapping`,
   a classmethod that merges the module constants into the payload when a key is absent. The plan
   also stated that "the check, the publisher, and the test fixtures call this wrapper". That makes
   the enforcement path accept a profile without the keys, so the constant is again the effective
   source for the install. The same revision listed a named test that asserts the fallback
   behaviour, while the file table said a missing key must fail. Decision: no-go.

## Measurement used

- The ast walk over the source package counted 21 files and 323 unique string constants equal to
  the account name; 294 of them are data rows in one module.
- The raw token appeared in 39 files and 381 times, including subpackage imports. This difference is
  why the literal test must match an exact string constant, not a raw token.
- The layer map listed the identity module as core and the config module as service, and one
  existing core module already imported the identity module. The plan claimed the opposite
  direction.

## Reusable decision value

- A default on a "required" field and a fallback constructor have the same effect: the constant
  survives. The criterion and the helper cannot both hold.
- Test-only churn is the correct place to absorb constructor edits. A production wrapper that
  exists to avoid test edits changes the enforcement path.
- A criterion check must run the strict loader. A check that runs the wrapper proves the wrapper.