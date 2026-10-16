# resource-pressure-001 injection

This setup-only fixture records a short API latency baseline, starts two bounded synthetic CPU workers, and enables bounded CPU work in `demo-api.service`. The API remains healthy and reachable while response latency increases.

Run it only against the disposable local QEMU target:

~~~bash
./lab/scenarios/resource-pressure-001/inject.sh resource-pressure-001
./lab/scenarios/resource-pressure-001/verify.sh resource-pressure-001
~~~

The baseline and pressure measurements are stored under the ignored lab runtime directory. `prepare-run.sh` copies only the baseline reference into the run so the agent can compare behavior without receiving evaluator thresholds or injection details. Resetting the disposable overlay removes the workers and marker automatically.
