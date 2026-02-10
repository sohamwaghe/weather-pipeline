# ADR 0001: Architecture Overview

## Status
Accepted

## Context
The project requires a scalable, low-cost, and professional-grade data pipeline to extract weather data from an API, transform it for analytics, and visualize it for end-users. The goal is to demonstrate modern data engineering practices suitable for a professional portfolio.

## Decision
We chose a containerized ELT (Extract, Load, Transform) architecture using the following stack:

1.  **Orchestration**: Apache Airflow. Chosen for its robustness, ability to handle complex task dependencies, and industry-standard status.
2.  **Storage**: PostgreSQL. A reliable, scalable relational database that supports both JSONB (for raw data) and structured relations (for analytics).
3.  **Transformation**: dbt (data build tool). Enables modular SQL development with embedded testing and documentation, fitting the "transformation as code" paradigm.
4.  **API**: WeatherStack. Selected as a reliable source for current global weather data with a friendly free tier.
5.  **Visualization**: Streamlit. Allows for rapid development of data-focused web apps using pure Python, with excellent support for Plotly interactive charts.
6.  **Environment**: Docker Compose. Ensures local reproducibility and easy deployment by isolating services into distinct containers.

## Alternatives Considered
- **ETL Approach**: Extracting and transforming data in Python before loading. *Rejected* because ELT is more modern, better for troubleshooting (raw data preservation), and leverages the database for compute.
- **SQLite**: *Rejected* due to lack of JSONB support and concurrency limitations.
- **Prefect**: *Rejected* in favor of Airflow to demonstrate mastery of the more complex, widely-used enterprise tool.

## Consequences
- **Positive**: Clear separation of concerns, automated data quality checks, and high visibility into pipeline health.
- **Neutral**: Requires more local resources (Docker) compared to a single script.
- **Negative**: Higher setup complexity than a monolithic Python script.
