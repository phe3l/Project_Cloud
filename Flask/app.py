from flask import Flask, request, jsonify
from google.cloud import bigquery
import os
import requests
import json
from flask_cors import CORS
import logging
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
#CORS(app, origins=['https://your-trusted-origin.com'])

# Authenticate to Google Cloud securely
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "//Users/phil/Desktop/IS M.02/Cloud and Advanced Analytics/Projet/Project_Cloud/Flask/weather-project-421218-514efeab5430.json"

# Constants for BigQuery dataset
PROJECT_ID = "weather-project-421218"
DATASET_NAME = "weather_dataset" 
WEATHER_TABLE = "weather-records"
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

# Configure BigQuery client
client = bigquery.Client(project=PROJECT_ID)

@app.route('/send-to-bigquery', methods=['POST'])
def send_to_bigquery():
    try:
        data = request.get_json(force=True)["values"]
        # Generate current timestamp
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        # Prepare data including timestamp
        data['date'] = date_str
        data['time'] = time_str

        column_names = ", ".join([f"`{key}`" for key in data.keys()])
        column_values = ", ".join([f"'{value}'" if isinstance(value, str) else str(value) for value in data.values()])
        
        insert_query = f"""
        INSERT INTO `{PROJECT_ID}.{DATASET_NAME}.{WEATHER_TABLE}` ({column_names})
        VALUES ({column_values})
        """
        query_job = client.query(insert_query)
        query_job.result()  # Waits for the query to finish
        
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        logging.error(f"Error inserting data into BigQuery: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)