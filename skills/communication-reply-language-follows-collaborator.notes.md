# Supporting notes: reply language follows the collaborator

The main entry carries the rule. These notes carry the evidence and the edge cases that give it
weight.

## Evidence

- One agent session received operator feedback of the form "do not use that language on an
  English-speaking collaborator's machine". The feedback was prompted by an agent writing a status
  table and progress lines in a non-default language during a long automated run.
- The trigger was not the operator's request language. The trigger was a mixed context: a
  multi-step automated workflow, harness and tool text from several sources, and one delegated
  agent with a non-default language in its own report.

## How the failure builds up

1. A delegated report, a tool summary, or a pasted block arrives in language `L`.
2. The agent treats the most recent input as a style cue and writes its own prose in `L`.
3. The next reply repeats `L` because the previous reply did.
4. After many turns, the whole thread is in `L`, and the operator cannot read their own run record.

Step 2 is the decision point. The language of a tool result, a subagent report, or a harness
message is data. It is not a style instruction.

## Separating prose from payload

| Part of the output | Language rule |
| --- | --- |
| Sentence prose, headings in a narrative reply | The collaborator's language |
| A status table's words | The collaborator's language, except values |
| Values, IDs, hashes, exit codes, file paths, commands | Verbatim |
| A quoted error, log line, or test name | Verbatim |
| A commit subject and body | The repository's working language, usually the language of the surrounding history |
| A PR body or issue comment | The language the reviewers of that repository use |

## Edge cases

- **A repository with a documented language policy.** Follow the policy. It is an explicit
  instruction from the owners and outranks the local inference.
- **An operator who asks for a translation.** Translate the requested part. Do not switch the
  whole collaboration.
- **A quoted string the reader must act on.** Keep it verbatim even when it is in another language,
  and add one sentence in the reader's language that says what it means.
- **Two collaborators, two languages.** Reply to each in their language. Do not force one person
  to read the other's language when the thread is shared; prefer one neutral language and say so.

## Verification status

The rule was applied after the feedback in the same session. There is no merged delivery that
exercises it yet, so the entry is `unverified`. Promote it to `verified-local` after a review cycle
shows the rule held across a multi-agent run.