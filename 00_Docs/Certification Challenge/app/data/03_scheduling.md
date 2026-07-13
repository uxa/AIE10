# Scheduling, Data Intervals, and Backfill

## The schedule parameter

The `schedule` argument controls how often a DAG runs. It accepts:

- Cron expressions: `"0 3 * * *"` (daily at 03:00).
- Cron presets: `"@hourly"`, `"@daily"`, `"@weekly"`, `"@monthly"`.
- `timedelta` objects: `timedelta(hours=6)` for interval-based scheduling.
- `None` or `"@once"`: manual / single-run DAGs.
- Datasets (data-aware scheduling): pass a list of `Dataset` objects to trigger
  a DAG when upstream datasets are updated instead of on a clock.

## Data intervals and logical date

Airflow runs are interval-based. A DAG run covers a **data interval**
(`data_interval_start` to `data_interval_end`). A run is triggered **after** the
end of its interval. For a `@daily` DAG, the run with logical date Jan 1 starts
executing shortly after midnight Jan 2, because it is responsible for Jan 1's
data.

## Catchup and backfill

- `catchup=True` (default): when a DAG is unpaused, Airflow creates runs for
  every missed interval since `start_date`. This can flood the scheduler; most
  teams set `catchup=False`.
- Backfill: run `airflow dags backfill -s <start> -e <end> <dag_id>` to
  intentionally re-run a historical date range.

## Timetables

For scheduling logic that cron cannot express (e.g. skip weekends/holidays),
implement a custom **Timetable** or use the built-in `CronTriggerTimetable`.

## Common pitfall

If your DAG "isn't running," check: it is unpaused, the `start_date` is in the
past, `catchup` behavior is what you expect, and the schedule interval has
actually elapsed.
