# Data Quality Framework

## Overview
Our weather data pipeline includes a multi-layered data quality (DQ) framework to ensure that the analytics dashboard displays accurate and timely information. We use a combination of **dbt tests** for schema validation and **custom Python checks** for business logic and pipeline health.

## Monitoring Layers

### 1. dbt Tests (Schema & Constraints)
- **Tool:** dbt
- **Scope:** `analytics` schema (marts).
- **Key Checks:**
    - `not_null`: Ensures critical columns (temp, city_id) are populated.
    - `unique`: Prevents duplicate records in dimension tables.
    - `expression_is_true`: Validates temperature (-50°C to 60°C) and humidity (0-100%).

### 2. Pipeline Health Checks (Airflow)
- **Tool:** Python (`data_quality_checks.py`)
- **Scope:** Raw and Marts layers.
- **Key Checks:**
    - **Freshness**: Monitoring `ingestion_timestamp`. Fails if data is > 120 minutes old.
    - **Completeness**: Verifies all 5 target cities have records in the last 2 hours.
    - **Anomalies**: Detects sudden temperature swings (> 20°C/hr) and physically impossible values.
    - **NULL Monitoring**: Tracks the percentage of NULL values in measurements. Fails if > 5% in 24 hours.

## Failure Thresholds & Actions

| Check Type | Threshold (WARN) | Threshold (FAIL) | Action on FAIL |
|------------|------------------|------------------|----------------|
| Freshness  | > 90 min         | > 120 min        | Fail DAG, Alert |
| Completeness| Minor missing   | Any city missing | Fail DAG, Alert |
| Anomalies  | Suspicious jump  | Extreme outlier  | Fail DAG, Alert |
| NULLs      | 2-5%             | > 5%             | Fail DAG, Alert |

## Debugging Quality Issues

### If Freshness Fails:
- Check Airflow logs for `extract_weather_data` failure.
- Verify WeatherStack API status and remaining credit usage.
- Ensure the `weather_airflow_scheduler` is running.

### If Anomalies Found:
- Verify if the jump is localized (e.g., extreme weather event).
- Check raw JSON in `raw.weather_data` to see if the API returned an error string in a numeric field.

### If NULLs Spike:
- Check for schema changes in the WeatherStack API response.
- Inspect the `stg_weather` dbt model for casting errors.

## Historical Perspective
Data quality checks were introduced to catch "Garbage In, Garbage Out" scenarios early, preventing downstream analytics from being skewed by API transient errors or ingestion delays.
