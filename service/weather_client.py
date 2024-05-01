import requests
import os


class WeatherClient:
    def __init__(self):
        self.ipinfo_api_key = os.getenv('IPINFO_API_KEY')
        self.openweathermap_api_key = os.getenv('OPENWEATHERMAP_API_KEY')

    def fetch_location_data(self, ip):
        """Fetch location data from IPInfo."""
        url = f"http://ipinfo.io/{ip}/json?token={self.ipinfo_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to get location data: HTTP {response.status_code}")

    def fetch_weather_data(self, lat, lon, current_weather=False):
        """Fetch weather forecast data from OpenWeatherMap."""
        if current_weather:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.openweathermap_api_key}&units=metric"
        else:
            url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.openweathermap_api_key}&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to get weather data: HTTP {response.status_code}")

