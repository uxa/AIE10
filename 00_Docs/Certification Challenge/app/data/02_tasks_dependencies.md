# Tasks, Operators, and Dependencies

## Tasks and Operators

A **task** is a single unit of work in a DAG. Tasks are created from
**operators**, which are templates for a type of work:

- `PythonOperator` / `@task`: run Python code.
- `BashOperator`: run a shell command.
- `EmptyOperator`: a no-op placeholder, useful for grouping.
- Provider operators (e.g. `PostgresOperator`, `S3ToRedshiftOperator`) integrate
  with external systems and are installed via provider packages.

A **sensor** is a special operator that waits for a condition to be true (for
example `S3KeySensor` waits for a file to land). Prefer `mode="reschedule"` for
long waits so the worker slot is freed between checks, or use deferrable
operators to release the worker entirely.

## Setting task dependencies

Use the bitshift operators to declare order:

```python
extract >> transform >> load        # chain
extract >> [transform_a, transform_b]  # fan-out
[transform_a, transform_b] >> load     # fan-in
```

You can also use `.set_downstream()` / `.set_upstream()`, or the `chain()` and
`cross_downstream()` helpers from `airflow.models.baseoperator`.

With the TaskFlow API, dependencies are inferred automatically from how you pass
the output of one `@task` function into another.

## Task instances and states

A **task instance** is a specific run of a task for a given DAG run. Common
states include `queued`, `running`, `success`, `failed`, `skipped`,
`up_for_retry`, and `upstream_failed`.

## Retries and trigger rules

Set `retries` and `retry_delay` in `default_args` to handle transient failures.
The `trigger_rule` parameter controls when a task runs relative to its upstreams
(default `all_success`; others include `all_done`, `one_failed`,
`none_failed_min_one_success`).
