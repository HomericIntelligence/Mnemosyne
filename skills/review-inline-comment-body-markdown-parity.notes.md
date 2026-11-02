# Inline comment body Markdown parity - supporting evidence

## Source context

A terminal pull-request review delivery prepared a review carrier with a visible
content section, an anchor annex, and an inline comment batch. The carrier and the
visible content parsed clean. Carrier extraction succeeded and returned the expected
state digest. The inline comment batch was then handed to the delivery helper.

## Observed failure

The delivery helper rejected the batch during pre-publication validation with:

```text
The Athena review-finding marker is inside an open Markdown block.
```

The rejection names the marker, but the cause was earlier in two bodies. Three comment
bodies contained a generic angle-bracket placeholder, such as a user-home segment or a
session-file name. The Markdown validator read each placeholder as an unclosed inline
HTML tag. Because the block stayed open, the finding marker that followed was not a
top-level line.

## Repair

1. Re-parsed each body with the helper's own validator in isolation. One body passed
   and two failed, which localized the defect.
2. Wrapped each placeholder in inline code spans.
3. Re-parsed every body. All passed.
4. Rebuilt only the comment list. The state envelope, the visible content, the finding
   identifiers, the finding locations, and every digest stayed unchanged.
5. Retried delivery. It succeeded.

The failed attempt made no forge mutation. The forge showed zero reviews and zero
inline comments between attempts.

## Isolated parser behavior

| Body | Result |
| ------ | -------- |
| `See /home/<user> for details.` | Rejected: open HTML block |
| ``See `/home/<user>` for details.`` | Accepted |
| `Example:` followed by an unclosed triple-backtick fence | Rejected: open code fence |
| The same example with a closed fence | Accepted |

## Prevention

Run the per-body parse check as a gate before publication. It costs one local process
and no forge write. It also catches the marker-inside-block class before the helper
reports it.

Do not infer body validity from a carrier extraction. The carrier parser, the visible
content parser, and the inline body validator are separate call sites. Keep them
separate in your checks too. Call the helper's function rather than reimplementing the
rule.