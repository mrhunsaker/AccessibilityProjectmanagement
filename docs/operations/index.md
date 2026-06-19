# Operations

Running APM beyond a single developer's laptop: deployment options,
monitoring, and the practical limits of the single-SQLite-file design.

| Page | Description |
|------|-------------|
| [Deployment](deployment.md) | Local, systemd, Windows Task Scheduler, and reverse-proxy deployment |
| [Monitoring](monitoring.md) | Operations Dashboard metrics, resource monitor, and audit log |
| [Scaling](scaling.md) | Practical entity limits and paths to scale beyond single-user use |

For a shared studio deployment, read [Deployment](deployment.md) and
[Scaling](scaling.md) together — APM's SQLite backend supports a handful of
concurrent users on a LAN but has real limits.
