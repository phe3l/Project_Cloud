from m5stack_ui import *
from uiflow import *
import network
import usocket as socket
import time
import unit
import urequests
import wifiCfg

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

# WiFi credentials
ssid = 'TP-Link_76C4_5G'
password = '49032826'

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(1)
    IPLabel.set_text('WiFi IP: ' + wlan.ifconfig()[0])
    return wlan

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

def send_data(ip):
    data = {
        "values": {
            "indoor_temp": round(env3_0.temperature),
            "indoor_humidity": round(env3_0.humidity),
            "ip_address": ip  # Include the IP address in the data sent
        }
    }
    try:
        response = urequests.post("http://192.168.0.106:8080/send-to-bigquery", json=data)
    except Exception as e:
        Forecast.set_text("Failed to send data: " + str(e))
    finally:
        if response:
            response.close()

def get_forecast(ip):
    try:
        response = urequests.post("http://192.168.0.106:8080/future-weather", json={"ip": ip})
        if response.status_code == 200:
            forecast_data = response.json()
            display_forecast(forecast_data["data"])
        else:
            Forecast.set_text("Forecast fetch failed: HTTP " + str(response.status_code))
    except Exception as e:
        Forecast.set_text("Failed to fetch forecast: " + str(e))
    finally:
        if response:
            response.close()
            
def get_forecast(ip):
    try:
        response = urequests.post("http://192.168.0.106:8080/future-weather", json={"ip": ip})
        if response.status_code == 200:
            forecast_data = response.json()
            display_forecast(forecast_data.get('data'))
            # Handle the outdoor temperature
            outdoor_temp = forecast_data.get('outdoor_temp', '0.0')
            print("Outdoor Temperature:", outdoor_temp)  # Example of using the outdoor temperature
        else:
            Forecast.set_text("Forecast fetch failed: HTTP " + str(response.status_code))
    except Exception as e:
        Forecast.set_text("Failed to fetch forecast: " + str(e))
    finally:
        if response:
            response.close()


def display_forecast(data):
    try:
        forecasts = data.get('list', [])
        if forecasts:
            # Extract the first forecast entry's weather description
            first_forecast = forecasts[0]
            weather_info = first_forecast['weather'][0]['description']
            forecast_str = "Forecast: " + weather_info
        else:
            forecast_str = "Forecast: No data available"
    except Exception as e:
        forecast_str = "Forecast Error: " + str(e)
    
    Forecast.set_text(forecast_str)

# Main program loop
while True:
    wlan = connect_wifi()
    public_ip = get_public_ip()
    send_data(public_ip)
    get_forecast(public_ip)
    temp_value_label.set_text(str(round(env3_0.temperature)) + " °C")
    humidity_value_label.set_text(str(round(env3_0.humidity)) + " %")
    wait(60)  # Delay for 1 minute before updating again








