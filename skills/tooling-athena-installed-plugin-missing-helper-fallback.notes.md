# Notes: Athena installed plugin missing — helper fallback

Companion evidence for
[tooling-athena-installed-plugin-missing-helper-fallback](tooling-athena-installed-plugin-missing-helper-fallback.md).
Timeline, commands, and measurements live here; the operational rules live in
the main file.

## Timeline (one continuous session)

1. First learn delivery (corrupt-database recovery skill) ran with the
   installed Athena plugin fully present. Helpers resolved at the installed
   path; delivery completed and later merged.
2. Before the second learn delivery (bulk transcript export), the harness
   reported the Athena skill IDs unavailable ("skills are no longer
   available... must not be used"). The installed skills ROOT was gone —
   not just one plugin directory: `ls ~/.local/share/opencode/skills/` →
   "No such file or directory".
3. Same session continued with the learn contract read from a user-attached
   Athena source checkout (`skills/learn/SKILL.md`, 409 lines) and helpers
   executed from that checkout's `skills/advise/scripts/`:
   `resolve_knowledge_checkout.py` (read-only then `--mode write`) and
   `list_retrievable_skills.py` by absolute path.
4. Second delivery completed end to end on checkout helpers — corpus
   discovery (813 entries), worktree bound to the resolved default-branch
   commit, draft, full validation, DCO commit, push, PR — and later merged.
5. Third delivery (this entry) started hours later; the installed root was
   still absent. Re-probed again and still absent at close-out.

## Near-miss recorded as the failed approach

The first probe after the unavailability report targeted the deep helper
path (`<installed>/athena/skills/advise/scripts/`). Its failure was real but
ambiguous: identical for "helpers gone" and "entire plugin tree gone". The
root listing requested next showed the latter. If recovery had treated it as
a per-plugin problem (reinstall one plugin, locate a renamed directory), it
would have pursued a fix for the wrong scope while the correct fallback —
the source checkout — was already available.

## Helper behavior observed (checkout vs installed)

- Identical JSON schema from both sources. `--mode read-only` and
  `--mode write` responses carried `repository`, `revision`,
  `local_revision`, `refresh_state: updated`, `refresh_verified: true`,
  `checkout`, `checkout_state: clean`, `trust_basis`, and
  `freshness_limit`/`limitations` fields.
- The helpers are self-contained: stdlib plus git invocations against
  `--knowledge-root`. No harness plugin runtime, no network beyond the
  configured remote of the knowledge checkout.
- `list_retrievable_skills.py` output shape identical: flat
  `skills/<name>.md` main-file list, notes/history companions excluded
  (813 entries at the second delivery's bound revision).

## Cross-verification after merge

Both deliveries made on checkout helpers merged into Mnemosyne. One entry
was later amended by an independent learn run (v1.1.0, adding a new
decision branch) — normal corpus evolution, confirming nothing about the
fallback path made the artifacts exceptional.

## Boundaries

- The fallback relocates *where helper scripts come from*. It does not
  change knowledge-checkout binding, duplicate/open-PR discovery
  requirements, worktree isolation, validation, or DCO delivery.
- If no trusted Athena checkout exists on the host, report the limit; do
  not substitute another repository's tooling (learn skill rule).
- Helper vintage vs delivery base: writes bind to the knowledge
  checkout's resolved default-branch commit (re-resolved with
  `--mode write` before the worktree), so an older Athena checkout only
  affects helper code, not the delivery base.
- The environment's skill list can change repeatedly during a session;
  treat each "skills changed" notice as informational and re-classify the
  installed root only when starting a new dependency-resolution step.
