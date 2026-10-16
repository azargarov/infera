# `pm-restart-001`

This is the first controlled preventive-maintenance experiment. It permits one
state-changing operation: restarting `demo-api.service`. The run has two
phases:

1. read-only prechecks and a dry-run plan ending at `approval_pending`;
2. an explicit operator approval followed by the narrow restart and
   post-action verification.

Prepare the run from a healthy QEMU baseline:

```bash
./lab/scenarios/pm-restart-001/prepare-run.sh pm-restart-001-20261001T120000Z
```

After the no-approval phase passes validation, record approval explicitly:

```bash
./lab/scenarios/pm-restart-001/approve.sh pm-restart-001-20261001T120000Z operator
```

Only the approved PM workflow may then execute the exact `demo-api.service`
restart. The injector/reset model remains disposable, and no general action
executor is provided.
