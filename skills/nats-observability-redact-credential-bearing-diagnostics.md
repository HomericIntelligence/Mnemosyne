---
name: nats-observability-redact-credential-bearing-diagnostics
license: BSD-3-Clause
description: "Keep NATS health responses and logs useful without publishing URL credentials, query secrets, fragments, or raw exception text. Use when: (1) a subscriber health payload includes its configured broker URL, (2) logger.exception or str(exception) can expose tokens, (3) operators still need stable broker identity, lifecycle, stream, circuit-breaker state, and failure category, (4) in-process callers must retain the original exception."
category: architecture
date: 2026-08-05
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - nats
  - observability
  - health
  - logging
  - secrets
  - url-redaction
  - exception-classification
  - circuit-breaker
  - python
  - security-boundary
---

# Credential-Safe Runtime Diagnostics for NATS Subscribers

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-05 |
| **Objective** | Prevent NATS health responses and logs from exposing URL userinfo, query secrets, fragments, or raw exception messages while retaining useful broker identity and subscriber state. |
| **Outcome** | Proposed boundary design: use the original URL only for connection, reconstruct an allowlisted diagnostic URL, retain the original exception in-process, and publish a bounded failure category through health and logs. |
| **Verification** | **unverified** — the design, regression cases, and acceptance commands were specified, but the implementation, local tests, type checking, and CI were not executed in the source session. |

## When to Use

- A health endpoint publishes a NATS URL that may contain `user:password@host`, query tokens, or fragments.
- A startup log interpolates the configured broker URL.
- `health_dict()` or another JSON boundary serializes `str(last_error)`.
- `logger.exception`, `exc_info=True`, or an interpolated exception can copy secret-bearing provider messages into externally retained logs.
- Operators need safe broker identity, lifecycle state, stream, circuit-breaker state, retry timing, subject, or sequence without the raw failure text.
- Existing callers inspect a `last_error` property and compatibility requires preserving the original exception object.
- A security fix must not mutate the credential-bearing URL passed to `nats.connect`.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until the implementation passes the focused regressions, the full NATS unit suite, static checks, and CI.

The marketplace validator currently requires a literal `## Verified Workflow` section. The
unverified procedure therefore appears under that compatibility heading below.

## Verified Workflow

> **Warning:** This is a proposed workflow, not a verified one. The heading is retained only for marketplace-schema compatibility.

### Quick Reference

```python
from urllib.parse import urlsplit, urlunsplit


def _diagnostic_nats_url(url: str) -> str:
    """Return a credential-free NATS URL suitable for health and logs."""
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return "<invalid-nats-url>"

    if not parsed.scheme or hostname is None:
        return "<invalid-nats-url>"

    display_host = f"[{hostname}]" if ":" in hostname else hostname
    netloc = display_host if port is None else f"{display_host}:{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
```

```python
# Keep both values under the existing state lock.
self._last_error: BaseException | None = None
self._last_error_kind: str | None = None

def health_dict(self) -> dict[str, Any]:
    """Return a JSON-serialisable health snapshot with safe diagnostics."""
    with self._state_lock:
        state_name = self._state.value
        error_kind = self._last_error_kind
        last_msg = self._last_message_at
    return {
        "state": state_name,
        "last_error": error_kind,
        "last_message_at": last_msg,
        "url": _diagnostic_nats_url(self._config.url),
        "stream": self._config.stream,
        "circuit_breaker_state": self._circuit_breaker.state.value,
        "uptime_seconds": time.monotonic() - self._started_at,
    }
```

```python
# Authentication still uses the untouched configured URL.
nc = await nats.connect(self._config.url, ...)

# External diagnostics use only sanitized identity and bounded categories.
logger.info(
    "NATSSubscriberThread started (url=%s, stream=%s, durable=%s)",
    _diagnostic_nats_url(self._config.url),
    self._config.stream,
    self._config.durable_name,
)
logger.error(
    "NATS connection error, retrying in %.1fs (kind=connection_error)",
    backoff,
)
```

### Detailed Steps

1. **Inventory every publication boundary.** Search the subscriber for the configured URL,
   `str(last_error)`, exception interpolation, `logger.exception`, and `exc_info`. Distinguish
   the connection call from health, log, metric, and API publication.

   ```bash
   SUBSCRIBER_PATH="<subscriber-module>"
   rg -n 'config\.url|str\(.*last_error\)|logger\.exception|exc_info' \
     "$SUBSCRIBER_PATH"
   ```

