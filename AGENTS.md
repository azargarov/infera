# Agent guidance

Infera is an experimental proof of concept for evidence-driven system diagnostics. The coding/LLM agent is intentionally part of the runtime being explored.

When working in this repository:

- Read the relevant public instructions and scenario manifest before acting.
- Treat evidence as the basis for factual conclusions.
- Treat prior knowledge as context, not evidence.
- Do not let knowledge override contradictory observations.
- Keep observed facts, hypotheses, interpretations, and unknowns distinct.
- Scenario IDs and expected outcomes are experiment metadata, never runtime knowledge.
- Unknown remains a valid result when evidence is incomplete.
- Use read-only diagnostic behavior by default.
- Treat state-changing behavior as unavailable unless a documented workflow explicitly permits it and an approval gate is satisfied.
- Treat synthetic scenario injection as test infrastructure setup. It is not agent remediation.
- Do not invent evidence, successful remediation, external impact, or certainty that artifacts do not support.
- Keep scenario IDs, evidence references, status values, and safety metadata structurally valid.
- Evidence files record observations; findings record interpretation. Confirmed claims must cite evidence.
- Keep unknowns explicit. A report must not introduce new factual conclusions beyond its findings and evidence references.
- PM execution claims require an action record and post-action verification evidence.
- Never add customer data, proprietary product or system references, real hostnames, real addresses, credentials, internal paths, or copied operational artifacts.
- Future QEMU access must use only the documented synthetic target and disposable scenario state.
- The QEMU lab verifies infrastructure only; do not treat its baseline checks as Infera findings.

The coding/LLM agent performs investigation and reasoning. Deterministic validators check contracts and artifacts. They do not replace agent reasoning or orchestration.
