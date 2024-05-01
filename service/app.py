from flask import Flask, request, jsonify
import logging
from bigquery_client import BigQueryClient
from weather_client import WeatherClient

app = Flask(__name__)
bq_client = BigQueryClient() 
weather_client = WeatherClient()

logging.basicConfig(level=logging.INFO)

@app.route('/send-to-bigquery', methods=['POST'])
def insert_weather():
    try:
        data = request.get_json(force=True)["values"]
        response = bq_client.insert_into_bigquery(data)
        return jsonify({'message': response}), 200

    except Exception as e:
        logging.error(f"Error inserting data into BigQuery: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
    
@app.route('/current-weather', methods=['POST'])
def get_current_weather():
    """Endpoint to fetch current weather based on the client's IP."""
    data = request.get_json()
    
    if 'ip' not in data:
        return jsonify({"error": "IP address is required"}), 400

    try:
        # Fetch location data using the IP address
        location_data = weather_client.fetch_location_data(data['ip'])
        lat, lon = location_data['loc'].split(',')
        
        # Fetch current weather using the latitude and longitude
        current_weather = weather_client.fetch_weather_data(lat, lon, current_weather=True)
        return jsonify(current_weather), 200
    except Exception as e:
        logging.error(f"Error fetching current weather: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/future-weather', methods=['POST'])
def get_future_weather():
    """Endpoint to fetch future weather forecast based on the client's IP."""
    data = request.get_json()
    if 'ip' not in data:
        return jsonify({"error": "IP address is required"}), 400

    try:
        # Fetch location data using the IP address
        location_data = weather_client.fetch_location_data(data['ip'])
        lat, lon = location_data['loc'].split(',')

        # Fetch weather forecast using the latitude and longitude
        future_weather = weather_client.fetch_weather_data(lat, lon, current_weather=False)
        return jsonify(future_weather), 200
    except Exception as e:
        logging.error(f"Error fetching future weather: {e}")
        return jsonify({"error": str(e)}), 500
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)


