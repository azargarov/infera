# Provider-neutral diagnostic workflow

This workflow is for a repository-aware, shell-capable coding agent working on a prepared Infera run. The agent is part of the experiment. It performs investigation and interpretation; deterministic tooling validates the resulting artifacts.

## Inputs

Read:

1. `AGENTS.md`;
2. the run's `agent-context.yaml` and `agent-request.md`;
3. only the listed synthetic knowledge entries;
4. the evidence, finding, run-state, action, and report schemas.

The full scenario manifest is evaluator input. Do not read its injection, expected observation, expected reasoning, forbidden claim, or validation sections during diagnosis. Scenario expectations must not become evidence or be copied into findings.

## Investigation

Connect only to the prepared local target described in `agent-context.yaml`. Confirm the hostname before collecting evidence. Use read-only SSH commands such as service status, service properties, recent journal entries, listener checks, health checks, dependency connectivity checks, hostname, OS identity, and basic system state.

Save raw stdout and stderr under the run's `evidence/raw/` directory. Create evidence records that describe observations and reference those files. Do not put interpretations or conclusions in evidence records.

Use prior knowledge as context. It can suggest useful probes, but it is not observed evidence and must not override contradictory observations.

## Artifacts

Create or update:

- `evidence/records.yaml`;
- `findings/findings.yaml`;
- `state/run-state.yaml`;
- `actions/actions.yaml`;
- `reports/final-report.yaml`;
- `validation/validation-result.yaml` after structural validation.

Keep observed facts, hypotheses, confirmed findings, and unknowns distinct. A confirmed finding must cite supporting evidence. Preserve missing evidence and unresolved questions explicitly. The report may summarize artifacts, but must not introduce unsupported factual claims.

The diagnostic safety mode is `read_only`. Do not restart, start, or stop services; change files or configuration; change networking; call scenario injection; or attempt remediation. Leave `actions/actions.yaml` empty unless the contract explicitly requires a non-executing record.

Stop when the report is complete. Do not repair the target.
