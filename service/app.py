from flask import Flask, request, jsonify, send_file
import logging, os

from bigquery_client import BigQueryClient
from weather_client import WeatherClient
from vertexai_client import VertexAIClient
from texttospeech_client import TextToSpeechClient

app = Flask(__name__)

bq_client = BigQueryClient() 
weather_client = WeatherClient()
vertex_ai_client = VertexAIClient()
text_to_speech_client = TextToSpeechClient()

logging.basicConfig(level=logging.INFO)
TMP_DIR = '/tmp'

@app.route('/')
def home():
    return "The service is up and running!"

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
    
    
@app.route('/generate-current-weather-spoken', methods=['POST'])
def generate_current_weather_spoken():
    """Endpoint to generate a spoken description of the current weather."""
    data = request.get_json()
    
    if 'ip' not in data:
        return jsonify({"error": "IP address is required"}), 400

    try:
        # Fetch location data using the IP address
        location_data = weather_client.fetch_location_data(data['ip'])
        lat, lon = location_data['loc'].split(',')
        
        # Fetch current weather using the latitude and longitude
        current_weather = weather_client.fetch_weather_data(lat, lon, current_weather=True)
        
        # Generate a spoken description of the current weather
        description = vertex_ai_client.get_weather_description(str(current_weather))
        voice_data = text_to_speech_client.generate_speech(description)
        
        #temp_file = os.path.join(TMP_DIR, 'output.mp3')
        temp_file = os.path.join(TMP_DIR, 'weather_output.wav')

        with open(temp_file, 'wb') as audio_file:
            audio_file.write(voice_data)
        
        #return send_file(temp_file, as_attachment=True, mimetype='audio/mp3')
        return send_file(temp_file, mimetype='audio/wav')

    except Exception as e:
        logging.error(f"Error generating spoken weather description: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/generate-weather-spoken-from-text', methods=['POST'])
def generate_weather_spoken_from_text():
    """Endpoint to generate a spoken description of the weather (or other conditions) from text. 
    Mention in the text if the prompt is about conditions inside or outside the building."""
    
    data = request.get_json()
    
    if 'text' not in data:
        return jsonify({"error": "Text is required"}), 400

    try:
        # Generate a spoken description of the weather from the given text
        description = vertex_ai_client.get_weather_description(data['text'])
        voice_data = text_to_speech_client.generate_speech(description)
        
        temp_file = os.path.join(TMP_DIR, 'output.mp3')
        with open(temp_file, 'wb') as audio_file:
            audio_file.write(voice_data)
        
        return send_file(temp_file, as_attachment=True, mimetype='audio/mp3')
    except Exception as e:
        logging.error(f"Error generating spoken weather description: {e}")
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

