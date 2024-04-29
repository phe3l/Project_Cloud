from flask import Flask, request, jsonify
import os
import requests
import json
from flask_cors import CORS
import logging
from datetime import datetime
from google.cloud import bigquery

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
CORS(app)

# Environment variables for API keys and credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "//Users/phil/Desktop/IS M.02/Cloud and Advanced Analytics/Projet/Project_Cloud/Flask/weather-project-421218-514efeab5430.json"
OPENWEATHERMAP_API_KEY= "6c1ec52962485a3d1f1eeea625b41687"
IPINFO_API_KEY = "903affb52eaa2a"

# Constants for BigQuery dataset
PROJECT_ID = "weather-project-421218"
DATASET_NAME = "weather_dataset" 
WEATHER_TABLE = "weather-records"

# Configure BigQuery client
client = bigquery.Client(project=PROJECT_ID)

"""Insert data into BigQuery."""
def insert_into_bigquery(data):
    now = datetime.now()
    data.update({'date': now.strftime('%Y-%m-%d'), 'time': now.strftime('%H:%M:%S')})
    columns = ", ".join([f"`{key}`" for key in data.keys()])
    values = ", ".join([f"'{value}'" if isinstance(value, str) else str(value) for value in data.values()])
    query = f"INSERT INTO `{PROJECT_ID}.{DATASET_NAME}.{WEATHER_TABLE}` ({columns}) VALUES ({values})"
    client.query(query).result()


"""Fetch location data from IPInfo."""
def fetch_location_data(ip):
    response = requests.get(f"http://ipinfo.io/{ip}/json?token={IPINFO_API_KEY}")
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(f"Failed to get location data: HTTP {response.status_code}")

"""Fetch weather forecast data from OpenWeatherMap."""
def fetch_weather_data(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise ValueError(f"Failed to get weather data: HTTP {response.status_code}")






@app.route('/send-to-bigquery', methods=['POST'])
def send_to_bigquery():
    try:
        data = request.get_json(force=True)["values"]
        insert_into_bigquery(data)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logging.error(f"Error inserting data into BigQuery: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/future-weather', methods=['POST'])
def get_future_weather():
    try:
        data = request.get_json(force=True)
        ip = data.get('ip')
        if not ip:
            raise ValueError("IP address is required")

        location_data = fetch_location_data(ip)
        lat, lon = location_data['loc'].split(',')
        weather_data = fetch_weather_data(lat, lon)

        return jsonify({"status": "success", "data": weather_data}), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"status": "error", "message": "An error occurred processing your request."}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)