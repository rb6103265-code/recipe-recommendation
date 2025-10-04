# weather.py
import os
import requests

API_KEY = os.getenv("OPENWEATHER_API_KEY")

def fetch_weather(location: str):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=metric"
        resp = requests.get(url, timeout=5)

        if resp.status_code != 200:
            # Invalid city or API error
            return None

        data = resp.json()

        return {
            "location": data.get("name", location),
            "condition": data["weather"][0]["main"] if data.get("weather") else "Unknown",
            "temp": data["main"]["temp"] if data.get("main") else None
        }

    except Exception as e:
        print(f"⚠️ Weather fetch error: {e}")
        return None
