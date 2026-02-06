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

*To be filled as we build the project*

## 🏗️ Architecture

*Architecture diagram coming soon*

## 📁 Project Structure

```
weather-pipeline/
├── airflow/          # Airflow DAGs and configurations
├── dbt/              # dbt models and transformations
├── sql/              # Database initialization scripts
├── dashboard/        # Streamlit dashboard application
├── docs/             # Documentation and diagrams
└── docker-compose.yml
```

## 🚀 Setup Instructions

*Detailed setup instructions will be added as we build the project*

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/sohamwaghe/weather-pipeline.git
cd weather-pipeline

# Copy environment template
cp .env.example .env

# Fill in your environment variables in .env

# Start the services
docker-compose up -d
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
