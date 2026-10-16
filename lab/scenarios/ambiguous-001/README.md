# ambiguous-001 injection

This setup-only fixture keeps `demo-db.service` healthy and enables a synthetic generic degraded response in `demo-api.service`. The API returns HTTP 503 without identifying a cause and emits no decisive dependency or configuration failure detail. This leaves more than one explanation plausible from the bounded evidence available to the diagnostic agent.

Run it only against the disposable local QEMU target:

~~~bash
./lab/scenarios/ambiguous-001/inject.sh ambiguous-001
./lab/scenarios/ambiguous-001/verify.sh ambiguous-001
~~~

The injector and verifier require the synthetic hostname and localhost SSH forwarding. The condition is reverted by destroying the disposable overlay with `lab/qemu/scripts/reset.sh`.
