from flask import Flask, request, jsonify, send_file
import logging, os
from bigquery_client import BigQueryClient
from weather_client import WeatherClient
from vertexai_client import VertexAIClient
from texttospeech_client import TextToSpeechClient
from PIL import Image, ImageDraw, ImageFont
import requests
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
from io import BytesIO

FONT_PATH = os.path.join(os.path.dirname(__file__), 'Mont-Regular.ttf')

app = Flask(__name__)

bq_client = BigQueryClient() 
weather_client = WeatherClient()
vertex_ai_client = VertexAIClient()
text_to_speech_client = TextToSpeechClient()

logging.basicConfig(level=logging.INFO)
TMP_DIR = '/tmp'

@app.route('/')
def home():
    """Home endpoint to check if the service is up."""
    return "The service is up and running!"

@app.route('/send-to-bigquery', methods=['POST'])
def insert_weather():
    """Endpoint to insert weather & sensors data into BigQuery."""
    try:
        data = request.get_json(force=True)["values"]
        
        # Fetch location data using the IP address
        location_data = weather_client.fetch_location_data(data['ip_address'])
        lat, lon = location_data['loc'].split(',')
        
        # Fetch current weather using the latitude and longitude
        current_weather = weather_client.fetch_weather_data(lat, lon, current_weather=True)
        
        # Add outdoor temperature and humidity to the data
        data['outdoor_temp'] = current_weather['main']['temp']
        data['outdoor_humidity'] = current_weather['main']['humidity']
        
        response = bq_client.insert_into_bigquery(data)
        return jsonify({'message': response}), 200

    except Exception as e:
        logging.error(f"Error inserting data into BigQuery: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/send-pending-to-bigquery', methods=['POST'])
def insert_pending_weather():
    """Endpoint to insert pending sensors data into BigQuery."""
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

@app.route('/generate-weather-image', methods=['POST'])
def generate_weather_image():
    """Endpoint to generate an image with the current weather."""
    data = request.get_json()
    
    if 'ip' not in data:
        return jsonify({"error": "IP address is required"}), 400

    try:
        # Fetch location data using the IP address
        location_data = weather_client.fetch_location_data(data['ip'])
        lat, lon = location_data['loc'].split(',')
        
        # Fetch current weather using the latitude and longitude
        current_weather = weather_client.fetch_weather_data(lat, lon, current_weather=True)

        # Extract temperature, humidity, and icon information
        temperature = current_weather['main']['temp']
        humidity = current_weather['main']['humidity']
        icon_code = current_weather['weather'][0]['icon']
        icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"

        # Download the weather icon image
        icon_response = requests.get(icon_url, stream=True)
        icon_response.raise_for_status()
        icon_image = Image.open(icon_response.raw).convert("RGBA")

        # Generate the image
        image = Image.new('RGB', (321, 65), color=(35, 35, 35))
        draw = ImageDraw.Draw(image)
        
        # Load custom font
        font_path = FONT_PATH

        draw.text((24, 24), f"{temperature}°C", font=ImageFont.truetype(font_path, 25), fill=(46,143,219))
        draw.text((139, 18), f"{humidity}%", font=ImageFont.truetype(font_path, 20), fill=(245,245,245))
        draw.text((133, 41), f"Humidity", font=ImageFont.truetype(font_path, 11), fill=((141,140,145)))

        icon_width, icon_height = icon_image.size
        icon_x = 320 - icon_width - 5
        icon_y = (65 - icon_height) // 2

        # Paste the weather icon
        image.paste(icon_image, (icon_x, icon_y), icon_image)

        # Save the image
        temp_file = os.path.join(TMP_DIR, 'weather_image.png')
        image.save(temp_file)

        return send_file(temp_file, mimetype='image/png')
    except Exception as e:
        logging.error(f"Error generating weather image: {e}")
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

@app.route('/generate-future-weather-image', methods=['POST'])
def generate_future_weather_image():
    """Endpoint to generate an image with future weather forecast."""
    data = request.get_json()

    if 'ip' not in data:
        return jsonify({"error": "IP address is required"}), 400

    ip = data['ip']

    try:
        # Fetch location data using the IP address
        location_data = weather_client.fetch_location_data(ip)
        lat, lon = location_data['loc'].split(',')
        
        # Fetch future weather forecast using the latitude and longitude
        future_weather = weather_client.fetch_weather_data(lat, lon, current_weather=False)

        # Extract forecast for 24, 48, and 72 hours
        forecast_24h = future_weather['list'][8] 
        forecast_48h = future_weather['list'][16]
        forecast_72h = future_weather['list'][24]

        forecasts = [forecast_24h, forecast_48h, forecast_72h]

        # Generate the image with future weather forecast
        image = Image.new('RGB', (321, 100), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Load custom font
        font_path = FONT_PATH

        # Starting position for text and icons
        x_positions = [30, 135, 240]
        y_date = 10
        y_temp_humidity = 30
        y_icon = 45

        for i, forecast in enumerate(forecasts):
            date_str = forecast['dt_txt']
            date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            formatted_date = date.strftime('%a %d')
            
            temperature = forecast['main']['temp']
            humidity = forecast['main']['humidity']
            icon_code = forecast['weather'][0]['icon']
            icon_url = f"https://openweathermap.org/img/wn/{icon_code}.png"
            
            # Download the weather icon image
            icon_response = requests.get(icon_url, stream=True)
            icon_response.raise_for_status()
            icon_image = Image.open(icon_response.raw).convert("RGBA")
            icon_image = icon_image.resize((50, 50), Image.LANCZOS)

            icon_x = x_positions[i]
            icon_y = y_icon

            # Paste the weather icon on the image
            image.paste(icon_image, (icon_x, icon_y), icon_image)
            
            draw.text((icon_x, y_date), formatted_date, font=ImageFont.truetype(font_path, 15), fill=(255,161,3))
            draw.text((icon_x, y_temp_humidity), f"{round(temperature)}°C | {humidity}%", font=ImageFont.truetype(font_path, 13), fill=(215,214,219))

        # Save the image
        temp_file = os.path.join(TMP_DIR, 'future_weather_image.png')
        image.save(temp_file)

        return send_file(temp_file, mimetype='image/png')
    except Exception as e:
        logging.error(f"Error generating future weather image: {e}")
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
        
        SYSTEM_INSTRUCTION = """This transformer takes weather conditions (might include temperature, weather condition, humidity, wind speed and others) as inputs. 
                    It processes these inputs to generate a PLAYFUL and engaging text description of the weather.
                    It makes it lyrical and engaging, with a touch of humor.
                    The generated text is crafted to be phonetically clear and simple, making it ideal for text-to-speech applications. 
                    No longer then 50 words. No emojis, special characters, or HTML tags."""
        
        # Generate a spoken description of the current weather
        description = vertex_ai_client.get_weather_description(str(current_weather), system_instruction=SYSTEM_INSTRUCTION)
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
    

@app.route('/generate-future-weather-spoken', methods=['POST'])
def generate_future_weather_spoken():
    """Endpoint to generate a spoken description of the future weather (in 6 hours) with dressing advice."""
    
    data = request.get_json()
    if 'ip' not in data:
        return jsonify({"error": "IP address is required"}), 400

    try:
        # Fetch location data using the IP address
        location_data = weather_client.fetch_location_data(data['ip'])
        lat, lon = location_data['loc'].split(',')
        
        # Fetch future weather using the latitude and longitude
        future_weather = weather_client.fetch_weather_data(lat, lon, current_weather=False)
        
        # Extract weather data for the next 6 hours (first forecast in the list)
        closest_forecast = future_weather['list'][1]

        # Get weather conditions
        weather_conditions = closest_forecast['weather'][0]['description']
        temp = closest_forecast['main']['temp']
        rain = closest_forecast.get('rain', {}).get('6h', 0)

        # Generate a spoken description using the text_to_speech service
        description_data = {
            "temperature": temp,
            "forecast_hour": (datetime.now() + timedelta(hours=6)).hour,
            "current_hour": datetime.now(),
            "weather_conditions": weather_conditions,
            "rain": rain,
        }
        
        SYSTEM_INSTRUCTION = """This transformer takes future weather conditions in 6 hours (including temperature, weather condition, humidity, wind speed, and others) as inputs. It processes these inputs to generate a text description of the future weather and advice for appropriate clothing and activities based on the forecasted conditions and time. Be inventive with the recommendations for clothing and activities. The advice is given in a serious tone. The generated text is crafted to be phonetically clear and simple, making it ideal for text-to-speech applications. No longer than 100 words. No emojis, special characters, or HTML tags."""

        description = vertex_ai_client.get_weather_description(str(description_data), system_instruction=SYSTEM_INSTRUCTION)
        voice_data = text_to_speech_client.generate_speech(description)
        
        temp_file = os.path.join(TMP_DIR, 'advice_output.wav')
        with open(temp_file, 'wb') as audio_file:
            audio_file.write(voice_data)
        
        return send_file(temp_file, mimetype='audio/wav')

    except Exception as e:
        logging.error(f"Error generating spoken weather description: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/fetch-bigquery-history', methods=['POST'])
def fetch_bigquery_history():
    """Endpoint to fetch weather data history from BigQuery."""
    
    try:
        results= bq_client.fetch_weather_data()
        return jsonify(results), 200
    
    except Exception as e:
        logging.error(f"Error fetching weather data history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/fetch-bigquery-history-image', methods=['GET'])
def fetch_bigquery_history_image():
    """
    Endpoint to retrieve historical weather data from BigQuery and generate a graphical representation.
    This endpoint fetches the weather data history stored in BigQuery for the last 7 days, 
    processes the data to calculate daily averages of temperature, humidity, and CO2 levels, 
    and then generates a visually appealing graph displaying these averages.
    """
    
    try:
        # Fetch data from BigQuery
        data = bq_client.fetch_average_weather_data(last_days=7)
        
        # Convert the data into a DataFrame
        df = pd.DataFrame(data)

        # Ensure the columns are of the correct data type
        df['date'] = pd.to_datetime(df['date'])  
        df['avg_temp'] = pd.to_numeric(df['avg_temp'])
        df['avg_humidity'] = pd.to_numeric(df['avg_humidity'])
        df['avg_co2'] = pd.to_numeric(df['avg_co2'])

        # Configure the size of the graph
        fig, axs = plt.subplots(3, 1, figsize=(3.2, 1.65), sharex=True)
        fig.patch.set_facecolor('black')
        
        # Configure the axes
        for ax in axs:
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            for spine in ax.spines.values():
                spine.set_visible(False)
        
        # Keep only the x-axis at the bottom visible
        axs[0].xaxis.set_visible(False)
        axs[1].xaxis.set_visible(False)

        
        # Plot the indoor temperature
        axs[0].plot(df['date'], df['avg_temp'], label='Indoor Temperature (°C)', marker='o', markersize=4, linewidth=1, color='#e058a7') 
        axs[0].set_ylabel('°C', fontsize=8, color='white')  
        axs[0].yaxis.set_ticks([])
        axs[0].yaxis.set_label_coords(-0.05, 0.5)
        axs[0].yaxis.label.set_rotation(0)

        # Show values for each point
        for i in range(len(df['date'])):
            axs[0].annotate(f"{int(df['avg_temp'].iloc[i])}", 
                            (df['date'].iloc[i], df['avg_temp'].iloc[i] + 0.2), 
                            fontsize=8, color='white',
                            ha='center', va='bottom')

        # Plot the indoor humidity
        axs[1].plot(df['date'], df['avg_humidity'], label='Indoor Humidity (%)', marker='o', markersize=4, linewidth=1, color='#007afe')
        axs[1].set_ylabel('H.%', fontsize=8, color='white')  
        axs[1].yaxis.set_ticks([])
        axs[1].yaxis.set_label_coords(-0.03, 0.5)
        axs[1].yaxis.label.set_rotation(0)

        # Show values for each point 
        for i in range(len(df['date'])):
            axs[1].annotate(f"{int(df['avg_humidity'].iloc[i])}", 
                            (df['date'].iloc[i], df['avg_humidity'].iloc[i] + 0.6), 
                            fontsize=8, color='white',
                            ha='center', va='bottom')

        # Plot the indoor air quality
        axs[2].plot(df['date'], df['avg_co2'], label='Indoor Air Quality (CO2)', marker='o', markersize=4, linewidth=1, color='#4cda63')
        axs[2].set_ylabel('CO2', fontsize=8, color='white') 
        axs[2].yaxis.set_ticks([])
        axs[2].yaxis.set_label_coords(-0.03, 0.5) 
        axs[2].yaxis.label.set_rotation(0)

        # Show values for each point
        for i in range(len(df['date'])):
            axs[2].annotate(f"{int(df['avg_co2'].iloc[i])}", 
                            (df['date'].iloc[i], df['avg_co2'].iloc[i] + 20), 
                            fontsize=8, color='white',
                            ha='center', va='bottom')
            
        # Configure the labels of the x-axis
        axs[2].xaxis.set_major_formatter(mdates.DateFormatter('%d'))
        axs[2].set_xticks(df['date'])
        axs[2].tick_params(axis='x', rotation=0, labelsize=8, colors='white')  

        # Adjust spacing between subplots
        plt.subplots_adjust(left=0.08, right=0.98, top=0.89, bottom=0.15, hspace=0.45)

        # Save the graph in a memory file
        img_io = BytesIO()
        plt.savefig(img_io, format='png', dpi=100, facecolor='black')
        img_io.seek(0)
        plt.close()

        return send_file(img_io, mimetype='image/png')
    
    except Exception as e:
        logging.error(f"Error fetching weather data history: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)