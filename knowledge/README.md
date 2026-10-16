# Synthetic knowledge base

This is a small, partially prefilled knowledge base for the public Infera experiment. It gives the agent useful expectations about a generic synthetic Linux system without giving it the answer to any scenario.

Prior knowledge is context, not evidence. A knowledge entry can suggest what to inspect, but a diagnostic conclusion must be supported by evidence collected during the run. If current observations contradict prior knowledge, the observations and the contradiction remain visible.

## Provenance classes

- baseline_fact — defined by the synthetic environment and verified by setup.
- documented_expectation — describes intended component behavior or a useful operational pattern.
- learned_observation — promoted from a reviewed future run.
- inferred_relationship — derived from evidence or reasoning.
- unresolved_hypothesis — a candidate explanation awaiting evidence.

Every entry has an ID, kind, subject, provenance, review status, content, and source reference. Learned and inferred entries require a source reference. v0.1 uses manual promotion; no automatic knowledge-maintenance process exists.

## Leakage guardrail

Scenario IDs and expected outcomes are deliberately excluded. The validator rejects known scenario IDs and obvious answer-key fields such as expected_root_cause. This is a narrow leakage guard, not semantic analysis: it cannot prove that every possible natural-language answer is absent.

## Layout

- system/ — synthetic platform expectations.
- components/ — generic service relationships.
- patterns/ — reusable operational signals and safe investigation guidance.

Future run observations should remain run-scoped until a human reviews and promotes them.
