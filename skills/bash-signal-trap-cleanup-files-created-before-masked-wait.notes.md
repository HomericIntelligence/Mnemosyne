# Notes: bash-signal-trap-cleanup-files-created-before-masked-wait

Supporting evidence for the main skill. Use these details to reproduce the residue test. Do not
treat them as rules. The main skill holds the rules.

## Source of the lesson

A review finding on a bash setup script. The model fetch created two temporary files in the
configuration directory before a fetch with a 20 second timeout. The script had an INT handler
that printed a cancel message and exited 130. The handler did not remove the two files. A cancel
during a slow fetch therefore left two hidden files.

The finding named the narrower exposure of the prior code. The prior code created the temporary
file only after a successful fetch, so its window was smaller. The new code created both files
before the wait to capture the HTTP status. That change widened the window and made the handler
gap visible.

## Residue harness

This harness shows the defect and then shows the fix. It has no dependency on the project test
suite. Run it twice: once on the code before the fix, and once after.

```python
"""Show or refute: Ctrl-C during the fetch leaves temp files behind.

Exit status: 0 when no residue, 1 when residue remains.
"""

import json
import os
import pathlib
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time

SCRIPT = pathlib.Path(sys.argv[1]).resolve()


def main() -> int:
    port_holder = pathlib.Path(tempfile.mkdtemp(prefix="int-check-")) / "port"

    def serve() -> None:
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        srv.listen(8)
        port_holder.write_text(str(srv.getsockname()[1]))
        while True:
            conn, _ = srv.accept()
            try:
                conn.settimeout(2)
                data = conn.recv(65536)
                if data.startswith(b"GET"):
                    time.sleep(60)          # stall the data fetch
                else:
                    conn.sendall(           # answer the preflight at once
                        b"HTTP/1.1 401 Unauthorized\r\n"
                        b"Content-Length: 0\r\nConnection: close\r\n\r\n"
                    )
            except OSError:
                pass
            finally:
                try:
                    conn.close()
                except OSError:
                    pass

    threading.Thread(target=serve, daemon=True).start()
    for _ in range(50):
        if port_holder.exists():
            break
        time.sleep(0.1)

    home = pathlib.Path(tempfile.mkdtemp(prefix="int-home-"))
    config = home / "config"
    config.mkdir()
    # Write the gateway record and credential files that the script expects.
    # Paths and field names come from the script under test.

    env = dict(os.environ)
    env.update(
        {
            "HOME": str(home),
            "CONFIG_DIR": str(config),
        }
    )

    proc = subprocess.Popen(
        ["bash", str(SCRIPT)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=True,       # own the process group for SIGINT
        text=True,
    )
    proc.stdin.write("1\n")
    proc.stdin.flush()

    during = []
    for _ in range(40):
        during = sorted(p.name for p in config.glob(".fetch-*"))
        if during:
            break
        time.sleep(0.1)
    time.sleep(0.5)                   # let the fetch settle
    print(f"temp files during fetch: {during}")

    os.killpg(os.getpgid(proc.pid), signal.SIGINT)
    try:
        proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
    print(f"exit code: {proc.returncode}")

    residue = sorted(p.name for p in config.glob(".fetch-*"))
    print(f"residue after SIGINT: {residue}")
    return 1 if residue else 0


if __name__ == "__main__":
    sys.exit(main())
```

## Recorded results

| Code state | Temp files during the fetch | Exit code | Residue after SIGINT |
| ---------- | --------------------------- | --------- | -------------------- |
| Handler without the paths | two files | 130 | both files |
| Handler with empty globals | two files | 130 | none |

The second row is the required result. The exit code stays the same in both rows. Only the residue
changes.

## Scope detail

The handler is a command that runs later. A `local` name from the interrupted function is not in
its scope. Confirm the scope before you edit the handler. A handler that names an unset variable
runs `rm -f ''`, which succeeds silently and removes nothing.

## Related corpus entries

- A process-group tree-kill trap pattern covers scripts that background work. It requires global
  state for the same scope reason. It does not cover file residue.
- A temporary-file plus function `RETURN` trap pattern covers cleanup inside a sourced function. It
  does not run when a signal handler exits the script.