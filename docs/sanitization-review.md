# Public sanitization review

This review supersedes earlier sanitization conclusions. It uses a fail-closed
allowlist: every tracked path must have a defined purpose in the synthetic
public proof of concept, and the boundary validator rejects paths outside that
allowlist.

## File classification

The pre-cleanup repository contained 515 tracked files. Path classification and
semantic review produced:

- 512 `KEEP` files;
- 0 `REMOVE` files;
- 3 `REWRITE` files;
- 0 `UNCERTAIN` files.

The rewrites are this report, the public-boundary validator, and one synthetic
service knowledge entry whose documented port did not match the public lab.
No tracked legacy tree or root control file was present at the start of this
pass. Ignored local release output, QEMU runtime/cache files, local run output,
and Python caches were removed from the checkout.

## Synthetic areas retained

- provider-neutral agent workflows;
- public schemas and scenario manifests;
- generic Linux and synthetic `demo-*` knowledge;
- the Ubuntu/QEMU lab and its synthetic scenario setup;
- reviewed runs produced against `infera-lab`;
- deterministic validators, evaluators, tests, and CI/CD definitions;
- concise public documentation.

The retained lab consists only of three small synthetic services, localhost
networking, deliberately synthetic high ports, a disposable test filesystem,
and bounded scenario controls. PM content is limited to the approval-gated
`demo-api.service` restart experiment.

## History result

The previous development history contained only the staged construction of the
synthetic public repository; no forbidden legacy path or direct product/vendor
identifier was detected. The history was nevertheless replaced with one clean
root commit so the future public repository does not publish development
archaeology or depend on earlier sanitization assumptions. A complete bundle of
the previous history is stored outside this repository for private recovery.

## Final repository tree

```text
.github/       public CI, QEMU integration, and release workflows
agent/         provider-neutral diagnostic and PM workflows
docs/          public architecture, limits, CI/CD, metadata, and maintenance docs
examples/      reviewed synthetic QEMU run artifacts
knowledge/     generic Linux and synthetic demo-service knowledge
lab/           disposable QEMU baseline and synthetic scenario setup
scenarios/     declarative synthetic experiment manifests
schemas/       public artifact and scenario contracts
tests/         offline contract, safety, and boundary tests
validation/    deterministic validators, evaluators, fixtures, and local CI
```

The root files provide the project entry point, agent guidance, security and
contribution policies, ignore rules, and the required development dependency.

## Remaining uncertainty

No tracked file remains unclassified. Automated checks cannot prove conceptual
provenance, so future knowledge, scenarios, and reviewed runs still require
human provenance review before commit. The current retained architecture uses
only the independently defined synthetic lab described above.
