# Airflow DAGs (Directed Acyclic Graphs)

A DAG (Directed Acyclic Graph) is the core concept of Apache Airflow. A DAG
represents a workflow: a collection of tasks organized with dependencies and
relationships that describe how they should run. "Acyclic" means the graph has
no cycles, so a task can never depend on itself directly or indirectly.

## Defining a DAG

The modern, recommended way to define a DAG is with the `@dag` TaskFlow
decorator or the `DAG` context manager.

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(schedule="@daily", start_date=datetime(2024, 1, 1), catchup=False)
def my_pipeline():
    @task
    def extract():
        return {"rows": 100}

    @task
    def transform(data: dict):
        return data["rows"] * 2

    transform(extract())

my_pipeline()
```

## Key DAG parameters

- `dag_id`: unique identifier for the DAG.
- `schedule`: how often the DAG runs (cron string, timedelta, or preset like
  `@daily`). Use `None` for manual-only runs.
- `start_date`: the logical date from which the DAG becomes eligible to run.
- `catchup`: when `True`, Airflow backfills all missed runs between
  `start_date` and now. Set to `False` to only run from now forward.
- `tags`: labels used for filtering DAGs in the UI.
- `default_args`: a dict of arguments applied to every task (e.g. `retries`,
  `retry_delay`, `owner`).

## DAG runs and logical date

Each execution of a DAG is a **DAG run**, identified by a `logical_date`
(historically called `execution_date`). The logical date represents the start
of the data interval the run is responsible for, which is why a `@daily` DAG
scheduled for Jan 2 actually runs after Jan 2's interval completes.
