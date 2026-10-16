# Contributing

Contributions should preserve Infera's scope as a small, agent-driven
diagnostic proof of concept.

- Use synthetic data and documented synthetic Linux targets only.
- Do not add customer data, proprietary commands, internal paths, credentials,
  copied logs, or real infrastructure artifacts.
- Scenario changes must preserve the public scenario contract and define
  expected observations, unknowns, safety boundaries, and reset behavior.
- Run the local CI-equivalent command before submitting changes:
  `./validation/ci-local.sh`.
- Changes to the QEMU lab require integration verification on a capable
  self-hosted runner when available.
- Reviewed example runs must contain no runtime keys, disks, logs, or secrets.
- Agent-generated code, prompts, findings, and reports require human review
  before they are committed.
- Keep deterministic validators small and do not replace agent reasoning with
  a hidden Core Engine.

The repository is licensed under Apache License 2.0. See `LICENSE`.
