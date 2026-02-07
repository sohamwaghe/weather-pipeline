# Real-Time Weather Data Pipeline

A modern data engineering portfolio project that demonstrates end-to-end ELT pipeline development using industry-standard tools and best practices.

## 📋 Description

This project implements a real-time weather data pipeline that:
- Extracts weather data from the WeatherStack API
- Loads raw data into PostgreSQL
- Transforms data using dbt (data build tool)
- Orchestrates workflows with Apache Airflow
- Visualizes insights through an interactive dashboard

## 🛠️ Tech Stack

- **Containerization:** Docker & Docker Compose
- **Orchestration:** Apache Airflow (LocalExecutor)
- **Data Warehouse:** PostgreSQL (v15 Alpine)
- **Transformation:** dbt (Data Build Tool)
- **Languages:** Python 3.9+, SQL

## 🏗️ Architecture

*Architecture diagram coming soon*

## 🚀 Quick Start Guide

### Prerequisites
- **Docker Desktop** installed and running
- **WeatherStack API Key**: Get a free key from [weatherstack.com](https://weatherstack.com/)
- **Git** installed
- At least 4GB RAM allocated to Docker

### Installation & Startup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sohamwaghe/weather-pipeline.git
   cd weather-pipeline
   ```

2. **Configure Environment**
   Create a `.env` file from the example template:
   ```bash
   # On Windows PowerShell
   Copy-Item .env.example .env
   # On Mac/Linux
   cp .env.example .env
   ```
   
   **Edit the `.env` file** and add your WeatherStack API key:
   ```env
   WEATHERSTACK_API_KEY=your_actual_api_key_here
   ```

3. **Launch Services**
   Build and start the Airflow and Database containers:
   ```bash
   docker-compose up -d --build
   ```
   *Note: The first run may take a few minutes to build the image and initialize the database.*

4. **Access Interfaces**
   - **Airflow UI:** [http://localhost:8080](http://localhost:8080) (Login: `airflow` / `airflow`)
   - **Database:** `localhost:5432` (User: `airflow`, Pass: `airflow`, DB: `weather_db`)


## 🔍 Verifying Setup

### 1. Check Container Status
Ensure all containers are healthy (running):
```bash
docker-compose ps
```

### 2. Run Comprehensive Pipeline Test
We've included a script to verify the entire pipeline (DB, Schemas, Data, Analytics). Run it inside the Airflow container:
```bash
docker-compose run --rm weather_airflow_webserver python test_pipeline.py
```

## 📈 Monitoring & usage

### Airflow DAGs
- Go to `http://localhost:8080`.
- Enable the `weather_etl_pipeline` DAG using the toggle switch.
- Trigger a run manually or wait for the hourly schedule.

### dbt Documentation
To view the generated lineage and model documentation:
1. Shell into the container: `docker-compose exec weather_airflow_webserver bash`
2. Run docs server: `cd /opt/dbt && dbt docs serve --port 8001`
3. Access at `http://localhost:8001` (requires port mapping in docker-compose)

## 🐛 Troubleshooting
See [docs/troubleshooting.md](docs/troubleshooting.md) for solutions to common errors like DB connection failures or API limits.

## 👤 Author

**Soham Waghe**

---

*This is a portfolio project demonstrating data engineering skills and best practices.*
