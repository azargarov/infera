# Reviewed `network-dependency-001` run

This reviewed synthetic run demonstrates layer discrimination. The agent
observed that `demo-upstream.local` resolved locally, the local route existed,
the expected listener was absent, and the API recorded connection refusal.
It concluded that the local dependency endpoint was unavailable without
claiming a remote, DNS, firewall, or route root cause.

No network configuration, service, route, firewall, or DNS settings were
changed during diagnosis. The run was validated structurally and by the
network scenario evaluator.
