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
You should see `weather_postgres`, `weather_redis`, `weather_airflow_webserver`, and `weather_airflow_scheduler` all in `Up` (healthy) state.

### 2. Run Connection Test
We've included a script to verify the database schema and connectivity. Run it inside the Airflow container:

```bash
docker-compose run --rm airflow-webserver python test_connection.py
```

**Expected Output:**
```
✅ Successfully connected to PostgreSQL!
Checking schemas...
  ✅ Schema 'raw' exists
  ✅ Schema 'staging' exists
  ✅ Schema 'analytics' exists
checking tables...
  ✅ Table 'raw.weather_data' exists
🎉 SYSTEM CHECK PASSED: Database is correctly initialized!
```

## 📊 Features

*Features will be documented as they are implemented*

## 📝 License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2026 Soham Waghe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 👤 Author

**Soham Waghe**

---

*This is a portfolio project demonstrating data engineering skills and best practices.*
