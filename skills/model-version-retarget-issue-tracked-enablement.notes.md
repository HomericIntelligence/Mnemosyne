# Notes: model-version-retarget-issue-tracked-enablement

Session evidence for the main entry. The internal tracker, repository, issue
numbers, cluster names, and issue titles are proprietary and are omitted by
policy. The upstream model repository and revision below are public.

## Trigger

A request said "update the github issue to enable this version of deepseek v1"
and gave a Hugging Face link to `deepseek-ai/DeepSeek-V4.1-Flash-1017`. The
spoken token ("v1") did not match the linked artifact ("V4.1" family refresh).
The tracker's working directory was not a checkout of the tracked project, and
no issue number was given.

## Public upstream facts used

- Repository: `deepseek-ai/DeepSeek-V4.1-Flash-1017` (public).
- Positioning from the model card: a minor dated update to
  `deepseek-ai/DeepSeek-V4.1-Flash`, published 2026-10-17.
- Immutable revision at observation time (2026-10-18):
  `1bae0e1088993b9b82de08f59de5be5a34e42170`.
- Resolution path: `GET https://huggingface.co/api/models/deepseek-ai/DeepSeek-V4.1-Flash-1017`.
  Relevant top-level JSON fields: `sha` (default-branch commit),
  `lastModified`, `pipeline_tag`, `tags`.

## How the canonical issue was found

`gh` was authenticated. Two searches ran:

1. `gh search issues --author=@me "<family-name>"`
2. `gh search issues --author=@me --involves=@me "<family-name>"` (union form)

The keyword matched approximately ten open issues: one epic, dashboard-alias
and cache-policy bugs, a release issue, and dependent build, qualification,
policy, and approval issues. Reading bodies and comments showed that exactly
one issue carried a machine-meaningful repository binding line
("Model repository: [org/repo](URL)") plus an instruction to pin an immutable
revision during planning and qualification. That one was the release issue;
it was the edit target. The epic's tracked-work rows mention the family name
generically and stayed valid after the retarget.

Gate signals read before mutation (all from the canonical issue's comments):

- A dependency-blocked plan comment requiring re-planning before
  implementation.
- An operator capacity decision recorded as a comment.
- One pending automation review state.

These signals said: a body edit of the binding lines is acceptable and in
scope; the stale plan must be flagged, not re-planned in the same step.

## The edit that shipped

- Body fetched to a local file (`--json body --jq .body > body.md`, 4,040
  bytes). An earlier inspection used `.body[0:3500]` and ended mid-word;
  rewriting from that buffer would have destroyed the automation and
  acceptance sections.
- Two binding lines changed: the outcome sentence and the model-repository
  line. One sentence added: classification of the new repository as the dated
  minor update, plus the observed SHA with the UTC observation date.
- The "pin the immutable revision during planning and qualification"
  instruction stayed byte-identical.
- Title kept: it names the model family, which still applies.
- Written with `gh issue edit --body-file`, then re-fetched and grepped to
  verify the published content.

## Propagation shape

With user confirmation, five comments were posted:

1. Canonical release issue: decision record — new repository, SHA,
   observation date, list of downstream records now stale, explicit statement
   that scope, grants, and gates are unchanged.
2-5. The four dependent issues (image build, isolated qualification,
   fair-share policy, input approval): one identical-shape flag each, stating
   that their DeepSeek-V4.1-Flash inputs must resolve to the `-1017`
   repository at an exact pinned revision, and that the sibling model
   `DeepSeek V4 Pro 0813` (bound in the same bodies) is unaffected.

Flags instead of dependent body edits because the dependent bodies bind two
models; a scoped text edit could rewrite the sibling's inputs and defeat the
approval issue's decision-record function.

## Cross-check limits

- The HF `sha` field is a point-in-time default-branch commit. A later push
  moves it; that is why the observation date accompanies it and why planning
  must pin rather than trust this record.
- Issue discovery tied to the authenticated account's involvement. Issues the
  account neither authored nor touched fall outside `--author @me` /
  `--involves @me` searches.
