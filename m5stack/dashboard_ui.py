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
screen.set_screen_bg_color(0xd5d5d5)

# Initialize the ENV3 unit connected to port A
env3_0 = unit.get(unit.ENV3, unit.PORTA)
# Initialize the PIR Motion sensor connected to port B
pir_sensor = unit.get(unit.PIR, unit.PORTB)
# Initialize the Gas unit connected to port C
gas_unit = unit.get(unit.TVOC, unit.PORTC)

# Create labels to display sensor values
IPLabel = M5Label('IP: Loading...', x=20, y=0, color=0x000)
env3_temp_label = M5Label('ENV3 Temp: ', x=20, y=30, color=0x000)
env3_hum_label = M5Label('ENV3 Humidity: ', x=20, y=50, color=0x000)
gas_label = M5Label('Gas TVOC: ', x=20, y=70, color=0x000)
motion_label = M5Label('Motion Detected: No', x=20, y=90, color=0x000)
outdoor_temp_label = M5Label('Outdoor Temp:', x=20, y=130, color=0x000)
outdoor_hum_label = M5Label('Outdoor Humidity.', x=20, y=150, color=0x000)

# WiFi credentials for connecting to the network
wifi_credentials = [('TP-Link_76C4', '49032826'),('iot-unil', '4u6uch4hpY9pJ2f9')]
flask_url = "http://192.168.0.103:8080"

def connect_wifi(wifi_credentials):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        get_public_ip()
        return wlan

    for ssid, password in wifi_credentials:
        try:
            wlan.connect(ssid, password)
            start_time = time.time()
            while time.time() - start_time < 10:  # Attendre 10 secondes pour la connexion
                if wlan.isconnected():
                    get_public_ip()
                    return wlan
                time.sleep(1)
            wlan.disconnect()  # Déconnecte proprement si la connexion échoue
        except OSError as e:
            IPLabel.set_text('Connection error: ' + str(e))
            continue
    return None

# Function to get the public IP address of the device
def get_public_ip():
    try:
        response = urequests.get('http://api.ipify.org/?format=text')
        public_ip = response.text
        response.close()
        IPLabel.set_text('Public IP: ' + public_ip)
        return public_ip
    except Exception as e:
        return None

def get_current_weather(ip):
    response = None  # Initialiser response ici pour garantir qu'elle est définie avant le bloc try
    try:
        url = "{}/current-weather".format(flask_url)
        response = urequests.post(url, json={"ip": ip})
        if response.status_code == 200:
            weather_data = response.json()
            outdoor_temp = weather_data['main']['temp']
            outdoor_humidity = weather_data['main']['humidity']
            icon_code = weather_data['weather'][0]['icon']
            return outdoor_temp, outdoor_humidity, icon_code
        else:
            outdoor_temp_label.set_text("Weather fetch failed: HTTP " + str(response.status_code))
            return None
    except Exception as e:
        outdoor_temp_label.set_text("Failed to fetch weather: " + str(e))
        return None
    finally:
        if response:
            response.close()


# Function to update sensor values and PIR state on the display
def update_display():
    env3_temp = env3_0.temperature 
    env3_hum = env3_0.humidity 
    gas_value = gas_unit.TVOC
    motion_detected = "Yes" if pir_sensor.state == 1 else "No"  # Check if motion is detected
    env3_temp_label.set_text('ENV3 Temp: {:.2f} C'.format(env3_temp))
    env3_hum_label.set_text('ENV3 Humidity: {:.2f} %'.format(env3_hum))
    gas_label.set_text('Gas TVOC: {} ppb'.format(gas_value))
    motion_label.set_text('Motion Detected: ' + motion_detected)

    current_weather = get_current_weather(get_public_ip())
    outdoor_hum_label.set_text('Outdoor Temp: {:.2f} C'.format(current_weather[0]))
    outdoor_temp_label.set_text('Outdoor Humidity: {:.2f} %'.format(current_weather[1]))
    imageplus0 = M5ImagePlus(200, 140, url='http://openweathermap.org/img/w/{}.png'.format(current_weather[1]), timer=True, interval=3000)


while True:
    connect_wifi(wifi_credentials)
    update_display()
    time.sleep(60)