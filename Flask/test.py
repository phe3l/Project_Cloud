from m5stack_ui import *
from uiflow import *
import network
import usocket as socket
import time
import unit
import urequests
import ntptime
from machine import RTC

screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xFFFFFF)

# Initialize the ENV3 unit connected to port A
env3_0 = unit.get(unit.ENV3, unit.PORTA)

wifi_credentials = [('TP-Link_76C4', '49032826'), ('iot-unil', '4u6uch4hpY9pJ2f9')]
flask_url = "http://192.168.0.103:8080"


# Revised UI setup for enhanced appearance
current_temp_label = M5Label('00.0°C', x=70, y=20, color=0x000, font=FONT_MONT_26, parent=None)
current_condition_label = M5Label('NoInfo', x=70, y=50, color=0x000, font=FONT_MONT_18, parent=None)

humidity_label = M5Label('Humidity: ', x=170, y=20, color=0x000, font=FONT_MONT_14, parent=None)
humidity = M5Label('H: ', x=250, y=20, color=0x000, font=FONT_MONT_14, parent=None)

pressure_label = M5Label('Air pressure: ', x=170, y=40, color=0x000, font=FONT_MONT_14, parent=None)
pressure = M5Label('P: ', x=250, y=40, color=0x000, font=FONT_MONT_14, parent=None)

forecast_label = M5Label('Forecast: Loading...', x=20, y=80, color=0x000, font=FONT_MONT_14, parent=None)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan

    for ssid, password in wifi_credentials:
        wlan.connect(ssid, password)
        for i in range(5):  # Attempt to connect for up to 10 seconds
            if wlan.isconnected():
                #current_condition_label.set_text('WiFi IP: ' + wlan.ifconfig()[0])
                return wlan
            time.sleep(1)
        wlan.disconnect()  # Cleanly disconnect if failed to connect

    #current_condition_label.set_text('Failed to connect to all networks.')
    return None

def get_public_ip():
    try:
        response = socket.getaddrinfo('api.ipify.org', 80)[0][-1]
        s = socket.socket()
        s.connect(response)
        s.send(b'GET /?format=text HTTP/1.1\r\nHost: api.ipify.org\r\n\r\n')
        data = s.recv(1024)
        s.close()
        ip_start = data.find(b'\r\n\r\n') + 4
        ip_end = data.find(b'\r\n', ip_start)
        public_ip = data[ip_start:ip_end].decode()
        #current_condition_label.set_text('Public IP: ' + public_ip)
        return public_ip
    except Exception as e:
        #current_condition_label.set_text('Error getting IP: ' + str(e))
        return None

def update_sensor_readings():
    current_temp_label.set_text(str(round(env3_0.temperature)) + " °C")
    pressure.set_text(str(round(env3_0.humidity)) + " %")

def get_forecast(ip):
    try:
        url = "{}/future-weather".format(flask_url)  # Using .format() for string formatting
        response = urequests.post(url, json={"ip": ip})
        if response.status_code == 200:
            forecast_data = response.json()
            display_forecast(forecast_data.get('data'))
            outdoor_temp = forecast_data['current_weather']['main']['temp']
            outdoor_humidity = forecast_data['current_weather']['main']['humidity']  # Humidity percentage

            return outdoor_temp, outdoor_humidity   # Return the outdoor temperature for further use
        else:
            forecast_label.set_text("Forecast fetch failed: HTTP " + str(response.status_code))
    except Exception as e:
        forecast_label.set_text("Failed to fetch forecast: " + str(e))
    finally:
        if response:
            response.close()
    return None  # Return None if no data was fetched or in case of an error

def send_data(ip, outdoor_temp, outdoor_humidity):
    data = {
        "values": {
            "indoor_temp": round(env3_0.temperature),
            "indoor_humidity": round(env3_0.humidity),
            "ip_address": ip,
            "outdoor_temp": outdoor_temp,
            "outdoor_humidity": outdoor_humidity,
        }
    }
    try:
        url = "{}/send-to-bigquery".format(flask_url)  # Using .format() for string formatting
        response = urequests.post(url, json=data)
    except Exception as e:
        forecast_label.set_text("Failed to send data: " + str(e))
    finally:
        if response:
            response.close()

def display_forecast(data):
    try:
        if data and 'list' in data and data['list']:
            # Assuming that the data['list'] contains at least one forecast entry
            first_forecast = data['list'][0]
            weather_info = first_forecast['weather'][0]['description']
            forecast_label.set_text("Forecast: " + weather_info)
        else:
            # Handle cases where the forecast data might not be as expected
            forecast_label.set_text("Forecast: No data available")
    except Exception as e:
        # Catch and handle any exceptions that occur when parsing the forecast data
        forecast_label.set_text("Forecast Error: " + str(e))
    
    
    
def display_forecast(data):
    try:
        forecasts = data['list']
        forecast_texts = []
        for forecast in forecasts[:5]:  # Limit to first 5 entries for display purposes
            temp = forecast['main']['temp']
            description = forecast['weather'][0]['description']
            forecast_texts.append("{}°C, {}".format(temp, description))
        
        forecast_str = "Forecasts: " + "; ".join(forecast_texts)  # Join all forecasts into one string
        forecast_label.set_text(forecast_str)
    except Exception as e:
        forecast_label.set_text("Forecast Error: ")
        
        
def main_loop():
    wlan = connect_wifi()
    if not wlan:
        print("Unable to connect to WiFi. Please check your settings.")
        return

    last_data_sent_time = time.ticks_ms()

    while True:
        update_sensor_readings()
        
        if time.ticks_diff(time.ticks_ms(), last_data_sent_time) >= 60000:  # Every 60 seconds
            public_ip = get_public_ip()
            if public_ip:
                outdoor_temp, outdoor_humidity = get_forecast(public_ip)  # Updates the forecast display as well
                if outdoor_temp is not None and outdoor_humidity is not None:
                    send_data(public_ip, outdoor_temp, outdoor_humidity)
            last_data_sent_time = time.ticks_ms()

        time.sleep(1) # Update sensor readings every second

main_loop()






