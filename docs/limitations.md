# Limitations and non-goals

Infera is an experimental proof of concept for exploring agent-driven, evidence-first system diagnostics. Its contracts and validators make the experiment understandable and reviewable. Production software is outside the current scope.

## Current limits

- The public lab is one synthetic Ubuntu Linux environment with deliberately small services and bounded scenario injectors.
- The five diagnostic scenarios and one PM scenario are representative experiments, not broad operating-system coverage.
- Live agent sessions are manually invoked and reviewed. Model choice, prompts, tool behavior, and conclusions can vary between runs.
- Validators check structure, references, safety invariants, and selected reasoning constraints. They cannot prove that an agent's interpretation is correct or replace human review.
- The lab requires a Linux host with QEMU/KVM and cloud-init seed tooling for full integration verification. Ordinary repository validation does not require those tools.
- The public examples use synthetic data only. They do not represent customer systems, production infrastructure, or real operational impact.

## Explicit non-goals

Infera does not aim to provide:

- production monitoring, incident response, or support software;
- autonomous remediation or unrestricted command execution;
- a deterministic Core Engine that replaces the coding/LLM agent;
- integration with real customer or proprietary systems;
- medical-device, clinical, or safety-critical functionality;
- a guarantee of support across Linux distributions or arbitrary topologies;
- Kubernetes, multi-host networking, or a monitoring stack in the initial public release;
- automatic learning or promotion of knowledge from agent output;
- a security product or a guarantee that the lab is safe for untrusted workloads.

The PM experiment demonstrates one explicit approval boundary around one synthetic service restart. It is not a general change-management or rollback system.
