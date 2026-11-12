# Notes: LLM Behavioral Benchmark Failure Channels

Supporting evidence from the 61-case, four-model prime-count sweep that produced
the main entry. Aggregated metrics only; no hostnames, paths, or credentials.

## The sweep

- Base word of 10 characters, 8 distinct letters; the target letter is drawn from
  those 8.
- Magnitude parameter: the letter's final count, one case per prime count across
  3..73 (20 prime values, avoiding accidental regularity in the count sequence).
- Placements: extras after the letter's first occurrence, after its last, or
  split between the two; one untouched baseline. One case per (value, placement)
  from a fixed seed = 61 cases.
- The answer contract: exactly one `Total: <letter> = <count>` line standing
  alone on its line. Structural arity: one asked-for letter means exactly one
  entry; two entries or an unrelated entry yield no prediction. Prose on the
  answer line yields no prediction. A repeated answer (two well-formed forms) is
  an error, not a choice.

## Per-model profile

| profile | scored | correct | accuracy | score | response loops | reasoning mentions |
| ------- | ------ | ------- | -------- | ----- | -------------- | ------------------ |
| no reasoning channel, writes everything in the response | 61 | 26 | 42.6% | 0.426 | 0 | n/a (0 credit earnable) |
| reasoning channel, repeat-and-stall | 61 | 19 | 31.1% | 0.285 | 840 response-side | 0/61 stated exactly once |
| reasoning channel, slow generator | 21 of 61 | 10 | 47.6% | 0.433 | 0 | 31/31 stated exactly once |
| reasoning channel, repeat-and-guess | 54 | 23 | 42.6% | 0.367 | 654 | rare |

Errors by model: 37 runner timeouts + 3 capacity 503s (slow generator); 7
timeouts + 4 capacity 503s (repeat-and-guess); none for the other two.

## Doom-loop signatures (repeat-and-stall model)

Worst reasoning traces, by loop count:

- 62 loops, 22.7k characters, exit at max tokens, empty response: counted the
  run one character at a time (`b — 1`, `b — 2`, ...) past the 28th.
- 58 loops, 21.4k characters, exit at max tokens, empty response: built two
  whole models of the string ("positions 6-42 = 37 b's, or positions 6-47 = 42
  b's? So which is it") and could not choose.
- 49 loops, 20.7k characters, exit at max tokens, empty response: re-counted a
  run it had already concluded ("45 total. Let me count it one more time").
- 45 loops, 19.2k characters, committed: paired the run ("ss ss ss ... (40
  pairs) = 80"), said "I keep getting 80. I'll go with 80" for a true count of
  73.

The repeat-and-guess model showed metacognitive guess-seeking: its reasoning
recalled exposures to similar prompts ("Usually answer 80? They often use
exactly 80 repeated letters?") and guessed from prompt length rather than
counting.

## Degradation curve by band (repeat-and-guess model)

| true count band | accuracy |
| --------------- | -------- |
| 3–13 | 11/13 (85%) |
| 17–31 | 6/10 (60%) |
| 37–53 | 4/15 (27%) |
| 59–73 | 1/15 (7%) |

## Difficulty-construction effect

Drawing the target letter from the whole alphabet (about 88% absent from the
base word, compensated with inserted runs at the word edges) measured 65.6%
correct with the first failing count at 29. Drawing from the letters that occur
in the word measured 54.1% with the first failing count at 17. The removed
cases were the easy ones: a long single-character run at a word edge is
trivially countable.

## Endpoint pacing

Replica counts changed during the campaign (3 → 1 for the fastest model). An
8-wide burst at a single-replica pool starved: 14+ minutes with no batch
completion, while a trivial probe to the same pool returned in 0.4 s. Serial
execution (one request in flight) completed the full sweep in about 8 minutes
for that model. The repeat-and-stall model at 2 replicas ran about 250–300 s per
long generation.

## Contract evolution (answer arity)

Three readings of the repeated-character answer, in order:

1. "Last entry wins" — accepted `r = 1, r = 5` as 5.
2. "Duplicate is malformed because the count is ambiguous" — rejected a parseable
   answer.
3. Structural arity (final): one asked-for item means exactly one entry; two
   entries yield no prediction, and an entry for an unrelated item answers a
   different question and yields no prediction.

The structural reading subsumes both earlier readings and extends to unrelated
entries.

## Score-channel effect

With mentions as an exactly-once existence check and loops at 0.1 per repeat
(capped 0.3):

- The no-reasoning-channel model: score equals accuracy (0.426 vs 42.6%).
- The repeat-and-stall model: score (0.285) sits 2.6 points below accuracy
  (31.1%), entirely from loop penalties.
- An earlier revision had 2–3 and 4+ mention penalty tiers; with the mention
  count at 0/1 those tiers were dead code and were removed.

## Spec/fixture alignment

An automated task audit reported a specification/verifier contradiction: the
instruction said a letter or digit after the answer form made it malformed,
while a fixture accepted `Total: r = 3 cats.` as 3. Three of three honest agent
trials failed on exactly that mismatch (one reached 10 of 11 tests), not on
capability. Resolution: adopt the stricter rule (the form stands alone on its
line), align the fixtures, and re-run.
