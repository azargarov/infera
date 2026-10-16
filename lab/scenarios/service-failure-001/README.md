# service-failure-001 injection

This setup-only fixture targets the disposable local QEMU guest `infera-lab`. It stops `demo-db.service`, records a synthetic unrelated warning under the `demo-api` journal tag, and probes the API so its journal records the dependency failure.

Run it only after creating and booting a lab overlay:

~~~bash
./lab/scenarios/service-failure-001/inject.sh service-failure-001
./lab/scenarios/service-failure-001/verify.sh service-failure-001
~~~

The scripts refuse non-local port-forward settings, verify the synthetic hostname, and write a setup record under the ignored lab runtime directory. They are experiment setup, not agent remediation. The fault is reverted by destroying the disposable overlay with `lab/qemu/scripts/reset.sh`.
