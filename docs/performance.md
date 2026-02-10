# Performance Optimizations

This document outlines the performance optimization strategies implemented in the Weather Data Pipeline to ensure scalability, efficiency, and low latency.

## 💾 Database Layer

### 1. Incremental Loading
- **Pattern**: Although currently using a full refresh for small volumes, the `raw.weather_data` table is designed with a `unique(city_name, api_call_timestamp)` constraint.
- **Benefit**: Prevents duplicate ingestion without requiring complex logic in Airflow.

### 2. Analytical Schema (Star Schema)
- **Pattern**: Data is moved from a single JSONB blob in `raw` to a structured Star Schema in `analytics`.
- **Benefit**: Significantly faster query performance for the Streamlit dashboard. Instead of parsing JSON at runtime, queries perform simple joins on integer IDs.

### 3. dbt Materialization
- **Strategy**: Marts are materialized as `tables` rather than `views`.
- **Benefit**: Calculations (like temperature conversions and timestamp parsing) are performed once during the `dbt run` rather than every time the dashboard refreshes.

## 🚀 Orchestration (Airflow)

### 1. Task Atomicity
- **Strategy**: The DAG is broken down into small, single-responsibility tasks (`extract`, `load`, `seed`, `run`).
- **Benefit**: Failing tasks can be retried independently without re-running the entire pipeline, saving API credits and compute time.

### 2. Connection Pooling
- **Strategy**: Airflow uses the `psycopg2` module which is optimized for PostgreSQL connections.
- **Benefit**: Efficient management of database handles across multiple concurrent tasks.

## 📊 Visualization (Streamlit)

### 1. Data Caching
- **Implementation**: Used `@st.cache_data` for all heavy PostgreSQL queries.
- **Benefit**: Multiple users viewing the dashboard simultaneously or a single user refreshing the page results in zero database load if the data hasn't changed (5-minute TTL).

### 2. Resource Caching
- **Implementation**: Used `@st.cache_resource` for the database connection object.
- **Benefit**: Reuses a single connection pool across the entire user session, reducing the overhead of establishing new TLS/TCP connections.

### 3. Query Optimization
- **Implementation**: Used `SELECT DISTINCT ON (city_name) ... ORDER BY timestamp DESC` to fetch only the latest state.
- **Benefit**: Minimizes data transfer between PostgreSQL and the Streamlit container.

## ⚡ Infrastructure (Docker)

### 1. Multi-Stage Builds
- **Implementation**: Dockerfiles use `python:3.11-slim` to minimize image size.
- **Benefit**: Faster deployment times and reduced disk usage in production environments.

### 2. Environment Segregation
- **Implementation**: Separating Airflow, PostgreSQL, and Streamlit into distinct containers.
- **Benefit**: Prevents a single service (like a heavy dbt run) from starving the visualization layer of resources.
