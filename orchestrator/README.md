### For migrations run:

```bash
alembic -c orchestrator/alembic.ini revision --autogenerate -m "migration message"
```

### Result consumer

The orchestrator runs a background consumer that processes `result_queue` messages
and updates query state to `COMPLETED` or `FAILED`, then publishes to
`results:{user_id}` channels.

Standalone runner:

```bash
uv run python -m orchestrator.tools.result_consumer_smoke
```
