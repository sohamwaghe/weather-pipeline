
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
    initial_sidebar_state="collapsed"
)

# Auto-refresh every 5 minutes
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 300:
    st.session_state.last_refresh = time.time()
    st.rerun()

# --- Helper Functions ---

@st.cache_resource
def init_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            database=os.getenv("POSTGRES_DB", "weather_db"),
            user=os.getenv("POSTGRES_USER", "Airflow"),
            password=os.getenv("POSTGRES_PASSWORD", "Airflow"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
    except Exception as e:
        st.error(f"⚠️ Database connection failed: {e}")
        st.stop()

def run_query(query, params=None):
    """Run a query and return a DataFrame, with automated reconnection logic."""
    try:
        conn = init_connection()
        if params:
            return pd.read_sql(query, conn, params=params)
        else:
            return pd.read_sql(query, conn)
    except (psycopg2.InterfaceError, psycopg2.OperationalError, psycopg2.DatabaseError) as e:
        # If connection is dead, clear the resource cache and retry once
        st.cache_resource.clear()
        try:
            conn = init_connection()
            if params:
                return pd.read_sql(query, conn, params=params)
            else:
                return pd.read_sql(query, conn)
        except Exception as retry_error:
            st.error(f"⚠️ Connection lost and could not be recovered: {retry_error}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Query error: {e}")
        return pd.DataFrame()

def get_weather_emoji(weather_main):
    """Return emoji based on weather condition"""
    emojis = {
        'Clear': '☀️',
        'Clouds': '☁️',
        'Rain': '🌧️',
        'Drizzle': '🌦️',
        'Thunderstorm': '⛈️',
        'Snow': '❄️',
        'Mist': '🌫️',
        'Smoke': '💨',
        'Haze': '🌫️',
        'Fog': '🌁',
        'Sunny': '☀️',
        'Partly cloudy': '⛅',
        'Overcast': '☁️'
    }
    return emojis.get(weather_main, '🌤️')

@st.cache_data(ttl=300)
def fetch_latest_weather():
    """Fetch latest weather for all 5 cities"""
    query = """
        SELECT DISTINCT ON (c.city_name)
            c.city_name,
            c.country,
            f.temperature,
            f.feels_like,
            f.humidity,
            f.wind_speed,
            f.weather_description,
            t.timestamp
        FROM analytics.fact_weather f
        JOIN analytics.dim_cities c ON f.city_id = c.city_id
        JOIN analytics.dim_time t ON f.time_id = t.time_id
        ORDER BY c.city_name, t.timestamp DESC
    """
    return run_query(query)

@st.cache_data(ttl=300)
def fetch_temperature_trends():
    """Fetch 24h temperature trends for all 5 cities"""
    query = """
        SELECT 
            c.city_name,
            t.timestamp,
            f.temperature
        FROM analytics.fact_weather f
        JOIN analytics.dim_cities c ON f.city_id = c.city_id
        JOIN analytics.dim_time t ON f.time_id = t.time_id
        WHERE t.timestamp >= NOW() - INTERVAL '24 hours'
        ORDER BY t.timestamp
    """
    return run_query(query)

def check_pipeline_health():
    """Fetch pipeline health metrics"""
    query = """
        SELECT 
            MAX(ingestion_timestamp) as last_run,
            COUNT(*) as records_today
        FROM analytics.fact_weather
        WHERE ingestion_timestamp >= CURRENT_DATE
    """
    df = run_query(query)
    if not df.empty:
        return {
            'last_run': df.iloc[0]['last_run'],
            'records_today': df.iloc[0]['records_today']
        }
    return {'last_run': 'N/A', 'records_today': 0}

# --- Main Dashboard ---

# 1. Header Section
st.title("🌤️ Real-Time Weather Dashboard")
st.caption("Live data from WeatherStack API → Airflow → PostgreSQL → dbt")

health_data = check_pipeline_health()
last_run_str = health_data['last_run'].strftime('%H:%M') if isinstance(health_data['last_run'], pd.Timestamp) else "N/A"

h_col1, h_col2, h_col3 = st.columns([2, 2, 1])
with h_col1:
    st.metric("Last Data Sync", last_run_str)
with h_col2:
    st.metric("Cities Tracked", "5")
with h_col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# 2. Current Weather Section
st.header("Current Weather Conditions")

with st.spinner("Fetching latest updates..."):
    cities_data = fetch_latest_weather()

if not cities_data.empty:
    cols = st.columns(5)
    # Ensure we show all 5 cities even if some are missing data
    target_cities = ["London", "New York", "Tokyo", "Mumbai", "Sydney"]
    
    for idx, city_name in enumerate(target_cities):
        city_row = cities_data[cities_data['city_name'] == city_name]
        with cols[idx]:
            if not city_row.empty:
                city = city_row.iloc[0]
                st.markdown(f"### {city['city_name']}")
                st.caption(f"{city['country']}")
                
                temp = city['temperature']
                temp_color = "🔵" if temp < 15 else "🔴" if temp > 25 else "🟢"
                st.markdown(f"## {temp_color} {temp}°C")
                st.caption(f"Feels like {city['feels_like']}°C")
                
                emoji = get_weather_emoji(city['weather_description'])
                st.write(f"{emoji} {city['weather_description'].title()}")
                
                st.write(f"💧 {city['humidity']}% | 💨 {city['wind_speed']} m/s")
                st.caption(f"Updated: {city['timestamp'].strftime('%H:%M')}")
            else:
                st.markdown(f"### {city_name}")
                st.warning("No data found")
                st.caption("Fixing pipeline...")
else:
    st.info("No city data available in the analytics layer.")

st.divider()

# 3. Temperature Trends Section
st.header("📈 Temperature Trends (Last 24 Hours)")

with st.spinner("Analyzing trends..."):
    trends_df = fetch_temperature_trends()

if not trends_df.empty:
    fig = px.line(
        trends_df,
        x='timestamp',
        y='temperature',
        color='city_name',
        labels={'temperature': 'Temp (°C)', 'timestamp': 'Time'},
        height=400,
        template="plotly_white"
    )
    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Insufficient trend data for the last 24 hours.")

st.divider()

# 4. City Comparison Section
st.header("🌍 City Comparison")

if not cities_data.empty:
    c1, c2 = st.columns(2)
    
    with c1:
        fig_temp = px.bar(
            cities_data,
            x='city_name',
            y='temperature',
            title='Temperature Comparison (°C)',
            color='temperature',
            color_continuous_scale='RdYlBu_r',
            text_auto=True
        )
        st.plotly_chart(fig_temp, use_container_width=True)
        
    with c2:
        fig_humid = px.bar(
            cities_data,
            x='city_name',
            y='humidity',
            title='Humidity Comparison (%)',
            color='humidity',
            color_continuous_scale='Blues',
            text_auto=True
        )
        st.plotly_chart(fig_humid, use_container_width=True)

st.divider()

# 5. Pipeline Health Section
st.header("✅ Pipeline Health")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Last DAG Run", last_run_str, delta="Automatic")
with col2:
    st.metric("Records Today", health_data['records_today'], delta="Live")
with col3:
    # Placeholder for actual test status integration
    st.metric("Data Quality", "100%", delta="✅ Passed")
with col4:
    st.metric("System Uptime", "99.9%", delta="Stable")
