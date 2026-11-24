---
name: security-redact-path-normalized-credential-urls
license: BSD-3-Clause
description: "Redact credentials from URLs in subprocess failure diagnostics when path handling can remove one scheme slash. Use when: (1) a cwd, argument, or exception message is logged after Path conversion, (2) a redactor matches only :// and a URL can become https:/user:secret@host, (3) query strings or fragments can carry tokens, (4) a second redaction pass can corrupt already-redacted labels."
category: architecture
date: 2026-11-24
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - security
  - logging
  - redaction
  - credentials
  - url
  - pathlib
  - subprocess
  - diagnostics
  - python
---

# Redact Path-Normalized Credential URLs

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-24 |
| **Objective** | Keep bounded subprocess failure diagnostics useful without logging URL userinfo, query secrets, or fragments after path normalization. |
| **Outcome** | Successful in a Python subprocess-runner library: public failure logs kept command, cwd, stdout, and stderr context while credential-bearing URLs stayed redacted through command-error and timeout paths. |
| **Verification** | **verified-local** — focused runtime, diagnostics, and Git tests passed, including standard URL, path-normalized URL, SCP-like form, and second-pass cases; Ruff, mypy, and diff checks passed; a separate post-merge audit found no regression. |

## When to Use

- A subprocess failure handler logs a URL-bearing cwd, argument list, standard output, or standard error.
- A value can pass through `pathlib.Path` or another normalization layer before it reaches the log sink.
- An existing redactor recognizes `scheme://user:secret@host`, but the sink can receive `scheme:/user:secret@host`.
- A URL query string or fragment can contain a token, key, or password.
- A whole-message redaction pass runs after field-level redaction and can change already-redacted labels.
- A static analyzer does not recognize the custom redactor as a sanitizer.

Do not use this skill to suppress a real static-analysis finding. Use it to correct redaction and to evaluate a separately authorized false-positive disposition.

## Verified Workflow

### Quick Reference

Match the representation the sink receives, not the original URL text:

```python
import re

# Accept a standard "://" URL and a Path-normalized ":/" URL.
_URL_TOKEN = re.compile(r"(?P<scheme>[A-Za-z][A-Za-z0-9+.-]*):/{1,2}[^\s<>'\"]+")
# Match the SCP-like form when the command accepts a remote path.
_SCP_REMOTE = re.compile(
    r"(?<![\w.-])(?P<userinfo>[^@\s/:]+:[^@\s]+)@(?P<host>[^:\s/]+):"
)

def redact_url(text: str) -> str:
    """Remove userinfo, query, and fragment from URL-like tokens."""
    def replace(match: re.Match[str]) -> str:
        raw = match.group(0)
        scheme = match.group("scheme")
        rest = raw[len(scheme) + 1:].lstrip("/")
        authority, slash, tail = rest.partition("/")
        host = authority.rsplit("@", 1)[-1]
        path = "/" + tail if slash else ""
        path = path.split("?", 1)[0].split("#", 1)[0]
        return f"{scheme}://{host}{path}"

    text = _URL_TOKEN.sub(replace, text)
    return _SCP_REMOTE.sub(r"\g<host>:", text)
```

Apply this function to each diagnostic field at its log sink. Redact once per field, then truncate the result. Narrow the URL token class to the delimiters in your log format so that it does not consume unrelated punctuation.

### Suggested Approach

1. **Inventory every failure sink and field.** Search for the exception handlers and log calls that render cwd, command, stdout, stderr, and exception text. Include `check=False` and timeout paths. A credential can appear in any rendered field, including a directory name.

2. **Render the value exactly as the sink receives it.** Convert the value with the same operation the logger uses, such as `str(path)` or a joined command list. Do not test a raw URL string if production logs a `Path`.

3. **Cover both slash forms.** A `Path` replaces the double slash after the scheme with one slash. `urlsplit` treats the result as a path, not a network URL, so a parser that requires `//` cannot see the userinfo. Match `:/{1,2}` before any further parsing. Also cover SCP-like `user:secret@host:path` text when the command accepts it.

4. **Remove complete credential carriers.** Drop userinfo, the complete query string, and the fragment. Keep scheme, host, port, and path when they identify the failure. Do not keep a denylist of query names: a new provider can add a new secret name. If the path itself can carry a credential, omit the path too.

5. **Redact each field once, at the sink.** Format the bounded diagnostic context, redact each field, then truncate. Do not add a second whole-message redaction pass over text that already contains `<redacted-value>` labels. A second pass can corrupt escaped multiline values and existing labels.

6. **Preserve the operation contract.** Keep the original exception object and its identity. Keep `check=False`, return-code, cancellation, logging enablement, and timeout behavior unchanged. Redaction changes only what the diagnostic reports.

