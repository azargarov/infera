# Fixture runs

These directories are synthetic, offline examples of the structured artifacts a future agent run should produce. The `*-valid` fixtures must pass `validation/validate_run.py`; the `invalid-*` fixtures intentionally violate one contract so the validator has a deterministic failure to report.

The PM approved fixture records a simulated execution only. It does not restart a service or require a target system.
