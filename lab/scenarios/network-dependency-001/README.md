# `network-dependency-001`

This setup fixture uses a local synthetic dependency endpoint. In the healthy
baseline, `demo-upstream.local` resolves to the QEMU guest and
`demo-upstream.service` listens on port `19090`. Injection enables the API's
network-dependency mode and stops only that disposable listener.

The name still resolves, the local route remains available, SSH is unaffected,
and the API records a failed connection. This lets the agent distinguish an
unavailable local endpoint from unsupported claims about remote DNS, routing,
firewall state, or another host.

Run after booting the healthy lab:

```bash
./lab/scenarios/network-dependency-001/inject.sh network-dependency-001
./lab/scenarios/network-dependency-001/verify.sh network-dependency-001
./lab/scenarios/network-dependency-001/prepare-run.sh network-dependency-001-20261001T120000Z
```

Reset the disposable overlay after the experiment. The injector is setup, not
agent remediation.