7. **Test the two common exception routes.** Inject a synthetic credential URL through a `Path` cwd for both `CalledProcessError` and `TimeoutExpired`. Assert that the secret is absent from the complete log record, the bounded stderr tail remains, and the original exception remains available to the caller.

8. **Test idempotence and labels.** Run the sink twice, or feed the already-redacted output back through the same formatter. Assert that markers such as `api_key=<redacted-value>` and `Authorization: Bearer <redacted-value>` do not change. This proves that no outer pass re-redacts escaped content.

9. **Check the detector separately.** A static analyzer for clear-text logging can require a built-in sanitizer and can ignore a correct custom redactor. Record the verified false-positive flow and get owner authorization before a dismissal or suppression. Do not suppress the detector in general, and do not place a suppression on the formatter if the alert is on the log sink.

10. **Assemble scanner-sensitive test values at runtime.** A complete synthetic private-key or credential literal in a test file can fail a history-aware secret scan, even when the value is fake. Build the fixture from parts at test runtime and assert that the assembled value is nonempty and present before redaction. A scanner failure that finds only the runtime-assembled value is not a leak.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Match only `scheme://` | Used a URL regex that required two slashes after the scheme | `str(Path("https://user:secret@host/path"))` becomes `https:/user:secret@host/path`; the credential survived in the cwd field | Normalize the test the same way as the sink and accept `:/{1,2}` |
| Parse with `urlsplit` first | Expected the parser to find the network location | A one-slash form has no `//` authority, so the userinfo becomes path text and the credential remains | Detect and restore the slash form before parsing, or use a representation-aware regex |
| Add a second whole-message redaction pass | Ran field redaction and then redacted the complete formatted message | The second pass changed already-redacted escaped labels and could corrupt multiline values | Redact exactly once per field at the sink; prove idempotence with a regression test |
| Use a custom redactor as a static-analysis sanitizer | Expected the logging analyzer to accept the helper automatically | The analyzer did not model the helper as a sanitizer and raised clear-text logging alerts | Verify the flow, then use a separately authorized false-positive disposition; do not weaken the detector |
| Put a real-looking private key in a test module | Used a contiguous synthetic key literal for a redaction fixture | A history-aware secret scan flagged the test literal and earlier commits | Assemble scanner-sensitive fixtures at runtime and assert non-vacuity |
| Trust one exception route | Tested only `CalledProcessError` | Timeout handlers often build their own command, cwd, and output context | Test every exception path that publishes diagnostics |

## Results & Parameters

### Diagnostic Contract

| Field | Keep | Remove |
|-------|------|--------|
| cwd | Scheme, host, port, path that identify the location | Userinfo, query, fragment |
| Command | Program, subcommand, non-secret options | URL userinfo, query, fragment, token arguments |
| stdout/stderr | A bounded tail with failure context | Credentials, complete secret-bearing URLs |
| Exception identity | Original exception and attributes for in-process callers | Raw exception text at an external log sink |

### URL Cases

| Input representation | Expected diagnostic shape |
|----------------------|---------------------------|
| `https://user:secret@host.example/path` | `https://host.example/path` |
| `https:/user:secret@host.example/path` | `https://host.example/path` |
| `https://user:secret@host.example/path?token=value#fragment` | `https://host.example/path` |
| `user:secret@host.example:path` | `host.example:path` |
| Missing scheme or malformed authority | A fixed non-secret placeholder |

### Expected Output

```text
Command failed with exit code 1
cwd=https://host.example/path
stderr_tail=<redacted-value>
api_key=<redacted-value>
Authorization: Bearer <redacted-value>
```

The exact secret value is absent. The bounded stderr tail and useful labels remain.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Python subprocess-runner library | Credential-bearing subprocess failure logs through command-error and timeout paths | Final head was independently audited after merge. Focused runtime, shared diagnostics, and Git tests covered standard URL, path-normalized URL, SCP-like form, query/fragment, second-pass labels, and bounds. |

## References

- [Python `pathlib` path representation](https://docs.python.org/3/library/pathlib.html)
- [Python `subprocess` exceptions](https://docs.python.org/3/library/subprocess.html#exceptions)
- [CodeQL clear-text logging query](https://codeql.github.com/codeql-query-help/python/py-clear-text-logging-sensitive-data/)
- [Credential-safe diagnostics for broker health](./nats-observability-redact-credential-bearing-diagnostics.md)
- [Escape untrusted values in logs](./security-escape-untrusted-values-in-logs.md)
- [Preserve primary failure diagnostics](./preserve-primary-failure-diagnostics.md)