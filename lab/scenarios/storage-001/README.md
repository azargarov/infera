# `storage-001`

This setup fixture fills only the disposable synthetic filesystem mounted at
`/srv/infera-data` inside the QEMU guest. It first confirms that the synthetic
application can write there, fills the mount as the `infera` user, and then
triggers the documented application write probe so the failure is recorded in
the service journal. The API remains running and SSH remains available.

The injector and verifier know the setup details. The prepared agent context
does not disclose the mount, fill threshold, or expected conclusion; the agent
must discover the affected scope through read-only evidence collection.

Run the setup only after booting the healthy lab:

```bash
./lab/scenarios/storage-001/inject.sh storage-001
./lab/scenarios/storage-001/verify.sh storage-001
./lab/scenarios/storage-001/prepare-run.sh storage-001-20261001T120000Z
```

Reset the disposable QEMU overlay after the experiment. No cleanup command is
part of diagnosis, and the injector's changes are not remediation.
