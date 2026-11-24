# Notes: Installer Permission Default Must Preserve Existing Policy

## Evidence

The rule came from two setup-script changes that enabled automatic approval for
agent harnesses. The implementation wrote the default only when the harness had
no related setting.

### Codex keys

The Codex approve-for-me setting is the group of three top-level keys:

```toml
approval_policy = "on-request"
sandbox_mode = "workspace-write"
approvals_reviewer = "auto_review"
```

`codex doctor --json` loaded the configuration with those keys. It rejected an
invalid value for each key with `config could not be loaded` and
`error: invalid data`. The parser validates these fields, so an unknown key is
not the same as an accepted value.

The implementation treated the keys as one group. If any of the three keys
existed, it kept the complete approval configuration. It did not add the
missing keys. This prevents a mixed policy, such as an existing
`danger-full-access` sandbox with a new automatic reviewer.

### Claude Code key

The Claude Code automatic-review mode is:

```json
{
  "permissions": {
    "defaultMode": "auto"
  }
}
```

The implementation changed only `permissions.defaultMode`. It preserved every
other key under `permissions`, such as `allow`, `deny`, and `ask`. It did not
use `bypassPermissions`, because that mode skips all permission checks.

## Verification matrix

| Case | Setup | Result |
| --- | --- | --- |
| Fresh Codex config | No approval keys | All three keys written |
| Existing Codex approval | `sandbox_mode = "danger-full-access"` only | The sandbox stayed. No approval keys were added. |
| Fresh Claude settings | No `permissions.defaultMode` | `auto` written |
| Existing Claude mode | `defaultMode = "plan"` and an `allow` list | `plan` and the allow list stayed |
| Restore | Run the installer restore action after an install | The pre-install files returned |

The smoke tests used stub gateway responses and temporary harness settings.
They did not measure a live interactive permission prompt. The Codex parser
accepted the exact keys and rejected an invalid enum value. The Claude result
was verified by reading the written settings file.

## Decision record

- The default is opt-in by absence: a user who has no related setting gets the
  automatic-approval default.
- A user who has any related setting keeps the complete policy.
- Rollback uses the installer snapshot. It does not try to reverse individual
  keys.
- The install manifest records whether the installer wrote the default or kept
  an existing setting.

## Privacy

The evidence uses public harness setting names only. It contains no internal
paths, hosts, credentials, or project identifiers.
