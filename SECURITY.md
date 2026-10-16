# Security policy

Infera is a portfolio proof of concept, not production or security software. The only supported public target is the synthetic QEMU lab. Do not submit real customer data, production logs, credentials, proprietary system details, or other confidential material in issues, pull requests, or example runs.

## Reporting an accidental secret or unsafe public artifact

If a public checkout contains an accidentally committed secret or private material, avoid reproducing it in an issue. Contact the repository owner through the private contact mechanism associated with the eventual GitHub repository and include the file path, commit, and a short description. If the material is already public, rotate or revoke it first where possible.

For ordinary defects in the synthetic lab or validators, a public issue is appropriate once the report contains only synthetic information.

The repository's boundary checks and secret scanner reduce publication risk; they do not prove that a repository contains no secrets. Human review is still required before release.