2. **Preserve the operational URL.** Keep `NATSConfig.url` unchanged and continue passing it
   directly to `nats.connect`. Sanitizing the configured value itself can break authentication
   and silently changes runtime behavior.

3. **Reconstruct an allowlisted diagnostic URL.** Parse with `urlsplit`, read `hostname` and
   `port` inside the `try` because malformed brackets or ports can raise `ValueError`, bracket
   IPv6 hosts when rebuilding the netloc, and use `urlunsplit` with empty query and fragment.
   Preserve only scheme, hostname, port, and path. Do not maintain a sensitive-query-key denylist:
   unknown providers and future options can introduce new secret names.

4. **Separate forensic state from publication state.** Retain the original
   `BaseException | None` for in-process compatibility and add a bounded category under the same
   lock. The raw object is not a serialization source.

   ```python
   def _record_error(self, exc: BaseException) -> None:
       """Record a connection failure and transition to DISCONNECTED."""
       with self._state_lock:
           self._last_error = exc
           self._last_error_kind = "connection_error"
           self._state = SubscriberState.DISCONNECTED
       self._increment_error_metric("connection")
       self._emit_metrics()

   def _record_terminal_error(
       self,
       exc: BaseException,
       *,
       kind: str = "terminal_error",
   ) -> None:
       """Record a classified terminal failure and transition to ERROR."""
       with self._state_lock:
           self._last_error = exc
           self._last_error_kind = kind
           self._state = SubscriberState.ERROR
       self._increment_error_metric("terminal")
       self._emit_metrics()

   def _record_handler_error(self, exc: BaseException) -> None:
       """Record a handler failure without changing delivery semantics."""
       with self._state_lock:
           self._last_error = exc
           self._last_error_kind = "handler_error"
       self._increment_error_metric("handler")
       self._emit_metrics()
   ```

5. **Classify at the boundary where context is known.** Use only the closed set
   `connection_error`, `handler_error`, `circuit_breaker_open`, `terminal_error`, and
   `shutdown_timeout`. A recorder called from a generic outer boundary defaults to
   `terminal_error`; a circuit-breaker or timeout path passes its explicit kind.

6. **Replace traceback-bearing logs with fixed messages.** Do not interpolate `exc`, call
   `logger.exception`, or pass `exc_info=True` on this externally retained log surface.
   Preserve only explicitly reviewed context such as retry delay, lifecycle transition, stream,
   subject, sequence, and bounded kind.

   ```python
   except Exception as exc:
       self._record_handler_error(exc)
       logger.error(
           "Handler raised on subject %s (seq=%d, kind=handler_error)",
           event.subject,
           event.sequence,
       )
   ```

   ```python
   error = TimeoutError(
       "NATS subscriber thread did not stop within "
       f"{effective_timeout:g}s — still running"
   )
   self._record_terminal_error(error, kind="shutdown_timeout")
   logger.error(
       "NATS subscriber shutdown timed out after %gs (kind=shutdown_timeout)",
       effective_timeout,
   )
   ```

7. **Keep delivery semantics unchanged.** If the subscriber intentionally acknowledges a
   message after the handler raises, preserve that placement. Error redaction changes the
   observability boundary, not at-most-once versus at-least-once policy.

8. **Test both absence and retained utility.** Use credential-bearing URLs and token-bearing
   exceptions. Assert that secrets are absent from `health_dict()` and `caplog.text`, the
   sanitized URL and bounded kind are present, the original exception remains identical through
   `last_error`, and lifecycle, stream, circuit-breaker, ack, and message-coordinate behavior
   remain unchanged.

9. **Document the trust boundary.** State that logs and health fields are observability signals,
   not durable exception storage. Code needing full detail may inspect the in-process exception,
   but must not copy its text into an external diagnostic.

10. **Re-run leak-oriented searches after implementation.** Confirm that the raw URL remains only
    at the connection boundary and no health or log path serializes the exception.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Publish `str(last_error)` in health JSON | Reused the convenient exception message as a diagnostic field | Provider and handler exceptions can embed credentials, query tokens, payload fragments, filesystem paths, or other untrusted text | Publish a bounded category; retain the exception only in-process |
