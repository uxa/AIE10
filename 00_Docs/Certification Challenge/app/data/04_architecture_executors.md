# Airflow Architecture and Executors

## Core components

- **Scheduler**: monitors DAGs and task instances, decides what to run and when,
  and submits ready tasks to the executor. It is the heart of Airflow.
- **Executor**: defines *how* and *where* tasks run. The executor is a
  configuration property of the scheduler, not a separate service.
- **Workers**: the processes that actually execute task code (for distributed
  executors).
- **Webserver**: serves the Airflow UI (built on FastAPI in Airflow 3;
  Flask/Gunicorn in Airflow 2).
- **Metadata database**: a relational DB (Postgres recommended) that stores DAG,
  task, run, and state information.
- **DAG files**: Python files in the `dags/` folder, parsed by the dag processor.

## Scheduler vs Executor

The **scheduler** figures out *what* should run (dependency resolution,
scheduling, queuing). The **executor** determines *how* those queued tasks are
run (locally, in Celery workers, or in Kubernetes pods). They work together: the
scheduler enqueues tasks, the executor runs them.

## Executor types

- **LocalExecutor**: runs tasks as subprocesses on a single machine. Good for
  small/medium single-node deployments.
- **CeleryExecutor**: distributes tasks to a pool of Celery workers via a broker
  (Redis/RabbitMQ). Scales horizontally.
- **KubernetesExecutor**: launches each task in its own Kubernetes pod, giving
  per-task isolation and elastic scaling.
- **SequentialExecutor**: runs one task at a time (default with SQLite; for
  testing only).

## Choosing an executor

Use LocalExecutor for simplicity, CeleryExecutor for steady high-throughput
worker pools, and KubernetesExecutor for bursty workloads needing isolation and
custom per-task resources.
