
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
st.set_page_config(
    page_title="Weather Pipeline Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Database Connection ---
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "weather_db"),
        user=os.getenv("POSTGRES_USER", "airflow"),
        password=os.getenv("POSTGRES_PASSWORD", "airflow"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

def run_query(query, params=None):
    conn = init_connection()
    try:
        if params:
            return pd.read_sql(query, conn, params=params)
        else:
            return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error running query: {e}")
        return pd.DataFrame()

# --- Header ---
st.title("🌤️ Real-Time Weather Data Pipeline Dashboard")
st.markdown("**Live data output from: WeatherStack API → Airflow → PostgreSQL → dbt**")
st.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# --- Sidebar ---
st.sidebar.header("Filters")

# Fetch available cities
city_df = run_query("SELECT city_name FROM analytics.dim_cities ORDER BY city_name")
if not city_df.empty:
    cities = city_df['city_name'].tolist()
else:
    cities = []

selected_cities = st.sidebar.multiselect("Select Cities", cities, default=cities[:3] if cities else [])

time_range = st.sidebar.selectbox(
    "Time Range",
    ["Last 6 Hours", "Last 12 Hours", "Last 24 Hours", "Last 7 Days"],
    index=2
)

if st.sidebar.button("Refresh Data"):
    st.rerun()

# --- Helper Logic ---
hours_map = {
    "Last 6 Hours": 6,
    "Last 12 Hours": 12,
    "Last 24 Hours": 24,
    "Last 7 Days": 168
}
hours = hours_map[time_range]

if not selected_cities:
    st.warning("Please select at least one city.")
    st.stop()

# --- Page 1: Current Weather ---
st.subheader("Current Weather Conditions")

# Query latest weather for selected cities
placeholders = ', '.join(['%s'] * len(selected_cities))
latest_query = f"""
    SELECT DISTINCT ON (c.city_name)
        c.city_name,
        c.country,
        f.temperature,
        f.feels_like,
        f.humidity,
        f.weather_description,
        t.timestamp
    FROM analytics.fact_weather f
    JOIN analytics.dim_cities c ON f.city_id = c.city_id
    JOIN analytics.dim_time t ON f.time_id = t.time_id
    WHERE c.city_name IN ({placeholders})
    ORDER BY c.city_name, t.timestamp DESC
"""

latest_df = run_query(latest_query, tuple(selected_cities))

if not latest_df.empty:
    cols = st.columns(len(latest_df))
    for idx, row in latest_df.iterrows():
        with cols[idx % 3]: # Wrap cols if many cities
            st.metric(
                label=f"{row['city_name']}, {row['country']}",
                value=f"{row['temperature']}°C",
                delta=f"Feels like {row['feels_like']}°C",
                delta_color="off"
            )
            st.write(f"💧 Humidity: {row['humidity']}%")
            st.write(f"📝 {row['weather_description']}")
            st.caption(f"Updated: {row['timestamp'].strftime('%H:%M')}")
            st.divider()

# --- Page 2: Temperature Trends ---
st.subheader(f"Temperature Trends ({time_range})")

trend_query = f"""
    SELECT 
        c.city_name,
        t.timestamp,
        f.temperature,
        f.feels_like
    FROM analytics.fact_weather f
    JOIN analytics.dim_cities c ON f.city_id = c.city_id
    JOIN analytics.dim_time t ON f.time_id = t.time_id
    WHERE t.timestamp >= NOW() - INTERVAL '{hours} hours'
    AND c.city_name IN ({placeholders})
    ORDER BY t.timestamp
"""

trend_df = run_query(trend_query, tuple(selected_cities))

if not trend_df.empty:
    fig = px.line(
        trend_df, 
        x="timestamp", 
        y="temperature", 
        color="city_name",
        title="Temperature Over Time",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No trend data available for the selected period.")

# --- Page 3: Comparisons ---
st.subheader("City Comparison")
metric = st.selectbox("Select Metric", ["Temperature", "Humidity", "Wind Speed", "Pressure"])

mapping = {
    "Temperature": "temperature",
    "Humidity": "humidity",
    "Wind Speed": "wind_speed",
    "Pressure": "pressure"
}
col_name = mapping.get(metric, "temperature")

# Re-use latest_df if metric is in it, otherwise query
# For simplicity, assuming these cols exist in fact_weather and we fetch them
# Let's verify cols in fact_weather... yes wind_speed, pressure exist.
# But latest_query didn't fetch them. Let's start a new query for comparison.
comp_query = f"""
    SELECT DISTINCT ON (c.city_name)
        c.city_name,
        f.{col_name} as value
    FROM analytics.fact_weather f
    JOIN analytics.dim_cities c ON f.city_id = c.city_id
    JOIN analytics.dim_time t ON f.time_id = t.time_id
    WHERE c.city_name IN ({placeholders})
    ORDER BY c.city_name, t.timestamp DESC
"""
comp_df = run_query(comp_query, tuple(selected_cities))

if not comp_df.empty:
    fig_bar = px.bar(
        comp_df.sort_values("value", ascending=False),
        x="city_name",
        y="value",
        color="city_name",
        title=f"Latest {metric} by City",
        text_auto=True
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# --- Page 4: Pipeline Health ---
st.subheader("Pipeline Health Checks")

health_query = """
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE WHEN ingestion_timestamp >= NOW() - INTERVAL '1 hour' THEN 1 END) as recent_records,
        MAX(ingestion_timestamp) as last_ingestion
    FROM analytics.fact_weather
"""
health_df = run_query(health_query)

if not health_df.empty:
    h_col1, h_col2, h_col3 = st.columns(3)
    h_col1.metric("Total Weather Records", health_df.iloc[0]['total_records'])
    h_col2.metric("Records Last Hour", health_df.iloc[0]['recent_records'])
    h_col3.metric("Last Ingestion", str(health_df.iloc[0]['last_ingestion']))

# Auto-refresh logic
time.sleep(60)
st.rerun()
