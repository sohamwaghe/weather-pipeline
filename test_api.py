import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_weather(city_name):
    api_key = os.getenv("WEATHERSTACK_API_KEY")
    if not api_key:
        print("Error: WEATHERSTACK_API_KEY not found in .env file.")
        return

    base_url = "http://api.weatherstack.com/current"
    params = {
        "access_key": api_key,
        "query": city_name
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        data = response.json()
        
        # Check for API-specific errors (WeatherStack returns 200 even for some errors)
        if "error" in data:
            print(f"API Error for {city_name}: {data['error']['info']}")
            return

        # Print full JSON response
        print(f"--- Full Response for {city_name} ---")
        print(json.dumps(data, indent=4))
        print("-" * 30)

        # Extract and print key fields
        current = data.get("current", {})
        location = data.get("location", {})
        
        temperature = current.get("temperature")
        humidity = current.get("humidity")
        weather_descriptions = current.get("weather_descriptions", [])
        description = weather_descriptions[0] if weather_descriptions else "N/A"
        
        print(f"City: {location.get('name')}")
        print(f"Temperature: {temperature}°C")
        print(f"Humidity: {humidity}%")
        print(f"Weather: {description}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {city_name}: {e}")

if __name__ == "__main__":
    get_weather("London")
