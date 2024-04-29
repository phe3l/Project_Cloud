from m5stack_ui import *
from uiflow import *
import network
import usocket as socket
import time
import unit
import urequests

screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0xd5d5d5)

# Initialize the ENV3 unit connected to port A
env3_0 = unit.get(unit.ENV3, unit.PORTA)

# UI Labels for Temperature, Humidity, Weather Forecast, and IP
Temp = M5Label('Temp:', x=19, y=82, color=0x000, font=FONT_MONT_22, parent=None)
Humidity = M5Label('Humidity:', x=19, y=123, color=0x000, font=FONT_MONT_22, parent=None)
temp_value_label = M5Label('T', x=163, y=82, color=0x000, font=FONT_MONT_22, parent=None)
humidity_value_label = M5Label('H', x=158, y=123, color=0x000, font=FONT_MONT_22, parent=None)
Forecast = M5Label('Forecast: Loading...', x=20, y=160, color=0x000, font=FONT_MONT_22, parent=None)
IPLabel = M5Label('IP: Loading...', x=20, y=40, color=0x000, font=FONT_MONT_22, parent=None)

wifi_credentials = [('TP-Link_76C4_5G', '49032826'),('iot-unil', '4u6uch4hpY9pJ2f9')]

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan

    for ssid, password in wifi_credentials:
        wlan.connect(ssid, password)
        for i in range(10):  # Attempt to connect for up to 10 seconds
            if wlan.isconnected():
                IPLabel.set_text('WiFi IP: ' + wlan.ifconfig()[0])
                return wlan
            time.sleep(1)
        wlan.disconnect()  # Cleanly disconnect if failed to connect

    IPLabel.set_text('Failed to connect to all networks.')
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
        IPLabel.set_text('Public IP: ' + public_ip)
        return public_ip
    except Exception as e:
        IPLabel.set_text('Error getting IP: ' + str(e))
        return None


def update_sensor_readings():
    temp_value_label.set_text(str(round(env3_0.temperature)) + " °C")
    humidity_value_label.set_text(str(round(env3_0.humidity)) + " %")

def get_forecast(ip):
    try:
        response = urequests.post("http://192.168.0.103:8080/future-weather", json={"ip": ip})
        if response.status_code == 200:
            forecast_data = response.json()
            display_forecast(forecast_data.get('data'))
            outdoor_temp = forecast_data['current_weather']['main']['temp']
            outdoor_humidity = forecast_data['current_weather']['main']['humidity']  # Humidity percentage

            return outdoor_temp, outdoor_humidity   # Return the outdoor temperature for further use
        else:
            Forecast.set_text("Forecast fetch failed: HTTP " + str(response.status_code))
    except Exception as e:
        Forecast.set_text("Failed to fetch forecast: " + str(e))
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
        response = urequests.post("http://192.168.0.103:8080/send-to-bigquery", json=data)
    except Exception as e:
        Forecast.set_text("Failed to send data: " + str(e))
    finally:
        if response:
            response.close()

def display_forecast(data):
    try:
        if data and 'list' in data and data['list']:
            # Assuming that the data['list'] contains at least one forecast entry
            first_forecast = data['list'][0]
            weather_info = first_forecast['weather'][0]['description']
            forecast_str = "Forecast: " + weather_info
        else:
            # Handle cases where the forecast data might not be as expected
            forecast_str = "Forecast: No data available"
    except Exception as e:
        # Catch and handle any exceptions that occur when parsing the forecast data
        forecast_str = "Forecast Error: " + str(e)
    
    Forecast.set_text(forecast_str)
    
def main_loop():
    wlan = connect_wifi()
    if not wlan:
        print("Unable to connect to WiFi. Please check your settings.")
        return

    last_data_sent_time = time.ticks_ms()

    while True:
        update_sensor_readings()
        
        if time.ticks_diff(time.ticks_ms(), last_data_sent_time) >= 60000:
            public_ip = get_public_ip()
            if public_ip:
                outdoor_temp, outdoor_humidity = get_forecast(public_ip)  # This will also update the forecast on display
                if outdoor_temp is not None:
                    send_data(public_ip, outdoor_temp, outdoor_humidity)
            last_data_sent_time = time.ticks_ms()
        
        time.sleep(1)  # Update sensor readings every second

main_loop()







