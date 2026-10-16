# v0.1 release checklist

Use this checklist before creating the first public portfolio release. The current local target is `v0.1.0-rc1`; no tag or GitHub release is created by this repository preparation step.

## Repository

- [ ] Working tree is clean after the intended release commit.
- [ ] Intended public files are tracked.
- [ ] Runtime overlays, seed images, keys, logs, and PID files are absent.
- [ ] Public-boundary scan passes.
- [ ] Secret scan passes, with manual review of any findings.
- [ ] Local links and referenced paths resolve.

## Tests

- [ ] Offline test suite passes.
- [ ] All scenario manifests validate.
- [ ] Knowledge entries validate.
- [ ] Reviewed example runs validate.
- [ ] Local QEMU integration passes on a capable host.

## Documentation

- [ ] README describes only implemented behavior and identifies the PoC clearly.
- [ ] Architecture documentation matches the agent, VM, artifact, and validator boundaries.
- [ ] Limitations document reflects the current release candidate.
- [ ] `SECURITY.md` and `CONTRIBUTING.md` are present and proportional.
- [ ] Release manifest command works for the selected version.
- [x] Apache License 2.0 is declared in `LICENSE`.

## GitHub

- [ ] Remote points to the intended public repository.
- [ ] Default branch is correct.
- [ ] Workflows are enabled.
- [ ] PR CI passes in GitHub Actions.
- [ ] Self-hosted QEMU runner decision is documented and, if used, verified.

## Release

- [ ] Version is decided (`v0.1.0` or an explicitly documented pre-release).
- [ ] Release candidate tag is tested before the final tag.
- [ ] Release manifest and checksums are generated from the intended commit.
- [ ] Final tag is created only after the checks above pass.
- [ ] GitHub release is created with repository-safe artifacts only.

## Privacy and public boundary

- [ ] No real-system data or copied operational logs are present.
- [ ] No customer names or proprietary product/system details are present.
- [ ] No private hostnames, URLs, IP addresses, keys, or credentials are present.
- [ ] No runtime disks, SSH keys, logs, or temporary output are present.
- [ ] Reviewed examples contain synthetic data only.

The Apache License 2.0 decision is complete. The remaining publication steps still require explicit repository, workflow, and release actions.
