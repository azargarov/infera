# CI/CD and release model

Infera uses CI/CD to make this proof of concept repeatable and easy to review. Production service deployment is outside its scope.

## Local validation

Run:

```bash
./validation/ci-local.sh
```

This runs the offline test suite, scenario and knowledge validation, reviewed example validation, YAML and shell checks, public-boundary checks, and tracked runtime-artifact checks. The command is intentionally transparent and focused on repository validation.

## Pull-request CI

`.github/workflows/ci.yml` runs on pull requests and pushes to the default branch. It installs the small Python dependency set, runs local validation, and performs repository checks including secret scanning. The workflow runs without QEMU/KVM, model credentials, SSH credentials, or an external target.

## QEMU integration

`.github/workflows/qemu-integration.yml` is manually dispatched on a self-hosted Linux runner with usable KVM. It checks prerequisites, verifies the pinned image, boots and validates a healthy target, exercises the supported scenario injector/verifier/reset paths, and cleans overlays, seed images, keys, logs, and PID files even after failure.

This workflow verifies VM infrastructure and deterministic scenario tooling. Live agent reasoning is reviewed separately. The local QEMU integration path has been executed successfully; GitHub runner execution is pending because this checkout has no configured remote or runner.

## Manual agent evaluation

The reviewed example runs were produced through manually invoked compatible coding agents. That step remains manual because a vendor-specific model API is not a reproducible CI dependency. Human review remains necessary for the quality and provenance of agent-generated content.

## Release workflow

`.github/workflows/release.yml` runs for tags matching `v*`. It calls the normal validation workflow, repeats the public-boundary and secret checks, generates a machine-readable release manifest and checksums, and prepares a GitHub release. It does not package VM images, runtime keys, disks, or logs.

The release manifest records the version/tag, commit, test summary, supported Python version, pinned Ubuntu image metadata, reviewed scenario list, and known limitations. A release candidate can be generated locally with:

```bash
python3 validation/create_release_manifest.py \
  --version v0.1.0-rc1 \
  --output /tmp/infera-release-manifest.yaml
```

Publication still requires GitHub repository setup and external workflow verification. See [`docs/release-checklist.md`](release-checklist.md).
