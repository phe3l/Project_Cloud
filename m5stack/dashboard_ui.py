from m5stack_ui import *
from uiflow import *
import network
import usocket as socket
import time
import unit
import urequests
import ntptime
from machine import RTC
from libs.image_plus import *
import utime


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
date_time_label = M5Label('Date & Time: Loading...', x=20, y=110, color=0x000)
outdoor_temp_label = M5Label('Outdoor Temp:', x=20, y=130, color=0x000)
outdoor_hum_label = M5Label('Outdoor Humidity.', x=20, y=150, color=0x000)

# WiFi credentials for connecting to the network
wifi_credentials = [('TP-Link_76C4', '49032826'),('iot-unil', '4u6uch4hpY9pJ2f9')]
flask_url = "http://192.168.0.103:8080"

public_ip = None


def connect_wifi(wifi_credentials):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan
    for ssid, password in wifi_credentials:
        wlan.connect(ssid, password)
        start_time = time.time()
        while not wlan.isconnected() and time.time() - start_time < 10:
            time.sleep(1)
        if wlan.isconnected():
            return wlan
        wlan.disconnect()
    return None




# Function to get the public IP address of the device
def get_public_ip():
    global public_ip
    try:
        response = urequests.get('http://api.ipify.org/?format=text')
        public_ip = response.text
        response.close()
        IPLabel.set_text('Public IP: ' + public_ip)
    except Exception as e:
        IPLabel.set_text('Connection error: ' + str(e))


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

import socket
import struct

def get_ntp_time(host):
    NTP_DELTA = 3155673600  # 1900-01-01 00:00:00 to 2000-01-01 00:00:00
    NTP_QUERY = b'\x1b' + 47 * b'\0'
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.sendto(NTP_QUERY, addr)
        msg, _ = s.recvfrom(48)
    finally:
        s.close()
    val = struct.unpack('!I', msg[40:44])[0]
    return val - NTP_DELTA

def get_current_time():
    # Obtenez l'heure NTP
    ntp_time = get_ntp_time('ch.pool.ntp.org')  # Serveur NTP pour la Suisse

    # Ajoutez le décalage horaire (2 heures en standard, 3 heures en heure d'été)
    ntp_time += 2 * 3600  # Changez cela en 3 * 3600 si vous êtes en heure d'été

    # Convertissez l'heure NTP en heure locale
    local_time = utime.localtime(ntp_time)

    # Définissez l'heure du système
    rtc = RTC()
    rtc.datetime((local_time[0], local_time[1], local_time[2], 0, local_time[3], local_time[4], local_time[5], 0))

    # Mettez à jour le texte du label avec l'heure et la date
    date_time_label.set_text('Date & Time: {}/{}/{} {}:{}:{}'.format(local_time[0], local_time[1], local_time[2], local_time[3], local_time[4], local_time[5]))



def send_data(ip, outdoor_temp, outdoor_humidity):
    # Obtenez l'heure et la date actuelles
    local_time = utime.localtime()
    date = '{:04d}-{:02d}-{:02d}'.format(local_time[0], local_time[1], local_time[2])
    time = '{:02d}:{:02d}:{:02d}'.format(local_time[3], local_time[4], local_time[5])

    data = {
        "values": {
            "indoor_temp": env3_0.temperature,
            "indoor_humidity": env3_0.humidity,
            "ip_address": ip,
            "outdoor_temp": outdoor_temp,
            "outdoor_humidity": outdoor_humidity,
            "indoor_air_quality": gas_unit.TVOC,
            "date": date,
            "time": time
        }
    }
    try:
        url = "{}/send-to-bigquery".format(flask_url)
        response = urequests.post(url, json=data)
    except Exception as e:
        print("Failed to send data to BigQuery:", str(e))
    finally:
        if response:
            response.close()

# Function to update sensor values and PIR state on the display
def update_sensor_display():
    env3_temp = env3_0.temperature 
    env3_hum = env3_0.humidity 
    gas_value = gas_unit.TVOC
    motion_detected = "Yes" if pir_sensor.state == 1 else "No"  # Check if motion is detected
    env3_temp_label.set_text('ENV3 Temp: {:.2f} C'.format(env3_temp))
    env3_hum_label.set_text('ENV3 Humidity: {:.2f} %'.format(env3_hum))
    gas_label.set_text('Gas TVOC: {} ppb'.format(gas_value))
    motion_label.set_text('Motion Detected: ' + motion_detected)

def update_api_display(current_weather):
    outdoor_hum_label.set_text('Outdoor Temp: {:.2f} C'.format(current_weather[0]))
    outdoor_temp_label.set_text('Outdoor Humidity: {:.2f} %'.format(current_weather[1]))
    imageplus0 = M5ImagePlus(200, 140, url='http://openweathermap.org/img/w/{}.png'.format(current_weather[2]), timer=True, interval=3000)

# Fonction pour démarrer la boucle principale
def main_loop():
    global public_ip
    api_last_update = time.time() - 300  # Force immediate update at start

    while True:
        wlan = connect_wifi(wifi_credentials)
        if wlan:
            if public_ip is None:  # Obtient l'IP publique seulement si nécessaire
                get_public_ip()
            # Utilisez l'IP publique pour d'autres opérations ici, si nécessaire
            update_sensor_display()
            get_current_time()
            if time.time() - api_last_update > 300:
                current_weather = get_current_weather(public_ip)
                update_api_display(current_weather)
                api_last_update = time.time()

                send_data(public_ip, current_weather[0], current_weather[1])

        else:
            IPLabel.set_text('Failed to connect to WiFi')
            public_ip = None  # Réinitialisez l'IP publique si la connexion échoue
        time.sleep(1)

# Assurez-vous d'appeler main_loop() pour démarrer la boucle
main_loop()