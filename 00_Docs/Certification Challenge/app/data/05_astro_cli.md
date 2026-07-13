# Running Airflow Locally with the Astro CLI

The Astro CLI (from Astronomer) is the fastest way to run Apache Airflow locally
in Docker. It wraps Docker Compose to spin up the scheduler, webserver, and a
Postgres metadata database.

## Install

```bash
# macOS (Homebrew)
brew install astro

# or via the install script
curl -sSL https://install.astronomer.io | sudo bash -s
```

Verify with `astro version`. Docker Desktop (or a compatible engine) must be
running.

## Create and run a project

```bash
mkdir my-airflow && cd my-airflow
astro dev init      # scaffolds dags/, Dockerfile, requirements.txt, etc.
astro dev start     # builds the image and starts Airflow locally
```

By default the Airflow UI is at `http://localhost:8080` (login `admin`/`admin`).

## Project structure created by `astro dev init`

- `dags/`: your DAG Python files.
- `Dockerfile`: pins the Astro Runtime image (a production Airflow distribution).
- `requirements.txt`: Python packages to install into the image.
- `packages.txt`: OS-level (apt) packages.
- `plugins/`: custom Airflow plugins.
- `include/`: extra files (SQL, configs) available to DAGs.
- `airflow_settings.yaml`: local-only Connections, Variables, and Pools.

## Common commands

- `astro dev stop`: stop the running containers.
- `astro dev restart`: restart after changing the Dockerfile or requirements.
- `astro dev logs`: stream component logs.
- `astro dev bash`: open a shell inside the scheduler container.

## Fixing a port 8080 conflict

If another service already uses 8080, override the webserver port:

```bash
astro config set webserver.port 8081
astro dev restart
```

You can similarly change `postgres.port` if 5432 is taken.
