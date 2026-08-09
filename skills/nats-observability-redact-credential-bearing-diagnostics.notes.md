# NATS Credential-Safe Diagnostics — Source Session Notes

## Verification Status

`unverified`. The source session supplied a detailed implementation plan and acceptance matrix.
It did not execute the implementation, local tests, static checks, or CI.

## Project-Specific Scope

The plan targeted ProjectHephaestus and kept the change inside the
`hephaestus.nats` library package with standard-library URL parsing only.

Planned modified files:

- `hephaestus/nats/subscriber.py`
- `tests/unit/nats/test_subscriber.py`
- `tests/unit/nats/test_subscriber_circuit_breaker.py`
- `tests/unit/nats/test_subscriber_polling.py`
- `docs/nats.md`

No dependency, configuration migration, public interface, or ADR was planned. Existing health
keys were to remain stable while the values of `url` and `last_error` became
sanitized/classified. The original `NATSConfig.url` remained the value passed to
`nats.connect`.

## Planned Error Categories

| Failure boundary | Health/log category |
|------------------|---------------------|
| Connect or subscribe failure | `connection_error` |
| Handler exception | `handler_error` |
| Work rejected by an already-open breaker | `circuit_breaker_open` |
| Defensive outer failure | `terminal_error` |
| Thread shutdown timeout | `shutdown_timeout` |

The raw `BaseException` was to remain available through the in-process `last_error` property.
Only the bounded category was to cross `health_dict()` and log boundaries.

## Planned Regression Cases

### Health and startup logs

- Configure a URL assembled as
  `"tls://alice:credential-value" + "@broker.example.com:4222/jetstream?token=query-value&name=diagnostic#fragment"`.
- Assert the health/log URL is exactly
  `tls://broker.example.com:4222/jetstream`.
- Assert `alice`, `credential-value`, and `query-value` are absent.
- Assert lifecycle state, stream, and circuit-breaker state remain present.

### Connection and circuit-breaker failures

- Raise a connection exception containing `token=known-test-value`.
- Assert the original exception still contains the sentinel in-process.
- Assert health reports `connection_error`, the breaker reports `open`, logs contain
  `kind=connection_error`, and logs do not contain the sentinel.
- For a call rejected because the breaker was already open, assert
  `circuit_breaker_open`.

### Handler failures

- Raise a handler exception containing `token=known-test-value`.
- Preserve unconditional acknowledgment and the at-most-once delivery contract.
- Assert `thread.last_error is boom`, health reports `handler_error`,
  `last_message_at` remains unset, and the sentinel is absent from logs.

### Shutdown timeout

- Preserve the in-process `TimeoutError` identity and controlled timeout duration.
- Replace raw health text with `shutdown_timeout` and log only the duration plus bounded kind.

## Proposed Acceptance Commands

```bash
uv run pytest \
  tests/unit/nats/test_subscriber.py::TestHealthObservability::test_health_dict_redacts_url_credentials_and_query \
  tests/unit/nats/test_subscriber.py::TestHealthObservability::test_startup_log_redacts_url_credentials_and_query -v

uv run pytest \
  tests/unit/nats/test_subscriber_circuit_breaker.py::TestNATSSubscriberCircuitBreaker::test_persistent_connection_failures_open_circuit_and_enter_error \
  tests/unit/nats/test_subscriber_polling.py::test_ack_is_awaited_even_when_handler_raises -v

uv run pytest \
  tests/unit/nats/test_subscriber.py::TestHealthObservability::test_health_dict_preserves_non_sensitive_diagnostics -v

uv run pytest tests/unit/nats -v

uv run ruff check \
  hephaestus/nats/subscriber.py \
  tests/unit/nats/test_subscriber.py \
  tests/unit/nats/test_subscriber_circuit_breaker.py \
  tests/unit/nats/test_subscriber_polling.py

uv run mypy \
  hephaestus/nats/subscriber.py \
  tests/unit/nats/test_subscriber.py \
  tests/unit/nats/test_subscriber_circuit_breaker.py \
  tests/unit/nats/test_subscriber_polling.py
```

Post-change leak search:

```bash
rg -n 'str\(self\._last_error\)|self\._config\.url|logger\.exception' \
  hephaestus/nats/subscriber.py
```

Expected interpretation: `self._config.url` remains at the trusted connection call and may appear
inside the private diagnostic formatter invocation, but no health/log publication interpolates it
directly; raw exception serialization and `logger.exception` have no matches.
