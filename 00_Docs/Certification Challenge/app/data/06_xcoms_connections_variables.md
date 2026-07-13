# XComs, Connections, and Variables

## XComs (cross-communication)

XComs let tasks pass small amounts of data between each other. A task "pushes"
a value and a downstream task "pulls" it.

```python
@task
def push():
    return 42          # implicitly pushed as an XCom

@task
def pull(value: int):  # TaskFlow auto-pulls the upstream return value
    print(value)

pull(push())
```

With classic operators, use `ti.xcom_push(key="k", value=v)` and
`ti.xcom_pull(task_ids="push", key="k")`.

**Important:** XComs are stored in the metadata database and are meant for small
data (IDs, file paths, counts) — not large datasets. For big data, write to
external storage (S3, a database) and pass a reference via XCom. A custom XCom
backend can redirect XCom storage to S3/GCS.

## Connections

Connections store credentials and endpoints for external systems (databases,
APIs, cloud services). Manage them in the UI under Admin > Connections, via the
`airflow connections` CLI, or with the `AIRFLOW_CONN_<CONN_ID>` environment
variable. Operators and hooks reference a connection by its `conn_id`.

## Variables

Variables are key-value pairs for configuration you want to reuse across DAGs.

```python
from airflow.models import Variable
bucket = Variable.get("data_bucket")
```

Set them in the UI (Admin > Variables), the `airflow variables` CLI, or via
`AIRFLOW_VAR_<KEY>` environment variables. Store secrets in a secrets backend
(AWS Secrets Manager, HashiCorp Vault) rather than plaintext Variables.

## Hooks

A **hook** is a reusable interface to an external system (e.g. `PostgresHook`,
`S3Hook`). Operators use hooks under the hood; you can also call hooks directly
inside a `@task` for custom logic.
