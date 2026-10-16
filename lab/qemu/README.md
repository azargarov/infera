# Synthetic QEMU lab

This lab provides the disposable Linux target for Infera experiments. It provisions a generic Ubuntu Server 24.04 cloud image with the synthetic host name `infera-lab`, user `infera`, `demo-db.service`, `demo-upstream.service`, `demo-api.service`, and a small disposable filesystem for storage experiments. It verifies infrastructure only. Diagnostic scenarios and agent runs happen separately.

## Prerequisites

The host must be Linux with an amd64 CPU and usable KVM, QEMU, `qemu-img`, `curl`, OpenSSH client tools, `sha256sum`, and one cloud-init seed builder. The scripts use `cloud-localds` when available, then `xorriso` or `mkisofs`. They do not install packages or modify host networking. Check the environment with:

~~~bash
./lab/qemu/scripts/check-prereqs.sh
~~~

The v0.1 lab requires `/dev/kvm` to be readable and writable. Software emulation is not used because it would make this experiment unnecessarily slow.

## Pinned image

The lab uses the official Ubuntu Cloud Images release build `release-20260911`:

- image: Ubuntu Server 24.04 LTS cloud image, amd64
- source: `https://cloud-images.ubuntu.com/releases/noble/release-20260911/ubuntu-24.04-server-cloudimg-amd64.img`
- SHA-256: `612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354`

The metadata and license/source note are in [config/image.yaml](config/image.yaml). The image is downloaded into `.lab/qemu-cache/`, verified, and never committed.

## Lifecycle

Run these commands from the repository root:

~~~bash
./lab/qemu/scripts/check-prereqs.sh
./lab/qemu/scripts/fetch-base-image.sh
./lab/qemu/scripts/create-overlay.sh
./lab/qemu/scripts/create-seed.sh
./lab/qemu/scripts/boot.sh
./lab/qemu/scripts/wait-for-ssh.sh
./lab/qemu/scripts/verify-baseline.sh
./lab/qemu/scripts/shutdown.sh
./lab/qemu/scripts/reset.sh
~~~

The base image is immutable. Each boot uses a qcow2 overlay and a generated cloud-init seed. `reset.sh` stops QEMU, removes only disposable overlay, seed, key, PID, and log files, and preserves the verified base-image cache at `.lab/qemu-cache/`.

The VM uses QEMU user-mode networking. SSH is forwarded only to `127.0.0.1:2222`; no bridged interface or host firewall change is required. The manual connection, after the seed and VM are running, is:

~~~bash
ssh -i .lab/qemu/id_ed25519 -p 2222 -o UserKnownHostsFile=.lab/qemu/known_hosts -o StrictHostKeyChecking=no infera@127.0.0.1
~~~

The key and known-hosts file are generated per lab runtime and are ignored by Git. Private keys must not be copied into run artifacts.

## Synthetic services

`demo-db.service` is a small Python TCP service on `127.0.0.1:15432`. Sending `health` returns `OK demo-db` and produces a journal entry.

`demo-api.service` is a small Python HTTP service on `127.0.0.1:18080`. Its `/health` endpoint checks the demo database and returns `200 OK demo-api` when the dependency responds, or `503 DEGRADED dependency-unavailable` when it does not. Both units run under the synthetic `infera` user and write to journald.

The first implemented setup fixture is `service-failure-001`. It is deliberately separate from agent remediation and is documented in [lab/scenarios/service-failure-001/README.md](../scenarios/service-failure-001/README.md).

## Troubleshooting

- If prerequisite checks fail, install the missing host package using the distribution's normal package manager; the repository does not use `sudo` or install packages automatically.
- If the image checksum fails, remove only the reported partial or cached image after checking the pinned metadata and retry.
- If SSH does not become ready, inspect `.lab/qemu/serial.log`, then run `shutdown.sh` and `reset.sh`.
- If a stale PID file remains after an interrupted host process, confirm no `qemu-system-x86_64` process for this lab is running before removing the disposable runtime with `reset.sh`.

The lab is intentionally local, synthetic, and small. It does not support production systems, external networks, broad distribution coverage, or persistent credentials.
