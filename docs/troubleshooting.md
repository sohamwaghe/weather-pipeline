# Troubleshooting Guide

This guide covers common issues you might encounter when running the Weather Data Pipeline.

## 🐳 Docker Issues

### `Container exited with code 1`
*   **Cause**: Usually a configuration error or missing dependency.
*   **Fix**: Check the logs for the specific service.
    ```bash
    docker-compose logs <service_name>
    ```
    *Example: `docker-compose logs weather_airflow_scheduler`*

### `Can't connect to PostgreSQL`
*   **Cause**: Database container isn't running or credentials are wrong.
*   **Fix**:
    1.  Check if postgres is healthy: `docker-compose ps`
    2.  Verify `.env` POSTGRES variables match what's in `docker-compose.yml`.

## 🌬️ Airflow Issues

### `Airflow DAG not appearing`
*   **Cause**: Syntax error in the DAG file or scheduler isn't picking it up.
*   **Fix**:
    1.  Check Scheduler logs for python errors: `docker-compose logs weather_airflow_scheduler`
    2.  Look for "Broken DAGs" capability in the Airflow UI home page.

### `Tasks stuck in "Queued"`
*   **Cause**: Task runner (Worker/LocalExecutor) has died or resource starvation.
*   **Fix**: Restart the scheduler/airflow containers.
    ```bash
    docker-compose restart weather_airflow_scheduler
    ```

## 🛠️ dbt Issues

### `dbt connection failed`
*   **Cause**: `profiles.yml` misconfiguration or network issue.
*   **Fix**:
    1.  Ensure `profiles.yml` uses environment variables `{{ env_var(...) }}`.
    2.  Verify the `host` is set to `postgres` (Service name) not `localhost` when running inside Docker.

### `Model not found`
*   **Cause**: Model file not in the correct directory or not enabled in `dbt_project.yml`.
*   **Fix**: Run `dbt list` to see what models dbt picks up.

## 🔌 API Issues

### `API rate limit exceeded` / `Success: False`
*   **Cause**: WeatherStack Free tier has limits (e.g. monthly cap).
*   **Fix**: Check your usage on the [WeatherStack Dashboard](https://weatherstack.com/dashboard). Wait for reset or upgrade.

### `No data in tables`
*   **Cause**: DAG hasn't run or tasks failed.
*   **Fix**:
    1.  Check Airflow Tree View for red (failed) tasks.
    2.  Check task logs for specific error messages.
