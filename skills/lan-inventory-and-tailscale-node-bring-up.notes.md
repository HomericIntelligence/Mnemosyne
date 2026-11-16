# Notes: LAN Inventory and Tailscale Node Bring-Up

Supporting evidence and failure signatures for
[lan-inventory-and-tailscale-node-bring-up](./lan-inventory-and-tailscale-node-bring-up.md).
No hostnames, addresses, MAC addresses, domains, credentials, or one-time login
URLs are stored here. Generalized evidence only.

## What the evidence shows

- A two-pass scan (ICMP, then TCP 22) converged on the same SSH-capable device
  set; the ARP/neighbor table added reachability state and MACs, and local
  reverse-DNS resolved names for most responders (the LAN's DHCP-registered
  names), with a minority returning no name.
- The tailnet map from `tailscale status` included both online peers and peers
  offline for weeks or months; several offline-on-tailnet peers were online on
  the LAN and reachable over SSH — so "last seen N days ago" on the tailnet is
  not evidence the machine is absent or decommissioned.
- BatchMode SSH probing from the owner account classified the fleet without any
  password attempts: some nodes granted key-only access, others denied with a
  publickey-only answer, one presented a banner that hung (sshd not usable), and
  one presented a host key that did not match the remembered key.
- Nodes confirmed running the tailnet daemon while logged out printed single-use
  login URLs; interactive authorization by the owner is mandatory. A plain
  (non-root, non-operator) `tailscale up` was denied, and a re-run without the
  node's previously stored non-default flag was also refused until the flag was
  repeated explicitly.
- A changed host key was identified and left untouched pending owner
  confirmation; no connection was made to the affected node.

## Reusable failure signatures

| Signature | Meaning | Correct handling |
| --------- | ------- | ---------------- |
| Port 22 open, banner exchange times out | sshd broken or filtered | Not a login problem; report, do not retry with other flags |
| `Permission denied (publickey)` (BatchMode) | No key authorized; no password available | Hand to the owner; never try passwords |
| `Permission denied (publickey,password)` | Server accepts passwords too; owner needs to supply or authorize | Same boundary |
| Host key verification failed with a *changed* key | Unknown identity: stale remembered entry, reimage, swapped NIC, or MITM | Halt; out-of-band verification; stale remembered entry removed only with owner confirmation |
| `tailscale up` → access denied / operator error | Interactive authorization or operator role missing | `sudo tailscale up` interactively; never claim bring-up succeeded without `tailscale status` |

## Verification status

Evidence is local and session-bound: the inventory, the SSH probes, and the
login-flow outcomes were all observed on one owned LAN. Nothing here is
verified-inference for other networks; the workflow is the reusable part, and it
relies on owner authorization at every privilege boundary.

## Explicit exclusions

- No secrets or one-time login URLs are included; URLs printed by the daemon
  are single-use and node-specific and must never appear in durable artifacts.
- No inventory identifiers (addresses, MACs, names, domains) are included.