| Use `logger.exception` for every failure | Captured the message and traceback for post-mortem debugging | The traceback includes the raw exception string and can cross retention, aggregation, and support boundaries | On externally retained logs, use fixed messages and reviewed structured context without `exc_info` |
| Log the configured broker URL | Included `NATSConfig.url` directly in startup diagnostics | URL userinfo, queries, and fragments can carry secrets | Reconstruct a diagnostic URL from an allowlist of parsed components |
| Redact only known query keys | Removed names such as `token` and `password` | A denylist is incomplete as providers add aliases or arbitrary query credentials | Drop the complete query and fragment |
| Strip URL text with regex or string splitting | Removed text around `@`, `?`, or `#` manually | Userinfo, IPv6 brackets, percent encoding, malformed ports, and path handling make ad hoc parsing brittle | Use `urlsplit` and `urlunsplit`; fail closed on malformed input |
| Sanitize `NATSConfig.url` before connecting | Replaced the authoritative configuration with its display form | Credentials needed for authentication disappear and runtime semantics change | Sanitize only at publication sites |
| Replace the original exception with its kind | Stored only `connection_error` or `handler_error` | Existing in-process diagnostics lose exception identity and structured attributes | Store raw exception and bounded publication kind separately under the same lock |
| Redact all context | Removed stream, state, circuit-breaker state, retry delay, and message coordinates | Operators could no longer distinguish broker identity or locate the failing lifecycle path | Use an explicit safe-context allowlist, not empty diagnostics |

## Results & Parameters

### Diagnostic Contract

| Surface | Retain | Remove |
|---------|--------|--------|
| NATS connection | Original configured URL | Nothing; this is the trusted operational input |
| Health `url` | Scheme, hostname, port, path | Userinfo, complete query, fragment |
| Health `last_error` | Bounded error category or `None` | Exception message and traceback |
| In-process `last_error` | Original exception object and identity | Nothing; callers must keep it in-process |
| Logs | Fixed event, safe retry/lifecycle/message context, bounded kind | Raw configured URL, exception interpolation, traceback |

### Bounded Categories

| Kind | Boundary |
|------|----------|
| `connection_error` | Connect/subscribe failure, including sustained failures that open the breaker |
| `handler_error` | User handler raised while delivery policy continues |
| `circuit_breaker_open` | Work was rejected because the breaker was already open |
| `terminal_error` | Defensive unhandled terminal failure |
| `shutdown_timeout` | Subscriber thread failed to stop within its bounded timeout |

### URL Cases

| Input | Diagnostic output |
|-------|-------------------|
| Credential URL assembled as `"tls://alice:secret" + "@broker.example.com:4222/jetstream?token=value#fragment"` | `tls://broker.example.com:4222/jetstream` |
| `nats://[2001:db8::1]:4222/events?credential=value` | `nats://[2001:db8::1]:4222/events` |
| Missing scheme/host, invalid bracket, or invalid port | `<invalid-nats-url>` |

The path is intentionally retained because it is part of the proposed broker identity contract.
If an integration places credentials in URL paths, revise that contract and its tests before
deployment; do not assume path components are universally non-sensitive.

### Proposed Acceptance Layers

1. Run focused health-URL and startup-log tests with credential-bearing URLs.
2. Run connection, circuit-breaker, handler, and shutdown tests with token-bearing exceptions.
3. Run the complete subscriber/NATS unit-test package.
4. Lint and type-check the subscriber plus every modified test module.
5. Re-run the leak-oriented search and manually confirm the raw configured URL appears only at
   the connection call.

The exact ProjectHephaestus paths and copy-paste commands from the source session are preserved
in [the session notes](./nats-observability-redact-credential-bearing-diagnostics.notes.md).

### Expected Post-Change Invariants

```text
health["url"] == "tls://broker.example.com:4222/jetstream"
health["last_error"] in {
    None,
    "connection_error",
    "handler_error",
    "circuit_breaker_open",
    "terminal_error",
    "shutdown_timeout",
}
thread.last_error is original_exception
secret_text not in caplog.text
secret_text not in serialized_health
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | NATS subscriber diagnostic-hardening design session | [Plan-specific paths, tests, and commands](./nats-observability-redact-credential-bearing-diagnostics.notes.md). No implementation, local verification, or CI evidence was supplied. |

## Related Skills

- [NATS subscriber acknowledgment semantics](./nats-subscriber-ack-atmost-once-design.md) —
  preserve its ack-on-handler-error contract while changing publication behavior.
- [Silent-boundary exception classification](./silent-boundary-observability-exception-classification.md) —
  useful for trusted internal logs; its traceback recommendation must not be copied onto an
  externally retained or secret-bearing diagnostic surface.
- [Communication redaction](./communication-redaction-avoid-internal-leaks.md) — applies the
  same least-disclosure principle to durable documentation and artifacts.
- [Exception discriminator enums](./exception-discriminator-enums-state-machine-pola.md) —
  use when callers need structured recovery reasons rather than a publication-only health kind.
