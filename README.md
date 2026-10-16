# Infera

**An experimental prototype for evidence-driven system diagnostics**

Infera explores how a coding/LLM agent can investigate a Linux system using explicit workflows, collected evidence, partial knowledge, persistent state, uncertainty, and safety boundaries.

The agent chooses bounded read-only probes, interprets what the system reports, and writes structured artifacts. Deterministic validators check those artifacts. The public experiments use synthetic Linux systems only.

## Why I built this

The project started as an experiment to see whether a coding/LLM agent could investigate a complex system through collected evidence, explicit uncertainty, and structured diagnostic state.

## What makes Infera interesting

- Evidence and interpretation are separate.
- Prior knowledge is context, not evidence.
- Unknown is a valid result.
- Findings link back to evidence.
- State-changing work requires explicit approval.
- Deterministic validators check the artifacts produced by the agent.

## Reasoning scenarios

The five reviewed diagnostic experiments map a reasoning property to a synthetic failure:

```text
service failure       → evidence-backed diagnosis
ambiguous evidence   → preserved uncertainty
resource pressure    → qualified causality
storage               → scoped diagnosis
network dependency    → bounded layer conclusion
```

They test reasoning properties, not broad Linux failure coverage. The reviewed artifacts are in [`examples/runs/`](examples/runs/).

## PM workflow

The separate `pm-restart-001` experiment covers one controlled restart:

```text
precheck → plan → approval → execute → verify
```

Planning, approval, and verification are separate artifacts. The approved action is limited to restarting the synthetic `demo-api.service`.

## QEMU lab

QEMU supplies a repeatable synthetic target with deliberate failures and a clean reset after each experiment. Each run uses a disposable overlay, so no customer infrastructure is involved. The full lifecycle is in [lab/qemu/README.md](lab/qemu/README.md).

## Quick start

### Validate the repository

```bash
python3 -m pip install -r requirements-dev.txt
./validation/ci-local.sh
```

This validates the offline tests, reviewed examples, schemas, YAML, shell scripts, public boundary, and tracked runtime artifacts. It does not require QEMU, credentials, or a model provider.

### Run the synthetic lab

On a Linux host with QEMU/KVM and cloud-init seed tooling:

```bash
./lab/qemu/scripts/check-prereqs.sh
./lab/qemu/scripts/fetch-base-image.sh
./lab/qemu/scripts/create-overlay.sh
./lab/qemu/scripts/create-seed.sh
./lab/qemu/scripts/boot.sh
./lab/qemu/scripts/wait-for-ssh.sh
./lab/qemu/scripts/verify-baseline.sh
```

The recommended diagnostic path is documented in [agent/diagnose.md](agent/diagnose.md). The live agent is invoked manually by a compatible repository-aware coding agent.

## Example finding

```yaml
observation: demo-db.service unavailable
finding: database dependency failure is the leading explanation for degraded API health
evidence_refs: [ev-service-status, ev-api-health]
unknown: external client impact was not measured
remediation: none
```

This is a compact example from `service-failure-001`; the reviewed run artifacts are the source of validation.

## Architecture

```text
human request
    ↓
coding/LLM agent ← instructions + partial knowledge
    ↓ read-only probes
synthetic Linux target
    ↓
evidence → findings / state / report
                    ↓
          deterministic validation
```

The agent investigates and interprets. The synthetic target exposes observations. Evidence records observations; findings record interpretation; state and reports summarize the run. Validators check structure, references, uncertainty, scope, safety, and consistency. See [docs/architecture.md](docs/architecture.md).

## Evaluation

Exact prose is not scored. The evaluators check structured properties including evidence coverage, evidence references, uncertainty, unsupported conclusions, scope, safety, approval lifecycle, and consistency between state and report. Validators check the artifacts; they do not choose the diagnosis or replace agent reasoning.

## Current status

The repository contains:

- five reviewed live diagnostic experiments;
- one reviewed PM approval experiment;
- a reproducible QEMU lab and synthetic knowledge base;
- structured artifact contracts and deterministic validators;
- offline tests and CI/CD workflow definitions.

Local validation and the local QEMU integration path have been run successfully. GitHub Actions and a self-hosted QEMU runner have not been run from this checkout.

## Limitations

Infera is an experimental proof of concept. The public target is one synthetic Ubuntu environment with a bounded scenario set. Live coding-agent evaluation is partly manual, broad Linux/platform compatibility has not been evaluated, and production operation and autonomous remediation are outside the current scope. See [docs/limitations.md](docs/limitations.md).

## Later projects

Infera also informed later experiments where more responsibilities were moved into deterministic software and validation. Those projects are separate from this repository.

## License

Licensed under the Apache License 2.0. See `LICENSE`.

## Repository map

- `agent/` — provider-neutral diagnostic and PM workflows.
- `docs/` — architecture, limits, CI/CD, release, and maintenance notes.
- `examples/` — reviewed synthetic run artifacts.
- `knowledge/` — partial synthetic prior knowledge.
- `lab/` — QEMU target and scenario setup.
- `scenarios/` — declarative scenario definitions.
- `schemas/` — public artifact and scenario contracts.
- `tests/` — offline contract and safety tests.
- `validation/` — deterministic validators, evaluators, and local CI.
