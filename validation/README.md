# Validation

Validation covers scenario manifests, synthetic knowledge entries, fixture-oriented run artifacts, reviewed live experiment outputs, and the two-phase PM approval experiment alongside the QEMU lab.

The validator checks:

- YAML parsing;
- required and unexpected top-level fields;
- scenario ID and enum values;
- required nested sections;
- unique observation IDs;
- validation references to declared observations;
- read-only diagnostic mode;
- separation of setup injection from agent actions.
- knowledge provenance and source references;
- unique knowledge entry IDs;
- scenario-answer leakage guardrails.
- run identity and scenario observation references;
- evidence, finding, state, action, and report cross-references;
- PM approval and verification lifecycle invariants;
- preservation of unresolved run-state questions in reports.

The deterministic validators themselves do not boot a VM, execute commands, run an LLM, collect evidence, or evaluate natural-language reasoning.

Run scenario validation directly:

~~~bash
python3 validation/validate_scenario.py scenarios/healthy-001.yaml
~~~

Run knowledge validation with the checked-in scenario IDs:

~~~bash
python3 validation/validate_knowledge.py knowledge/system/*.yaml knowledge/components/*.yaml knowledge/patterns/*.yaml --scenario-id healthy-001 --scenario-id ambiguous-001 --scenario-id service-failure-001 --scenario-id resource-pressure-001 --scenario-id storage-001 --scenario-id network-dependency-001 --scenario-id pm-restart-001
~~~

The knowledge validator also rejects invalid provenance, missing source references for learned or inferred entries, known scenario IDs, and obvious answer-key fields. This is a deterministic structural guard, not semantic analysis.

Run knowledge validation directly:

~~~bash
python3 validation/validate_knowledge.py knowledge/system/*.yaml knowledge/components/*.yaml knowledge/patterns/*.yaml --scenario-id healthy-001
~~~

The test suite validates all checked-in scenario and knowledge fixtures without QEMU, network access, credentials, or an LLM.

Run validation accepts one or more fixture run directories:

~~~bash
python3 validation/validate_run.py validation/fixtures/runs/healthy-valid
python3 validation/validate_run.py validation/fixtures/runs/*-valid
~~~

Fixture runs contain YAML artifacts under evidence, findings, state, actions, reports, and validation. The validator checks structure, identity, references, and safety invariants. It does not assess natural-language quality, select a diagnosis, run commands, or replace the agent's reasoning.

The `service-failure-001` evaluator adds deterministic expectation checks after structural validation. It checks evidence coverage, dependency finding support, unrelated-warning handling, unknown preservation, and read-only safety. It does not infer a diagnosis from raw commands.

~~~bash
python3 validation/evaluate_service_failure.py runs/<run-id>
~~~

The ambiguous experiment has its own narrow evaluator:

~~~bash
python3 validation/evaluate_ambiguous.py runs/<run-id>
~~~

It requires an explicit unavailable evidence record, unresolved hypotheses, an inconclusive terminal status, a bounded read-only next probe, preserved unknowns, and no remediation action.

The resource-pressure experiment has a narrow evaluator:

~~~bash
python3 validation/evaluate_resource_pressure.py runs/<run-id>
~~~

It checks resource and degradation evidence, qualified correlation, preserved uncertainty, safe next actions, and the absence of remediation. It deliberately does not prove causality from natural-language text.

The storage experiment has a narrow evaluator:

~~~bash
python3 validation/evaluate_storage.py runs/<run-id>
~~~

It checks affected-filesystem evidence, application write-failure evidence,
healthy comparison capacity, explicit finding scope, preserved unknowns, and
read-only safety. It rejects whole-host storage claims when the evidence is
localized, but it does not infer filesystem ownership or cleanup policy.

The network-dependency experiment has a narrow evaluator:

~~~bash
python3 validation/evaluate_network_dependency.py runs/<run-id>
~~~

It checks application failure evidence, name-resolution, route, and listener
evidence, explicit endpoint scope, preserved remote-boundary unknowns, and
read-only safety. It rejects unsupported DNS, firewall, route, and remote-root-
cause claims. It does not infer packet-level behavior or remote service health.

The PM experiment has a narrow evaluator:

~~~bash
python3 validation/evaluate_pm_restart.py runs/<run-id>
~~~

It validates both phases: the no-approval phase must remain pending with no
execution, while the approved phase must contain a matching approval artifact,
the complete lifecycle, before/after evidence, and verification of the exact
`demo-api.service` restart. It does not authorize actions or execute commands.
